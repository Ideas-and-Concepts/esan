"""
Database Configuration
Uses DATABASE_URL from Streamlit secrets, or defaults to SQLite for local dev.
"""

import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Read from secrets (production) or fallback to SQLite (local development)
DATABASE_URL = st.secrets.get("DATABASE_URL", "sqlite:///esan_erp.db")

# For PostgreSQL, we don't need check_same_thread
if "postgresql" in DATABASE_URL:
    engine = create_engine(DATABASE_URL)
else:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()