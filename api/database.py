"""
Database configuration for Vercel API
Uses environment variables only (no streamlit secrets)
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# On Vercel, set DATABASE_URL as an environment variable (Project Settings → Environment Variables)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///esan_erp.db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()