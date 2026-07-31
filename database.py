"""
Database Configuration
- Uses DATABASE_URL from Streamlit secrets if valid.
- Falls back to SQLite for local dev or invalid placeholders.
"""

import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Get the secret (or None)
raw_url = st.secrets.get("DATABASE_URL", "")

# Detect obvious placeholder strings
INVALID_PLACEHOLDERS = ["your_real_user", "your_real_password", "ep-xxxx", "username:password"]

if raw_url and not any(p in raw_url for p in INVALID_PLACEHOLDERS):
    DATABASE_URL = raw_url
else:
    # Fallback to SQLite (local / no valid secret)
    DATABASE_URL = "sqlite:///esan_erp.db"

# Create engine accordingly
if "postgresql" in DATABASE_URL:
    engine = create_engine(DATABASE_URL)
else:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()