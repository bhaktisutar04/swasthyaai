# SwasthyaAI — Implementation Plan
**Version:** 1.0  
**Date:** 2026  
**Author:** Solo Developer  
**Document:** SDD Section 7 of 7

---

## 1. Overview

This is the build order. Follow it exactly — every sprint builds on the previous one. Do not jump ahead. The system is built bottom-up: database → auth → agents → API → frontend → PDF → deploy.

**Total MVP: 7 sprints**  
**Time estimate per sprint:** 1–3 days depending on complexity

---

## 2. Pre-Build Setup (Do This First)

Before writing any code, complete these steps:

### 2.1 Project Folder

```bash
mkdir SwasthyaAI
cd SwasthyaAI
mkdir docs backend frontend
mkdir backend/agents backend/routes backend/models backend/db backend/memory backend/pdf backend/data
mkdir frontend/css frontend/js
```

### 2.2 Python Environment

```bash
cd backend
python -m venv venv
source venv/bin/activate       # Mac/Linux
# venv\Scripts\activate        # Windows

pip install fastapi uvicorn[standard] python-jose[cryptography] bcrypt \
            crewai langchain-groq pinecone-client reportlab requests \
            pydantic[email] python-dotenv sentence-transformers
```

### 2.3 `.env` File

```bash
# backend/.env
GROQ_API_KEY=your_groq_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX_NAME=swasthyaai-patient-memory
JWT_SECRET_KEY=generate_a_random_64_char_string_here
JWT_ALGORITHM=HS256
JWT_ACCESS_EXPIRE_MINUTES=1440
JWT_REFRESH_EXPIRE_DAYS=7
DATABASE_URL=sqlite:///./swasthyaai.db
APP_ENV=development
PDF_STORAGE_PATH=./pdfs/
```

### 2.4 `.gitignore`

```
.env
*.db
/pdfs/
__pycache__/
venv/
.venv/
*.pyc
.DS_Store
```

### 2.5 Pinecone Setup (one-time)

```python
# Run this once to create the Pinecone index
import pinecone
pc = pinecone.Pinecone(api_key=PINECONE_API_KEY)
pc.create_index(
    name="swasthyaai-patient-memory",
    dimension=384,        # all-MiniLM-L6-v2 output size
    metric="cosine",
    spec=pinecone.ServerlessSpec(cloud="aws", region="us-east-1")
)
```

---

## 3. Sprint 1 — Database & Auth Backend

**Goal:** Working register + login API with SQLite.

### Tasks

1. Create `backend/db/database.py`
   - SQLite connection with SQLAlchemy
   - Create all tables: `users`, `consultations`, `expenses`, `refresh_tokens`, `notifications`

2. Create `backend/models/schemas.py`
   - Pydantic models: `RegisterRequest`, `LoginRequest`, `ExpenseRequest`

3. Create `backend/auth/password.py`
   - `hash_password()` and `verify_password()` using bcrypt

4. Create `backend/auth/jwt_handler.py`
   - `create_access_token()`, `create_refresh_token()`, `decode_token()`

5. Create `backend/auth/rate_limiter.py`
   - In-memory rate limiting (5 attempts / 15 min)

6. Create `backend/auth/dependencies.py`
   - `get_current_user()` FastAPI dependency

7. Create `backend/routes/auth.py`
   - `POST /auth/register`
   - `POST /auth/login`
   - `POST /auth/refresh`
   - `POST /auth/logout`
   - `GET /auth/me`
   - `PATCH /auth/profile`

8. Create `backend/main.py`
   - FastAPI app setup with CORS
   - Register all routers

### Test Sprint 1

```bash
cd backend
uvicorn main:app --reload
# Open: http://localhost:8000/docs
# Test register and login via Swagger UI
```

**Sprint 1 is done when:** You can register a user, log in, get a JWT, and use it to hit `GET /auth/me` successfully.

---

## 4. Sprint 2 — Agent 1 (Symptom Intake)

**Goal:** Working Agent 1 that takes a message and returns a structured symptom JSON via FastAPI.

### Tasks

1. Create `backend/agents/agent1_intake.py`
   - Define the CrewAI agent with role, goal, backstory
   - Write the system prompt (from 03_agent_design.md)
   - Implement `emergency_detector_tool`
   - Implement `nominatim_hospital_tool`
   - Implement `pinecone_memory_tool`

