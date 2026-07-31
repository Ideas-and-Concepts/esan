"""
Esan ERP Controller
Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Version 1.2.0 Alpha
"""

import streamlit as st
import os
from sqlalchemy import inspect

from config import COMPANY_NAME, VERSION
from database import Base, engine, SessionLocal, DATABASE_URL
from models import User
from auth import verify_password

# ------------------------------------------------------------------------------
# CRITICAL SERVICE / COMPONENT IMPORTS (with safe fallbacks)
# ------------------------------------------------------------------------------
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
                role="Administrator",
                full_name="System Administrator",
                email="admin@nileharvest.com"
            )
            db.add(admin)
            db.commit()

try:
    from components.navigation import esan_navigation
except ImportError:
    def esan_navigation():
        menu_options = [
            "Overview", "🌾 Procurement", "📦 Warehouse", "🏭 Milling",
            "📦 Packaging", "🚚 Sales", "💰 Finance", "📊 Reports"
        ]
        if st.session_state.get("role", "user") == "Administrator":
            menu_options.append("🔐 Administration")
        return st.sidebar.selectbox("Navigation", menu_options)

try:
    from components.themes import esan_theme
except ImportError:
    def esan_theme(theme):
        pass

# ------------------------------------------------------------------------------
# OPTIONAL SEED DATA
# ------------------------------------------------------------------------------
try:
    from seed.seed_data import load_seed_data
except Exception:
    load_seed_data = None

# ------------------------------------------------------------------------------
# MODULE IMPORTS (all with fallbacks)
# ------------------------------------------------------------------------------
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

# Sales submodules
try:
    from modules.sales.customers import customers_page
except ImportError:
    customers_page = None
try:
    from modules.sales.orders import sales_orders_page
except ImportError:
    sales_orders_page = None
try:
    from modules.sales.quotations import quotations_page
except ImportError:
    quotations_page = None
try:
    from modules.sales.delivery import delivery_page
except ImportError:
    delivery_page = None
try:
    from modules.sales.dispatch import dispatch_page
except ImportError:
    dispatch_page = None

# Finance submodules
try:
    from modules.finance.invoices import invoices_page
except ImportError:
    invoices_page = None
try:
    from modules.finance.payments import payments_page
except ImportError:
    payments_page = None
try:
    from modules.finance.accounting import accounting_page
except ImportError:
    accounting_page = None
try:
    from modules.finance.costing import costing_page
except ImportError:
    costing_page = None
try:
    from modules.finance.profitability import profitability_page
except ImportError:
    profitability_page = None

# Logistics
try:
    from modules.logistics.dashboard import logistics_dashboard
except ImportError:
    logistics_dashboard = None

# HR
try:
    from modules.hr.dashboard import hr_dashboard
except ImportError:
    hr_dashboard = None

# Maintenance
try:
    from modules.maintenance.dashboard import maintenance_dashboard
except ImportError:
    maintenance_dashboard = None

# Reports
try:
    from modules.reports.dashboard import reports_dashboard
except ImportError:
    reports_dashboard = None

# AI Assistant
try:
    from modules.ai_assistant.ai_page import ai_assistant_page
except ImportError:
    ai_assistant_page = None

# Administration (user management, password change)
try:
    from modules.administration.user_management import user_management_page
except ImportError:
    user_management_page = None
try:
    from modules.administration.change_password import change_password_page
except ImportError:
    change_password_page = None

# ------------------------------------------------------------------------------
# PAGE CONFIGURATION
# ------------------------------------------------------------------------------
st.set_page_config(page_title="Esan ERP", page_icon="🌾", layout="wide")

