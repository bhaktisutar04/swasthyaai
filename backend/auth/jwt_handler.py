import os
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from jose import jwt, JWTError, ExpiredSignatureError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_EXPIRE_MINUTES", "1440")) # 24h default
JWT_REFRESH_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_EXPIRE_DAYS", "7"))

def create_access_token(user_id: int) -> str:
    """Creates a JWT access token valid for JWT_ACCESS_EXPIRE_MINUTES."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_ACCESS_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": datetime.now(timezone.utc),
        "exp": expire
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def create_refresh_token(user_id: int) -> str:
    """Creates a JWT refresh token valid for JWT_REFRESH_EXPIRE_DAYS."""
    expire = datetime.now(timezone.utc) + timedelta(days=JWT_REFRESH_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "iat": datetime.now(timezone.utc),
        "exp": expire
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    """Decodes and validates a JWT token. Raises HTTPException on error."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
