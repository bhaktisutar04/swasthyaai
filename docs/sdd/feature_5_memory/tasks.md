# Tasks: Persistent Patient Memory (Vector DB)

## Module 1: Vector Database Setup
- [ ] **Task 1.1**: Create a Pinecone account and generate an API key. Add `PINECONE_API_KEY` and `PINECONE_INDEX_NAME` to `.env`.
- [ ] **Task 1.2**: Create a Pinecone index named `swasthyaai-patient-memory` with dimensions `384` (to match the `all-MiniLM-L6-v2` model) and metric `cosine`.
- [ ] **Task 1.3**: Add `pinecone-client` and `sentence-transformers` to `requirements.txt`.

## Module 2: Memory Service Implementation
- [ ] **Task 2.1**: Create `backend/memory/pinecone_service.py`. Initialize the Pinecone client and the global `SentenceTransformer` model.
- [ ] **Task 2.2**: Implement `store_session(user_id, session_id, summary_text)`. Embed the `summary_text`, construct the metadata dictionary, and upsert the vector to Pinecone.
- [ ] **Task 2.3**: Implement `retrieve_relevant_history(user_id, current_query)`. Embed the `current_query`, perform a similarity search with `filter={"user_id": user_id}`, and return a concatenated string of the top 3 matching summaries. Wrap in a try-except block to return an empty string if Pinecone fails.

## Module 3: Pipeline Integration
- [ ] **Task 3.1**: In `backend/crew/crew_runner.py`, update `run_pipeline_background`. At the very beginning, call `retrieve_relevant_history(user.id, query)`.
- [ ] **Task 3.2**: Modify the input parameters passed to `Agent 1` (Intake Specialist) to include a new `patient_history` variable containing the retrieved string.
- [ ] **Task 3.3**: At the end of `run_pipeline_background` (after successful DB commit), create a brief summary string formatted as: `Symptoms: [...]. Diagnosed: [...]. Prescribed: [...]`.
- [ ] **Task 3.4**: Asynchronously trigger `store_session(user.id, consultation_id, summary_string)` so the user's frontend is not blocked waiting for the Pinecone upsert to finish.
