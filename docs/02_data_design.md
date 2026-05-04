# SwasthyaAI — Data Design
**Version:** 1.0  
**Date:** 2026  
**Author:** Solo Developer  
**Document:** SDD Section 2 of 7

---

## 1. Overview

SwasthyaAI uses three data stores:

| Store | Technology | What it holds |
|---|---|---|
| Relational DB | SQLite (dev) / Supabase PostgreSQL (prod) | Users, expenses, sessions, consultations |
| Vector DB | Pinecone | Patient memory embeddings for cross-session recall |
| In-memory | Python dict (`patient_profile`) | Live session state shared between all 4 agents |

---

## 2. SQLite / Supabase — Table Schemas

### 2.1 `users` table

```sql
CREATE TABLE users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    email           TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    age             INTEGER NOT NULL,
    gender          TEXT NOT NULL,              -- Male | Female | Other | Prefer not to say
    city            TEXT NOT NULL,
    diet_pref       TEXT NOT NULL DEFAULT 'veg', -- veg | non-veg | vegan
    language        TEXT NOT NULL DEFAULT 'english', -- english | hindi | marathi
    allergies       TEXT DEFAULT '[]',           -- JSON array stored as text
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login      DATETIME
);

CREATE INDEX idx_users_email ON users(email);
```

**Notes:**
- `email` is stored in lowercase always (normalised on insert)
- `allergies` is a JSON string e.g. `'["nuts", "dairy"]'` — parse in Python with `json.loads()`
- `password_hash` uses bcrypt with salt rounds = 10

---

### 2.2 `consultations` table

```sql
CREATE TABLE consultations (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    consultation_id     TEXT NOT NULL UNIQUE,   -- e.g. CNS-2026-04-001
    user_id             INTEGER NOT NULL REFERENCES users(id),
    session_date        DATETIME DEFAULT CURRENT_TIMESTAMP,
    status              TEXT DEFAULT 'in_progress', -- in_progress | completed | follow_up_pending

    -- Agent 1 output
    symptoms            TEXT,                   -- JSON array
    duration            TEXT,
    severity            INTEGER,                -- 1-10
    emergency_flag      INTEGER DEFAULT 0,      -- 0 = false, 1 = true

    -- Agent 2 output
    conditions          TEXT,                   -- JSON array of {name, confidence, reasoning}
    medicines           TEXT,                   -- JSON array
    specialist_type     TEXT,
    severity_flag       TEXT,                   -- mild | moderate | severe
    see_doctor          INTEGER DEFAULT 0,

    -- Agent 3 output
    deficiencies        TEXT,                   -- JSON array
    meal_plan           TEXT,                   -- JSON (7-day plan)
    daily_intake        TEXT,                   -- JSON
    recommended_intake  TEXT,                   -- JSON

    -- Agent 4 output
    monthly_total       REAL DEFAULT 0,
    expense_breakdown   TEXT,                   -- JSON
    savings_estimate    REAL DEFAULT 0,

    -- Report
    pdf_path            TEXT,                   -- filepath or Supabase storage URL
    pdf_generated_at    DATETIME
);

CREATE INDEX idx_consultations_user_id ON consultations(user_id);
CREATE INDEX idx_consultations_session_date ON consultations(session_date);
```

---

### 2.3 `expenses` table

```sql
CREATE TABLE expenses (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id             INTEGER NOT NULL REFERENCES users(id),
    consultation_id     TEXT REFERENCES consultations(consultation_id),
    expense_date        DATE NOT NULL,
    category            TEXT NOT NULL,  -- medicine | consultation | tests | hospital | other
    amount              REAL NOT NULL,
    description         TEXT,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_expenses_user_id ON expenses(user_id);
CREATE INDEX idx_expenses_date ON expenses(expense_date);
```

---

### 2.4 `refresh_tokens` table

```sql
CREATE TABLE refresh_tokens (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id),
    token_hash  TEXT NOT NULL UNIQUE,
    expires_at  DATETIME NOT NULL,
    revoked     INTEGER DEFAULT 0,    -- 0 = valid, 1 = revoked
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_refresh_tokens_user ON refresh_tokens(user_id);
```

---

### 2.5 `notifications` table

