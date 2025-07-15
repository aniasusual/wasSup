from fastapi import APIRouter
from fastapi import HTTPException, Depends
from fastapi.responses import RedirectResponse
import httpx
import os
from datetime import datetime, timedelta
from ..helpers.authHelper import get_current_user, create_access_token, store_user_tokens, get_user_tokens, remove_user_tokens

router = APIRouter(tags=["auth"])

# @router.get("/auth/login")
# async def login():
#     return {"message": "Hello, World!"}

# Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS"))

# Google OAuth2 URLs
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

# OAuth2 endpoints
@router.get("/auth/login")
async def login():
    """Redirect to Google OAuth2 login"""
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": (
            "openid email profile "
            "https://www.googleapis.com/auth/logging.read "
            "https://www.googleapis.com/auth/cloud-platform"
        ),
        "access_type": "offline",
        "prompt": "consent"
    }
    auth_url = f"{GOOGLE_AUTH_URL}?" + "&".join([f"{k}={v}" for k, v in params.items()])
    return {"auth_url": auth_url}

@router.get("/auth/callback")
async def auth_callback(code: str):
    """Handle Google OAuth2 callback"""
    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code"
            }
        )
        
        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to exchange code for token")
        
        tokens = token_response.json()
        
        # Get user info
        user_response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        
        if user_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get user info")
        
        user_info = user_response.json()
        email = user_info["email"]
        
        # Store tokens using shared token manager
        store_user_tokens(
            email=email,
            access_token=tokens["access_token"],
            refresh_token=tokens.get("refresh_token"),
            expires_in=tokens["expires_in"]
        )
        
        # Create JWT for frontend
        jwt_token = create_access_token({"sub": email})

        print(f"{FRONTEND_URL}/auth/success?token={jwt_token}")
        
        # Redirect to frontend with token
        return RedirectResponse(url=f"{FRONTEND_URL}/auth/success?token={jwt_token}")

@router.post("/auth/refresh")
async def refresh_token(current_user: str = Depends(get_current_user)):
    """Refresh Google access token"""
    user_token_data = get_user_tokens(current_user)
    if not user_token_data or not user_token_data.get("refresh_token"):
        raise HTTPException(status_code=400, detail="No refresh token available")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "refresh_token": user_token_data["refresh_token"],
                "grant_type": "refresh_token"
            }
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to refresh token")
        
        new_tokens = response.json()
        store_user_tokens(
            email=current_user,
            access_token=new_tokens["access_token"],
            refresh_token=user_token_data.get("refresh_token"),
            expires_in=new_tokens["expires_in"]
        )
        
        return {"success": True}

@router.get("/auth/logout")
async def logout(current_user: str = Depends(get_current_user)):
    """Logout user"""
    remove_user_tokens(current_user)
    return {"success": True}
