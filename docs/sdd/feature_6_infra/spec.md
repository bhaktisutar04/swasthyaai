# Specification: Infrastructure & Database Layer

## 1. Feature Overview
This feature defines the robust, scalable data persistence layer for SwasthyaAI. To balance developer velocity with production readiness, the system is designed to support a dual-database architecture: a lightweight, file-based SQLite database for local development, and a robust PostgreSQL database for production deployments.

## 2. Behavioral Specification

### 2.1 Dual Database Configuration
- **Behavior**: The application must automatically select the appropriate database engine upon startup based on environment variables.
- **Rules**:
  - If the environment variable `APP_ENV` is set to `development` (or omitted), the system connects to a local SQLite database file.
  - If `APP_ENV` is set to `production`, the system connects to a PostgreSQL database using the provided `POSTGRES_URL`.
  - The ORM layer (SQLAlchemy) must abstract the underlying database dialect so that application code remains identical regardless of the active database.

### 2.2 Automated Safe Migrations
- **Behavior**: When the application initializes the database (`init_db`), it must automatically apply structural schema updates without causing data loss or crashes.
- **Rules**:
  - The system must attempt to create all required tables if they do not exist.
  - The system must execute `ALTER TABLE` statements to append newly introduced columns (e.g., `consultation_id`, `source` in the `expenses` table).
  - Migration logic must account for dialect differences (e.g., SQLite does not support `ADD COLUMN IF NOT EXISTS`, requiring `try-except` fallback blocks, whereas PostgreSQL does).

## 3. Data Models & Database Schema

*(This layer governs the creation of all application models defined in previous specs).*

| Model | Primary Purpose | Relationships |
| :--- | :--- | :--- |
| `User` | Authentication and Demographics | 1:N with Consultations, Expenses, RefreshTokens |
| `Consultation` | Stores AI pipeline output JSONs | N:1 with User, 1:N with Expenses |
| `Expense` | Tracks medical and auto-logged costs | N:1 with User, N:1 with Consultation |
| `RefreshToken` | Session security | N:1 with User |

## 4. API Contracts
*(This is an infrastructure-level feature; it does not directly expose HTTP API endpoints. It provides the `get_db()` dependency used by all routes).*

### Dependency Injection
- FastApi routes utilize `Depends(get_db)` to yield an active database session.
- The system must ensure the session is safely closed after the HTTP request is completed (via `try...finally` blocks).

## 5. Deployment Flows
1. **Local Development**: Developer runs `uvicorn main:app`. System reads `.env`, defaults to SQLite, creates `swasthyaai.db` in the local directory, and runs migrations.
2. **Production Deployment**: DevOps sets `APP_ENV=production` and `POSTGRES_URL` in the server environment. Server boots, connects to the remote Postgres instance, and runs `ALTER TABLE` scripts safely.

## 6. Edge Cases & Error Handling
- **Database Connection Failure**: If the `POSTGRES_URL` is invalid or unreachable in production, the application must fail fast during the startup sequence and log a clear connection error.
- **Migration Collisions**: If a migration attempts to add a column that already exists, the system must gracefully catch the `OperationalError` and proceed, ensuring application boot is not halted.