```sql
CREATE TABLE notifications (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(id),
    message         TEXT NOT NULL,
    type            TEXT,             -- follow_up | refill | general
    due_date        DATE,
    is_read         INTEGER DEFAULT 0,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 3. Shared patient_profile — Live Session Object

This Python dictionary is the contract between all 4 agents. It lives in memory during a session and is persisted to the `consultations` table at the end.

```python
patient_profile = {
    # ── Identity (loaded from users table on login) ──────────────
    "user_id":          int,       # FK to users.id
    "name":             str,       # "Rahul Kumar"
    "age":              int,       # 32
    "gender":           str,       # "Male"
    "city":             str,       # "Pune"
    "language":         str,       # "english" | "hindi" | "marathi"
    "diet_pref":        str,       # "veg" | "non-veg" | "vegan"
    "allergies":        list,      # ["nuts", "dairy"]

    # ── Session (created on consultation start) ───────────────────
    "session_id":       str,       # "CNS-2026-04-001"
    "session_date":     str,       # ISO datetime string
    "status":           str,       # "in_progress" | "completed"

    # ── Agent 1 Output ────────────────────────────────────────────
    "symptoms":         list,      # ["persistent cough", "mild fever"]
    "duration":         str,       # "3 days"
    "severity":         int,       # 6  (1-10)
    "associated":       list,      # ["night cough", "no appetite"]
    "emergency_flag":   bool,      # False
    "chat_history":     list,      # [{role, content, timestamp}]

    # ── Agent 2 Output ────────────────────────────────────────────
    "conditions": [
        {
            "name":         str,   # "Common Cold (Viral URTI)"
            "confidence":   int,   # 75  (percent)
            "reasoning":    str,   # "Cough, fever, 3 days duration"
            "likelihood":   str    # "most_likely" | "possible" | "less_likely"
        }
    ],
    "medicines": [
        {
            "name":         str,   # "Paracetamol"
            "use":          str    # "for fever"
        }
    ],
    "specialist_type":  str,       # "General Physician (GP)"
    "severity_flag":    str,       # "mild" | "moderate" | "severe"
    "see_doctor":       bool,      # False
    "home_care":        list,      # ["Rest", "Stay hydrated"]
    "red_flags":        list,      # ["High fever >101°F", "Chest pain"]

    # ── Agent 3 Output ────────────────────────────────────────────
    "deficiencies": [
        {
            "nutrient":     str,   # "Iron"
            "current_mg":   float, # 8.0
            "required_mg":  float  # 18.0
        }
    ],
    "daily_intake":     dict,      # {"iron_mg": 8, "protein_g": 45}
    "recommended_intake": dict,    # {"iron_mg": 18, "protein_g": 60}
    "meal_plan": [
        {
            "day":          int,   # 1
            "day_name":     str,   # "Monday"
            "breakfast":    dict,  # {items: [], nutrients: {}}
            "mid_morning":  dict,
            "lunch":        dict,
            "evening":      dict,
            "dinner":       dict
        }
        # ... 7 entries total
    ],
    "nutrition_tips":   list,      # ["Pair iron with Vitamin C"]

    # ── Agent 4 Output ────────────────────────────────────────────
    "monthly_total":    float,     # 4500.0
    "expense_breakdown": {
        "medicine":     float,     # 3000.0
        "consultation": float,     # 1500.0
        "tests":        float,     # 0.0
        "hospital":     float,     # 0.0
        "other":        float      # 0.0
    },
    "savings_estimate": float,     # 1600.0
    "savings_breakdown": {
        "medicine_reduction":      float,
        "consultation_reduction":  float,
        "nutrition_cost_increase": float
    },

    # ── Pinecone Memory (loaded on session start) ─────────────────
    "past_conditions":  list,      # ["Iron Deficiency Anemia (March 2026)"]
    "session_history":  list       # last N consultation summaries
}
```

---

## 4. Pinecone Index Structure

### Index name: `swasthyaai-patient-memory`

| Setting | Value |
|---|---|
| Dimension | 1536 (OpenAI compatible) or 768 (use `sentence-transformers`) |
| Metric | cosine |
| Environment | Free tier (gcp-starter) |

### Vector metadata schema

Each vector stored in Pinecone has this metadata:

```json
{
    "user_id":          "42",
    "session_id":       "CNS-2026-04-001",
    "session_date":     "2026-04-21",
    "primary_condition":"Common Cold",
    "severity_flag":    "mild",
    "summary":          "Patient Rahul, 32, presented with cough and mild fever for 3 days. Diagnosed with Common Cold. Recommended Paracetamol and rest."
}
```

### How Pinecone is used

1. **On session start** — Agent 1 queries Pinecone with the patient's `user_id` filter to retrieve past session summaries
2. **On session end** — The consultation summary is embedded and upserted into Pinecone with the metadata above
3. **Embedding model** — Use `sentence-transformers/all-MiniLM-L6-v2` (free, runs locally) OR Groq-generated summaries stored as text (simpler)

```python
# pinecone_client.py — query past sessions
def get_patient_memory(user_id: int, top_k: int = 3):
    results = index.query(
        vector=embed(f"patient {user_id} health history"),
        top_k=top_k,
        filter={"user_id": str(user_id)},
        include_metadata=True
    )
    return [r.metadata["summary"] for r in results.matches]

