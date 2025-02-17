from fastapi import FastAPI, HTTPException, Request, Depends, APIRouter
import httpx
import os
import logging
from typing import Optional, List
import uuid
import json
import urllib.parse

from fastapi.responses import RedirectResponse, JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth
from xero_python.accounting import AccountingApi
from xero_python.api_client import ApiClient, serialize
from xero_python.api_client.configuration import Configuration
from xero_python.api_client.oauth2 import OAuth2Token
from dotenv import load_dotenv

from app.services.xero import store_xero_credentials, get_xero_credentials, delete_xero_credentials
from app.services.supabase import get_supabase
from app.core.auth import get_current_user, validate_token

# Load and validate environment variables
load_dotenv()

# Settings class for better configuration management
class Settings:
    XERO_CLIENT_ID = os.getenv("XERO_CLIENT_ID")
    XERO_CLIENT_SECRET = os.getenv("XERO_CLIENT_SECRET")
    XERO_REDIRECT_URI = os.getenv("XERO_REDIRECT_URI")
    XERO_STATE = os.getenv("XERO_STATE", str(uuid.uuid4()))
    XERO_DEBUG = os.getenv("XERO_DEBUG", "False").lower() == "true"

    def validate(self):
        if not all([self.XERO_CLIENT_ID, self.XERO_CLIENT_SECRET, self.XERO_REDIRECT_URI]):
            raise ValueError("Missing required Xero environment variables. Please check XERO_CLIENT_ID, XERO_CLIENT_SECRET, XERO_REDIRECT_URI")

settings = Settings()
settings.validate()

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter()

# Configure OAuth
oauth = OAuth()
oauth.register(
    name="xero",
    client_id=settings.XERO_CLIENT_ID,
    client_secret=settings.XERO_CLIENT_SECRET,
    authorize_url="https://login.xero.com/identity/connect/authorize",
    authorize_params=None,
    token_url="https://identity.xero.com/connect/token",
    client_kwargs={
        "scope": "offline_access openid profile email accounting.transactions "
                "accounting.transactions.read accounting.reports.read "
                "accounting.journals.read accounting.settings accounting.settings.read "
                "accounting.contacts accounting.contacts.read accounting.attachments "
                "accounting.attachments.read assets projects files",
        "token_endpoint_auth_method": "client_secret_post"
    },
    server_metadata_url="https://identity.xero.com/.well-known/openid-configuration"
)

# Configure API client
api_client = ApiClient(
    Configuration(
        debug=settings.XERO_DEBUG,
        oauth2_token=OAuth2Token(
            client_id=settings.XERO_CLIENT_ID,
            client_secret=settings.XERO_CLIENT_SECRET
        ),
    ),
    pool_threads=1,
)

# Token management
async def get_token(request: Request) -> Optional[dict]:
    return request.session.get("token")

async def save_token(request: Request, token: dict):
    request.session["token"] = token
    request.app.state.token = token

@api_client.oauth2_token_getter
async def obtain_xero_oauth2_token():
    request = Request.get_current()
    return request.app.state.token if hasattr(request.app.state, 'token') else None

@api_client.oauth2_token_saver
async def store_xero_oauth2_token(token):
    request = Request.get_current()
    request.app.state.token = token

