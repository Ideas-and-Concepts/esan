"""
Nile Harvest Foods Ltd.
Enterprise Resource Planning System
Version 1.4.0 Alpha – Resilient Startup (Handles Missing Modules)
"""

import logging
import sys

import streamlit as st

# ==================================================
# ATTEMPT TO IMPORT CORE MODULES (with fallbacks)
# ==================================================

try:
    from config import COMPANY_NAME, VERSION
except ImportError:
    COMPANY_NAME = "Nile Harvest Foods Ltd."
    VERSION = "1.4.0"

try:
    from database import Base, engine, SessionLocal
except ImportError:
    # Stub to keep the app running – real DB will be missing but app won't crash
    Base = None
    engine = None
    SessionLocal = None

try:
    from models import User
except ImportError:
    # Minimal User class stub for fallback
    class User:
        username = "admin"
        full_name = "System Administrator"
        email = "admin@nileharvest.com"
        password_hash = "hashed"
        role = "Administrator"
        active = True

try:
    from auth import verify_password
except ImportError:
    # Fallback verification (plain text, for demo only)
    def verify_password(plain_password, hashed):
        # In a real setup you would compare properly; here just accept "admin123"
        return plain_password == "admin123"

try:
    from sqlalchemy import inspect
except ImportError:
    inspect = None

# ==================================================
# LOGGING
# ==================================================

