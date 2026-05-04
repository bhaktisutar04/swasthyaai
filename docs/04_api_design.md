# SwasthyaAI — API Design
**Version:** 1.0  
**Date:** 2026  
**Author:** Solo Developer  
**Document:** SDD Section 4 of 7

---

## 1. Overview

The SwasthyaAI backend is a FastAPI application. All endpoints return JSON. All protected endpoints require a JWT access token in the `Authorization: Bearer <token>` header.

**Base URL (dev):** `http://localhost:8000`  
**Base URL (prod):** `https://swasthyaai.onrender.com`

---

## 2. Standard Response Format

### Success
```json
{
    "success": true,
    "data": { },
    "message": "Optional human-readable message"
}
```

### Error
```json
{
    "success": false,
    "error": "ERROR_CODE",
    "message": "Human-readable description"
}
```

### Common Error Codes

| Code | HTTP Status | Meaning |
|---|---|---|
| `VALIDATION_ERROR` | 422 | Request body failed validation |
| `UNAUTHORIZED` | 401 | Missing or invalid JWT token |
| `FORBIDDEN` | 403 | Valid token but access denied |
| `NOT_FOUND` | 404 | Resource not found |
| `DUPLICATE_EMAIL` | 409 | Email already registered |
| `RATE_LIMITED` | 429 | Too many login attempts |
| `SERVER_ERROR` | 500 | Internal server error |

---

## 3. Auth Endpoints

### POST `/auth/register`

Creates a new user account and initialises an empty patient profile.

**Request Body:**
```json
{
    "name": "Rahul Kumar",
    "email": "rahul@example.com",
    "password": "SecurePass@123",
    "age": 32,
    "gender": "Male",
    "city": "Pune",
    "diet_pref": "veg",
    "language": "english",
    "allergies": ["nuts"],
    "terms_accepted": true
}
```

**Validation:**
- `name`: 2–50 chars, letters/spaces/hyphens only
- `email`: valid format, stored lowercase, unique
- `password`: min 8 chars, 1 uppercase, 1 lowercase, 1 digit, 1 special char
- `age`: integer 1–120
- `gender`: one of `Male | Female | Other | Prefer not to say`
- `diet_pref`: one of `veg | non-veg | vegan`
- `language`: one of `english | hindi | marathi`
- `terms_accepted`: must be `true`

**Success Response (201):**
```json
{
    "success": true,
    "data": {
        "user_id": 1,
        "name": "Rahul Kumar",
        "email": "rahul@example.com",
        "access_token": "eyJhbGci...",
        "refresh_token": "eyJhbGci...",
        "token_type": "Bearer"
    },
    "message": "Account created successfully"
}
```

**Error Responses:**
- `409 DUPLICATE_EMAIL` — email already registered
- `422 VALIDATION_ERROR` — invalid field values

---

### POST `/auth/login`

Authenticates a user and returns JWT tokens.

**Request Body:**
```json
{
    "email": "rahul@example.com",
    "password": "SecurePass@123"
}
```

**Success Response (200):**
```json
{
    "success": true,
    "data": {
        "user_id": 1,
        "name": "Rahul Kumar",
        "access_token": "eyJhbGci...",
        "refresh_token": "eyJhbGci...",
        "token_type": "Bearer",
        "profile": {
            "age": 32,
            "city": "Pune",
            "diet_pref": "veg",
            "language": "english",
            "allergies": ["nuts"]
        }
    }
}
```

**Error Responses:**
- `401 UNAUTHORIZED` — invalid credentials (same message for wrong email or password — prevents enumeration)
- `429 RATE_LIMITED` — 5+ failed attempts in 15 min

---

### POST `/auth/refresh`

Exchanges a valid refresh token for a new access token.

**Request Body:**
```json
{
    "refresh_token": "eyJhbGci..."
}
```

**Success Response (200):**
```json
{
    "success": true,
    "data": {
        "access_token": "eyJhbGci...",
        "token_type": "Bearer"
    }
}
```

