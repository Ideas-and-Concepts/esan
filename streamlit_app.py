"""
Esan ERP Controller
Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Version 1.4.0 Alpha – Full Repository Integration
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
    #MainMenu { display:none; }
    footer { display:none; }
    header { display:none; }
    .block-container { padding-top:1.5rem; }
    div[data-testid="stSidebar"] { border-right:1px solid #ddd; }
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
        module = __import__(module_path, fromlist=[function_name])
        if hasattr(module, function_name):
            return getattr(module, function_name)
        module_errors.append(f"{module_path}: missing {function_name}")
        return None
    except Exception as e:
        logging.error(f"{module_path}: {e}")
        module_errors.append(f"{module_path}: {e}")
        return None


# ==================================================
# ADMIN CREATION (fallback if user_service missing)
# ==================================================

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
                role="Administrator"
            )
            db.add(admin)
            db.commit()


# ==================================================
# SEED DATA (optional)
# ==================================================

try:
    from seed.seed_data import load_seed_data
except ImportError:
    load_seed_data = None


# ==================================================
# MODULE REGISTRY – matches your repository structure
# ==================================================

# --- Dashboard ---
dashboard_home = safe_import("modules.dashboard.home", "dashboard_home")

# --- Procurement ---
procurement_dashboard = safe_import("modules.procurement.dashboard", "procurement_dashboard")
procurement_suppliers = safe_import("modules.procurement.suppliers", "suppliers_page")
procurement_purchases = safe_import("modules.procurement.purchases", "purchases_page")

# --- Warehouse ---
warehouse_dashboard = safe_import("modules.warehouse.dashboard", "warehouse_dashboard")
warehouse_inventory = safe_import("modules.warehouse.inventory", "inventory_page")

# --- Milling & Packaging ---
milling_dashboard   = safe_import("modules.milling.dashboard",   "milling_dashboard")
packaging_dashboard = safe_import("modules.packaging.dashboard", "packaging_dashboard")

# --- Sales & Distribution (with sub-pages) ---
sales_dashboard   = safe_import("modules.sales.dashboard",   "sales_dashboard")
sales_customers   = safe_import("modules.sales.customers",    "customers_page")
sales_quotations  = safe_import("modules.sales.quotations",   "quotations_page")
sales_orders      = safe_import("modules.sales.orders",       "sales_orders_page")
sales_deliveries  = safe_import("modules.sales.deliveries",   "deliveries_page")
sales_invoices    = safe_import("modules.sales.invoices",     "invoices_page")
sales_payments    = safe_import("modules.sales.payments",     "payments_page")

# --- Finance ---
finance_dashboard = safe_import("modules.finance.dashboard", "finance_dashboard")

# --- Reports ---
reports_dashboard = safe_import("modules.reports.dashboard", "reports_dashboard")


# ==================================================
# INLINE FALLBACKS for missing module pages
# (so navigation never shows "page unavailable")
# ==================================================

def _fallback_page(title):
    def _render():
        st.info(f"{title} – This section will be available soon.")
    return _render

# Replace any missing function with a friendly placeholder
procurement_suppliers   = procurement_suppliers   or _fallback_page("Suppliers")
procurement_purchases   = procurement_purchases   or _fallback_page("Purchase Orders")
warehouse_inventory     = warehouse_inventory     or _fallback_page("Inventory")
sales_deliveries        = sales_deliveries        or _fallback_page("Deliveries")
sales_invoices          = sales_invoices          or _fallback_page("Invoices")
sales_payments          = sales_payments          or _fallback_page("Payments")


# ==================================================
# DATABASE INITIALIZATION
# ==================================================

def initialize_database():
    try:
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        missing_tables = []

        for table in Base.metadata.tables:
            if table not in existing_tables:
                missing_tables.append(table)

        if missing_tables:
            st.info("🔄 Creating missing ERP database tables...")

        Base.metadata.create_all(bind=engine)

        db = SessionLocal()
        try:
            create_admin(db)
        finally:
            db.close()

        if load_seed_data:
            try:
                load_seed_data()
            except Exception as e:
                logging.warning(f"Seed failed: {e}")

    except Exception as e:
        logging.error(f"Database error: {e}")
        st.error("Database initialization failed")

initialize_database()


# ==================================================
# SESSION MANAGEMENT
# ==================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None
    st.session_state.current_page = "🏠 Overview"


# ==================================================
# LOGIN FUNCTION
# ==================================================

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


# ==================================================
# LOGIN SCREEN
# ==================================================

if not st.session_state.logged_in:
    st.markdown(
        """
        <div style="text-align:center">
        <h1>🌾 Esan ERP</h1>
        <h3>Nile Harvest Foods Ltd.</h3>
        <p>Enterprise Milling & Packaging Management System</p>
        </div>
        """,
        unsafe_allow_html=True
    )

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


# ==================================================
# MAIN HEADER
# ==================================================

st.title("🌾 Esan ERP")
st.caption(f"{COMPANY_NAME} | Version {VERSION}")


# ==================================================
# SIDEBAR NAVIGATION (mirrors repository structure)
# ==================================================

with st.sidebar:
    st.markdown("""<h2 style="text-align:center">🌾 Esan ERP</h2>""", unsafe_allow_html=True)
    st.divider()

    def nav_button(label):
        if st.button(label, use_container_width=True):
            st.session_state.current_page = label

    # MAIN
    nav_button("🏠 Overview")

    # OPERATIONS
    st.markdown("**OPERATIONS**")
    nav_button("🌾 Procurement")
    nav_button("📦 Warehouse")
    nav_button("🏭 Milling")
    nav_button("📦 Packaging")

    # COMMERCIAL
    st.markdown("**COMMERCIAL**")
    nav_button("🚚 Sales & Distribution")

    # FINANCE
    st.markdown("**FINANCE**")
    nav_button("💰 Finance")

    # REPORTING
    st.markdown("**REPORTING**")
    nav_button("📊 Reports")

    st.divider()

    # USER PANEL
    st.markdown("### 👤 User Panel")
    st.write(f"User: **{st.session_state.username}**")
    st.write(f"Role: **{st.session_state.role}**")

    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.role = None
        st.session_state.current_page = "🏠 Overview"
        st.rerun()


# Current selected page
menu = st.session_state.current_page


# ==================================================
# ERP ROUTER
# ==================================================

if menu == "🏠 Overview":
    if dashboard_home:
        dashboard_home()
    else:
        st.info("Overview dashboard not available")

elif menu == "🌾 Procurement":
    st.header("🌾 Procurement")
    # Allow sub-navigation within Procurement
    procurement_menu = st.radio(
        "Procurement Module",
        ["Dashboard", "Suppliers", "Purchase Orders"]
    )
    if procurement_menu == "Dashboard":
        if procurement_dashboard:
            procurement_dashboard()
        else:
            st.warning("Procurement dashboard unavailable")
    elif procurement_menu == "Suppliers":
        procurement_suppliers()
    elif procurement_menu == "Purchase Orders":
        procurement_purchases()

elif menu == "📦 Warehouse":
    st.header("📦 Warehouse")
    warehouse_menu = st.radio(
        "Warehouse Module",
        ["Dashboard", "Inventory"]
    )
    if warehouse_menu == "Dashboard":
        if warehouse_dashboard:
            warehouse_dashboard()
        else:
            st.warning("Warehouse dashboard unavailable")
    elif warehouse_menu == "Inventory":
        warehouse_inventory()

elif menu == "🏭 Milling":
    if milling_dashboard:
        milling_dashboard()
    else:
        st.warning("Milling module unavailable")

elif menu == "📦 Packaging":
    if packaging_dashboard:
        packaging_dashboard()
    else:
        st.warning("Packaging module unavailable")

elif menu == "🚚 Sales & Distribution":
    st.header("🚚 Sales & Distribution")
    sales_menu = st.radio(
        "Sales Module",
        ["Dashboard", "Customers", "Quotations", "Sales Orders", "Deliveries", "Invoices", "Payments"]
    )
    sales_pages = {
        "Dashboard":    sales_dashboard,
        "Customers":    sales_customers,
        "Quotations":   sales_quotations,
        "Sales Orders": sales_orders,
        "Deliveries":   sales_deliveries,
        "Invoices":     sales_invoices,
        "Payments":     sales_payments
    }
    page_func = sales_pages.get(sales_menu)
    if page_func:
        page_func()
    else:
        st.warning(f"{sales_menu} page unavailable")

elif menu == "💰 Finance":
    if finance_dashboard:
        finance_dashboard()
    else:
        st.warning("Finance module unavailable")

elif menu == "📊 Reports":
    if reports_dashboard:
        reports_dashboard()
    else:
        st.warning("Reports module unavailable")


# ==================================================
# MODULE IMPORT WARNINGS (expandable)
# ==================================================

if module_errors:
    with st.expander("⚠️ Module Loading Information"):
        for error in module_errors:
            st.write(error)


# ==================================================
# FOOTER
# ==================================================

st.divider()
st.caption("© Nile Harvest Foods Ltd. | Esan ERP Enterprise Platform")