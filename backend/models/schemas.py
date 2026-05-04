import re
from datetime import date
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator

class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=50, pattern=r"^[A-Za-z\s\-]+$")
    email: EmailStr
    password: str = Field(min_length=8)
    age: int = Field(ge=1, le=120)
    gender: str
    city: str = Field(min_length=2)
    diet_pref: str
    language: str = "english"
    allergies: List[str] = Field(default_factory=list)
    terms_accepted: bool

    @field_validator("email", mode="after")
    @classmethod
    def email_to_lower(cls, v: str) -> str:
        return v.lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*]", v):
            raise ValueError("Password must contain at least one special character from !@#$%^&*")
        return v

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: str) -> str:
        valid_genders = ["Male", "Female", "Other", "Prefer not to say"]
        if v not in valid_genders:
            raise ValueError(f"Gender must be one of {valid_genders}")
        return v

    @field_validator("diet_pref")
    @classmethod
    def validate_diet_pref(cls, v: str) -> str:
        valid_diets = ["veg", "non-veg", "vegan"]
        if v not in valid_diets:
            raise ValueError(f"Diet preference must be one of {valid_diets}")
        return v

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        valid_languages = ["english", "hindi", "marathi"]
        if v not in valid_languages:
            raise ValueError(f"Language must be one of {valid_languages}")
        return v

    @field_validator("terms_accepted")
    @classmethod
    def validate_terms(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Terms must be accepted (terms_accepted must be True)")
        return v

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class LogoutRequest(BaseModel):
    refresh_token: str

class UpdateProfileRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=50, pattern=r"^[A-Za-z\s\-]+$")
    age: Optional[int] = Field(None, ge=1, le=120)
    city: Optional[str] = Field(None, min_length=2)
    diet_pref: Optional[str] = None
    language: Optional[str] = None
    allergies: Optional[List[str]] = None

    @field_validator("diet_pref")
    @classmethod
    def validate_diet_pref(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ["veg", "non-veg", "vegan"]:
            raise ValueError("Diet preference must be one of ['veg', 'non-veg', 'vegan']")
        return v

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ["english", "hindi", "marathi"]:
            raise ValueError("Language must be one of ['english', 'hindi', 'marathi']")
        return v

class ExpenseRequest(BaseModel):
    expense_date: date
    category: str
    amount: float = Field(gt=0)
    description: Optional[str] = None
    consultation_id: Optional[str] = None

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        valid_categories = ["medicine", "consultation", "tests", "hospital", "other"]
        if v not in valid_categories:
            raise ValueError(f"Category must be one of {valid_categories}")
        return v

class MealLogRequest(BaseModel):
    session_id: str
    meal_type: str
    items: List[str]
    date: date

class ConsultationMessageRequest(BaseModel):
    session_id: str
    message: str