# ------------------------------------------------------------------------------
# CLEAN UI (hide default Streamlit chrome)
# ------------------------------------------------------------------------------
st.markdown("""
<style>
    #MainMenu {display:none;}
    footer {display:none;}
    header {display:none;}
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# DATABASE INITIALIZATION (auto-repair + safe fallback)
# ------------------------------------------------------------------------------
def rebuild_database():
    """Drop and recreate all tables when schema mismatch is detected."""
    try:
        if "sqlite:///" in DATABASE_URL:
            db_path = DATABASE_URL.replace("sqlite:///", "")
            if os.path.exists(db_path):
                os.remove(db_path)
    except Exception:
        pass
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

try:
    needs_rebuild = False
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    if existing_tables:
        for table_name, table in Base.metadata.tables.items():
            if table_name in existing_tables:
                existing_cols = {col['name'] for col in inspector.get_columns(table_name)}
                model_cols = {c.name for c in table.columns}
                if model_cols - existing_cols:
                    needs_rebuild = True
                    break

    if needs_rebuild:
        st.warning("🔄 Database schema updated. Rebuilding with fresh tables...")
        rebuild_database()
    else:
        Base.metadata.create_all(bind=engine)

    # Always ensure admin exists
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

# ------------------------------------------------------------------------------
# SESSION STATE
# ------------------------------------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None

# ------------------------------------------------------------------------------
# LOGIN FUNCTION
# ------------------------------------------------------------------------------
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

# ------------------------------------------------------------------------------
# LOGIN SCREEN
# ------------------------------------------------------------------------------
if not st.session_state.logged_in:
    st.markdown("""
    <div style="text-align:center; margin-top: 10vh;">
        <h1>🌾 Esan ERP</h1>
        <h3>Nile Harvest Foods Ltd.</h3>
        <p>Enterprise Milling & Packaging Management System</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True):
            if login(username, password):
                st.success("Login successful")
                st.rerun()
            else:
                st.error("Invalid username or password")
        st.info("Default administrator: admin / admin123")
    st.stop()

# ------------------------------------------------------------------------------
# APPLICATION HEADER
# ------------------------------------------------------------------------------
st.title("🌾 Esan ERP")
st.caption(f"{COMPANY_NAME} | Version {VERSION}")

# ------------------------------------------------------------------------------
# SIDEBAR – User, Theme, Logout, Navigation
# ------------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 👤 User Panel")
    st.success(f"User: **{st.session_state.username}**")
    st.info(f"Role: **{st.session_state.role}**")

    theme = st.selectbox("🎨 Appearance", ["Light", "Dark"])
    esan_theme(theme)

    if st.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.role = None
        st.rerun()

    st.divider()
    st.markdown("## 📋 Navigation")
    menu = esan_navigation()   # Renders navigation inside sidebar

# ------------------------------------------------------------------------------
# MAIN ROUTER
# ------------------------------------------------------------------------------
# --- Dashboard / Overview ---
if menu == "Overview":
    if module_functions["Overview"]:
        module_functions["Overview"]()
    else:
        st.info("Dashboard module not available.")

# --- Procurement ---
elif menu == "🌾 Procurement":
    if module_functions["🌾 Procurement"]:
        module_functions["🌾 Procurement"]()
    else:
        st.warning("Procurement module not available.")

# --- Warehouse ---
elif menu == "📦 Warehouse":
    if module_functions["📦 Warehouse"]:
        module_functions["📦 Warehouse"]()
    else:
        st.warning("Warehouse module not available.")

# --- Milling ---
elif menu == "🏭 Milling":
    if module_functions["🏭 Milling"]:
        module_functions["🏭 Milling"]()
    else:
        st.warning("Milling module not available.")

# --- Packaging ---
elif menu == "📦 Packaging":
    if module_functions["📦 Packaging"]:
        module_functions["📦 Packaging"]()
    else:
        st.warning("Packaging module not available.")