2. Create `backend/memory/pinecone_client.py`
   - `get_patient_memory(user_id, top_k)` — query Pinecone
   - `store_session_summary(user_id, session_id, summary, metadata)` — upsert to Pinecone

3. Create `backend/routes/consultation.py`
   - `POST /consultation/start` — load patient profile, greet user
   - `POST /consultation/message` — route message to Agent 1, return response

4. Create a session manager (in-memory dict for now)
   - `sessions = {}` — keyed by `session_id`
   - Stores `patient_profile` during active session

### Test Sprint 2

- Start a consultation via API
- Send a normal symptom message → agent asks follow-up question
- Send "I have chest pain" → emergency response with hospitals

**Sprint 2 is done when:** Agent 1 holds a natural conversation and correctly populates the symptom JSON.

---

## 5. Sprint 3 — Agent 2 (Diagnosis)

**Goal:** Agent 2 takes the symptom JSON from Agent 1 and returns a diagnosis JSON.

### Tasks

1. Create `backend/agents/agent2_diagnosis.py`
   - Define CrewAI agent with system prompt
   - No external tools needed — pure LLM reasoning

2. Update `backend/crew/crew_runner.py`
   - Connect Task 1 (Agent 1) → Task 2 (Agent 2) with `context=[task1]`
   - Run the 2-agent crew in sequence

3. Update `backend/routes/consultation.py`
   - After Agent 1 completes → trigger Agent 2 automatically
   - Store diagnosis output back into `patient_profile`

4. Create `backend/routes/consultation.py`
   - `GET /consultation/report/{session_id}` — return full patient_profile as structured JSON (partial — agents 3+4 not done yet)

### Test Sprint 3

- Complete a full 2-agent session (symptom intake → diagnosis)
- Verify diagnosis JSON has conditions, medicines, severity_flag
- Verify `see_doctor` boolean is set correctly

**Sprint 3 is done when:** A full 2-agent pipeline runs and returns a structured diagnosis.

---

## 6. Sprint 4 — Agent 3 (Nutrition) + IFCT Dataset

**Goal:** Agent 3 generates a 7-day Indian meal plan based on the diagnosis.

### Tasks

1. Build `backend/data/ifct_nutrition.json`
   - Collect 50–100 common Indian foods with macros/micros from IFCT 2017
   - Include: iron, protein, vitamin C, B12, calcium, calories
   - Tag each food: `diet_type: veg | non-veg | vegan`

2. Create `backend/agents/agent3_nutrition.py`
   - Define CrewAI agent with system prompt
   - Implement `ifct_nutrition_tool`
   - Implement dietary filtering (veg/non-veg/vegan) + allergy exclusion

3. Update `backend/crew/crew_runner.py`
   - Add Task 3 with `context=[task2]`

4. Create `backend/routes/nutrition.py`
   - `POST /nutrition/log-meal`
   - `GET /nutrition/trends`

### Test Sprint 4

- Run 3-agent pipeline for a patient with Iron deficiency
- Verify meal plan contains only veg foods (for veg patients)
- Verify allergen exclusion works
- Verify 7 days are present

**Sprint 4 is done when:** A 3-agent pipeline produces a valid 7-day Indian meal plan.

---

## 7. Sprint 5 — Agent 4 (Finance) + PDF Generation

**Goal:** Agent 4 calculates expenses and generates the final PDF report.

### Tasks

1. Create `backend/agents/agent4_finance.py`
   - Define CrewAI agent
   - Implement `expense_summary_tool` (reads from SQLite)
   - Implement savings projection formula
   - Implement `pdf_generator_tool`

2. Create `backend/pdf/report_generator.py`
   - ReportLab PDF template
   - 5 sections: Patient Info, Symptoms, Diagnosis, Nutrition, Finance
   - Medical disclaimer in header and footer
   - Save to `/pdfs/` folder
   - Return file path

3. Update `backend/crew/crew_runner.py`
   - Add Task 4 with `context=[task2, task3]`
   - Full 4-agent crew runs sequentially

4. Create `backend/routes/finance.py`
   - `POST /finance/add-expense`
   - `GET /finance/summary`

