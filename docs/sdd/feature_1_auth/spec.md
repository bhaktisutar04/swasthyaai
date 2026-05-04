# Specification: User Authentication & Profile Management

## 1. Feature Overview
This feature encompasses the secure onboarding of users, session management via JWT, and the collection of essential user health demographics (profiles). This is the foundational layer upon which personalized health and financial insights are built.

## 2. Behavioral Specification

### 2.1 User Registration
- **Behavior**: Users must provide a valid email, name, and strong password to create an account.
- **Rules**:
  - Email must be unique.
  - Password must be securely hashed before storage.
  - Upon successful registration, the user is redirected to the login flow (or automatically logged in).

### 2.2 User Login & Session Management
- **Behavior**: Users log in using their email and password. The system grants temporary access tokens and long-lived refresh tokens.
- **Rules**:
  - System shall validate credentials against hashed passwords in the database.
  - Successful login returns a JWT Access Token (short expiration) and a Refresh Token (long expiration).
  - Protected API routes must reject requests lacking a valid Access Token.

### 2.3 Profile Management
- **Behavior**: Users can view and update their health demographics.
- **Rules**:
  - Users can specify: Age, Gender, City, Diet Preference (Veg/Non-Veg/Vegan), Preferred Language, and Allergies.
  - The profile must be tied exclusively to the authenticated user.

## 3. Data Models & Database Schema

### `users` Table
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | Integer | Primary Key, Auto-increment | Unique identifier |
| `name` | String | Not Null | Full name |
| `email` | String | Unique, Indexed, Not Null | User's email |
| `password_hash` | String | Not Null | Bcrypt hashed password |
| `age` | Integer | Nullable | User's age |
| `gender` | String | Nullable | User's gender |
| `city` | String | Nullable | User's location |
| `diet_pref` | String | Default: 'veg' | veg, non-veg, vegan |
| `language` | String | Default: 'english' | Preferred language |
| `allergies` | Text | Nullable | JSON array of allergens |
| `created_at` | DateTime | Default: CURRENT_TIMESTAMP | Registration date |
| `last_login` | DateTime | Nullable | Last login timestamp |

### `refresh_tokens` Table
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | Integer | Primary Key, Auto-increment | Unique identifier |
| `user_id` | Integer | Foreign Key (`users.id`) | Associated user |
| `token_hash` | String | Unique, Indexed | Hashed refresh token |
| `expires_at` | DateTime | Not Null | Expiration date |
| `revoked` | Integer | Default: 0 | 1 if revoked, else 0 |

## 4. API Contracts

### `POST /auth/register`
- **Request Body**:
  ```json
  {
    "name": "Rahul Sharma",
    "email": "rahul@example.com",
    "password": "SecurePassword123!"
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "success": true,
    "message": "User registered successfully",
    "user_id": 1
  }
  ```

### `POST /auth/login`
- **Request Body**:
  ```json
  {
    "email": "rahul@example.com",
    "password": "SecurePassword123!"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "access_token": "eyJhbG...",
    "refresh_token": "def456...",
    "token_type": "bearer"
  }
  ```

### `PUT /api/profile`
- **Headers**: `Authorization: Bearer <access_token>`
- **Request Body**:
  ```json
  {
    "age": 28,
    "gender": "Male",
    "diet_pref": "veg",
    "allergies": ["peanuts", "dust"]
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "message": "Profile updated"
  }
  ```

## 5. UI Flows & Screen Descriptions
1. **Landing/Login Screen**: Simple form with Email and Password inputs. A link to "Create Account".
2. **Registration Screen**: Form capturing Name, Email, and Password.
3. **Profile Setup Modal/Screen**: Displayed post-login if profile is incomplete, capturing age, gender, diet, and allergies via dropdowns and tag-inputs.

## 6. Edge Cases & Error Handling
- **Duplicate Email**: Return `400 Bad Request` with "Email already registered."
- **Invalid Credentials**: Return `401 Unauthorized` with "Invalid email or password." (Do not reveal which is incorrect).
- **Expired Token**: Protected routes return `401 Unauthorized` indicating token expiration. Frontend should intercept this and use the refresh token to get a new access token.
