# Tasks: Infrastructure & Database Layer

## Module 1: Environment & Dependency Setup
- [ ] **Task 1.1**: Update `backend/.env` to include variables: `APP_ENV=development` and `POSTGRES_URL=postgresql://user:password@localhost:5432/swasthyaai`.
- [ ] **Task 1.2**: Update `requirements.txt` to include `psycopg2-binary` (the PostgreSQL adapter for Python).
- [ ] **Task 1.3**: Ensure `python-dotenv` and `sqlalchemy` are present in `requirements.txt`.

## Module 2: Database Configuration
- [ ] **Task 2.1**: In `backend/db/database.py`, import `os` and load `.env` variables.
- [ ] **Task 2.2**: Implement conditional logic to read `APP_ENV`. If `production`, set `DATABASE_URL` to `POSTGRES_URL`. Else, default to `sqlite:///./swasthyaai.db`.
- [ ] **Task 2.3**: Instantiate the SQLAlchemy `engine`. Ensure SQLite-specific arguments (`connect_args={"check_same_thread": False}`) are applied *only* when the dialect is SQLite.
- [ ] **Task 2.4**: Create the `SessionLocal` factory bound to the dynamic engine, and configure the `Base` declarative class.
- [ ] **Task 2.5**: Define the `get_db()` FastAPI dependency to yield a session and close it in a `finally` block.

## Module 3: Schema Migrations
- [ ] **Task 3.1**: Define all SQLAlchemy models (`User`, `Consultation`, `Expense`, `RefreshToken`, `Notification`) inheriting from `Base`.
- [ ] **Task 3.2**: In `backend/db/database.py`, implement `init_db()`.
- [ ] **Task 3.3**: Inside `init_db()`, call `Base.metadata.create_all(bind=engine)`.
- [ ] **Task 3.4**: Implement safe `ALTER TABLE` statements for the `expenses` table to add `consultation_id` and `source` columns. Use PostgreSQL's `IF NOT EXISTS` syntax when in production, and wrap SQLite's `ALTER TABLE` in `try-except` blocks.

## Module 4: Application Integration
- [ ] **Task 4.1**: In `backend/main.py`, ensure `init_db()` is called during the application startup event (`@app.on_event("startup")` or lifespan context manager).
- [ ] **Task 4.2**: Verify that all FastAPI routers import and utilize `get_db` correctly.
