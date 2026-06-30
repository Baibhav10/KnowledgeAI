"""
SQLAlchemy engine and session setup.
The engine manages the connection pool to Postgres.
SessionLocal is a factory for creating database sessions per-request.
Base is what all our future ORM models will inherit from.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """
    Dependency for FastAPI routes that need DB access.
    Ensures the session is always closed after the request finishes,
    even if an error occurs.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()