5. Update `backend/routes/consultation.py`
   - `GET /consultation/report/{session_id}/pdf` — stream PDF file

### Test Sprint 5

- Run full 4-agent pipeline
- Verify PDF is generated with all 5 sections
- Verify PDF file downloads correctly via API

**Sprint 5 is done when:** Full 4-agent pipeline runs and produces a downloadable PDF.

---

## 8. Sprint 6 — Frontend (All 7 Screens)

**Goal:** Complete HTML/CSS/JS frontend connected to the FastAPI backend.

### Build Order Within Sprint 6

Build screens in this exact order (each depends on the previous):

| Step | Screen | File |
|---|---|---|
| 6.1 | Shared styles | `css/style.css` |
| 6.2 | Shared utilities | `js/utils.js` |
| 6.3 | Login / Register | `index.html` + `js/auth.js` |
| 6.4 | Dashboard | `dashboard.html` + `js/dashboard.js` |
| 6.5 | Consultation Chat | `consultation.html` + `js/consultation.js` |
| 6.6 | Health Report | `report.html` + `js/report.js` |
| 6.7 | Nutrition | `nutrition.html` + `js/nutrition.js` |
| 6.8 | Expenses | `expenses.html` + `js/expenses.js` |
| 6.9 | History | `history.html` + `js/history.js` |

### For Each Screen

1. Write the HTML structure
2. Connect to backend API via `fetch()`
3. Handle loading, empty, and error states
4. Add route guard (`requireAuth()`) on every protected page
5. Test manually in browser with Live Server

### Test Sprint 6

- Complete end-to-end flow: Register → Login → Start Consultation → Chat → Report → Download PDF
- Test all 7 screens manually
- Test on mobile screen size (375px width)
- Test empty states (new user with no history)
- Test error states (disconnect backend, check error messages)

**Sprint 6 is done when:** A real user can complete the full journey from login to PDF download through the browser.

---

## 9. Sprint 7 — History, Dashboard, Deploy

**Goal:** Complete history screen, analytics endpoints, and deploy to free hosting.

### Tasks

1. Create `backend/routes/history.py`
   - `GET /history` with pagination
   - `GET /history/analytics/nutrition`
   - `GET /history/analytics/expenses`

2. Create `backend/routes/dashboard.py`
   - `GET /dashboard` — aggregate all data in one call

3. Complete `history.html` and `js/history.js`
   - Timeline view with pagination
   - Trends tab with Chart.js charts

4. Test Pinecone memory
   - Complete 2 consultations
   - On 3rd consultation, verify Agent 1 references past history

5. Deploy backend to Render (free tier)
   - Create `render.yaml`
   - Push to GitHub
   - Connect to Render

6. Deploy frontend to GitHub Pages
   - Update `API_BASE` in `utils.js` to production URL
   - Push `frontend/` folder to GitHub Pages

### Render Deploy Config

```yaml
# render.yaml
services:
  - type: web
    name: swasthyaai-backend
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: GROQ_API_KEY
        sync: false
      - key: PINECONE_API_KEY
        sync: false
      - key: JWT_SECRET_KEY
        sync: false
```

**Sprint 7 is done when:** The app is live on a public URL and a full end-to-end test passes on production.

---

## 10. Phase 2 Features (After MVP)

Build these only after the MVP is fully working and deployed:

| # | Feature | Complexity | Notes |
|---|---|---|---|
| P2.1 | Hindi / Marathi language support | Medium | Change Groq system prompt to respond in user's language |
| P2.2 | Pinecone persistent memory | Medium | Already scaffolded — just needs testing |
| P2.3 | Weekly nutrition trend charts | Low | Backend data already collected, just render charts |
| P2.4 | Nearby doctor finder | Low | Nominatim already used for hospitals — extend for doctors |
| P2.5 | Profile Settings screen | Low | PATCH /auth/profile already built |
| P2.6 | Notification system | Medium | `notifications` table already created |
| P2.7 | WhatsApp PDF sharing | Low | `navigator.share()` Web API |
| P2.8 | CSV expense export | Low | Generate CSV from finance data |

---

## 11. Build Checklist

Use this to track your progress:

