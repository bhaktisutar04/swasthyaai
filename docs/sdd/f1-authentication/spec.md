# F1 — Authentication & User Management: Specification

> **Feature ID**: F1  
> **Status**: ✅ Implemented  
> **Last Updated**: 2026-05-05  
> **Owner**: SwasthyaAI Team

---

## 1. Overview

The Authentication & User Management feature provides secure user registration, login, session management, and profile operations for the SwasthyaAI health platform. It serves as the foundational security layer that all other features depend on.

---

## 2. Goals

1. Allow users to create accounts with health-relevant profile data (age, gender, city, diet preference, language, allergies).
2. Authenticate users via email/password and issue JWT tokens.
3. Support token refresh to maintain long-lived sessions without re-login.
4. Allow users to view and update their profile.
5. Provide secure logout with token revocation.
6. Protect against brute-force login attacks via rate limiting.
7. Auto-logout idle users after 30 minutes of inactivity.

---

## 3. User Stories

| ID | Story | Priority |
|----|-------|----------|
| US-1.1 | As a new user, I can register with my name, email, password, age, gender, city, diet preference, and language so that I can access the health platform. | P0 |
| US-1.2 | As a registered user, I can login with my email and password to access my dashboard. | P0 |
| US-1.3 | As a logged-in user, my session persists across page refreshes without re-logging in. | P0 |
| US-1.4 | As a logged-in user, my session automatically refreshes before token expiry so I don't get logged out unexpectedly. | P1 |
| US-1.5 | As a logged-in user, I can view my profile information. | P1 |
| US-1.6 | As a logged-in user, I can update my name, age, city, diet preference, language, and allergies. | P1 |
| US-1.7 | As a logged-in user, I can logout securely, revoking my refresh token. | P1 |
| US-1.8 | As a user, I am rate-limited to 5 failed login attempts per 15-minute window to prevent brute force. | P1 |
| US-1.9 | As a logged-in user, I am automatically logged out after 30 minutes of inactivity. | P2 |
| US-1.10 | As a user, if I'm already logged in and visit the login page, I am redirected to the dashboard. | P2 |

---

## 4. Functional Requirements

### 4.1 Registration
- **FR-1.1**: Accept fields: name, email, password, age, gender, city, diet_pref, language, allergies, terms_accepted.
- **FR-1.2**: Validate name: 2–50 characters, letters/spaces/hyphens only.
- **FR-1.3**: Validate email: standard email format, normalized to lowercase.
- **FR-1.4**: Validate password: minimum 8 characters, at least 1 uppercase, 1 lowercase, 1 digit, 1 special character (`!@#$%^&*`).
- **FR-1.5**: Validate gender: one of `Male`, `Female`, `Other`, `Prefer not to say`.
- **FR-1.6**: Validate diet_pref: one of `veg`, `non-veg`, `vegan`.
- **FR-1.7**: Validate language: one of `english`, `hindi`, `marathi`.
- **FR-1.8**: Require `terms_accepted = true`.
- **FR-1.9**: Reject duplicate emails with HTTP 409.
- **FR-1.10**: On success, return access token + refresh token + user data.

### 4.2 Login
- **FR-1.11**: Accept email + password.
- **FR-1.12**: Check rate limit before authentication attempt.
- **FR-1.13**: Return error on invalid credentials (generic message to prevent enumeration).
- **FR-1.14**: On success, return access token + refresh token + user profile.
- **FR-1.15**: Update `last_login` timestamp on successful login.
- **FR-1.16**: Reset rate limit counter on successful login.

### 4.3 Token Management
- **FR-1.17**: Access token: JWT with `sub` (user_id), `type: "access"`, valid for 1440 minutes (24 hours).
- **FR-1.18**: Refresh token: JWT with `sub` (user_id), `type: "refresh"`, valid for 7 days.
- **FR-1.19**: Refresh endpoint accepts refresh token, validates it, returns new access token.
- **FR-1.20**: Refresh tokens stored as SHA-256 hashes in database.
- **FR-1.21**: Revoked refresh tokens cannot be reused.

### 4.4 Profile
- **FR-1.22**: `GET /auth/me` returns full user profile (excluding password).
- **FR-1.23**: `PATCH /auth/profile` accepts partial updates for name, age, city, diet_pref, language, allergies.

### 4.5 Logout
- **FR-1.24**: Mark the provided refresh token as revoked in the database.
- **FR-1.25**: Clear all client-side tokens and redirect to login page.

### 4.6 Rate Limiting
- **FR-1.26**: Track failed login attempts per email address.
- **FR-1.27**: Maximum 5 attempts per 15-minute sliding window.
- **FR-1.28**: Return HTTP 429 when rate limit exceeded.

