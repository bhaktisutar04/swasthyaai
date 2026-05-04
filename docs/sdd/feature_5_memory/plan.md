# Technical Plan: Persistent Patient Memory (Vector DB)

## 1. Architecture Overview

```text
[ CrewAI Pipeline (Completed) ]
        |
        v
[ Session Summarizer (LLM) ] ---> string
                                     |
                                     v
[ Embedding Model (Sentence-Transformers) ] ---> vector [0.12, 0.45...]
                                     |
                                     v
[ Pinecone Vector Database (Index: swasthyaai-patient-memory) ]

-------------------------------------------------------------------

[ New Consultation Request ] ---> [ Embedding Model ] ---> vector
                                     |
                                     v
[ Pinecone Vector Database ] <--- (Similarity Search + user_id filter)
        |
        v
[ Retrieved Context Strings ] ---> [ CrewAI Pipeline (Input) ]
```

## 2. Tech Stack & Rationale
- **Pinecone**: A fully managed, cloud-native vector database. Chosen for its extremely low latency in nearest-neighbor searches and built-in support for metadata filtering (essential for isolating user data).
- **Sentence-Transformers (`all-MiniLM-L6-v2`)**: A lightweight, fast, and open-source embedding model that runs locally. It converts medical summaries into dense vectors without incurring external API costs (like OpenAI embeddings would).
- **LLM Summarization**: Uses the existing Groq client to condense verbose consultation results into a single paragraph before embedding, saving vector storage space and improving search relevance.

## 3. Component Breakdown
1. **Memory Service Module (`backend/memory/pinecone_service.py`)**:
   - `init_pinecone()`: Connects to the Pinecone index using the API key from `.env`.
   - `get_embedding(text)`: Runs the text through the local `sentence-transformers` model.
   - `store_session(user_id, session_id, summary)`: Embeds the summary, attaches metadata, and upserts to Pinecone.
   - `retrieve_relevant_history(user_id, query)`: Embeds the current query, searches Pinecone with a metadata filter (`{"user_id": user_id}`), and returns the top 3 results.
2. **Integration with CrewRunner (`backend/crew/crew_runner.py`)**:
   - **Pre-execution**: Calls `retrieve_relevant_history` and injects the resulting string into the prompt context for Agent 1.
   - **Post-execution**: Extracts the final `symptoms`, `conditions`, and `medicines`, formats them into a short string, and asynchronously calls `store_session`.

## 4. Dependencies & Risks
### Dependencies
- `pinecone-client`: For interacting with the Pinecone API.
- `sentence-transformers`: For local text-to-vector embeddings.
- `torch`: Required backend for sentence-transformers.

### Risks & Mitigations
- **Risk**: Server memory bloat from loading the `sentence-transformers` model into RAM.
  - **Mitigation**: Use the highly optimized, lightweight `all-MiniLM-L6-v2` model. Ensure the model is loaded globally once upon server startup, rather than instantiated on every API call.
- **Risk**: Pinecone index dimensionality mismatch.
  - **Mitigation**: Ensure the Pinecone index is explicitly created with dimensions matching the embedding model (e.g., 384 dimensions for `MiniLM`). Document this requirement in deployment guides.