# --- Sales & Distribution ---
elif menu == "🚚 Sales":
    st.header("🚚 Sales & Distribution")
    sales_menu = st.radio(
        "Sales Module",
        ["Dashboard", "Customers", "Quotations", "Sales Orders",
         "Dispatch", "Deliveries", "Invoices", "Payments"]
    )

    if sales_menu == "Dashboard":
        if module_functions["🚚 Sales"]:
            module_functions["🚚 Sales"]()
        else:
            st.warning("Sales dashboard unavailable.")
    elif sales_menu == "Customers":
        if customers_page:
            customers_page()
        else:
            st.warning("Customers module unavailable.")
    elif sales_menu == "Quotations":
        if quotations_page:
            quotations_page()
        else:
            st.warning("Quotation module unavailable.")
    elif sales_menu == "Sales Orders":
        if sales_orders_page:
            sales_orders_page()
        else:
            st.warning("Sales Orders module unavailable.")
    elif sales_menu == "Dispatch":
        if dispatch_page:
            dispatch_page()
        else:
            st.warning("Dispatch module unavailable.")
    elif sales_menu == "Deliveries":
        if delivery_page:
            delivery_page()
        else:
            st.warning("Delivery module unavailable.")
    elif sales_menu == "Invoices":
        if invoices_page:
            invoices_page()
        else:
            st.warning("Invoices module unavailable.")
    elif sales_menu == "Payments":
        if payments_page:
            payments_page()
        else:
            st.warning("Payments module unavailable.")
    else:
        st.info(f"{sales_menu} module will be developed next.")

# --- Finance ---
elif menu == "💰 Finance":
    st.header("💰 Finance Management")
    finance_menu = st.radio(
        "Finance Module",
        ["Dashboard", "Invoices", "Payments", "Accounting", "Costing", "Profitability"]
    )

    if finance_menu == "Dashboard":
        if module_functions["💰 Finance"]:
            module_functions["💰 Finance"]()
        else:
            st.warning("Finance dashboard unavailable.")
    elif finance_menu == "Invoices":
        if invoices_page:
            invoices_page()
        else:
            st.warning("Invoices module unavailable.")
    elif finance_menu == "Payments":
        if payments_page:
            payments_page()
        else:
            st.warning("Payments module unavailable.")
    elif finance_menu == "Accounting":
        if accounting_page:
            accounting_page()
        else:
            st.warning("Accounting module unavailable.")
    elif finance_menu == "Costing":
        if costing_page:
            costing_page()
        else:
            st.warning("Costing module unavailable.")
    elif finance_menu == "Profitability":
        if profitability_page:
            profitability_page()
        else:
            st.warning("Profitability module unavailable.")
    else:
        st.info(f"{finance_menu} module will be developed next.")

# --- Logistics ---
elif menu == "🚚 Logistics":
    if logistics_dashboard:
        logistics_dashboard()
    else:
        st.warning("Logistics module not available.")

# --- HR & Employees ---
elif menu == "👥 HR & Employees":
    if hr_dashboard:
        hr_dashboard()
    else:
        st.warning("HR module not available.")

# --- Maintenance ---
elif menu == "🔧 Maintenance":
    if maintenance_dashboard:
        maintenance_dashboard()
    else:
        st.warning("Maintenance module not available.")

# --- Reports ---
elif menu == "📊 Reports":
    if module_functions["📊 Reports"]:
        module_functions["📊 Reports"]()
    else:
        st.warning("Reports module not available.")

# --- AI Assistant ---
elif menu == "🤖 AI Assistant":
    if ai_assistant_page:
        ai_assistant_page()
    else:
        st.warning("AI Assistant module not available.")

# --- Administration (only if admin) ---
elif menu == "🔐 Administration":
    if st.session_state.get("role") != "Administrator":
        st.error("Access denied. Administrator role required.")
    else:
        st.header("🔐 Administration")
        admin_tabs = st.radio("Admin Menu", ["User Management", "Change Password"])
        if admin_tabs == "User Management":
            if user_management_page:
                user_management_page()
            else:
                st.warning("User Management module unavailable.")
        elif admin_tabs == "Change Password":
            if change_password_page:
                change_password_page()
            else:
                st.warning("Change Password module unavailable.")

# --- Fallback ---
else:
    st.info("Select a module from the navigation menu.")

# ------------------------------------------------------------------------------
# FOOTER
# ------------------------------------------------------------------------------
st.divider()
st.caption("© Nile Harvest Foods Ltd. | Esan ERP Enterprise Platform")