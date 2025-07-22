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

user_tokens: Dict[str, Dict] = {}
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
    
    if email not in user_tokens:
        raise HTTPException(status_code=401, detail="User not found")
    
    return email


def store_user_tokens(email: str, access_token: str, refresh_token: Optional[str], expires_in: int):
    """Store user tokens"""
    user_tokens[email] = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_at": datetime.utcnow() + timedelta(seconds=expires_in)
    }

    # print("userTokens", user_tokens)

def get_user_tokens(email: str) -> Optional[Dict]:
    """Get user tokens"""
    return user_tokens.get(email)

def remove_user_tokens(email: str):
    """Remove user tokens"""
    if email in user_tokens:
        del user_tokens[email]

def is_token_expired(email: str) -> bool:
    """Check if user token is expired"""
    user_token_data = user_tokens.get(email)
    if not user_token_data:
        return True
    return datetime.utcnow() >= user_token_data["expires_at"] 