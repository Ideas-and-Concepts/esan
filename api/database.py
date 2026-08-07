"""
Database configuration – works on Vercel, Streamlit Cloud, and locally.
Does NOT import streamlit unless it is actually available.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ------------------------------------------------------------------
# 1. Environment variable (set in Vercel dashboard)
# ------------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL")

# ------------------------------------------------------------------
# 2. Fallback: SQLite in /tmp (writable on Vercel) or local file
# ------------------------------------------------------------------
if not DATABASE_URL:
    # On Vercel, only /tmp is writable
    if os.path.isdir("/tmp"):
        DATABASE_URL = "sqlite:////tmp/esan_erp.db"
    else:
        DATABASE_URL = "sqlite:///esan_erp.db"

# ------------------------------------------------------------------
# 3. Create engine
# ------------------------------------------------------------------
if "postgresql" in DATABASE_URL:
    engine = create_engine(DATABASE_URL)
else:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()