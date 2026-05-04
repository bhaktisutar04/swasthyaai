# SwasthyaAI — Security Design
**Version:** 1.0  
**Date:** 2026  
**Author:** Solo Developer  
**Document:** SDD Section 6 of 7

---

## 1. Overview

SwasthyaAI handles sensitive health and financial data. Security is non-negotiable. This document defines the complete auth flow, token management, route protection, rate limiting, and data safety measures — all using free, open-source tools.

**No external auth service is used.** Auth is handled entirely with JWT + bcrypt inside FastAPI.

---

## 2. Authentication Flow

### 2.1 Registration

```
User fills form
    │
    ▼
Frontend validates (client-side)
    │
    ▼
POST /auth/register
    │
    ├── Backend validates all fields (Pydantic)
    │
    ├── Check email uniqueness in DB
    │   └── If exists → 409 DUPLICATE_EMAIL
    │
    ├── Hash password with bcrypt (rounds=10)
    │   password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=10))
    │
    ├── Insert user into users table
    │
    ├── Generate access_token (JWT, 24h expiry)
    ├── Generate refresh_token (JWT, 7d expiry)
    ├── Store hashed refresh_token in refresh_tokens table
    │
    └── Return tokens + user data to frontend

Frontend stores:
    localStorage.setItem("access_token", ...)
    localStorage.setItem("refresh_token", ...)
    Cookie (httpOnly) ← set by backend for refresh token
```

### 2.2 Login

```
POST /auth/login
    │
    ├── Find user by email (case-insensitive)
    │   └── If not found → 401 (same message as wrong password — prevents enumeration)
    │
    ├── Check rate limit (max 5 attempts per email per 15 min)
    │   └── If exceeded → 429 RATE_LIMITED
    │
    ├── Verify password with bcrypt
    │   bcrypt.checkpw(password.encode(), stored_hash)
    │   └── If wrong → increment attempt counter → 401
    │
    ├── Reset attempt counter on success
    ├── Update last_login timestamp
    │
    ├── Generate access_token (JWT, 24h)
    ├── Generate refresh_token (JWT, 7d)
    ├── Store hashed refresh_token in refresh_tokens table
    │
    └── Return tokens + profile to frontend
```

### 2.3 Protected Request Flow

```
Frontend makes protected request
    │
    ├── Attach header: Authorization: Bearer <access_token>
    │
    ▼
FastAPI dependency: get_current_user()
    │
    ├── Extract token from header
    ├── Decode JWT with JWT_SECRET_KEY
    ├── Check expiry (exp claim)
    │   └── If expired → 401 UNAUTHORIZED
    ├── Extract user_id from payload
    ├── Load user from DB
    │
    └── Return user to endpoint function
```

### 2.4 Token Refresh Flow

```
Access token expires (frontend detects 401)
    │
    ▼
Frontend calls POST /auth/refresh
    │
    ├── Backend decodes refresh token
    ├── Checks refresh_tokens table — not revoked, not expired
    │   └── If invalid/expired → 401 → Frontend calls logout()
    │
    ├── Generate new access_token
    └── Return new access_token to frontend

Frontend updates: localStorage.setItem("access_token", newToken)
```

### 2.5 Logout Flow

```
User clicks Logout
    │
    ├── Frontend checks for unsaved consultation
    │   └── If yes → show confirmation modal
    │
    ├── POST /auth/logout (sends refresh_token)
    │
    ├── Backend marks refresh_token as revoked in DB
    │
    ├── Frontend:
    │   ├── localStorage.clear()
    │   ├── sessionStorage.clear()
    │   └── Redirect to index.html
    │
    └── Any subsequent protected route → 401 → redirect to login
```

---

## 3. JWT Implementation

```python
# backend/auth/jwt_handler.py

import jwt
from datetime import datetime, timedelta
from config import JWT_SECRET_KEY, JWT_ALGORITHM

def create_access_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(minutes=1440)  # 24 hours
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def create_refresh_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

---

## 4. Password Hashing

```python
# backend/auth/password.py

import bcrypt

def hash_password(plain_password: str) -> str:
    salt = bcrypt.gensalt(rounds=10)
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )
```

---

## 5. FastAPI Route Guard (Dependency)

```python
# backend/auth/dependencies.py

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from auth.jwt_handler import decode_token
from db.database import get_db

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db = Depends(get_db)
):
    token = credentials.credentials
    payload = decode_token(token)  # raises 401 if invalid

    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user

# Usage in any protected route:
@router.get("/dashboard")
async def get_dashboard(current_user = Depends(get_current_user)):
    # current_user is the authenticated User object
    ...
```

---

## 6. Rate Limiting

Rate limiting is implemented in-memory using a simple dictionary. For production, use Redis or Supabase to persist across restarts.

```python
# backend/auth/rate_limiter.py

from datetime import datetime, timedelta
from collections import defaultdict

# {email: [timestamp1, timestamp2, ...]}
login_attempts: dict = defaultdict(list)

MAX_ATTEMPTS = 5
WINDOW_MINUTES = 15

def check_rate_limit(email: str) -> bool:
    """Returns True if allowed, False if rate limited."""
    now = datetime.utcnow()
    window_start = now - timedelta(minutes=WINDOW_MINUTES)

    # Remove attempts outside the window
    login_attempts[email] = [
        t for t in login_attempts[email] if t > window_start
    ]

    if len(login_attempts[email]) >= MAX_ATTEMPTS:
        return False  # rate limited

    return True  # allowed

def record_attempt(email: str):
    login_attempts[email].append(datetime.utcnow())