---

### POST `/auth/logout`
🔒 Protected

Invalidates the refresh token server-side.

**Request Body:**
```json
{
    "refresh_token": "eyJhbGci..."
}
```

**Success Response (200):**
```json
{
    "success": true,
    "message": "Logged out successfully"
}
```

---

### GET `/auth/me`
🔒 Protected

Returns the currently logged-in user's profile.

**Success Response (200):**
```json
{
    "success": true,
    "data": {
        "user_id": 1,
        "name": "Rahul Kumar",
        "email": "rahul@example.com",
        "age": 32,
        "gender": "Male",
        "city": "Pune",
        "diet_pref": "veg",
        "language": "english",
        "allergies": ["nuts"],
        "created_at": "2026-01-15T10:30:00"
    }
}
```

---

### PATCH `/auth/profile`
🔒 Protected

Updates the user's profile details.

**Request Body (all fields optional):**
```json
{
    "name": "Rahul Kumar",
    "age": 33,
    "city": "Mumbai",
    "diet_pref": "non-veg",
    "language": "hindi",
    "allergies": ["nuts", "dairy"]
}
```

**Success Response (200):**
```json
{
    "success": true,
    "data": { /* updated profile */ },
    "message": "Profile updated successfully"
}
```

---

## 4. Dashboard Endpoint

### GET `/dashboard`
🔒 Protected

Returns all data needed to populate the dashboard in one call.

**Success Response (200):**
```json
{
    "success": true,
    "data": {
        "greeting_name": "Rahul Kumar",
        "latest_consultation": {
            "consultation_id": "CNS-2026-04-001",
            "session_date": "2026-04-21",
            "primary_condition": "Common Cold",
            "status": "completed",
            "follow_up_days": 5
        },
        "monthly_expense_total": 4500.00,
        "previous_month_total": 5000.00,
        "expense_change_percent": -10.0,
        "nutrition_score_this_week": 85,
        "nutrition_score_last_week": 80,
        "notifications": [
            {
                "id": 1,
                "message": "Follow-up with GP in 5 days",
                "type": "follow_up",
                "due_date": "2026-04-26"
            }
        ]
    }
}
```

---

## 5. Consultation Endpoints

### POST `/consultation/start`
🔒 Protected

Starts a new consultation session. Loads patient profile and begins Agent 1.

**Request Body:**
```json
{}
```
*(No body needed — user identity from JWT)*

**Success Response (200):**
```json
{
    "success": true,
    "data": {
        "session_id": "CNS-2026-04-021",
        "greeting": "Namaste Rahul! How are you feeling today? Please describe your symptoms.",
        "language": "english"
    }
}
```

---

### POST `/consultation/message`
🔒 Protected

Sends a patient message to the active agent. Returns the agent's response.

**Request Body:**
```json
{
    "session_id": "CNS-2026-04-021",
    "message": "I have a persistent cough and slight fever since 3 days."
}
```

**Success Response (200):**
```json
{
    "success": true,
    "data": {
        "response": "I understand. On a scale of 1-10, how would you rate the severity of your cough?",
        "agent": "agent1",
        "emergency_detected": false,
        "consultation_complete": false
    }
}
```

**Emergency Response (200 — not an error, handled in frontend):**
```json
{
    "success": true,
    "data": {
        "response": "I noticed you mentioned chest pain. Please seek immediate medical attention.",
        "emergency_detected": true,
        "hospitals": [
            {
                "name": "City General Hospital",
                "address": "MG Road, Pune",
                "maps_link": "https://maps.google.com/?q=18.5204,73.8567"
            }
        ],
        "emergency_number": "108"
    }
}
```

---

### GET `/consultation/report/{session_id}`
🔒 Protected

Returns the full 4-section report for a completed consultation.

