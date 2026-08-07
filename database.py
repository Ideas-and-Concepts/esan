"""
Database Configuration
Works on Streamlit Cloud (with secrets) and Vercel (with env vars).
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Try to import streamlit (only available on Streamlit Cloud)
try:
    import streamlit as st
    IN_STREAMLIT = True
except ImportError:
    IN_STREAMLIT = False

# Get DATABASE_URL – priority: env var, then Streamlit secrets, then SQLite fallback
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL and IN_STREAMLIT:
    DATABASE_URL = st.secrets.get("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///esan_erp.db"

# Create engine accordingly
if "postgresql" in DATABASE_URL:
    engine = create_engine(DATABASE_URL)
else:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()