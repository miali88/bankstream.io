from fastapi import APIRouter
from app.api import transactions, gocardless, clerk

api_router = APIRouter()

# Include routers
api_router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
api_router.include_router(gocardless.router, prefix="/gocardless", tags=["gocardless"])
api_router.include_router(clerk.router, prefix="/clerk", tags=["clerk"])
