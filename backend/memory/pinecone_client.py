import os
import logging
import requests
from dotenv import load_dotenv
from pinecone import Pinecone

# Setup logger for fail-safes
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "swasthyaai-patient-memory")

HF_API_KEY = os.getenv("HF_API_KEY")
HF_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
HF_API_URL = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{HF_MODEL}"

def embed(text: str) -> list:
    """Embed text using HuggingFace Inference API."""
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {"inputs": text, "options": {"wait_for_model": True}}
    try:
        response = requests.post(
            HF_API_URL,
            headers=headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        if isinstance(result[0], list):
            return result[0]
        return result
    except requests.exceptions.Timeout:
        logger.error("HuggingFace model is waking up, please retry in 30 seconds")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"Embedding API failed: {str(e)}")
        return []


# Initialize Pinecone Client
try:
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(PINECONE_INDEX_NAME)
except Exception as e:
    logger.error(f"Failed to initialize Pinecone: {e}")
    index = None

def get_patient_memory(user_id: int, top_k: int = 3) -> list:
    """
    Retrieve past patient memory/summaries directly from Pinecone vector DB.
    Never crashes the app if connection to Pinecone drops.
    """
    if not index:
        logger.error("Pinecone index is not available.")
        return []
    
    try:
        query_text = f"patient {user_id} health history"
        query_vector = embed(query_text)
        
        if not query_vector:
            return []
            
        result = index.query(
            vector=query_vector,
            filter={"user_id": {"$eq": str(user_id)}},
            top_k=top_k,
            include_metadata=True
        )
        
        summaries = []
        if result and "matches" in result:
            for match in result.get("matches", []):
                metadata = match.get("metadata", {})
                if "summary" in metadata:
                    summaries.append(metadata["summary"])
                    
        return summaries
    except Exception as e:
        logger.error(f"Error retrieving pinecone memory for user_id={user_id}: {e}")
        return []

def store_session_summary(user_id: int, session_id: str, summary: str, metadata: dict) -> None:
    """
    Stores an embedded session summary snippet into Pinecone.
    """
    if not index:
        logger.error("Pinecone index is not available.")
        return
        
    try:
        vector = embed(summary)
        if not vector:
            return
            
        upsert_metadata = {**metadata, "user_id": str(user_id), "summary": summary}
        
        index.upsert(
            vectors=[{
                "id": session_id,
                "values": vector,
                "metadata": upsert_metadata
            }]
        )
    except Exception as e:
        logger.error(f"Error storing pinecone summary [user_id={user_id}, session_id={session_id}]: {e}")

