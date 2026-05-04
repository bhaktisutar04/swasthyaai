# Technical Plan: Multi-Agent AI Consultation Pipeline

## 1. Architecture Overview

```text
[ User Query ] -> [ POST /consultation/start ]
                        |
                        v
        [ Background Task: CrewRunner ]
                        |
          +-------------+-------------+
          |                           |
[ Agent 1: Intake ]          [ Agent 2: Diagnosis ]
  (Extracts JSON)              (Maps Conditions)
          |                           |
[ Agent 3: Nutrition ]       [ Agent 4: Finance ]
  (Indian Meal Plan)           (Cost Estimation)
          |                           |
          +-------------+-------------+
                        |
            [ Database: Update Consultation ]
```

## 2. Tech Stack & Rationale
- **CrewAI**: Provides a robust framework for orchestrating multiple AI agents, allowing them to pass contextual data (like symptoms -> diagnosis -> nutrition) sequentially.
- **Groq API (`llama-3.3-70b-versatile`)**: Chosen for its ultra-fast inference speeds, ensuring that a 4-agent sequential pipeline completes within an acceptable user wait time (sub-60 seconds).
- **FastAPI BackgroundTasks**: Allows the HTTP endpoint to return immediately with a `consultation_id`, freeing up the client while the heavy LLM processing happens asynchronously.
- **JSON Structured Output**: Forces LLMs to output parsable JSON rather than free text, ensuring seamless mapping to database columns and frontend UI components.

## 3. Component Breakdown
1. **Agent Prompts & Tasks (`backend/agents/`)**:
   - `agent1_intake.py`: Defines the Intake Specialist prompt.
   - `agent2_diagnosis.py`: Defines the Medical Analyst prompt, including the Indian medicine price mapping logic.
   - `agent3_nutrition.py`: Defines the Clinical Dietitian prompt, enforcing regional Indian diets.
   - `agent4_finance.py`: Defines the Health Finance Advisor prompt.
2. **Crew Orchestration (`backend/crew/crew_runner.py`)**: The `run_pipeline_background` function that assembles the Crew, executes it, catches exceptions, and parses the final JSON string into a Python dictionary.
3. **Database Integration (`backend/db/database.py`)**: Saving the parsed pipeline output into the respective columns of the `Consultation` model.
4. **API Routes (`backend/routes/consultation.py`)**: Endpoints to trigger the pipeline and poll for status/results.

## 4. Dependencies & Risks
### Dependencies
- `crewai` and `langchain-groq` for orchestration and LLM access.
- Groq API Key must be securely managed in `.env`.

### Risks & Mitigations
- **Risk**: Hallucinations in medical diagnosis.
  - **Mitigation**: Strict prompt engineering requiring the AI to append "Possible" or "Less Likely" tags. Mandatory UI disclaimers stating the system is not a replacement for a doctor.
- **Risk**: LLM returning malformed JSON, breaking the parsing pipeline.
  - **Mitigation**: Use robust JSON extraction regex (`\{.*\}`) in the `crew_runner`. Implement fallback empty arrays if a specific key fails to parse.
- **Risk**: Long execution times causing user abandonment.
  - **Mitigation**: Implement frontend polling that shows a loading animation and updates the user on which agent is currently thinking.
