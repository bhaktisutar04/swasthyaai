# SwasthyaAI — System Overview
**Version:** 1.0  
**Date:** 2026  
**Author:** Solo Developer  
**Document:** SDD Section 1 of 7

---

## 1. What is SwasthyaAI?

SwasthyaAI is an AI-powered virtual doctor system built specifically for Indian patients. It is a multi-agent application where four specialised AI agents work together in sequence — each one handling a different part of a patient's health journey — to deliver a complete health consultation, nutrition plan, expense report, and downloadable PDF summary, all in one session.

India has a doctor-to-patient ratio of 1:1,456 — far below the WHO-recommended 1:1,000. Millions of people in tier-2 and tier-3 cities visit a doctor for issues that could be resolved at home with the right guidance. SwasthyaAI fills that gap. It is not a replacement for a real doctor — it is a first-response health companion that speaks the patient's language, knows Indian food, and understands Indian healthcare costs.

---

## 2. Problem Statement

|           Without SwasthyaAI              |                    With SwasthyaAI                        |
|-------------------------------------------|-----------------------------------------------------------|
| Patient googles symptoms and gets anxious | AI asks the right questions and gives structured guidance |
| Visits a doctor for a simple iron deficiency | Gets a tailored Indian meal plan and avoids unnecessary visit |
| Does not track medical spending | Full expense history with monthly breakdown and savings tips |
| Cannot explain symptoms in English | Can type in Hindi or Marathi — system responds in same language |
| No record to show a real doctor | Downloadable PDF report ready to share with any doctor |

---

## 3. System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    PATIENT (User)                       │
└───────────────────────────┬─────────────────────────────┘
                            │ Browser / Mobile
┌───────────────────────────▼──────────────────────────────┐
│              FRONTEND — HTML / CSS / JavaScript          │
│   Login · Dashboard · Chat · Report · Nutrition ·        │
│                Expense · History                         │
└───────────────────────────┬──────────────────────────────┘
                            │ REST API calls (JSON)
┌───────────────────────────▼──────────────────────────────┐
│               BACKEND — FastAPI (Python)                 │
│         REST endpoints · JWT auth · session mgmt         │
└───────────────────────────┬──────────────────────────────┘
                            │ triggers
┌───────────────────────────▼──────────────────────────────┐
│              CrewAI ORCHESTRATOR                         │
│       Sequential task chaining · parallel 3a+3b          │
└──────┬─────────────┬──────────────┬─────────────┬────────┘
       │             │              │             │
┌──────▼──┐   ┌──────▼──┐   ┌──────▼──┐   ┌─────▼───┐
│ Agent 1 │   │ Agent 2 │   │ Agent 3 │   │ Agent 4 │
│ Patient │   │Diagnosis│   │Nutrition│   │Finance  │
│ Intake  │   │         │   │         │   │+ PDF    │
└──────┬──┘   └──────┬──┘   └──────┬──┘   └─────┬───┘
       │             │              │             │
       └─────────────┴──────────────┴─────────────┘
                            │ all agents read/write
┌───────────────────────────▼──────────────────────────────┐
│           SHARED patient_profile (Python dict)           │
│  symptoms · diagnosis · meal_plan · expenses · history   │
└──────────────┬───────────────────────────────────────────┘
               │
    ┌──────────┼──────────────┐
    │          │              │
┌───▼──┐  ┌───▼────┐   ┌──────▼───┐
│SQLite│  │Pinecone│   │ReportLab │
│/Supa │  │vectors │   │  PDF     │
│base  │  │        │   │          │
└──────┘  └───┬────┘   └──────────┘
              │
┌─────────────▼───────────────────┐
│         Groq LLM API            │
│  Powers all 4 agents' reasoning │
└─────────────────────────────────┘
```

---

## 4. Technology Stack

| Layer | Technology | Purpose | Cost |
|---|---|---|---|
| AI Agents | CrewAI | Orchestrates all 4 agents, manages task handoffs | Free (open-source) |
| LLM | Groq API | Powers reasoning for all agents | Free tier (locked) |
| Memory | Pinecone | Persistent patient history across sessions | Free tier (locked) |
| Backend API | FastAPI (Python) | Exposes agent pipeline as REST endpoints | Free (open-source) |
| Frontend | HTML + CSS + JavaScript | Chat interface, dashboard, login, report viewer | Free |
| Authentication | JWT + bcrypt | User login, session management | Free (no external service) |
| Database | SQLite (dev) / Supabase (prod) | Stores user profiles, expenses, session logs | Free |
| PDF Generation | ReportLab (Python) | Generates downloadable health report | Free (open-source) |
| Translation | Groq prompt-based | Hindi and Marathi language support via LLM | Free (uses Groq) |
| Nearby Hospitals | OpenStreetMap / Nominatim | Emergency hospital search by location | Free (no key needed) |
| Charts | Chart.js or Recharts | Nutrition and expense visualisations | Free (open-source) |
| Hosting | Render / Railway / HF Spaces | Deploy FastAPI backend | Free tier |

---

## 5. The Four Agents — Responsibilities

### Agent 1 — Patient Interaction & Memory
- **Role:** First point of contact for every session
- **Input:** Raw patient message, language preference, past Pinecone memory
- **Output:** Structured symptom JSON
- **Key capability:** Emergency keyword detection → show nearest hospitals via Nominatim

### Agent 2 — Diagnosis & Treatment
- **Role:** Diagnostic brain
- **Input:** Symptom JSON from Agent 1 via shared `patient_profile`
- **Output:** Diagnosis JSON with ranked conditions, medicines, specialist type
- **Key capability:** Severity flagging, see-doctor boolean

### Agent 3 — Nutrition & Health
- **Role:** Nutrition analyst and Indian meal planner
- **Input:** Diagnosis JSON from Agent 2, dietary preference from profile
- **Output:** 7-day Indian meal plan, deficiency breakdown
- **Key capability:** Uses IFCT 2017 dataset, respects Veg/Non-Veg/Vegan

### Agent 4 — Medical Finance & Report
- **Role:** Expense tracker and PDF generator
- **Input:** All outputs from Agents 1, 2, 3 + expense history from SQLite
- **Output:** Finance JSON + final PDF report
- **Key capability:** Savings projection, PDF assembly via ReportLab

---

## 6. Agent Execution Order

```
Session Start
     │
     ▼
