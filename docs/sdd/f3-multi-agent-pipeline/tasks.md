# F3 — Multi-Agent AI Pipeline (CrewAI): Tasks

> **Feature ID**: F3  
> **Status**: ✅ All Complete  
> **Last Updated**: 2026-05-05

---

## Task Checklist

### Agent 1 — Patient Interaction Specialist
- [x] **T3.1**: Define Agent 1 with role, goal, backstory, LLM config
- [x] **T3.2**: Implement `emergency_detector_tool` — keyword matching in English, Hindi, Marathi
- [x] **T3.3**: Implement `nominatim_hospital_tool` — OpenStreetMap hospital search with Google Maps links
- [x] **T3.4**: Implement `pinecone_memory_tool` — retrieve past medical history via vector search
- [x] **T3.5**: Implement `create_agent1_task()` — structured task prompt with expected JSON output format

### Agent 2 — Medical Diagnosis Specialist
- [x] **T3.6**: Define Agent 2 with role, goal, backstory, LLM config (no tools)
- [x] **T3.7**: Implement `create_agent2_task()` — prompt for ranked conditions, medicines, home care, red flags, severity
- [x] **T3.8**: Implement `parse_diagnosis_output()` — strip markdown fences, parse JSON, return defaults on failure

### Agent 3 — Indian Nutrition Specialist
- [x] **T3.9**: Define Agent 3 with role, goal, backstory, LLM config
- [x] **T3.10**: Implement `ifct_nutrition_tool` — search local IFCT 2017 JSON by food name (English + Hindi)
- [x] **T3.11**: Implement `create_agent3_task()` — prompt for 7-day meal plan with diet/allergy constraints
- [x] **T3.12**: Implement `parse_nutrition_output()` — parse JSON with defaults for empty meal plans

### Agent 4 — Medical Finance Analyst
- [x] **T3.13**: Define Agent 4 with role, goal, backstory, LLM config
- [x] **T3.14**: Implement `expense_summary_tool` — SQLite query for last month's expenses by category
- [x] **T3.15**: Implement `create_agent4_task()` — prompt for expense breakdown and savings calculation
- [x] **T3.16**: Implement `parse_finance_output()` — parse JSON with zero defaults

### Crew Orchestrator
- [x] **T3.17**: Implement `run_full_crew()` — execute 3 crews sequentially with 15s delays
- [x] **T3.18**: Implement `run_intake_crew()` — Agent 1 only execution
- [x] **T3.19**: Implement `run_diagnosis_crew()` — Agent 1 + 2 execution with context chaining
- [x] **T3.20**: Implement `run_nutrition_only()` — Agent 3 standalone execution

### Post-Pipeline Operations
- [x] **T3.21**: Implement `save_consultation_to_db()` — update Consultation record with all agent outputs
- [x] **T3.22**: Implement `save_to_pinecone()` — create summary text, embed, upsert to Pinecone
- [x] **T3.23**: Trigger PDF generation after all agents complete
- [x] **T3.24**: Update in-memory session dict with all computed data

### Vector Memory (Pinecone)
- [x] **T3.25**: Implement `embed()` — HuggingFace Inference API call with 60s timeout
- [x] **T3.26**: Implement `get_patient_memory()` — query Pinecone by user_id, return top 3 summaries
- [x] **T3.27**: Implement `store_session_summary()` — upsert vector with session metadata
- [x] **T3.28**: Initialize Pinecone client at module level with error handling

### Data Files
- [x] **T3.29**: Create/curate `ifct_nutrition.json` with Indian food items and per-100g nutrient data

---

## Verification

- [x] Full pipeline completes within 2-3 minutes for a typical consultation
- [x] Agent 2 produces ranked conditions with confidence percentages
- [x] Agent 3 generates 7-day meal plan respecting diet preferences
- [x] Agent 4 reads expense data from database
- [x] Consultation record updated in DB with all fields after pipeline
- [x] Session summary stored in Pinecone
- [x] Pipeline doesn't crash if individual agent fails (graceful defaults)
- [x] PDF generated and uploaded to Cloudinary
