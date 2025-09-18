from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import HTTPException, Request
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import httpx

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
    # Deprecated: Token freshness should be handled via ensure_fresh_access_token
    return False 


# ---- Google OAuth token refresh (YYY) ----

GOOGLE_TOKEN_URL = os.getenv("GOOGLE_TOKEN_URL", "https://oauth2.googleapis.com/token")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")


def _needs_refresh(expires_at: Optional[datetime], skew_seconds: int = 120) -> bool:
    if not expires_at:
        return True
    try:
        now = datetime.utcnow()
        return now + timedelta(seconds=skew_seconds) >= expires_at
    except Exception:
        return True


async def _refresh_google_access_token(email: str, refresh_token: str) -> Tuple[str, int]:
    """Refresh Google access token via OAuth2 refresh_token grant.

    Returns:
        (access_token, expires_in_seconds)
    """
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=400, detail=f"Failed to refresh token: {resp.text}")
    data = resp.json()
    return data["access_token"], data.get("expires_in", 3600)


async def ensure_fresh_access_token(email: str, skew_seconds: int = 120) -> str:
    """Return a fresh Google access token for the user.

    - Reads tokens from DB
    - If near expiry (within skew) or expired, refreshes and updates DB
    - Returns a valid access token string
    """
    from app.services.user_service import user_service

    user = await user_service.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # If token is missing or close to expiry, refresh
    if _needs_refresh(getattr(user, "token_expires_at", None), skew_seconds):
        if not user.refresh_token:
            raise HTTPException(status_code=401, detail="No refresh token available")
        new_access, expires_in = await _refresh_google_access_token(email, user.refresh_token)
        # Persist updated token
        await user_service.update_user_tokens(email, new_access, user.refresh_token, expires_in)
        return new_access

    # Otherwise return current access token
    if not user.access_token:
        raise HTTPException(status_code=401, detail="Missing access token")
    return user.access_token
