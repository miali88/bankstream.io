from fastapi import APIRouter
from app.api import auth, database, gocardless

api_router = APIRouter()

# Include routers
api_router.include_router(database.router, prefix="/db", tags=["Database"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(gocardless.router, prefix="/gocardless", tags=["GoCardless"])
