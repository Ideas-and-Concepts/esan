"""
Esan ERP Controller
Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System
Version 1.2.0 Alpha
"""

import streamlit as st
import os
from sqlalchemy import inspect

from modules.procurement.dashboard import procurement_dashboard
from modules.milling.dashboard import milling_dashboard
from modules.packaging.dashboard import packaging_dashboard
from modules.warehouse.dashboard import warehouse_dashboard 
from modules.finance.dashboard import finance_dashboard
from  modules.sales.dashboard import sales_dashboard
from modules.reports.dashboard import reports_dashboard


from config import COMPANY_NAME, VERSION
from database import Base, engine, SessionLocal, DATABASE_URL
from models import User
from auth import verify_password

# =====================================
# SAFE IMPORT HELPER
# =====================================
def safe_import(module_path, name):
    """Dynamically import a module and return a fallback if missing."""
    try:
        return __import__(module_path, fromlist=[name])
    except Exception:
        return None

# =====================================
# CRITICAL SERVICE IMPORTS
# =====================================
# create_admin is essential – we have a fallback inside
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

# Navigation component
try:
    from components.navigation import esan_navigation
except ImportError:
    def esan_navigation():
        menu_options = [
            "🏠 Overview", "🌾 Procurement", "📦 Warehouse", "🏭 Milling",
            "📦 Packaging", "🚚 Sales", "💰 Finance", "🚚 Logistics",
            "👥 HR & Employees", "🔧 Maintenance", "📊 Reports", "🤖 AI Assistant"
        ]
        if st.session_state.get("role", "user") == "Administrator":
            menu_options.append("🔐 Administration")
        return st.sidebar.selectbox("Navigation", menu_options)

# Theme
try:
    from components.themes import esan_theme
except ImportError:
    def esan_theme(theme):
        pass

# Seed data
try:
    from seed.seed_data import load_seed_data
except ImportError:
    load_seed_data = None

# =====================================
# MODULE IMPORTS (all with fallbacks)
# =====================================
def get_module(import_path, func_name):
    mod = safe_import(import_path, func_name)
    if mod and hasattr(mod, func_name):
        return getattr(mod, func_name)
    return None

# Dashboard
dashboard_home = get_module("modules.dashboard.home", "dashboard_home")
# Procurement
procurement_dashboard = get_module("modules.procurement.dashboard", "procurement_dashboard")
# Warehouse
warehouse_dashboard = get_module("modules.warehouse.dashboard", "warehouse_dashboard")
# Milling
milling_dashboard = get_module("modules.milling.dashboard", "milling_dashboard")
# Packaging
packaging_dashboard = get_module("modules.packaging.dashboard", "packaging_dashboard")
# Sales
sales_dashboard = get_module("modules.sales.dashboard", "sales_dashboard")
customers_page = get_module("modules.sales.customers", "customers_page")
sales_orders_page = get_module("modules.sales.orders", "sales_orders_page")
quotations_page = get_module("modules.sales.quotations", "quotations_page")
delivery_page = get_module("modules.sales.delivery", "delivery_page")
dispatch_page = get_module("modules.sales.dispatch", "dispatch_page")
# Finance
finance_dashboard = get_module("modules.finance.dashboard", "finance_dashboard")
invoices_page = get_module("modules.finance.invoices", "invoices_page")
payments_page = get_module("modules.finance.payments", "payments_page")
accounting_page = get_module("modules.finance.accounting", "accounting_page")
costing_page = get_module("modules.finance.costing", "costing_page")
profitability_page = get_module("modules.finance.profitability", "profitability_page")
# Logistics
logistics_dashboard = get_module("modules.logistics.dashboard", "logistics_dashboard")
# HR
hr_dashboard = get_module("modules.hr.dashboard", "hr_dashboard")
# Maintenance
maintenance_dashboard = get_module("modules.maintenance.dashboard", "maintenance_dashboard")
# Reports
reports_dashboard = get_module("modules.reports.dashboard", "reports_dashboard")
# AI
ai_assistant_page = get_module("modules.ai_assistant.ai_page", "ai_assistant_page")
# Administration
user_management_page = get_module("modules.administration.user_management", "user_management_page")
change_password_page = get_module("modules.administration.change_password", "change_password_page")

# =====================================
# PAGE CONFIGURATION
# =====================================
st.set_page_config(page_title="Esan ERP", page_icon="🌾", layout="wide")

# Clean UI
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

# =====================================
# DATABASE INITIALIZATION (auto-repair)
# =====================================
def rebuild_database():
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

# =====================================
# MAIN APP
# =====================================
st.title("🌾 Esan ERP")
st.caption(f"{COMPANY_NAME} | Version {VERSION}")

# Sidebar
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
    menu = esan_navigation()

# =====================================
# ROUTER
# =====================================
if menu == "🏠 Overview":
    if dashboard_home:
        dashboard_home()
    else:
        st.info("Dashboard module not available.")

elif menu == "🌾 Procurement":
    if procurement_dashboard:
        procurement_dashboard()
    else:
        st.warning("Procurement module not available.")

elif menu == "📦 Warehouse":
    if warehouse_dashboard:
        warehouse_dashboard()
    else:
        st.warning("Warehouse module not available.")

elif menu == "🏭 Milling":
    if milling_dashboard:
        milling_dashboard()
    else:
        st.warning("Milling module not available.")

elif menu == "📦 Packaging":
    if packaging_dashboard:
        packaging_dashboard()
    else:
        st.warning("Packaging module not available.")

elif menu == "🚚 Sales":
    st.header("🚚 Sales & Distribution")
    sales_menu = st.radio(
        "Sales Module",
        ["Dashboard", "Customers", "Quotations", "Sales Orders",
         "Dispatch", "Deliveries", "Invoices", "Payments"]
    )

    if sales_menu == "Dashboard":
        if sales_dashboard:
            sales_dashboard()
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
            st.warning("Quotations module unavailable.")
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
            st.warning("Deliveries module unavailable.")
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

elif menu == "💰 Finance":
    st.header("💰 Finance Management")
    finance_menu = st.radio(
        "Finance Module",
        ["Dashboard", "Invoices", "Payments", "Accounting", "Costing", "Profitability"]
    )

    if finance_menu == "Dashboard":
        if finance_dashboard:
            finance_dashboard()
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

elif menu == "🚚 Logistics":
    if logistics_dashboard:
        logistics_dashboard()
    else:
        st.warning("Logistics module not available.")

elif menu == "👥 HR & Employees":
    if hr_dashboard:
        hr_dashboard()
    else:
        st.warning("HR module not available.")

elif menu == "🔧 Maintenance":
    if maintenance_dashboard:
        maintenance_dashboard()
    else:
        st.warning("Maintenance module not available.")

elif menu == "📊 Reports":
    if reports_dashboard:
        reports_dashboard()
    else:
        st.warning("Reports module not available.")

elif menu == "🤖 AI Assistant":
    if ai_assistant_page:
        ai_assistant_page()
    else:
        st.warning("AI Assistant module not available.")

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

else:
    st.info("Select a module from the navigation menu.")

st.divider()
st.caption("© Nile Harvest Foods Ltd. | Esan ERP Enterprise Platform")
