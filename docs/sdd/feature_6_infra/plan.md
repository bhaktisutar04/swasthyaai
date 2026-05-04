# Technical Plan: Infrastructure & Database Layer

## 1. Architecture Overview

```text
[ .env Configuration ]
        |
        v
[ APP_ENV Check ]
        |
    +---+---+
    |       |
[ dev ]   [ prod ]
    |       |
[ SQLite] [ PostgreSQL ]
    |       |
    +---+---+
        |
        v
[ SQLAlchemy Engine ]
        |
[ init_db() Migrations ] ---> [ Database Tables ]
        |
[ SessionLocal Factory ] ---> [ FastAPI Dependency Injection ]
```

## 2. Tech Stack & Rationale
- **SQLAlchemy**: The undisputed standard for Python ORMs. It allows us to define models once using Python classes and interact with them using standard Python objects, seamlessly translating queries to either SQLite or PostgreSQL dialects.
- **psycopg2-binary**: The necessary database adapter (driver) that allows Python to interface with PostgreSQL databases efficiently in production.
- **python-dotenv**: Allows secure parsing of `.env` files to keep sensitive database URLs and keys out of version control.

## 3. Component Breakdown
1. **Environment Configuration (`backend/.env`)**:
   - Variables: `APP_ENV`, `DATABASE_URL`, `POSTGRES_URL`.
2. **Database Module (`backend/db/database.py`)**:
   - Reads `APP_ENV`. If `production`, instantiates the engine using `POSTGRES_URL`. Otherwise, uses `DATABASE_URL` (SQLite).
   - Configures SQLite-specific arguments (`connect_args={"check_same_thread": False}`) necessary for FastAPI's async thread pooling.
   - Defines `Base = declarative_base()` from which all models inherit.
   - Provides the `get_db()` generator function for dependency injection.
3. **Migration Logic (`init_db` within `database.py`)**:
   - Calls `Base.metadata.create_all()` to ensure base tables exist.
   - Executes raw SQL via `sqlalchemy.text` to apply `ALTER TABLE` commands. Includes specific `try-except` blocks to handle SQLite's lack of `IF NOT EXISTS` for column creation.
4. **Dependencies (`requirements.txt`)**:
   - Ensure `sqlalchemy` and `psycopg2-binary` are explicitly version-locked.

## 4. Dependencies & Risks
### Dependencies
- `SQLAlchemy`
- `psycopg2-binary`
- `python-dotenv`

### Risks & Mitigations
- **Risk**: SQLite and PostgreSQL handle certain data types differently (e.g., Boolean, JSON).
  - **Mitigation**: SwasthyaAI standardizes complex data structures (like arrays of symptoms or dictionaries) by dumping them to JSON strings and storing them in SQLAlchemy `Text` columns. This ensures 100% cross-compatibility between the two databases without relying on Postgres-specific `JSONB` fields.
- **Risk**: Production database credentials leaked via source control.
  - **Mitigation**: Strictly enforce `.gitignore` rules for `.env` files. Ensure deployment platforms (e.g., Render, Heroku) inject environment variables directly into the OS rather than via files.
