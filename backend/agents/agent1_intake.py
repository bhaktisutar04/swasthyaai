import os
import json
import requests
from dotenv import load_dotenv
from crewai import Agent, Task
from crewai.tools import tool
from crewai import LLM
from memory.pinecone_client import get_patient_memory

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

llm = LLM(
    model="groq/llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.3
)

@tool("emergency_detector_tool")
def emergency_detector_tool(message: str) -> dict:
    """Detects emergency keywords in a patient's message."""
    message_lower = message.lower()
    
    keywords = {
        "english": [
            "chest pain", "heart attack", "can't breathe", 
            "difficulty breathing", "severe bleeding", "unconscious", 
            "seizure", "stroke", "suicidal", "want to die", "end my life"
        ],
        "hindi": [
            "seene mein dard", "saans nahi aa raha", "behosh", "khud ko khatam"
        ],
        "marathi": [
            "chhati dukhte", "shwas ghet nahi", "shudh haralo"
        ]
    }
    
    for lang, kws in keywords.items():
        for kw in kws:
            if kw in message_lower:
                return {
                    "emergency_detected": True,
                    "keyword": kw,
                    "language": lang
                }
                
    return {
        "emergency_detected": False,
        "keyword": None,
        "language": None
    }

@tool("nominatim_hospital_tool")
def nominatim_hospital_tool(city: str) -> list:
    """Finds up to 3 nearby hospitals in a given city in India."""
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": f"hospital in {city}, India",
            "format": "json",
            "limit": 3,
            "addressdetails": 1
        }
        headers = {"User-Agent": "SwasthyaAI/1.0"}
        
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        hospitals = []
        for item in data:
            lat = item.get("lat")
            lon = item.get("lon")
            hospitals.append({
                "name": item.get("name", "Unknown Hospital"),
                "address": item.get("display_name", "Unknown Address"),
                "lat": lat,
                "lon": lon,
                "maps_link": f"https://www.google.com/maps/place/{lat},{lon}"
            })
        return hospitals
    except Exception as e:
        print(f"Error finding hospitals: {e}")
        return []

@tool("pinecone_memory_tool")
def pinecone_memory_tool(user_id: int) -> list:
    """Retrieves patient's past medical history from vector database."""
    try:
        # Cast to int to ensure correct underlying database typing
        return get_patient_memory(int(user_id), top_k=3)
    except Exception as e:
        print(f"Error fetching memory for user {user_id}: {e}")
        return []

agent1 = Agent(
    role="Patient Interaction Specialist",
    goal="Collect complete structured symptom profile through empathetic conversation",
    backstory="""You are a compassionate AI health assistant for Indian patients.
    You ask intelligent follow-up questions, detect emergencies immediately,
    and respond in the patient's preferred language (English, Hindi, Marathi).
    You never diagnose — that is Agent 2's job. Your job is to listen and collect.""",
    llm=llm,
    tools=[emergency_detector_tool, nominatim_hospital_tool, pinecone_memory_tool],
    verbose=True,
    allow_delegation=False
)

def create_agent1_task(patient_profile: dict) -> Task:
    name = patient_profile.get("name", "Patient")
    language = patient_profile.get("language", "english")
    user_id = patient_profile.get("user_id", "")
    
    description = f"""Greet the patient {name} in {language}.
Ask about their symptoms through natural conversation.
Ask follow-up questions: duration, severity (1-10), associated symptoms,
recent diet changes, current medications.
Detect any emergencies using the emergency_detector tool.
Load past medical history from Pinecone for user_id {user_id}.

NEVER diagnose. NEVER suggest medicines.

Once enough info is collected, output ONLY this JSON:
{{
    "symptoms": ["symptom1"],
    "duration": "X days",
    "severity": 6,
    "associated_symptoms": [],
    "current_medications": [],
    "dietary_changes": false,
    "travel_history": false,
    "emergency_flag": false,
    "language_used": "{language}"
}}"""

    return Task(
        description=description,
        expected_output="Valid JSON with all symptom fields populated.",
        agent=agent1
    )


