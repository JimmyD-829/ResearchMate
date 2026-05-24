from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
import logging

logger = logging.getLogger(__name__)

load_dotenv()

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "")

logger.info(f"DATABASE_URL from env: {SQLALCHEMY_DATABASE_URL[:20]}..." if SQLALCHEMY_DATABASE_URL else "DATABASE_URL not set")

if not SQLALCHEMY_DATABASE_URL or not SQLALCHEMY_DATABASE_URL.startswith(("postgresql://", "sqlite://", "mysql://", "oracle://")):
    logger.warning("Invalid or empty DATABASE_URL, falling back to SQLite")
    SQLALCHEMY_DATABASE_URL = "sqlite:///./researchmate.db"

if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()