"""
Database session dependency for FastAPI.
"""

from typing import Generator
from app.db.base import SessionLocal


def get_db() -> Generator:
    """Yield a database session and ensure it's closed after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