**Success Response (200):**
```json
{
    "success": true,
    "data": {
        "session_id": "CNS-2026-04-001",
        "session_date": "2026-04-21",
        "status": "completed",
        "patient": {
            "name": "Rahul Kumar",
            "age": 32,
            "gender": "Male",
            "city": "Pune",
            "diet_pref": "veg"
        },
        "symptoms": {
            "list": ["persistent cough", "mild fever"],
            "duration": "3 days",
            "severity": 6,
            "emergency_flag": false
        },
        "diagnosis": {
            "conditions": [
                {"name": "Common Cold", "confidence": 75, "likelihood": "most_likely"}
            ],
            "specialist_type": "General Physician (GP)",
            "medicines": [
                {"name": "Paracetamol", "use": "for fever"}
            ],
            "severity_flag": "mild",
            "see_doctor": false,
            "home_care": ["Rest 7-8 hours", "Stay hydrated"]
        },
        "nutrition": {
            "deficiencies": [],
            "nutritional_focus": "Boosting immunity with Vitamin C and Zinc",
            "meal_plan": [ /* 7-day plan */ ]
        },
        "finance": {
            "monthly_total": 4500.00,
            "expense_breakdown": {"medicine": 3000, "consultation": 1500},
            "savings_estimate": 1200.00
        },
        "pdf_available": true
    }
}
```

---

### GET `/consultation/report/{session_id}/pdf`
🔒 Protected

Generates (or retrieves cached) PDF for a consultation. Returns the file.

**Response:** `application/pdf` binary stream  
**Headers:** `Content-Disposition: attachment; filename="SwasthyaAI_Report_Rahul_2026-04-21.pdf"`

---

## 6. Nutrition Endpoints

### POST `/nutrition/log-meal`
🔒 Protected

Logs a meal entry and updates daily intake.

**Request Body:**
```json
{
    "session_id": "CNS-2026-04-021",
    "meal_type": "breakfast",
    "items": ["Poha with peanuts", "Lemon water"],
    "date": "2026-04-21"
}
```

**Success Response (200):**
```json
{
    "success": true,
    "data": {
        "updated_daily_intake": {
            "iron_mg": 3.0,
            "protein_g": 8.0,
            "vitamin_c_mg": 12.0
        },
        "progress_percent": 22
    }
}
```

---

### GET `/nutrition/trends`
🔒 Protected

Returns 7-day nutrition trend data for the dashboard chart.

**Query Params:** `?days=7` (default 7, max 30)

**Success Response (200):**
```json
{
    "success": true,
    "data": {
        "labels": ["Apr 15", "Apr 16", "Apr 17", "Apr 18", "Apr 19", "Apr 20", "Apr 21"],
        "scores": [70, 75, 68, 80, 82, 80, 85],
        "average": 77.1,
        "trend": "improving"
    }
}
```

---

## 7. Finance Endpoints

### POST `/finance/add-expense`
🔒 Protected

Adds a new expense entry.

**Request Body:**
```json
{
    "expense_date": "2026-04-21",
    "category": "medicine",
    "amount": 450.00,
    "description": "Paracetamol strips x3",
    "consultation_id": "CNS-2026-04-001"
}
```

**Validation:**
- `category`: must be one of `medicine | consultation | tests | hospital | other`
- `amount`: must be a positive number > 0
- `expense_date`: valid date, not more than 1 year in future

**Success Response (201):**
```json
{
    "success": true,
    "data": {
        "expense_id": 15,
        "new_monthly_total": 4950.00
    },
    "message": "Expense added successfully"
}
```

---

### GET `/finance/summary`
🔒 Protected

Returns monthly expense breakdown and savings estimate.

**Query Params:** `?months=1` (default 1, max 12)

