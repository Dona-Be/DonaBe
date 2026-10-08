from sqlalchemy import create_engine

from src.core.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, hide_parameters=True)
