from fastapi import APIRouter

from src.api.routes import auth, health, profiles

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(profiles.router)