### 4.7 Idle Timeout
- **FR-1.29**: Client-side 30-minute inactivity timer (resets on mouse, keyboard, click, scroll, touch).
- **FR-1.30**: On timeout, alert the user and force logout.

---

## 5. Non-Functional Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-1.1 | Password hashing algorithm | bcrypt with 10 salt rounds |
| NFR-1.2 | Token signing algorithm | HS256 |
| NFR-1.3 | Login response time | < 500ms |
| NFR-1.4 | Token storage (client) | `localStorage` |
| NFR-1.5 | Rate limiter storage | In-memory (thread-safe) |
| NFR-1.6 | Validation | Server-side (Pydantic) + client-side (JS) |

---

## 6. API Contract

### POST `/auth/register`
```json
// Request
{
  "name": "Bhakti Sutar",
  "email": "bhakti@example.com",
  "password": "MyPass@123",
  "age": 25,
  "gender": "Female",
  "city": "Pune",
  "diet_pref": "veg",
  "language": "english",
  "allergies": ["peanuts"],
  "terms_accepted": true
}

// Response 200
{
  "success": true,
  "data": {
    "user_id": 1,
    "name": "Bhakti Sutar",
    "email": "bhakti@example.com",
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "token_type": "Bearer"
  }
}

// Response 409
{ "success": false, "error": "EMAIL_EXISTS", "message": "Email already registered" }
```

### POST `/auth/login`
```json
// Request
{ "email": "bhakti@example.com", "password": "MyPass@123" }

// Response 200
{
  "success": true,
  "data": {
    "user_id": 1,
    "name": "Bhakti Sutar",
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "token_type": "Bearer",
    "profile": {
      "age": 25, "city": "Pune", "diet_pref": "veg",
      "language": "english", "allergies": ["peanuts"]
    }
  }
}

// Response 401
{ "success": false, "error": "INVALID_CREDENTIALS", "message": "Invalid email or password" }

// Response 429
{ "success": false, "error": "RATE_LIMIT_EXCEEDED", "message": "Too many login attempts. Please try again later." }
```

### POST `/auth/refresh`
```json
// Request
{ "refresh_token": "eyJ..." }

// Response 200
{ "success": true, "data": { "access_token": "eyJ...", "token_type": "Bearer" } }
```

### POST `/auth/logout`
```json
// Request (Header: Authorization: Bearer <access_token>)
{ "refresh_token": "eyJ..." }

// Response 200
{ "success": true, "message": "Logged out successfully" }
```

### GET `/auth/me`
```json
// Response 200
{
  "success": true,
  "data": {
    "user_id": 1, "name": "Bhakti Sutar", "email": "bhakti@example.com",
    "age": 25, "gender": "Female", "city": "Pune",
    "diet_pref": "veg", "language": "english",
    "allergies": ["peanuts"], "created_at": "2026-05-01T..."
  }
}
```

### PATCH `/auth/profile`
```json
// Request
{ "name": "Bhakti S.", "city": "Mumbai" }

// Response 200
{
  "success": true,
  "data": { "name": "Bhakti S.", "age": 25, "city": "Mumbai", "diet_pref": "veg", "language": "english", "allergies": ["peanuts"] },
  "message": "Profile updated successfully"
}
```

---

## 7. Data Model

### Users Table
| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | PK, auto-increment |
| name | String | not null |
| email | String | unique, indexed |
| password_hash | String | bcrypt hash |
| age | Integer | 1–120 |
| gender | String | enum-like |
| city | String | not null |
| diet_pref | String | default "veg" |
| language | String | default "english" |
| allergies | Text | JSON array stored as string |
| created_at | DateTime | auto-set |
| last_login | DateTime | nullable |

### Refresh Tokens Table
| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | PK, auto-increment |
| user_id | Integer | FK → users.id |
| token_hash | String | SHA-256 hash, unique, indexed |
| expires_at | DateTime | token expiry |
| revoked | Integer | 0 = active, 1 = revoked |
| created_at | DateTime | auto-set |

---

## 8. UI Specification

### Login/Register Page (`index.html`)
- Single page with tab-switchable Login/Register forms.
- Login tab: email, password, toggle visibility button, login button.
- Register tab: name, age, gender (dropdown), city, email, password, diet preference (radio: veg/non-veg/vegan), language (dropdown: english/hindi/marathi), terms checkbox.
- Error messages displayed inline below forms.
- If already logged in → auto-redirect to `dashboard.html`.
- Enter key submits the active form.

---

## 9. Security Considerations

- Passwords never stored in plaintext — bcrypt with 10 rounds.
- Refresh tokens stored as SHA-256 hashes in DB, never in plaintext.
- Generic "Invalid email or password" message prevents user enumeration.
- Rate limiting prevents brute-force attacks.
- CORS restricted to specific origins.
- All protected endpoints require `Authorization: Bearer <token>` header.
- Idle timeout clears all client-side tokens.