**Success Response (200):**
```json
{
    "success": true,
    "data": {
        "monthly_total": 4500.00,
        "previous_month_total": 5000.00,
        "change_percent": -10.0,
        "breakdown": {
            "medicine": 3000.00,
            "consultation": 1500.00,
            "tests": 0.00,
            "hospital": 0.00,
            "other": 0.00
        },
        "savings_estimate": 1600.00,
        "savings_disclaimer": "Estimated projections based on average data. Actual savings may vary.",
        "monthly_trend": [
            {"month": "Nov 2025", "total": 5200},
            {"month": "Dec 2025", "total": 4800},
            {"month": "Jan 2026", "total": 5000},
            {"month": "Feb 2026", "total": 4700},
            {"month": "Mar 2026", "total": 5000},
            {"month": "Apr 2026", "total": 4500}
        ]
    }
}
```

---

## 8. History Endpoints

### GET `/history`
🔒 Protected

Returns all past consultations in reverse chronological order.

**Query Params:** `?page=1&limit=10&condition=&date_from=&date_to=`

**Success Response (200):**
```json
{
    "success": true,
    "data": {
        "consultations": [
            {
                "consultation_id": "CNS-2026-04-001",
                "session_date": "2026-04-21T10:30:00",
                "primary_condition": "Common Cold",
                "severity_flag": "mild",
                "status": "completed",
                "pdf_available": true
            }
        ],
        "total": 3,
        "page": 1,
        "total_pages": 1
    }
}
```

---

### GET `/history/analytics/nutrition`
🔒 Protected

Returns nutrition score trend data for the history charts.

**Query Params:** `?range=1m` (options: `1m | 3m | 6m | 1y`)

**Success Response (200):**
```json
{
    "success": true,
    "data": {
        "labels": ["Week 1", "Week 2", "Week 3", "Week 4"],
        "scores": [70, 78, 82, 85],
        "current_score": 85,
        "change_vs_last_week": 3
    }
}
```

---

### GET `/history/analytics/expenses`
🔒 Protected

Returns expense trend data for the history charts.

**Query Params:** `?range=6m`

**Success Response (200):**
```json
{
    "success": true,
    "data": {
        "labels": ["Nov", "Dec", "Jan", "Feb", "Mar", "Apr"],
        "totals": [5200, 4800, 5000, 4700, 5000, 4500],
        "current_month": 4500,
        "trend": "decreasing"
    }
}
```

---

## 9. FastAPI Project Structure

```python
# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import auth, consultation, nutrition, finance, history, dashboard

app = FastAPI(title="SwasthyaAI API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://swasthyaai.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(consultation.router, prefix="/consultation", tags=["Consultation"])
app.include_router(nutrition.router, prefix="/nutrition", tags=["Nutrition"])
app.include_router(finance.router, prefix="/finance", tags=["Finance"])
app.include_router(history.router, prefix="/history", tags=["History"])

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "SwasthyaAI"}
```

---

## 10. All Endpoints Summary

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | /auth/register | ❌ | Create new account |
| POST | /auth/login | ❌ | Login, get JWT |
| POST | /auth/refresh | ❌ | Refresh access token |
| POST | /auth/logout | 🔒 | Logout, revoke token |
| GET | /auth/me | 🔒 | Get current user profile |
| PATCH | /auth/profile | 🔒 | Update profile |
| GET | /dashboard | 🔒 | Dashboard aggregated data |
| POST | /consultation/start | 🔒 | Start new consultation |
| POST | /consultation/message | 🔒 | Send message to agent |
| GET | /consultation/report/{id} | 🔒 | Get full report JSON |
| GET | /consultation/report/{id}/pdf | 🔒 | Download PDF |
| POST | /nutrition/log-meal | 🔒 | Log a meal |
| GET | /nutrition/trends | 🔒 | Nutrition chart data |
| POST | /finance/add-expense | 🔒 | Add expense |
| GET | /finance/summary | 🔒 | Monthly expense summary |
| GET | /history | 🔒 | Past consultations list |
| GET | /history/analytics/nutrition | 🔒 | Nutrition trend data |
| GET | /history/analytics/expenses | 🔒 | Expense trend data |
| GET | /health | ❌ | Health check |

---

*Previous: [03_agent_design.md](./03_agent_design.md)*  
*Next: [05_ui_design.md](./05_ui_design.md)*
