"""
Esan ERP Controller
Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Version 1.2.0 Alpha
"""

import streamlit as st
from config import COMPANY_NAME, VERSION
from database import Base, engine, SessionLocal
from models import User  # keep for login
import models           # import the whole module to access all classes
from auth import verify_password
from sqlalchemy import inspect, text

# =====================================
# CRITICAL SERVICE / COMPONENT IMPORTS
# =====================================
try:
    from services.user_service import create_admin
except ImportError:
    def create_admin(db):
        """Fallback: create default admin if missing."""
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            from auth import hash_password
            admin = User(
                username="admin",
                password_hash=hash_password("admin123"),
                role="admin",
                email="admin@nileharvest.com"
            )
            db.add(admin)
            db.commit()

try:
    from components.themes import esan_theme
except ImportError:
    def esan_theme(theme):
        pass

# =====================================
# OPTIONAL SEED DATA
# =====================================
try:
    from seed.seed_data import load_seed_data
except ImportError:
    load_seed_data = None

# =====================================
# MODULE IMPORTS (with fallbacks) – unchanged
# =====================================
module_functions = {
    "Overview": None,
    "🌾 Procurement": None,
    "📦 Warehouse": None,
    "🏭 Milling": None,
    "📦 Packaging": None,
    "🚚 Sales": None,
    "💰 Finance": None,
    "📊 Reports": None,
}
# (same import blocks as before – omitted for brevity, they remain identical)

# =====================================
# PAGE CONFIGURATION
# =====================================
st.set_page_config(page_title="Esan ERP", page_icon="🌾", layout="wide")

# Clean Streamlit UI & bottom nav spacing – unchanged

# =====================================
# DATABASE MIGRATION HELPER
# =====================================
def auto_migrate():
    """Add missing columns to existing tables based on current model definitions."""
    inspector = inspect(engine)
    # Get all model classes from the 'models' module
    model_classes = [
        obj for name, obj in vars(models).items()
        if isinstance(obj, type) and hasattr(obj, '__tablename__')
    ]
    with engine.connect() as conn:
        for model in model_classes:
            table_name = model.__tablename__
            if table_name not in inspector.get_table_names():
                continue  # table doesn't exist yet, create_all will make it
            existing_cols = [col['name'] for col in inspector.get_columns(table_name)]
            # Columns defined in the model (ignore relationships, primary keys handled by create_all)
            for col in model.__table__.columns:
                if col.name not in existing_cols:
                    # Build a simple ALTER TABLE statement (SQLite compatible)
                    col_type = str(col.type).upper()
                    if isinstance(col.type, String):
                        col_type = "VARCHAR"  # SQLite doesn't care, but use standard
                    elif isinstance(col.type, Integer):
                        col_type = "INTEGER"
                    elif isinstance(col.type, Float):
                        col_type = "FLOAT"
                    elif isinstance(col.type, Boolean):
                        col_type = "BOOLEAN"
                    elif isinstance(col.type, DateTime):
                        col_type = "DATETIME"
                    elif isinstance(col.type, Text):
                        col_type = "TEXT"
                    else:
                        col_type = "TEXT"  # fallback
                    nullable = "" if col.nullable else " NOT NULL DEFAULT ''"
                    conn.exec_driver_sql(
                        f"ALTER TABLE {table_name} ADD COLUMN {col.name} {col_type}{nullable}"
                    )
        conn.commit()

# =====================================
# DATABASE INITIALIZATION
# =====================================
try:
    Base.metadata.create_all(bind=engine)    # create missing tables
    auto_migrate()                           # add any missing columns

    db = SessionLocal()
    try:
        create_admin(db)
    finally:
        db.close()

    if load_seed_data:
        load_seed_data()
except Exception as e:
    st.error("Database initialization failed")
    st.exception(e)

# ... rest of app.py unchanged (session state, login, UI, bottom nav) ...