### Sprint 1 — Auth
- [ ] SQLite tables created
- [ ] bcrypt password hashing works
- [ ] JWT access + refresh tokens generated
- [ ] POST /auth/register works
- [ ] POST /auth/login works
- [ ] POST /auth/logout revokes token
- [ ] GET /auth/me returns user profile
- [ ] Rate limiting (5 attempts/15min) works

### Sprint 2 — Agent 1
- [ ] CrewAI + Groq connected
- [ ] Agent 1 holds natural conversation
- [ ] Emergency keyword detection works
- [ ] Nominatim hospital search returns results
- [ ] Symptom JSON is correctly structured
- [ ] POST /consultation/start works
- [ ] POST /consultation/message works

### Sprint 3 — Agent 2
- [ ] Agent 2 receives symptom JSON
- [ ] Returns 1-3 ranked conditions
- [ ] Severity flag set correctly
- [ ] see_doctor boolean works
- [ ] Medical disclaimer included in output

### Sprint 4 — Agent 3
- [ ] IFCT dataset loaded (50+ foods)
- [ ] Allergen filtering works
- [ ] Diet preference filtering works (veg/non-veg/vegan)
- [ ] 7-day meal plan generated
- [ ] Deficiency detection linked to diagnosis

### Sprint 5 — Agent 4 + PDF
- [ ] Expense summary reads from SQLite
- [ ] Savings projection calculated correctly
- [ ] PDF generates with all 5 sections
- [ ] Medical disclaimers in PDF
- [ ] PDF downloads via browser

### Sprint 6 — Frontend
- [ ] Register form validates all fields
- [ ] Login stores JWT correctly
- [ ] Dashboard loads all widgets
- [ ] Chat interface streams responses
- [ ] Emergency modal shows with hospitals
- [ ] Report screen shows 4 sections
- [ ] PDF download button works
- [ ] Collapsible sections work
- [ ] Nutrition day navigator works
- [ ] Expense form validates + submits
- [ ] History timeline shows past sessions
- [ ] Route guards block unauthenticated access
- [ ] Idle timer logs out after 30 min
- [ ] All screens work on mobile (375px)

### Sprint 7 — Deploy
- [ ] History pagination works
- [ ] Dashboard aggregates correctly
- [ ] Pinecone memory carries across sessions
- [ ] Backend deployed to Render
- [ ] Frontend deployed to GitHub Pages
- [ ] End-to-end test on production passes

---

## 12. File Creation Order (Copy-Paste Reference)

```
Sprint 1:
  backend/db/database.py
  backend/models/schemas.py
  backend/auth/password.py
  backend/auth/jwt_handler.py
  backend/auth/rate_limiter.py
  backend/auth/dependencies.py
  backend/routes/auth.py
  backend/main.py

Sprint 2:
  backend/memory/pinecone_client.py
  backend/agents/agent1_intake.py
  backend/routes/consultation.py  (partial)

Sprint 3:
  backend/agents/agent2_diagnosis.py
  backend/crew/crew_runner.py  (tasks 1+2)
  backend/routes/consultation.py  (update)

Sprint 4:
  backend/data/ifct_nutrition.json
  backend/agents/agent3_nutrition.py
  backend/crew/crew_runner.py  (add task 3)
  backend/routes/nutrition.py

Sprint 5:
  backend/agents/agent4_finance.py
  backend/pdf/report_generator.py
  backend/crew/crew_runner.py  (add task 4, full crew)
  backend/routes/finance.py
  backend/routes/consultation.py  (add PDF endpoint)

Sprint 6:
  frontend/css/style.css
  frontend/js/utils.js
  frontend/index.html + frontend/js/auth.js
  frontend/dashboard.html + frontend/js/dashboard.js
  frontend/consultation.html + frontend/js/consultation.js
  frontend/report.html + frontend/js/report.js
  frontend/nutrition.html + frontend/js/nutrition.js
  frontend/expenses.html + frontend/js/expenses.js
  frontend/history.html + frontend/js/history.js

Sprint 7:
  backend/routes/history.py
  backend/routes/dashboard.py
  render.yaml
  requirements.txt
```

---

*Previous: [06_security_design.md](./06_security_design.md)*  
*This is the final SDD document. Begin Sprint 1.*
