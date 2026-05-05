# F1 — Authentication & User Management: Technical Plan

> **Feature ID**: F1  
> **Status**: ✅ Implemented  
> **Last Updated**: 2026-05-05

---

## 1. Architecture Overview

```mermaid
flowchart TD
    subgraph Frontend
        A[index.html] --> B[auth.js]
        B --> C[utils.js]
    end

    subgraph Backend
        D[routes/auth.py] --> E[auth/jwt_handler.py]
        D --> F[auth/password.py]
        D --> G[auth/rate_limiter.py]
        H[auth/dependencies.py] --> E
        D --> I[models/schemas.py]
        D --> J[db/database.py]
    end

    subgraph Database
        K[(users)]
        L[(refresh_tokens)]
    end

    B -->|HTTP| D
    C -->|apiFetch + auto-refresh| D
    H -->|get_current_user| D
    J --> K
    J --> L
```

---

## 2. Component Design

### 2.1 Backend Components

#### `routes/auth.py` — Auth Router
- **Pattern**: FastAPI `APIRouter` with 6 endpoints.
- **Error Handling**: Uses `create_error_response()` helper to return consistent JSON errors (not HTTPException), so the frontend always receives a parseable JSON body.
- **Token Flow**: On register/login → create access + refresh tokens → hash refresh token → store hash in `refresh_tokens` table → return both tokens in response.

#### `auth/jwt_handler.py` — JWT Token Manager
- **Library**: `python-jose` (JOSE implementation).
- **Token Structure**:
  - `sub`: user_id as string
  - `type`: "access" or "refresh"
  - `iat`: issued-at timestamp
  - `exp`: expiration timestamp
- **Config**: All parameters driven by environment variables with sensible defaults.

#### `auth/password.py` — Password Hasher
- **Library**: `bcrypt`.
- **Salt Rounds**: 10 (balance of security and performance).
- **Pattern**: Standalone utility functions, no class state.

#### `auth/rate_limiter.py` — Login Rate Limiter
- **Pattern**: In-memory sliding window using `defaultdict(list)` of timestamps.
- **Thread Safety**: `threading.Lock` protects all read/write operations.
- **Cleanup**: Old attempts pruned on every `check_rate_limit()` / `record_attempt()` call.
- **Limitation**: Not persistent across server restarts; not suitable for multi-instance deployment.

#### `auth/dependencies.py` — Auth Dependency
- **Pattern**: FastAPI dependency using `HTTPBearer` security scheme.
- **Flow**: Extract token from `Authorization` header → decode → query user by ID → return `User` ORM object.
- **Usage**: `current_user: User = Depends(get_current_user)` on any protected endpoint.

#### `models/schemas.py` — Pydantic Validation
- **Pattern**: Field-level validators using `@field_validator` decorators.
- **Validators**: Email normalization, password complexity, gender enum, diet_pref enum, language enum, terms acceptance.

### 2.2 Frontend Components

#### `index.html` — Login/Register Page
- **Layout**: Centered auth card with gradient background, tab-switching UI.
- **Forms**: Two forms (login/register), only one visible at a time.
- **Styling**: Custom radio buttons for diet preference, inline error display.

#### `auth.js` — Auth Logic
- **Dual Validation**: Client-side validation mirrors server-side rules for instant feedback.
- **Token Storage**: `localStorage` for `access_token`, `refresh_token`, `user_name`, `user_id`.
- **Redirect**: Auto-redirect to dashboard if token exists on page load.
- **Keyboard**: Enter key submits whichever form is visible.

#### `utils.js` — Shared Auth Infrastructure
- **`apiFetch()`**: Wrapper around `fetch()` that auto-attaches Bearer token, and on 401 → attempts token refresh → retries original request → if refresh fails → force logout.
- **`requireAuth()`**: Guard function called on every protected page; redirects to login if no token.
- **`logout()`**: Calls `/auth/logout` → clears `localStorage` → redirects to login.
- **Idle Timer**: 30-minute timeout, reset on any user interaction event.

---

## 3. File Map

```
backend/
├── auth/
│   ├── __init__.py
│   ├── dependencies.py      # get_current_user FastAPI dependency
│   ├── jwt_handler.py        # create/decode JWT tokens
│   ├── password.py            # bcrypt hash/verify
│   └── rate_limiter.py        # in-memory sliding window limiter
├── models/
│   └── schemas.py             # Pydantic request models
├── routes/
│   └── auth.py                # /auth/* endpoints
└── db/
    └── database.py            # User, RefreshToken ORM models

frontend/
├── index.html                 # Login/Register page
├── js/
│   ├── auth.js                # Login/Register handlers
│   └── utils.js               # apiFetch, requireAuth, logout, idle timer
└── css/
    └── style.css              # Shared design system
```

---

## 4. Data Flow Diagrams

