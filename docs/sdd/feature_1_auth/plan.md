# Technical Plan: User Authentication & Profile Management

## 1. Architecture Overview

```text
[ Frontend (HTML/JS) ]
        |
        | (JSON over HTTPS)
        v
[ FastAPI Router (/auth, /profile) ]
        |
        +-- [ Auth Dependency (JWT validation) ]
        |
[ SQLAlchemy ORM Models (User, RefreshToken) ]
        |
[ Database (SQLite/PostgreSQL) ]
```

## 2. Tech Stack & Rationale
- **FastAPI**: Provides robust, asynchronous routing and built-in OpenAPI documentation, which accelerates frontend integration.
- **python-jose (JWT)**: Industry-standard mechanism for stateless session management, allowing APIs to scale horizontally without hitting the database for every request.
- **bcrypt**: Slow-hashing algorithm resistant to brute-force attacks, crucial for securing user passwords.
- **SQLAlchemy**: Abstracted ORM that allows seamless switching between SQLite (local) and PostgreSQL (production).

## 3. Component Breakdown
1. **Authentication Router (`backend/routes/auth.py`)**: Handles `/register`, `/login`, and token refresh logic.
2. **Profile Router (`backend/routes/profile.py`)**: Handles GET and PUT requests for user demographics.
3. **Authentication Dependencies (`backend/auth/dependencies.py`)**: Reusable FastAPI `Depends()` functions to extract and validate JWTs from incoming requests.
4. **Database Models (`backend/db/database.py`)**: Defines the `User` and `RefreshToken` SQLAlchemy classes.
5. **Pydantic Schemas (`backend/models/schemas.py`)**: Enforces validation on incoming request payloads (e.g., ensuring email formats are valid, passwords meet complexity rules).

## 4. Dependencies & Risks
### Dependencies
- `passlib[bcrypt]`: For password hashing.
- `python-jose`: For JWT creation and validation.
- `pydantic[email]`: For strict email format validation.

### Risks & Mitigations
- **Risk**: Stolen JWT tokens could lead to account compromise.
  - **Mitigation**: Keep Access Tokens short-lived (e.g., 24 hours). Implement a `RefreshToken` blacklist in the database to revoke compromised sessions.
- **Risk**: Database injection attacks during registration.
  - **Mitigation**: Strict reliance on SQLAlchemy ORM parameters and Pydantic validation to sanitize inputs before they hit the database layer.
