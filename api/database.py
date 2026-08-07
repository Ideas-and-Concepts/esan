"""
Database Configuration
Works on Streamlit Cloud, Vercel, and locally.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Detect if Streamlit is available
try:
    import streamlit as st
    IN_STREAMLIT = True
except ImportError:
    IN_STREAMLIT = False

# 1. Environment variable
DATABASE_URL = os.getenv("DATABASE_URL")
# 2. Streamlit secrets
if not DATABASE_URL and IN_STREAMLIT:
    DATABASE_URL = st.secrets.get("DATABASE_URL")
# 3. Fallback to SQLite in a writable location
if not DATABASE_URL:
    # On Vercel (and most serverless), /tmp is the only writable directory
    if os.path.isdir("/tmp"):
        DATABASE_URL = "sqlite:////tmp/esan_erp.db"
    else:
        DATABASE_URL = "sqlite:///esan_erp.db"

# Create engine
if "postgresql" in DATABASE_URL:
    engine = create_engine(DATABASE_URL)
else:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()