from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import HTTPException, Request
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
from typing import Dict, Optional

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS"))

# Remove in-memory storage - now using MongoDB
# JWT utilities
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return email
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(request: Request):
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = token.split(" ")[1]
    email = verify_token(token)
    
    # Check if user exists in database
    from app.services.user_service import user_service
    user = await user_service.get_user_by_email(email)
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    if not user.is_active:
        raise HTTPException(status_code=401, detail="User account is inactive")
    
    # Check if access token is expired
    if datetime.utcnow() >= user.token_expires_at:
        raise HTTPException(status_code=401, detail="Access token expired")
    
    return email


async def store_user_tokens(email: str, access_token: str, refresh_token: Optional[str], expires_in: int):
    """Store user tokens in database"""
    from app.services.user_service import user_service
    
    # Check if user exists, if not create them
    user = await user_service.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update user tokens
    await user_service.update_user_tokens(email, access_token, refresh_token, expires_in)

async def get_user_tokens(email: str) -> Optional[Dict]:
    """Get user tokens from database"""
    from app.services.user_service import user_service
    
    user = await user_service.get_user_by_email(email)
    if not user:
        return None
    
    return {
        "access_token": user.access_token,
        "refresh_token": user.refresh_token,
        "expires_at": user.token_expires_at
    }

async def remove_user_tokens(email: str):
    """Remove user tokens (deactivate user)"""
    from app.services.user_service import user_service
    
    # Instead of deleting, we can deactivate the user
    from app.models.user import UserUpdate
    await user_service.update_user(email, UserUpdate(is_active=False))

def is_token_expired(email: str) -> bool:
    """Check if user token is expired - synchronous version for compatibility"""
    # This is now handled in get_current_user
    return False 