# Store session summary after completion
def store_session_summary(user_id: int, session_id: str, summary: str, metadata: dict):
    vector = embed(summary)
    index.upsert(vectors=[{
        "id": session_id,
        "values": vector,
        "metadata": {**metadata, "user_id": str(user_id), "summary": summary}
    }])
```

---

## 5. Data Flow — What Gets Stored Where

| Data | During Session | After Session |
|---|---|---|
| User credentials | users table (at register) | stays in users table |
| JWT tokens | refresh_tokens table | revoked on logout |
| patient_profile dict | Python memory (RAM) | serialised → consultations table |
| Chat messages | chat_history in patient_profile | stored in consultations.symptoms + context |
| Expenses | expenses table (on add) | stays in expenses table |
| Consultation summary | built in patient_profile | upserted to Pinecone |
| PDF | generated by ReportLab | saved to /pdfs/ folder or Supabase storage |

---

## 6. Indian Food Nutrition Dataset (IFCT 2017)

Agent 3 uses a local JSON/CSV file derived from IFCT 2017 (Indian Food Composition Tables). This file is stored in the backend as a static asset.

```
backend/
└── data/
    └── ifct_nutrition.json
```

### Sample structure

```json
[
    {
        "food_name": "Palak Dal",
        "food_name_hindi": "पालक दाल",
        "category": "dal",
        "diet_type": "veg",
        "per_100g": {
            "iron_mg": 5.2,
            "protein_g": 8.1,
            "vitamin_c_mg": 12.0,
            "vitamin_b12_ug": 0.0,
            "calcium_mg": 73.0,
            "calories_kcal": 121
        },
        "common_portion": "1 cup (200g)"
    }
]
```

---

## 7. Environment Variables (.env)

```
# Groq (locked)
GROQ_API_KEY=your_groq_api_key

# Pinecone (locked)
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=swasthyaai-patient-memory

# JWT
JWT_SECRET_KEY=your_random_secret_key_here
JWT_ALGORITHM=HS256
JWT_ACCESS_EXPIRE_MINUTES=1440
JWT_REFRESH_EXPIRE_DAYS=7

# Database
DATABASE_URL=sqlite:///./swasthyaai.db
# For production: postgresql://user:pass@host/dbname

# App
APP_ENV=development
PDF_STORAGE_PATH=./pdfs/
```

---

## 8. Data Validation Rules

| Field | Rule |
|---|---|
| name | 2–50 chars, letters/spaces/hyphens only |
| age | Integer 1–120 |
| email | Valid format, lowercase, unique |
| password | Min 8 chars, 1 uppercase, 1 lowercase, 1 digit, 1 special char |
| diet_pref | Must be one of: veg, non-veg, vegan |
| language | Must be one of: english, hindi, marathi |
| severity (symptom) | Integer 1–10 |
| amount (expense) | Positive float, > 0 |
| expense date | Cannot be more than 1 year in the future |
| category (expense) | Must be one of: medicine, consultation, tests, hospital, other |

---

*Previous: [01_system_overview.md](./01_system_overview.md)*  
*Next: [03_agent_design.md](./03_agent_design.md)*
