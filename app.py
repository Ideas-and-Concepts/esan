"""
Esan ERP Controller
Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Version 1.2.0 Alpha
"""

import streamlit as st
from config import COMPANY_NAME, VERSION
from database import Base, engine, SessionLocal
from models import User
from auth import verify_password
from sqlalchemy import inspect, text

# =====================================
# CRITICAL SERVICE / COMPONENT IMPORTS
# =====================================
try:
    from services.user_service import create_admin
except ImportError:
    def create_admin(db):
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
    from components.navigation import esan_navigation
except ImportError:
    def esan_navigation():
        return "Overview"

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
# MODULE IMPORTS (fallbacks)
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

try:
    from modules.dashboard.home import dashboard_home
    module_functions["Overview"] = dashboard_home
except ImportError:
    pass

try:
    from modules.procurement.dashboard import procurement_dashboard
    module_functions["🌾 Procurement"] = procurement_dashboard
except ImportError:
    pass

try:
    from modules.warehouse.dashboard import warehouse_dashboard
    module_functions["📦 Warehouse"] = warehouse_dashboard
except ImportError:
    pass

try:
    from modules.milling.dashboard import milling_dashboard
    module_functions["🏭 Milling"] = milling_dashboard
except ImportError:
    pass

try:
    from modules.packaging.dashboard import packaging_dashboard
    module_functions["📦 Packaging"] = packaging_dashboard
except ImportError:
    pass

try:
    from modules.sales.dashboard import sales_dashboard
    module_functions["🚚 Sales"] = sales_dashboard
except ImportError:
    pass

try:
    from modules.finance.dashboard import finance_dashboard
    module_functions["💰 Finance"] = finance_dashboard
except ImportError:
    pass

try:
    from modules.reports.dashboard import reports_dashboard
    module_functions["📊 Reports"] = reports_dashboard
except ImportError:
    pass

# =====================================
# PAGE CONFIGURATION
# =====================================
st.set_page_config(page_title="Esan ERP", page_icon="🌾", layout="wide")

# Clean Streamlit UI
st.markdown("""
<style>
#MainMenu {display:none;}
footer {display:none;}
header {display:none;}
</style>
""", unsafe_allow_html=True)

# =====================================
# DATABASE SCHEMA CHECK & RESET
# =====================================
def check_schema_integrity():
    """Check if the existing database matches the models. If not, drop and recreate."""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    if not tables:
        return True   # empty db – create_all will handle it

    # Get model table definitions
    for table_name, table in Base.metadata.tables.items():
        if table_name in tables:
            existing_cols = {col['name'] for col in inspector.get_columns(table_name)}
            model_cols = {c.name for c in table.columns}
            if model_cols - existing_cols:   # missing columns
                return False
    return True

# =====================================
# DATABASE INITIALIZATION
# =====================================
try:
    if not check_schema_integrity():
        st.warning("⚠️ Schema mismatch detected. Resetting database to match new models. All data will be lost.")
        Base.metadata.drop_all(bind=engine)
        st.success("Database reset. Creating fresh tables...")

    Base.metadata.create_all(bind=engine)

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

# =====================================
# SESSION STATE
# =====================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None
    st.session_state.page = "Overview"

# =====================================
# LOGIN FUNCTION
# =====================================
def login(username, password):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user and verify_password(password, user.password_hash):
            st.session_state.logged_in = True
            st.session_state.username = user.username
            st.session_state.role = user.role
            return True
        return False
    finally:
        db.close()

# =====================================
# LOGIN SCREEN
# =====================================
if not st.session_state.logged_in:
    st.markdown("""
    <div style="text-align:center">
    <h1>🌾 Esan ERP</h1>
    <h3>Nile Harvest Foods Ltd.</h3>
    <p>Enterprise Milling & Packaging Management System</p>
    </div>
    """, unsafe_allow_html=True)

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if login(username, password):
            st.success("Login successful")
            st.rerun()
        else:
            st.error("Invalid username or password")

    st.info("Default administrator: admin / admin123")
    st.stop()

# =====================================
# APPLICATION HEADER
# =====================================
st.title("🌾 Esan ERP")
st.caption(f"{COMPANY_NAME} | Version {VERSION}")

# =====================================
# SIDEBAR: USER, THEME, NAVIGATION
# =====================================
st.sidebar.success(f"User: {st.session_state.username}")
st.sidebar.info(f"Role: {st.session_state.role}")

theme = st.sidebar.selectbox("Appearance", ["Light", "Dark"])
esan_theme(theme)

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None
    st.rerun()

# Sidebar navigation (replaces bottom bar)
menu = esan_navigation()  # returns a string like "Overview", "🌾 Procurement", etc.

# =====================================
# ERP MODULE ROUTER
# =====================================
if menu == "Overview":
    if module_functions["Overview"]:
        module_functions["Overview"]()
    else:
        st.info("Dashboard module not available.")

elif menu == "🌾 Procurement":
    if module_functions["🌾 Procurement"]:
        module_functions["🌾 Procurement"]()
    else:
        st.warning("Procurement module not available.")

elif menu == "📦 Warehouse":
    if module_functions["📦 Warehouse"]:
        module_functions["📦 Warehouse"]()
    else:
        st.warning("Warehouse module not available.")

elif menu == "🏭 Milling":
    if module_functions["🏭 Milling"]:
        module_functions["🏭 Milling"]()
    else:
        st.warning("Milling module not available.")

elif menu == "📦 Packaging":
    if module_functions["📦 Packaging"]:
        module_functions["📦 Packaging"]()
    else:
        st.warning("Packaging module not available.")

elif menu == "🚚 Sales & Distribution":
    st.header("🚚 Sales & Distribution")
    # Sales sub‑menu can be implemented here
    if module_functions["🚚 Sales"]:
        module_functions["🚚 Sales"]()
    else:
        st.info("Sales module under development.")

elif menu == "💰 Finance":
    if module_functions["💰 Finance"]:
        module_functions["💰 Finance"]()
    else:
        st.warning("Finance module not available.")

elif menu == "📊 Reports":
    if module_functions["📊 Reports"]:
        module_functions["📊 Reports"]()
    else:
        st.warning("Reports module not available.")

else:
    st.info("Select a module from the sidebar.")

# Footer
st.divider()
st.caption("© Nile Harvest Foods Ltd. | Esan ERP Enterprise Platform")