def reset_attempts(email: str):
    login_attempts[email] = []
```

**Usage in login route:**
```python
@router.post("/login")
async def login(body: LoginRequest, db = Depends(get_db)):
    if not check_rate_limit(body.email):
        raise HTTPException(
            status_code=429,
            detail="Too many attempts. Try again in 15 minutes."
        )
    # ... verify password ...
    record_attempt(body.email)  # on failure
    # reset_attempts(body.email)  # on success
```

---

## 7. Input Validation (Pydantic Models)

```python
# backend/models/schemas.py

from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, List
import re

class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    email: EmailStr
    password: str
    age: int = Field(..., ge=1, le=120)
    gender: str
    city: str = Field(..., min_length=2)
    diet_pref: str
    language: str = Field(default="english")
    allergies: List[str] = []
    terms_accepted: bool

    @validator("name")
    def name_must_be_letters(cls, v):
        if not re.match(r"^[a-zA-Z\s\-']+$", v):
            raise ValueError("Name can only contain letters, spaces, and hyphens")
        return v

    @validator("password")
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain an uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain a lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain a number")
        if not re.search(r"[!@#$%^&*]", v):
            raise ValueError("Password must contain a special character (!@#$%^&*)")
        return v

    @validator("diet_pref")
    def valid_diet(cls, v):
        if v not in ["veg", "non-veg", "vegan"]:
            raise ValueError("diet_pref must be veg, non-veg, or vegan")
        return v

    @validator("gender")
    def valid_gender(cls, v):
        if v not in ["Male", "Female", "Other", "Prefer not to say"]:
            raise ValueError("Invalid gender option")
        return v

    @validator("language")
    def valid_language(cls, v):
        if v not in ["english", "hindi", "marathi"]:
            raise ValueError("Language must be english, hindi, or marathi")
        return v

    @validator("email")
    def lowercase_email(cls, v):
        return v.lower()

    @validator("terms_accepted")
    def terms_must_be_accepted(cls, v):
        if not v:
            raise ValueError("You must accept the Terms & Conditions")
        return v
```

---

## 8. CORS Configuration

```python
# main.py

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",      # VS Code Live Server (dev)
        "http://127.0.0.1:5500",
        "https://swasthyaai.github.io"  # GitHub Pages (prod)
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

---

## 9. Session Timeout (Frontend)

```javascript
// js/utils.js

const IDLE_TIMEOUT_MS = 30 * 60 * 1000; // 30 minutes
let idleTimer;

function resetIdleTimer() {
    clearTimeout(idleTimer);
    idleTimer = setTimeout(() => {
        alert("Your session has expired due to inactivity. Please log in again.");
        logout();
    }, IDLE_TIMEOUT_MS);
}

// Listen for user activity
["mousemove", "keydown", "click", "scroll", "touchstart"].forEach(event => {
    document.addEventListener(event, resetIdleTimer, true);
});

// Start timer on page load
resetIdleTimer();
```

---

## 10. Route Guards (Frontend)

Every protected page calls `requireAuth()` on load:

```javascript
// At the top of every .js file except auth.js

function requireAuth() {
    const token = localStorage.getItem("access_token");
    if (!token) {
        window.location.href = "index.html";
        return false;
    }
    return true;
}

// Call on page load
document.addEventListener("DOMContentLoaded", () => {
    if (!requireAuth()) return;
    loadPageData(); // only runs if auth passes
});
```

---

## 11. Sensitive Data Rules

| Data | Rule |
|---|---|
| Passwords | Never stored in plain text. Always bcrypt hash. Never logged. |
| JWT access token | Stored in `localStorage`. Expires in 24h. |
| JWT refresh token | Stored in `localStorage` + sent as httpOnly cookie. Expires in 7d. Revoked on logout. |
| Patient health data | Stored in SQLite/Supabase. Never sent to third parties. |
| Pinecone data | Only anonymised summaries (no raw chat). Indexed by `user_id`. |
| Groq API requests | Health conversation data is sent to Groq. Do not send full name or email in prompts. Use `patient_profile["name"]` only. |
| PDF files | Stored in server `/pdfs/` folder. Served only to the authenticated owner. |
| `.env` file | Never committed to Git. Add to `.gitignore`. |

---

## 12. .gitignore (Security Essentials)

```
# Environment
.env
.env.local
.env.production

# Database
*.db
*.sqlite
*.sqlite3

# PDFs
/pdfs/

# Python
__pycache__/
*.pyc
venv/
.venv/

# Node (if used)
node_modules/

# OS
.DS_Store
Thumbs.db
```

---

## 13. Medical Disclaimer Requirements

The following disclaimers must appear at specific touchpoints — this is a security and legal requirement:

| Location | Disclaimer Text |
|---|---|
| Before diagnosis results | "⚠️ This is an AI-powered analysis, NOT a medical diagnosis. Always consult a qualified healthcare professional." |
| Medicine list | "These medicines are for reference only. Do NOT self-medicate. Consult a doctor before taking any medication." |
| Nutrition plan | "This meal plan is AI-generated. Consult a certified nutritionist for chronic conditions." |
| Finance savings | "These are estimated projections based on average data. Actual savings may vary." |
| PDF header | "AI-Generated Health Report — Not a Medical Diagnosis" |
| PDF footer | "Consult a qualified healthcare professional for medical advice." |

---

*Previous: [05_ui_design.md](./05_ui_design.md)*  
*Next: [07_implementation_plan.md](./07_implementation_plan.md)*
