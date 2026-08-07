"""
Esan ERP Controller
Nile Harvest Foods Ltd.

Enterprise Milling & Packaging Management System

Version 1.4.0 Alpha
"""

import streamlit as st
import logging
from sqlalchemy import inspect

from config import COMPANY_NAME, VERSION
from database import Base, engine, SessionLocal
from models import User
from auth import verify_password


# ==================================================
# LOGGING
# ==================================================

logging.basicConfig(
    filename="esan_erp.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)



# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Esan ERP",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)



# ==================================================
# CLEAN ERP UI
# ==================================================

st.markdown(
    """
    <style>

    #MainMenu {
        display:none;
    }

    footer {
        display:none;
    }

    header {
        display:none;
    }


    .block-container {
        padding-top:1.5rem;
    }


    div[data-testid="stSidebar"] {

        border-right:1px solid #ddd;

    }


    </style>
    """,
    unsafe_allow_html=True
)



# ==================================================
# SAFE IMPORT SYSTEM
# ==================================================

module_errors = []


def safe_import(module_path, function_name):

    try:

        module = __import__(
            module_path,
            fromlist=[function_name]
        )


        if hasattr(
            module,
            function_name
        ):

            return getattr(
                module,
                function_name
            )


        module_errors.append(
            f"{module_path}: missing {function_name}"
        )


        return None


    except Exception as e:


        logging.error(
            f"{module_path}: {e}"
        )


        module_errors.append(
            f"{module_path}: {e}"
        )


        return None



# ==================================================
# ADMIN CREATION
# ==================================================

try:

    from services.user_service import create_admin


except ImportError:


    def create_admin(db):

        admin = (
            db.query(User)
            .filter(
                User.username=="admin"
            )
            .first()
        )


        if not admin:


            from auth import hash_password


            admin = User(

                username="admin",

                password_hash=
                hash_password(
                    "admin123"
                ),

                role="Administrator"

            )


            db.add(admin)

            db.commit()



# ==================================================
# SEED DATA
# ==================================================

try:

    from seed.seed_data import load_seed_data


except ImportError:

    load_seed_data = None



# ==================================================
# DATABASE INITIALIZATION
# ==================================================

def initialize_database():

    try:


        inspector = inspect(
            engine
        )


        existing_tables = (
            inspector.get_table_names()
        )


        missing_tables = []


        for table in Base.metadata.tables:


            if table not in existing_tables:

                missing_tables.append(
                    table
                )



        if missing_tables:


            st.info(
                "🔄 Creating ERP database tables..."
            )


        Base.metadata.create_all(
            bind=engine
        )



        db = SessionLocal()


        try:

            create_admin(db)


        finally:

            db.close()



        if load_seed_data:


            try:

                load_seed_data()


            except Exception as e:


                logging.warning(
                    f"Seed failed: {e}"
                )



    except Exception as e:


        logging.error(
            f"Database error: {e}"
        )


        st.error(
            "Database initialization failed"
        )



initialize_database()



# ==================================================
# SESSION MANAGEMENT
# ==================================================

if "logged_in" not in st.session_state:


    st.session_state.logged_in = False

    st.session_state.username = None

    st.session_state.role = None

    st.session_state.current_page = (
        "🏠 Overview"
    )



# ==================================================
# LOGIN FUNCTION
# ==================================================

def login(username, password):


    db = SessionLocal()


    try:


        user = (
            db.query(User)
            .filter(
                User.username == username
            )
            .first()
        )



        if user and verify_password(
            password,
            user.password_hash
        ):


            st.session_state.logged_in = True

            st.session_state.username = (
                user.username
            )

            st.session_state.role = (
                user.role
            )


            return True



        return False



    finally:

        db.close()