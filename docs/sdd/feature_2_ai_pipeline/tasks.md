# Tasks: Multi-Agent AI Consultation Pipeline

## Module 1: AI Agent Configuration
- [ ] **Task 1.1**: Define `Agent 1` (Intake Specialist) in `backend/agents/agent1_intake.py`. Draft the prompt to enforce outputting a JSON object containing `symptoms` array, `severity` score, and `emergency_flag`.
- [ ] **Task 1.2**: Define `Agent 2` (Medical Analyst) in `backend/agents/agent2_diagnosis.py`. Draft the prompt to intake Agent 1's JSON and output a JSON containing `conditions`, `medicines` (with predefined estimated costs), and `red_flags`.
- [ ] **Task 1.3**: Define `Agent 3` (Clinical Dietitian) in `backend/agents/agent3_nutrition.py`. Draft the prompt to enforce Indian-specific meal plans based on `diet_pref` and output a JSON array representing the 7-day plan and `nutrition_focus` areas.
- [ ] **Task 1.4**: Define `Agent 4` (Finance Advisor) in `backend/agents/agent4_finance.py`. Draft the prompt to aggregate medicine costs and output a `monthly_total` and `savings_estimate`.

## Module 2: CrewAI Orchestration
- [ ] **Task 2.1**: Set up the Crew in `backend/crew/crew_runner.py`. Instantiate the Groq LLM client (`llama-3.3-70b-versatile`).
- [ ] **Task 2.2**: Define the sequential CrewAI `Process` that passes the output of Agent 1 to Agent 2, and so on.
- [ ] **Task 2.3**: Implement a JSON cleaning utility function within the runner to strip markdown formatting (e.g., ```json) from the LLM's final output.

## Module 3: API & Background Processing
- [ ] **Task 3.1**: Create the `POST /consultation/start` route. It should generate a UUID, create a pending record in the `Consultation` table, and trigger the CrewAI pipeline via FastAPI `BackgroundTasks`.
- [ ] **Task 3.2**: Implement the background worker function `run_pipeline_background` that executes the Crew, parses the final JSON, updates the `Consultation` record with the granular data (symptoms, conditions, meal_plan, etc.), and sets status to "completed". Implement `try-except` for LLM failures.
- [ ] **Task 3.3**: Create the `GET /consultation/{session_id}` endpoint to allow the frontend to poll for the status and retrieve the final data.

## Module 4: Frontend Integration
- [ ] **Task 4.1**: Create `consultation.js`. Implement the form submission to send the natural language query to `/consultation/start`.
- [ ] **Task 4.2**: Implement a polling mechanism (e.g., `setInterval`) in the frontend to check the status of the consultation every 3 seconds until it returns "completed".
- [ ] **Task 4.3**: Display a visually engaging loading screen outlining the 4 steps (Intake -> Diagnosis -> Nutrition -> Finance) to keep the user informed during the 45-60 second wait time.
