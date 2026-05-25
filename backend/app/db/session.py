from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Create the SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL, 
    pool_pre_ping=True
)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    FastAPI Dependency to inject database sessions into endpoints.
    Ensures the session is cleanly closed after the request finishes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()