logging.basicConfig(
    filename="esan_erp.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Nile Harvest ERP",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==================================================
# CLEAN ERP UI (CSS)
# ==================================================

st.markdown(
    """
<style>
#MainMenu { display: none; }
footer { display: none; }
header { display: none; }
.block-container { padding-top: 1.5rem; }
div[data-testid="stSidebar"] { border-right: 1px solid #ddd; }

/* Login page */
.login-page {
    min-height: 82vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
}
.login-container {
    width: 420px;
    max-width: 100%;
    text-align: center;
}

/* Logo – sprout */
.logo {
    width: 112px;
    height: 112px;
    margin: 0 auto 18px auto;
    border-radius: 32px;
    background: linear-gradient(145deg, #2e7d32, #1b5e20);
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    box-shadow: 0 18px 45px rgba(20, 90, 55, 0.25);
}
.logo::before {
    content: "";
    position: absolute;
    bottom: 0;
    width: 100%;
    height: 28px;
    background: #4e342e;
    border-radius: 0 0 28px 28px;
}
.logo-stem {
    position: absolute;
    bottom: 28px;
    left: 50%;
    transform: translateX(-50%);
    width: 6px;
    height: 40px;
    background: #aed581;
    border-radius: 3px 3px 0 0;
}
.logo-leaf {
    position: absolute;
    bottom: 52px;
    width: 18px;
    height: 18px;
    background: #81c784;
    border-radius: 50%;
}
.logo-leaf.left {
    left: 24px;
    transform: rotate(-30deg);
}
.logo-leaf.right {
    right: 24px;
    transform: rotate(30deg);
}

/* Inputs & buttons */
div[data-testid="stTextInput"] label { font-weight: 600; }
div[data-testid="stTextInput"] input {
    border-radius: 10px;
    min-height: 45px;
    padding-left: 14px;
}
div[data-testid="stButton"] > button {
    border-radius: 10px;
    min-height: 46px;
    font-weight: 700;
}
</style>
""",
    unsafe_allow_html=True,
)

# ==================================================
# SAFE IMPORT SYSTEM FOR APPLICATION MODULES
# ==================================================

module_errors = []

def safe_import(module_path, function_name):
    """Safely import a module function."""
    try:
        module = __import__(module_path, fromlist=[function_name])
        if hasattr(module, function_name):
            return getattr(module, function_name)
        error = f"{module_path}: missing function '{function_name}'"
        module_errors.append(error)
        logging.error(error)
        return None
    except Exception as e:
        error = f"{module_path}: {type(e).__name__}: {e}"
        module_errors.append(error)
        logging.exception(f"Failed loading {module_path}")
        return None

# ==================================================
# ADMIN CREATION (skip if DB not available)
# ==================================================

if SessionLocal is not None:
    try:
        from services.user_service import create_admin
    except ImportError:
        def create_admin(db):
            admin = db.query(User).filter(User.username == "admin").first()
            if not admin:
                from auth import hash_password
                admin = User(
                    username="admin",
                    full_name="System Administrator",
                    email="admin@nileharvest.com",
                    password_hash=hash_password("admin123"),
                    role="Administrator",
                    active=True,
                )
                db.add(admin)
                db.commit()
else:
    create_admin = None

# ==================================================
# SEED DATA
# ==================================================

try:
    from seed.seed_data import load_seed_data
except ImportError:
    load_seed_data = None

# ==================================================
# MODULE REGISTRY (all imports using safe_import)
# ==================================================

dashboard_home = safe_import("modules.dashboard.home", "dashboard_home")

procurement_dashboard = safe_import("modules.procurement.dashboard", "procurement_dashboard")
procurement_suppliers = safe_import("modules.procurement.suppliers", "suppliers_page")
procurement_purchases = safe_import("modules.procurement.purchases", "purchases_page")
procurement_purchase_orders = safe_import("modules.procurement.purchase_orders", "purchase_orders_page")

warehouse_dashboard = safe_import("modules.warehouse.dashboard", "warehouse_dashboard")
warehouse_inventory = safe_import("modules.warehouse.inventory", "inventory_page")

milling_dashboard = safe_import("modules.milling.dashboard", "milling_dashboard")
packaging_dashboard = safe_import("modules.packaging.dashboard", "packaging_dashboard")

sales_dashboard = safe_import("modules.sales.dashboard", "sales_dashboard")
sales_customers = safe_import("modules.sales.customers", "customers_page")
sales_quotations = safe_import("modules.sales.quotations", "quotations_page")
sales_orders = safe_import("modules.sales.orders", "sales_orders_page")
sales_deliveries = safe_import("modules.sales.deliveries", "deliveries_page")
sales_invoices = safe_import("modules.sales.invoices", "invoices_page")
sales_payments = safe_import("modules.sales.payments", "payments_page")

finance_dashboard = safe_import("modules.finance.dashboard", "finance_dashboard")
reports_dashboard = safe_import("modules.reports.dashboard", "reports_dashboard")

# ==================================================
# FALLBACK PAGES (for optional modules)
# ==================================================

def _fallback_page(title):
    def _render():
        st.info(f"{title} – This section is currently being prepared.")
    return _render

procurement_suppliers = procurement_suppliers or _fallback_page("Suppliers")
procurement_purchases = procurement_purchases or _fallback_page("Purchases")
procurement_purchase_orders = procurement_purchase_orders or _fallback_page("Purchase Orders")
warehouse_inventory = warehouse_inventory or _fallback_page("Inventory")

# ==================================================
# DATABASE INITIALIZATION (skip if not available)
# ==================================================

def initialize_database():
    if engine is None or SessionLocal is None:
        st.warning("Database engine not configured. The application will run in demo mode without persistence.")
        return
    try:
        if inspect is not None:
            inspector = inspect(engine)
            existing_tables = inspector.get_table_names()
            missing_tables = [t for t in Base.metadata.tables if t not in existing_tables]
            if missing_tables:
                logging.info("Creating missing tables: %s", missing_tables)
                Base.metadata.create_all(bind=engine)

        db = SessionLocal()
        try:
            if create_admin:
                create_admin(db)
        finally:
            db.close()

        if load_seed_data:
            try:
                load_seed_data()
            except Exception as e:
                logging.warning("Seed data failed: %s", e)
    except Exception:
        logging.exception("Database initialization failed")
        st.error("Database initialization failed. Please check esan_erp.log.")

initialize_database()

# ==================================================
# SESSION MANAGEMENT
# ==================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None
    st.session_state.current_page = "Overview"

# ==================================================
# LOGIN FUNCTION (works with fallback User/verify)
# ==================================================

def login(username, password):
    # If real DB exists, use it; else use fallback admin check
    if SessionLocal is not None:
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.username == username).first()
            if user and user.active and verify_password(password, user.password_hash):
                st.session_state.logged_in = True
                st.session_state.username = user.username
                st.session_state.role = user.role
                return True
            return False
        finally:
            db.close()
    else:
        # Demo mode – only admin/admin123 works
        if username == "admin" and password == "admin123":
            st.session_state.logged_in = True
            st.session_state.username = "admin"
            st.session_state.role = "Administrator"
            return True
        return False

# ==================================================
# LOGIN SCREEN (only logo + form)
# ==================================================