### 4.1 Registration Flow
```mermaid
sequenceDiagram
    participant U as User (Browser)
    participant FE as auth.js
    participant BE as routes/auth.py
    participant DB as Database

    U->>FE: Fill form, click Register
    FE->>FE: Client-side validation
    FE->>BE: POST /auth/register {name, email, password, ...}
    BE->>BE: Pydantic validation (schemas.py)
    BE->>DB: Check email uniqueness
    alt Email exists
        BE-->>FE: 409 EMAIL_EXISTS
        FE-->>U: Show error
    else Email available
        BE->>BE: bcrypt hash password
        BE->>DB: INSERT user
        BE->>BE: Create access + refresh tokens
        BE->>DB: INSERT refresh_token (hashed)
        BE-->>FE: 200 {access_token, refresh_token, user_id, name}
        FE->>FE: Store tokens in localStorage
        FE-->>U: Redirect to dashboard.html
    end
```

### 4.2 Login Flow
```mermaid
sequenceDiagram
    participant U as User (Browser)
    participant FE as auth.js
    participant BE as routes/auth.py
    participant RL as rate_limiter.py
    participant DB as Database

    U->>FE: Enter email + password, click Login
    FE->>FE: Client-side validation
    FE->>BE: POST /auth/login {email, password}
    BE->>RL: check_rate_limit(email)
    alt Rate limit exceeded
        BE-->>FE: 429 RATE_LIMIT_EXCEEDED
    else Within limit
        BE->>DB: Query user by email
        alt User not found
            BE->>RL: record_attempt(email)
            BE-->>FE: 401 INVALID_CREDENTIALS
        else User found
            BE->>BE: verify_password()
            alt Password wrong
                BE->>RL: record_attempt(email)
                BE-->>FE: 401 INVALID_CREDENTIALS
            else Password correct
                BE->>RL: reset_attempts(email)
                BE->>DB: Update last_login
                BE->>BE: Create tokens
                BE->>DB: INSERT refresh_token
                BE-->>FE: 200 {tokens + profile}
                FE->>FE: Store in localStorage
                FE-->>U: Redirect to dashboard
            end
        end
    end
```

### 4.3 Token Refresh Flow
```mermaid
sequenceDiagram
    participant FE as utils.js (apiFetch)
    participant BE as routes/auth.py
    participant DB as Database

    FE->>BE: Any API call with expired access token
    BE-->>FE: 401 Unauthorized
    FE->>BE: POST /auth/refresh {refresh_token}
    BE->>BE: Decode refresh token JWT
    BE->>DB: Find refresh_token by hash
    alt Token valid & not revoked
        BE->>BE: Create new access token
        BE-->>FE: 200 {new access_token}
        FE->>FE: Update localStorage
        FE->>BE: Retry original API call with new token
    else Token invalid/revoked/expired
        BE-->>FE: 401
        FE->>FE: Force logout
    end
```

---

## 5. Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Token storage | `localStorage` | Simple for SPA; acceptable risk for health info app (not banking) |
| Error responses | JSON (not HTTPException) | Ensures frontend always gets parseable response body |
| Rate limiter | In-memory | Sufficient for single-instance deployment; no external dependency |
| Password rules | 4-rule validation | Balance of security and user friction for a health app |
| Email normalization | `.lower()` on both registration and login | Prevents case-mismatch login failures |
| Allergies storage | JSON string in Text column | Flexible for varying list lengths; avoids separate table complexity |
| Refresh token hashing | SHA-256 | Fast, deterministic; sufficient for token lookup (bcrypt too slow for lookups) |

---

## 6. Dependencies

### Backend
| Package | Version | Purpose |
|---------|---------|---------|
| `fastapi` | latest | Web framework |
| `python-jose[cryptography]` | latest | JWT encode/decode |
| `bcrypt` | latest | Password hashing |
| `pydantic[email-validator]` | latest | Request validation |
| `sqlalchemy` | latest | ORM |

### Frontend
| Dependency | Type | Purpose |
|------------|------|---------|
| None | — | Pure vanilla JS, no framework |

---

## 7. Environment Variables

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `JWT_SECRET_KEY` | `"your-secret-key"` | ✅ Yes (production) | Secret for signing JWTs |
| `JWT_ALGORITHM` | `"HS256"` | No | JWT signing algorithm |
| `JWT_ACCESS_EXPIRE_MINUTES` | `1440` (24h) | No | Access token lifetime |
| `JWT_REFRESH_EXPIRE_DAYS` | `7` | No | Refresh token lifetime |

---

## 8. Known Limitations & Future Improvements

| Limitation | Impact | Potential Fix |
|------------|--------|---------------|
| Rate limiter is in-memory | Resets on server restart; doesn't work across multiple instances | Redis-backed rate limiter |
| No email verification | Users can register with any email | Add email verification flow |
| No password reset | Users locked out if they forget password | Add forgot-password with email OTP |
| No OAuth/social login | Users must create password-based accounts | Add Google/GitHub OAuth |
| Allergies not validated | Free-text array, no standard allergy codes | Use standardized allergy taxonomy |
| No account deletion | GDPR compliance gap | Add `DELETE /auth/account` endpoint |
