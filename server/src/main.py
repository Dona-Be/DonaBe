from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from src.api.error_handlers import register_error_handlers
from src.api.middleware import NoStoreCacheMiddleware
from src.api.routes import api_router
from src.core.config import settings

OAUTH_STATE_MAX_AGE_SECONDS = 10 * 60

app = FastAPI(docs_url="/api/docs", openapi_url="/api/openapi.json", redoc_url=None)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET_KEY,
    max_age=OAUTH_STATE_MAX_AGE_SECONDS,
    https_only=settings.is_production,
)
app.add_middleware(NoStoreCacheMiddleware)
app.include_router(api_router, prefix="/api")
register_error_handlers(app)
