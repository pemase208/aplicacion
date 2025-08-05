from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from decouple import config
import os

# Database URL
DATABASE_URL = config(
    "DATABASE_URL",
    default="postgresql://user:password@localhost:5432/app_db"
)

# Create database engine
engine = create_engine(DATABASE_URL)

# Create session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()