[Agent 1] — Symptom Intake
     │ outputs symptom JSON
     ▼
[Agent 2] — Diagnosis
     │ outputs diagnosis JSON
     ├──────────────────┐
     ▼                  ▼
[Agent 3]          [Agent 4]
Nutrition          Finance
(parallel)         (parallel)
     │                  │
     └────────┬──────────┘
              ▼
         PDF Assembly
         (part of Agent 4)
```

CrewAI task context: `task3.context = [task2]`, `task4.context = [task2, task3]`

---

## 7. Application Screens (7 Total)

| # | Screen | Maps To |
|---|---|---|
| 1 | Login / Register | Auth system |
| 2 | Dashboard | All agent summary data |
| 3 | Consultation Chat | Agent 1 |
| 4 | Health Report Screen | Agents 1+2+3+4 |
| 5 | Nutrition Dashboard | Agent 3 |
| 6 | Expense Tracker | Agent 4 |
| 7 | History & Trends | All past sessions |

---

## 8. Shared patient_profile — Master Contract

All agents communicate through this single Python dictionary. No agent calls another agent directly.

```python
patient_profile = {
    # Set at registration
    "user_id": "",
    "name": "",
    "age": 0,
    "gender": "",
    "city": "",
    "language": "english",        # english | hindi | marathi
    "diet_pref": "veg",           # veg | non-veg | vegan
    "allergies": [],

    # Set by Agent 1
    "symptoms": [],
    "duration": "",
    "severity": 0,
    "emergency_flag": False,
    "session_id": "",

    # Set by Agent 2
    "conditions": [],
    "medicines": [],
    "specialist_type": "",
    "see_doctor": False,
    "severity_flag": "",           # mild | moderate | severe

    # Set by Agent 3
    "deficiencies": [],
    "meal_plan": [],
    "daily_intake": {},
    "recommended_intake": {},

    # Set by Agent 4
    "monthly_total": 0,
    "expense_breakdown": {},
    "savings_estimate": 0,

    # Loaded from Pinecone on session start
    "past_conditions": [],
    "session_history": []
}
```

---

## 9. Project Folder Structure

```
SwasthyaAI/
├── docs/
│   ├── 01_system_overview.md          ← this file
│   ├── 02_data_design.md
│   ├── 03_agent_design.md
│   ├── 04_api_design.md
│   ├── 05_ui_design.md
│   ├── 06_security_design.md
│   └── 07_implementation_plan.md
│
├── backend/
│   ├── main.py                        ← FastAPI entry point
│   ├── agents/
│   │   ├── agent1_intake.py
│   │   ├── agent2_diagnosis.py
│   │   ├── agent3_nutrition.py
│   │   └── agent4_finance.py
│   ├── crew/
│   │   └── crew_runner.py             ← CrewAI orchestrator
│   ├── routes/
│   │   ├── auth.py
│   │   ├── consultation.py
│   │   ├── nutrition.py
│   │   ├── finance.py
│   │   └── history.py
│   ├── models/
│   │   └── schemas.py                 ← Pydantic models
│   ├── db/
│   │   └── database.py                ← SQLite / Supabase setup
│   ├── memory/
│   │   └── pinecone_client.py
│   └── pdf/
│       └── report_generator.py
│
├── frontend/
│   ├── index.html                     ← Login / Register
│   ├── dashboard.html
│   ├── consultation.html
│   ├── report.html
│   ├── nutrition.html
│   ├── expenses.html
│   ├── history.html
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── auth.js
│       ├── dashboard.js
│       ├── consultation.js
│       ├── report.js
│       ├── nutrition.js
│       ├── expenses.js
│       └── history.js
│
├── requirements.txt
├── .env                               ← Groq key, Pinecone key, JWT secret
└── README.md
```

---

## 10. MVP Scope

### Must build first (MVP)
1. User registration and login (JWT + bcrypt)
2. Symptom intake conversation in English (Agent 1)
3. Diagnosis with 1–3 conditions and medicine list (Agent 2)
4. Indian meal logging and deficiency detection (Agent 3)
5. 7-day Indian meal plan generation (Agent 3)
6. Expense logging and monthly summary (Agent 4)
7. PDF report generation (Agent 4)
8. Emergency symptom detection and hospital alert (Agent 1)

### Phase 2 (after MVP works)
9. Hindi and Marathi language support
10. Persistent memory across sessions via Pinecone
11. Weekly nutrition trend dashboard charts
12. Nearby doctor finder in app

---

*Next: [02_data_design.md](./02_data_design.md)*
