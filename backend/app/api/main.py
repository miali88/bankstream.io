from fastapi import APIRouter
from app.api import transactions, auth, gocardless

api_router = APIRouter()

# Include routers
api_router.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])
api_router.include_router(gocardless.router, prefix="/gocardless", tags=["GoCardless"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