if not st.session_state.logged_in:
    st.markdown(
        """
        <div class="login-page">
            <div class="login-container">
                <div class="logo">
                    <div class="logo-stem"></div>
                    <div class="logo-leaf left"></div>
                    <div class="logo-leaf right"></div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        if st.button("Login", use_container_width=True, type="primary"):
            if login(username, password):
                st.success("Login successful")
                st.rerun()
            else:
                st.error("Invalid username or password")

    st.stop()

# ==================================================
# SIDEBAR (logo only, then navigation)
# ==================================================

with st.sidebar:
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 1rem;">
            <div class="logo" style="margin: 0 auto 0 auto;">
                <div class="logo-stem"></div>
                <div class="logo-leaf left"></div>
                <div class="logo-leaf right"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    def nav_button(label):
        if st.button(label, use_container_width=True):
            st.session_state.current_page = label

    nav_button("Overview")

    st.markdown("**OPERATIONS**")
    nav_button("Procurement")
    nav_button("Warehouse")
    nav_button("Milling")
    nav_button("Packaging")

    st.markdown("**COMMERCIAL**")
    nav_button("Sales & Distribution")

    st.markdown("**FINANCE**")
    nav_button("Finance")

    st.markdown("**REPORTING**")
    nav_button("Reports")

    st.divider()

    st.markdown("### User Panel")
    st.write(f"User: **{st.session_state.username}**")
    st.write(f"Role: **{st.session_state.role}**")

    if st.button("Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.role = None
        st.session_state.current_page = "Overview"
        st.rerun()

# ==================================================
# ROUTING TO MODULES
# ==================================================

menu = st.session_state.current_page

if menu == "Overview":
    if dashboard_home:
        dashboard_home()
    else:
        st.warning("Overview dashboard could not be loaded.")

elif menu == "Procurement":
    st.header("Procurement")
    procurement_menu = st.radio("Procurement Module", ["Dashboard", "Suppliers", "Purchase Orders", "Purchases"], horizontal=True)
    if procurement_menu == "Dashboard":
        if procurement_dashboard:
            procurement_dashboard()
        else:
            st.warning("Procurement dashboard unavailable.")
    elif procurement_menu == "Suppliers":
        procurement_suppliers()
    elif procurement_menu == "Purchase Orders":
        procurement_purchase_orders()
    elif procurement_menu == "Purchases":
        procurement_purchases()

elif menu == "Warehouse":
    st.header("Warehouse")
    warehouse_menu = st.radio("Warehouse Module", ["Dashboard", "Inventory"], horizontal=True)
    if warehouse_menu == "Dashboard":
        if warehouse_dashboard:
            warehouse_dashboard()
        else:
            st.warning("Warehouse dashboard unavailable.")
    elif warehouse_menu == "Inventory":
        warehouse_inventory()

elif menu == "Milling":
    if milling_dashboard:
        milling_dashboard()
    else:
        st.warning("Milling module unavailable.")

elif menu == "Packaging":
    if packaging_dashboard:
        packaging_dashboard()
    else:
        st.warning("Packaging module unavailable.")

elif menu == "Sales & Distribution":
    st.header("Sales & Distribution")
    sales_menu = st.radio("Sales Module", ["Dashboard", "Customers", "Quotations", "Sales Orders", "Deliveries", "Invoices", "Payments"], horizontal=True)
    sales_pages = {
        "Dashboard": sales_dashboard,
        "Customers": sales_customers,
        "Quotations": sales_quotations,
        "Sales Orders": sales_orders,
        "Deliveries": sales_deliveries,
        "Invoices": sales_invoices,
        "Payments": sales_payments,
    }
    page_func = sales_pages.get(sales_menu)
    if page_func:
        page_func()
    else:
        st.warning(f"{sales_menu} page unavailable.")

elif menu == "Finance":
    if finance_dashboard:
        finance_dashboard()
    else:
        st.warning("Finance module unavailable.")

elif menu == "Reports":
    if reports_dashboard:
        reports_dashboard()
    else:
        st.warning("Reports module unavailable.")

# ==================================================
# MODULE LOADING INFORMATION (if any errors)
# ==================================================

if module_errors:
    with st.expander("Module Loading Information"):
        st.warning("The following modules could not be loaded:")
        for error in module_errors:
            st.write(f"• {error}")

# ==================================================
# FOOTER
# ==================================================

st.divider()
st.caption(f"© {COMPANY_NAME} | Enterprise Resource Planning Platform")