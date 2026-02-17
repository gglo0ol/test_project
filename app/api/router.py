from fastapi import APIRouter

from app.api.endpoints import orders

# Main API router that aggregates all endpoint routers
api_router = APIRouter(prefix="/api/v1")

# Include all endpoint routers
api_router.include_router(orders.router)
