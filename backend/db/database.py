import os
from datetime import datetime
from dotenv import load_dotenv

from sqlalchemy import create_engine, Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey, text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

# Load environment variables from .env file
load_dotenv()

APP_ENV = os.getenv("APP_ENV", "development")

if APP_ENV == "production":
    DATABASE_URL = os.getenv("POSTGRES_URL")
    engine = create_engine(DATABASE_URL)
else:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./swasthyaai.db")
    # SQLAlchemy setup. check_same_thread=False is needed for SQLite in FastAPI.
    engine = create_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}
    )
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    age = Column(Integer)
    gender = Column(String)
    city = Column(String)
    diet_pref = Column(String, default="veg")
    language = Column(String, default="english")
    allergies = Column(Text)  # Stores JSON array as Text
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    consultations = relationship("Consultation", back_populates="user")
    expenses = relationship("Expense", back_populates="user")
    refresh_tokens = relationship("RefreshToken", back_populates="user")
    notifications = relationship("Notification", back_populates="user")

class Consultation(Base):
    __tablename__ = "consultations"

    id = Column(Integer, primary_key=True, index=True)
    consultation_id = Column(String, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    session_date = Column(DateTime, index=True)
    status = Column(String, default="in_progress")
    symptoms = Column(Text)
    duration = Column(String)
    severity = Column(String)
    emergency_flag = Column(Boolean, default=False)
    conditions = Column(Text)
    medicines = Column(Text)
    specialist_type = Column(String)
    severity_flag = Column(String)
    see_doctor = Column(Boolean, default=False)
    deficiencies = Column(Text)
    meal_plan = Column(Text)
    daily_intake = Column(Text)
    recommended_intake = Column(Text)
    monthly_total = Column(Float)
    expense_breakdown = Column(Text)
    savings_estimate = Column(Float)
    pdf_path = Column(String)
    pdf_generated_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="consultations")
    expenses = relationship("Expense", back_populates="consultation")

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    consultation_id = Column(String, ForeignKey("consultations.consultation_id"))
    expense_date = Column(DateTime, index=True)
    category = Column(String)
    amount = Column(Float)
    description = Column(Text)
    source = Column(String, default="manual")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="expenses")
    consultation = relationship("Consultation", back_populates="expenses")

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    token_hash = Column(String, unique=True, index=True)
    expires_at = Column(DateTime)
    revoked = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="refresh_tokens")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(Text)
    type = Column(String)
    due_date = Column(DateTime, nullable=True)
    is_read = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")

def init_db():
    """Create all tables and run safe migrations"""
    Base.metadata.create_all(bind=engine)
    
    # Safe column migrations
    try:
        with engine.connect() as conn:
            if APP_ENV == "production":
                conn.execute(text(
                    "ALTER TABLE expenses ADD COLUMN IF NOT EXISTS "
                    "consultation_id VARCHAR"
                ))
                conn.execute(text(
                    "ALTER TABLE expenses ADD COLUMN IF NOT EXISTS "
                    "source VARCHAR DEFAULT 'manual'"
                ))
            else:
                # SQLite does not support IF NOT EXISTS
                try:
                    conn.execute(text(
                        "ALTER TABLE expenses ADD COLUMN "
                        "consultation_id VARCHAR"
                    ))
                except:
                    pass
                try:
                    conn.execute(text(
                        "ALTER TABLE expenses ADD COLUMN "
                        "source VARCHAR DEFAULT 'manual'"
                    ))
                except:
                    pass
            conn.commit()
    except Exception as e:
        print(f"Migration note: {e}")

def get_db():
    """FastAPI dependency to get DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

