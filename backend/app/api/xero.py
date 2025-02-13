from fastapi import FastAPI, HTTPException, Request, Depends
import httpx
import os
import logging
from typing import Optional
from fastapi.responses import RedirectResponse, JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth
from xero_python.accounting import AccountingApi
from xero_python.api_client import ApiClient, serialize
from xero_python.api_client.configuration import Configuration
from xero_python.api_client.oauth2 import OAuth2Token
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Environment validation
def validate_env():
    required_vars = {
        "XERO_CLIENT_ID": os.getenv("XERO_CLIENT_ID"),
        "XERO_CLIENT_SECRET": os.getenv("XERO_CLIENT_SECRET"),
        "REDIRECT_URI": os.getenv("REDIRECT_URI")
    }
    missing = [key for key, value in required_vars.items() if not value]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    return required_vars

env_vars = validate_env()

app = FastAPI()

# Add session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key="your-secret-key",  # Replace with your secret key
    session_cookie="session"
)

# Settings class
class Settings:
    CLIENT_ID: str = env_vars["XERO_CLIENT_ID"]
    CLIENT_SECRET: str = env_vars["XERO_CLIENT_SECRET"]
    REDIRECT_URI: str = env_vars["REDIRECT_URI"]
    STATE: str = os.getenv("XERO_STATE", "random_state_string")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

settings = Settings()

# Configure OAuth
oauth = OAuth()
oauth.register(
    name="xero",
    client_id=settings.CLIENT_ID,
    client_secret=settings.CLIENT_SECRET,
    authorize_url="https://login.xero.com/identity/connect/authorize",
    authorize_params=None,
    token_url="https://identity.xero.com/connect/token",
    client_kwargs={
        "scope": "offline_access openid profile email accounting.transactions accounting.settings.read",
        "token_endpoint_auth_method": "client_secret_post"
    }
)

# Configure API client
api_client = ApiClient(
    Configuration(
        debug=settings.DEBUG,
        oauth2_token=OAuth2Token(
            client_id=settings.CLIENT_ID,
            client_secret=settings.CLIENT_SECRET
        ),
    ),
    pool_threads=1,
)

# Token management
async def get_token(request: Request) -> Optional[dict]:
    return request.session.get("token")

async def save_token(request: Request, token: dict):
    request.session["token"] = token

@api_client.oauth2_token_getter
async def obtain_xero_oauth2_token():
    return app.state.token

@api_client.oauth2_token_saver
async def store_xero_oauth2_token(token):
    app.state.token = token

# Authentication endpoints
@app.get("/login")
async def login(request: Request):
    logger.info("Starting login process")
    try:
        redirect_uri = settings.REDIRECT_URI
        response = await oauth.xero.authorize_redirect(
            request,
            redirect_uri,
            state=settings.STATE
        )
        return response
    except Exception as e:
        logger.error(f"Login error occurred: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"OAuth error: {str(e)}")

@app.get("/oauth/callback")
async def oauth_callback(request: Request):
    logger.info("OAuth callback received")
    try:
        token = await oauth.xero.authorize_access_token(request)
        await save_token(request, token)
        return RedirectResponse(url="/")
    except Exception as e:
        logger.error(f"Callback error occurred: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"OAuth callback error: {str(e)}")

# Modified chart of accounts endpoint to use token
@app.get("/chart-of-accounts")
async def get_chart_of_accounts(request: Request):
    token = await get_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    headers = {
        "Authorization": f"Bearer {token['access_token']}",
        "Accept": "application/json",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.xero.com/api.xro/2.0/Accounts", headers=headers)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch accounts")
        
        return response.json()


