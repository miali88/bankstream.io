from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()
security = HTTPBearer()

CLERK_API_KEY = os.getenv("CLERK_API_KEY")
CLERK_JWT_KEY = os.getenv("CLERK_JWT_KEY")

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = credentials.credentials
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.clerk.dev/v1/session",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )
        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
        return response.json()

@router.post("/login")
async def login(token: str):
    try:
        # Verify the token with Clerk
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.clerk.dev/v1/session",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            )
            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid authentication")
            return {"message": "Login successful", "user": response.json()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/me")
async def get_current_user(user_data: dict = Depends(verify_token)):
    return user_data

@router.post("/logout")
async def logout(user_data: dict = Depends(verify_token)):
    return {"message": "Logout successful"} 