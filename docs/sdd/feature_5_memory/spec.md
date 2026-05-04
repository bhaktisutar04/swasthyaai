# Specification: Persistent Patient Memory (Vector DB)

## 1. Feature Overview
To provide a holistic and continuous healthcare experience, SwasthyaAI implements "Patient Memory". Instead of treating every consultation as a blank slate, the system condenses and stores past clinical sessions in a vector database. When a user initiates a new consultation, relevant historical data is retrieved and fed to the AI pipeline to provide context-aware diagnostics.

## 2. Behavioral Specification

### 2.1 Memory Storage (Post-Consultation)
- **Behavior**: Upon successful completion of a consultation, the system summarizes the session and stores it securely.
- **Rules**:
  - The summary must condense the symptoms, final diagnosis, and prescribed medicines into a concise string.
  - This string is embedded into a high-dimensional vector.
  - The vector is stored in Pinecone with metadata linking it exclusively to the specific `user_id` and `consultation_id`.

### 2.2 Context Retrieval (Pre-Consultation)
- **Behavior**: Before passing a new query to Agent 1 (Intake), the system queries the vector database for clinically similar or relevant past sessions.
- **Rules**:
  - The user's new query is embedded into a vector.
  - A similarity search is performed in Pinecone, strictly filtered by the current `user_id` to ensure absolute data privacy.
  - If a relevant history is found (similarity score above a certain threshold), it is prepended as context to the AI pipeline's prompt.
  - If no history is found, the consultation proceeds normally.

## 3. Data Models & Database Schema

*(No new relational tables are created. This relies on external Vector DB architecture).*

### Pinecone Metadata Schema
When storing a vector, the following metadata dictionary must be attached:
```json
{
  "user_id": 1,
  "consultation_id": "uuid-1234",
  "date": "2026-05-04",
  "summary_text": "Patient reported fever. Diagnosed with Viral Infection. Prescribed Paracetamol."
}
```

## 4. API Contracts
*(This feature operates internally during the `POST /consultation/start` route and does not expose new frontend endpoints).*

### Internal Integration Flow
1. User calls `POST /consultation/start` with `"Severe headache again."`
2. Backend calls `memory.retrieve_context(user_id, "Severe headache again.")`
3. Memory module returns: `["Last month: Diagnosed with Migraine. Prescribed Ibuprofen."]`.
4. Backend injects this string into the CrewAI input parameters.

## 5. UI Flows & Screen Descriptions
- **Invisible to User**: This feature operates entirely in the background. The only UI impact is that the AI's diagnostic response may explicitly reference past history (e.g., "Given your previous history of migraines...").

## 6. Edge Cases & Error Handling
- **Pinecone Outage**: If the Pinecone API is unreachable or times out, the backend must catch the exception, log the error, and allow the consultation to proceed without historical context rather than failing the entire request.
- **Data Leakage Risk**: It is absolutely critical that the Pinecone query explicitly includes a metadata filter for `user_id == current_user.id`. Failure to do so would leak other patients' medical histories.
