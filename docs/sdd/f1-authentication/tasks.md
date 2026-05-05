# F1 — Authentication & User Management: Tasks

> **Feature ID**: F1  
> **Status**: ✅ All Complete  
> **Last Updated**: 2026-05-05

---

## Task Checklist

### Backend — Database Layer
- [x] **T1.1**: Define `User` SQLAlchemy model with all profile fields (name, email, password_hash, age, gender, city, diet_pref, language, allergies, created_at, last_login)
- [x] **T1.2**: Define `RefreshToken` SQLAlchemy model (user_id FK, token_hash, expires_at, revoked, created_at)
- [x] **T1.3**: Set up `init_db()` function to create all tables at startup
- [x] **T1.4**: Create `get_db()` FastAPI dependency for session management
- [x] **T1.5**: Configure SQLite for development and PostgreSQL for production via `APP_ENV`

### Backend — Auth Utilities
- [x] **T1.6**: Implement `hash_password()` and `verify_password()` using bcrypt (10 salt rounds)
- [x] **T1.7**: Implement `create_access_token()` — JWT with sub, type=access, iat, exp (24h default)
- [x] **T1.8**: Implement `create_refresh_token()` — JWT with sub, type=refresh, iat, exp (7d default)
- [x] **T1.9**: Implement `decode_token()` — validates JWT, raises 401 on expired/invalid
- [x] **T1.10**: Implement `get_current_user()` FastAPI dependency using `HTTPBearer` scheme
- [x] **T1.11**: Implement in-memory rate limiter: `check_rate_limit()`, `record_attempt()`, `reset_attempts()` with thread safety

### Backend — Pydantic Schemas
- [x] **T1.12**: Create `RegisterRequest` with field validators (name, email, password complexity, gender enum, diet_pref enum, language enum, terms_accepted)
- [x] **T1.13**: Create `LoginRequest` (email, password)
- [x] **T1.14**: Create `RefreshTokenRequest` (refresh_token)
- [x] **T1.15**: Create `LogoutRequest` (refresh_token)
- [x] **T1.16**: Create `UpdateProfileRequest` with optional fields and validators

### Backend — API Endpoints
- [x] **T1.17**: `POST /auth/register` — validate input, check email uniqueness, hash password, create user, issue tokens, store refresh token hash
- [x] **T1.18**: `POST /auth/login` — rate limit check, authenticate, issue tokens, update last_login, return profile data
- [x] **T1.19**: `POST /auth/refresh` — validate refresh token JWT, check DB record not revoked/expired, issue new access token
- [x] **T1.20**: `POST /auth/logout` — revoke refresh token in DB
- [x] **T1.21**: `GET /auth/me` — return full user profile (excluding password_hash)
- [x] **T1.22**: `PATCH /auth/profile` — partial update for name, age, city, diet_pref, language, allergies

### Backend — App Configuration
- [x] **T1.23**: Register auth router with `/auth` prefix in `main.py`
- [x] **T1.24**: Configure CORS middleware with allowed origins (localhost:5500, localhost:3000, GitHub Pages)
- [x] **T1.25**: Load environment variables via `dotenv` at startup

### Frontend — Login/Register Page
- [x] **T1.26**: Build `index.html` with auth card layout, gradient background, tab switcher (Login/Register)
- [x] **T1.27**: Login form: email input, password input with toggle visibility, login button
- [x] **T1.28**: Register form: name, age, gender dropdown, city, email, password, diet preference radios (veg/non-veg/vegan), language dropdown, terms checkbox
- [x] **T1.29**: Inline error message display for both forms
- [x] **T1.30**: Auto-redirect to dashboard if token already exists on page load

### Frontend — Auth Logic (`auth.js`)
- [x] **T1.31**: Client-side `validateLogin()` — email format, password not empty
- [x] **T1.32**: Client-side `validateRegister()` — all fields required, password complexity rules, email format, terms checked
- [x] **T1.33**: `handleLogin()` — call API, store tokens in localStorage, redirect to dashboard
- [x] **T1.34**: `handleRegister()` — call API, store tokens in localStorage, redirect to dashboard
- [x] **T1.35**: Enter key listener to submit active form
- [x] **T1.36**: Loading state on buttons during API calls

### Frontend — Shared Auth Infrastructure (`utils.js`)
- [x] **T1.37**: `API_BASE` constant (localhost:8000 for dev, Render URL for prod)
- [x] **T1.38**: `getToken()`, `getRefreshToken()`, `setTokens()` — localStorage helpers
- [x] **T1.39**: `requireAuth()` — redirect to login if no token
- [x] **T1.40**: `apiFetch()` — wrapper that auto-attaches Bearer token, auto-refreshes on 401, force-logouts on refresh failure
- [x] **T1.41**: `tryRefreshToken()` — calls `/auth/refresh`, updates localStorage
- [x] **T1.42**: `logout()` — calls `/auth/logout`, clears localStorage, redirects to login
- [x] **T1.43**: Idle timer — 30-minute timeout, resets on mousemove/keydown/click/scroll/touchstart
- [x] **T1.44**: `renderBottomNav()` — shared bottom navigation component used across all pages

---

## Verification

### Automated Checks
- [x] Server starts without errors (`uvicorn main:app`)
- [x] Registration creates user in DB and returns tokens
- [x] Login with correct credentials returns tokens
- [x] Login with wrong password returns 401
- [x] Rate limiter blocks after 5 failed attempts
- [x] Token refresh returns new access token
- [x] Logout revokes refresh token
- [x] Protected endpoints reject requests without valid token
- [x] `PATCH /auth/profile` updates user fields

### Manual Checks
- [x] Login form shows validation errors for empty/invalid fields
- [x] Register form validates all fields before submission
- [x] Tab switching between Login and Register works
- [x] Password toggle visibility works
- [x] Successful login redirects to dashboard
- [x] Page refresh maintains logged-in state
- [x] Idle timeout triggers logout after 30 minutes
- [x] Already-logged-in user is redirected from login page to dashboard
