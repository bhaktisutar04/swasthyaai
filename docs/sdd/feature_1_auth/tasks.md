# Tasks: User Authentication & Profile Management

## Module 1: Database & Models
- [ ] **Task 1.1**: Define `User` SQLAlchemy model in `backend/db/database.py` with columns for credentials, demographics (age, gender, city), and health profiles (diet_pref, allergies).
- [ ] **Task 1.2**: Define `RefreshToken` SQLAlchemy model to handle secure session management.
- [ ] **Task 1.3**: Create Pydantic schemas in `backend/models/schemas.py` for `UserCreate`, `UserLogin`, and `ProfileUpdate` with strict validation (e.g., email format, minimum password length).

## Module 2: Authentication Core
- [ ] **Task 2.1**: Implement password hashing utility functions using `bcrypt` in `backend/auth/security.py`.
- [ ] **Task 2.2**: Implement JWT creation functions (`create_access_token`, `create_refresh_token`) utilizing `python-jose` and loading secrets from `.env`.
- [ ] **Task 2.3**: Create `get_current_user` FastAPI dependency that validates the JWT from the `Authorization` header and fetches the associated user from the database.

## Module 3: Authentication Endpoints
- [ ] **Task 3.1**: Create `POST /auth/register` endpoint. Validate unique email, hash password, and save to DB.
- [ ] **Task 3.2**: Create `POST /auth/login` endpoint. Verify password, generate Access/Refresh tokens, and save the hashed refresh token to the DB.
- [ ] **Task 3.3**: Create `POST /auth/refresh` endpoint to issue new access tokens using a valid refresh token.

## Module 4: Profile Management
- [ ] **Task 4.1**: Create `GET /profile` endpoint (protected) to return the current user's demographic data.
- [ ] **Task 4.2**: Create `PUT /profile` endpoint (protected) to allow users to update their age, gender, city, diet preference, and allergies. Ensure JSON serialization/deserialization for the allergies array.

## Module 5: Frontend Integration
- [ ] **Task 5.1**: Build the HTML/CSS structure for the Login and Registration screens.
- [ ] **Task 5.2**: Implement `auth.js` to handle form submissions, call the backend `/register` and `/login` endpoints, and securely store the returned JWT in `localStorage` or `sessionStorage`.
- [ ] **Task 5.3**: Build the Profile Setup modal and wire it to the `PUT /profile` endpoint upon initial login or via a settings page.
