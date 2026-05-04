import json
import hashlib
import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from db.database import get_db, User, RefreshToken
from models.schemas import RegisterRequest, LoginRequest, RefreshTokenRequest, LogoutRequest, UpdateProfileRequest
from auth.password import hash_password, verify_password
from auth.jwt_handler import create_access_token, create_refresh_token, decode_token, JWT_REFRESH_EXPIRE_DAYS
from auth.rate_limiter import check_rate_limit, record_attempt, reset_attempts
from auth.dependencies import get_current_user

router = APIRouter()

def hash_token(token: str) -> str:
    """Helper function to hash tokens for DB storage"""
    return hashlib.sha256(token.encode('utf-8')).hexdigest()

def create_error_response(status_code: int, error_code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": error_code,
            "message": message
        }
    )

@router.post("/register")
def register_user(request: RegisterRequest, db: Session = Depends(get_db)):
    # Check email uniqueness
    existing_user = db.query(User).filter(User.email.ilike(request.email)).first()
    if existing_user:
        return create_error_response(409, "EMAIL_EXISTS", "Email already registered")

    # hash_password, insert user
    hashed_pw = hash_password(request.password)
    allergies_json = json.dumps(request.allergies) if request.allergies else "[]"
    
    new_user = User(
        name=request.name,
        email=request.email.lower(),
        password_hash=hashed_pw,
        age=request.age,
        gender=request.gender,
        city=request.city,
        diet_pref=request.diet_pref,
        language=request.language,
        allergies=allergies_json,
        created_at=datetime.utcnow()
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # generate access + refresh tokens
    access_token = create_access_token(new_user.id)
    refresh_token = create_refresh_token(new_user.id)

    # store hashed refresh token in refresh_tokens table
    token_hash = hash_token(refresh_token)
    expires_at = datetime.utcnow() + timedelta(days=JWT_REFRESH_EXPIRE_DAYS)
    
    rt_record = RefreshToken(
        user_id=new_user.id,
        token_hash=token_hash,
        expires_at=expires_at,
        revoked=0,
        created_at=datetime.utcnow()
    )
    db.add(rt_record)
    db.commit()

    return {
        "success": True,
        "data": {
            "user_id": new_user.id,
            "name": new_user.name,
            "email": new_user.email,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer"
        }
    }

@router.post("/login")
def login_user(request: LoginRequest, db: Session = Depends(get_db)):
    email_lower = request.email.lower()
    
    if not check_rate_limit(email_lower):
        return create_error_response(429, "RATE_LIMIT_EXCEEDED", "Too many login attempts. Please try again later.")

    user = db.query(User).filter(User.email.ilike(email_lower)).first()
    if not user:
        record_attempt(email_lower)
        return create_error_response(401, "INVALID_CREDENTIALS", "Invalid email or password")

    if not verify_password(request.password, user.password_hash):
        record_attempt(email_lower)
        return create_error_response(401, "INVALID_CREDENTIALS", "Invalid email or password")

    reset_attempts(email_lower)
    
    user.last_login = datetime.utcnow()
    db.commit()

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    token_hash = hash_token(refresh_token)
    expires_at = datetime.utcnow() + timedelta(days=JWT_REFRESH_EXPIRE_DAYS)
    
    rt_record = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
        revoked=0,
        created_at=datetime.utcnow()
    )
    db.add(rt_record)
    db.commit()

    allergies_list = []
    if user.allergies:
        try:
            allergies_list = json.loads(user.allergies)
        except json.JSONDecodeError:
            allergies_list = []

    return {
        "success": True, 
        "data": {
            "user_id": user.id, 
            "name": user.name, 
            "access_token": access_token, 
            "refresh_token": refresh_token, 
            "token_type": "Bearer", 
            "profile": {
                "age": user.age, 
                "city": user.city, 
                "diet_pref": user.diet_pref, 
                "language": user.language, 
                "allergies": allergies_list
            }
        }
    }

@router.post("/refresh")
def refresh_access_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    try:
        # decode_token will raise HTTPException if invalid/expired
        payload = decode_token(request.refresh_token)
    except HTTPException:
        return create_error_response(401, "INVALID_TOKEN", "Invalid or expired refresh token")

    if payload.get("type") != "refresh":
        return create_error_response(401, "INVALID_TOKEN", "Provided token is not a refresh token")

    token_hash = hash_token(request.refresh_token)
    rt_record = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    
    if not rt_record:
        return create_error_response(401, "INVALID_TOKEN", "Refresh token not found")
        
    if rt_record.revoked == 1:
        return create_error_response(401, "TOKEN_REVOKED", "Refresh token has been revoked")
        
    if getattr(rt_record, 'expires_at') and rt_record.expires_at < datetime.utcnow():
        return create_error_response(401, "TOKEN_EXPIRED", "Refresh token has expired")

    user_id = int(payload.get("sub"))
    new_access_token = create_access_token(user_id)

    return {
        "success": True, 
        "data": {
            "access_token": new_access_token, 
            "token_type": "Bearer"
        }
    }

@router.post("/logout")
def logout_user(request: LogoutRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    token_hash = hash_token(request.refresh_token)
    rt_record = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    
    if rt_record and rt_record.user_id == current_user.id:
        rt_record.revoked = 1
        db.commit()
        
    return {
        "success": True, 
        "message": "Logged out successfully"
    }

@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    allergies_list = []
    if current_user.allergies:
        try:
            allergies_list = json.loads(current_user.allergies)
        except json.JSONDecodeError:
            allergies_list = []
            
    return {
        "success": True, 
        "data": {
            "user_id": current_user.id, 
            "name": current_user.name, 
            "email": current_user.email, 
            "age": current_user.age, 
            "gender": current_user.gender, 
            "city": current_user.city, 
            "diet_pref": current_user.diet_pref, 
            "language": current_user.language, 
            "allergies": allergies_list, 
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None
        }
    }

@router.patch("/profile")
def update_profile(request: UpdateProfileRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    update_data = request.model_dump(exclude_unset=True)
    
    if not update_data:
        # Nothing to update
        allergies_list = []
        if current_user.allergies:
            try:
                allergies_list = json.loads(current_user.allergies)
            except json.JSONDecodeError:
                allergies_list = []
        return {
            "success": True, 
            "data": {
                "name": current_user.name,
                "age": current_user.age,
                "city": current_user.city,
                "diet_pref": current_user.diet_pref,
                "language": current_user.language,
                "allergies": allergies_list
            },
            "message": "Profile updated successfully"
        }

    if "allergies" in update_data:
        current_user.allergies = json.dumps(update_data["allergies"])
    if "name" in update_data:
        current_user.name = update_data["name"]
    if "age" in update_data:
        current_user.age = update_data["age"]
    if "city" in update_data:
        current_user.city = update_data["city"]
    if "diet_pref" in update_data:
        current_user.diet_pref = update_data["diet_pref"]
    if "language" in update_data:
        current_user.language = update_data["language"]
        
    db.commit()
    db.refresh(current_user)
    
    allergies_list = []
    if current_user.allergies:
        try:
            allergies_list = json.loads(current_user.allergies)
        except json.JSONDecodeError:
            allergies_list = []
            
    return {
        "success": True, 
        "data": {
            "name": current_user.name,
            "age": current_user.age,
            "city": current_user.city,
            "diet_pref": current_user.diet_pref,
            "language": current_user.language,
            "allergies": allergies_list
        }, 
        "message": "Profile updated successfully"
    }

