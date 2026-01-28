"""
Database connection and session management.
"""

from typing import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings
from app.models.database import Base


# Create engine
engine = create_engine(
    settings.database_url or "sqlite:///./receipt_ai.db",
    echo=settings.debug,
    pool_pre_ping=True,  # Verify connections before using
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI routes.
    
    Usage:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.
    
    Usage:
        with get_db_session() as db:
            db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """
    Initialize database tables.
    
    In production, use Alembic migrations instead.
    """
    Base.metadata.create_all(bind=engine)


def drop_db():
    """
    Drop all database tables.
    
    WARNING: Use only in development/testing!
    """
    Base.metadata.drop_all(bind=engine)
