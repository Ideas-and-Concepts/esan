import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Detect environment
try:
    import streamlit as st
    IN_STREAMLIT = True
except ImportError:
    IN_STREAMLIT = False

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL and IN_STREAMLIT:
    DATABASE_URL = st.secrets.get("DATABASE_URL")
if not DATABASE_URL:
    if os.path.exists("/tmp"):
        DATABASE_URL = "sqlite:////tmp/esan_erp.db"
    else:
        DATABASE_URL = "sqlite:///esan_erp.db"

if "postgresql" in DATABASE_URL:
    engine = create_engine(DATABASE_URL)
else:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()