# Authentication endpoints
@router.get("/login")
async def login(request: Request):
    logger.info("Starting login process")
    try:
        logger.debug(f"Using redirect URI: {settings.XERO_REDIRECT_URI}")
        
        # Get state from query params which includes Clerk token
        state = request.query_params.get('state')
        if not state:
            raise HTTPException(status_code=400, detail="Missing state parameter")
            
        # Validate state is proper JSON
        try:
            state_data = json.loads(state)
            if not state_data.get('clerk_token'):
                raise HTTPException(status_code=400, detail="Missing clerk_token in state")
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid state JSON")
        
        logger.debug(f"Received valid state with clerk token")
        
        auth_params = {
            "response_type": "code",
            "client_id": settings.XERO_CLIENT_ID,
            "redirect_uri": settings.XERO_REDIRECT_URI,
            "scope": oauth.xero.client_kwargs["scope"],
            "state": state
        }
        logger.debug(f"Authorization parameters: {auth_params}")
        
        response = await oauth.xero.authorize_redirect(
            request,
            settings.XERO_REDIRECT_URI,
            state=state
        )
        logger.info("Successfully generated authorization redirect")
        logger.debug(f"Redirect URL: {response.headers.get('location')}")
        return response
    except Exception as e:
        logger.error(f"Login error occurred: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"OAuth error: {str(e)}")

@router.get("/oauth/callback")
async def oauth_callback(request: Request):
    logger.info("OAuth callback received")
    try:
        # Log the incoming request parameters
        params = dict(request.query_params)
        logger.debug(f"Callback parameters received: {params}")
        
        if 'error' in params:
            logger.error(f"OAuth error returned: {params.get('error')}")
            logger.error(f"Error description: {params.get('error_description')}")
            raise HTTPException(status_code=400, detail=params.get('error_description'))
        
        # Ensure we have the authorization code
        if 'code' not in params:
            logger.error("No authorization code received in callback")
            raise HTTPException(status_code=400, detail="No authorization code received")
        
        # Get state parameter and extract Clerk token
        state = params.get('state')
        if not state:
            raise HTTPException(status_code=400, detail="Missing state parameter")
            
        try:
            state_data = json.loads(urllib.parse.unquote(state))
            clerk_token = state_data.get('clerk_token')
            if not clerk_token:
                raise HTTPException(status_code=400, detail="Missing Clerk token in state")
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid state parameter")
            
        # Get user_id from Clerk token using validate_token directly
        user_id = await validate_token(clerk_token)
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid Clerk token")
            
        # Get access token from Xero
        token = await oauth.xero.authorize_access_token(request)
        logger.info("Successfully obtained access token")
        logger.debug(f"Token type: {token.get('token_type')}")
        logger.debug(f"Expires in: {token.get('expires_in')}")
        
        # Save token to session for immediate use
        await save_token(request, token)
        
        # Get Xero tenant connections
        async with httpx.AsyncClient() as client:
            connections_response = await client.get(
                'https://api.xero.com/connections',
                headers={'Authorization': f"Bearer {token['access_token']}"}
            )
            
            if connections_response.status_code != 200:
                logger.error(f"Failed to get Xero connections: {connections_response.text}")
                raise HTTPException(
                    status_code=connections_response.status_code,
                    detail="Failed to get Xero tenant connections"
                )
            
            tenant_connections = connections_response.json()
            
            if not tenant_connections:
                logger.error("No Xero tenants found in connections response")
                raise HTTPException(
                    status_code=400,
                    detail="No Xero organizations found. Please ensure you have access to at least one Xero organization."
                )
            
            # Store credentials for each tenant
            for tenant in tenant_connections:
                tenant_id = tenant.get('tenantId')
                if not tenant_id:
                    logger.warning(f"Tenant missing tenantId: {tenant}")
                    continue
                    
                # Add tenant info to token data
                token_data = {
                    **token,
                    'tenant_id': tenant_id,
                    'tenant_name': tenant.get('tenantName', 'Unknown Organization')
                }
                
                await store_xero_credentials(user_id, token_data)
            
            logger.info(f"Successfully stored credentials for {len(tenant_connections)} tenants")
        
        # Redirect to the frontend application
        frontend_url = f"{os.getenv('FRONTEND_URL')}/dashboard/transactions"
        return RedirectResponse(url=frontend_url)
        
    except Exception as e:
        logger.error(f"Callback error occurred: {str(e)}")
        logger.exception("Full callback error details:")
        raise HTTPException(status_code=400, detail=f"OAuth callback error: {str(e)}")

@router.get("/chart-of-accounts")
async def get_chart_of_accounts(
    request: Request, 
    tenant_id: str,
    user_id: str = Depends(get_current_user)
):
    # Get credentials from database
    credentials = await get_xero_credentials(user_id, tenant_id)
    if not credentials:
        raise HTTPException(status_code=401, detail="Xero credentials not found or expired")

    headers = {
        "Authorization": f"Bearer {credentials['access_token']}",
        "Accept": "application/json",
        "Xero-tenant-id": tenant_id
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.xero.com/api.xro/2.0/Accounts",
            headers=headers
        )

        if response.status_code != 200:
            if response.status_code == 401:
                # Token might be expired, try to refresh
                # TODO: Implement token refresh logic
                raise HTTPException(status_code=401, detail="Xero token expired")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to fetch accounts: {response.text}"
            )
        
        return response.json()

@router.get("/tenants")
async def get_tenants(user_id: str = Depends(get_current_user)):
    """Get all Xero tenants the user has access to."""
    supabase = await get_supabase()
    result = supabase.table('xero_credentials').select('tenant_id').eq(
        'user_id', user_id
    ).execute()
    
    if hasattr(result, 'error') and result.error is not None:
        raise HTTPException(status_code=500, detail="Failed to fetch tenants")
        
    return {"tenants": [record['tenant_id'] for record in result.data]}

@router.delete("/disconnect")
async def disconnect_xero(
    tenant_id: Optional[str] = None,
    user_id: str = Depends(get_current_user)
):
    """Disconnect Xero integration for a user, optionally for a specific tenant."""
    await delete_xero_credentials(user_id, tenant_id)
    return {"message": "Successfully disconnected from Xero"}

# Function to setup middleware - to be called from main.py
def setup_xero_middleware(app: FastAPI):
    app.add_middleware(
        SessionMiddleware,
        secret_key="your-secret-key",  # Replace with your secret key
        session_cookie="session"
    )


