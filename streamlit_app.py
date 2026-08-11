"""
Esan ERP Controller
Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Version 1.4.0 Alpha – Full Repository Integration
"""

import logging

import streamlit as st
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
    format="%(asctime)s - %(levelname)s - %(message)s",
)


# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Esan ERP",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==================================================
# CLEAN ERP UI
# ==================================================

st.markdown(
    """
    <style>

    #MainMenu {
        display: none;
    }

    footer {
        display: none;
    }

    header {
        display: none;
    }

    .block-container {
        padding-top: 1.5rem;
    }

    div[data-testid="stSidebar"] {
        border-right: 1px solid #ddd;
    }

    /* ==========================================
       ESAN LOGIN DESIGN
       ========================================== */

    .esan-login-page {
        min-height: 78vh;
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 30px 20px;
    }

    .esan-login-container {
        width: 430px;
        max-width: 100%;
        text-align: center;
    }

    /* ==========================================
       ESAN LOGO MARK
       ========================================== */

    .esan-logo-mark {
        width: 108px;
        height: 108px;
        margin: 0 auto 20px auto;

        background:
            linear-gradient(
                145deg,
                #238653 0%,
                #17613d 55%,
                #0d452b 100%
            );

        border-radius: 30px;

        display: flex;
        align-items: center;
        justify-content: center;

        position: relative;

        box-shadow:
            0 18px 45px rgba(20, 90, 55, 0.25);
    }

    /*
       Outer ring
    */

    .esan-logo-ring {
        position: absolute;

        width: 72px;
        height: 72px;

        border: 2px solid rgba(255,255,255,0.9);

        border-radius: 50%;
    }

    /*
       Abstract E symbol
    */

    .esan-logo-symbol {
        position: relative;

        width: 50px;
        height: 50px;

        display: flex;
        align-items: center;
        justify-content: center;

        z-index: 2;
    }

    .esan-logo-symbol::before,
    .esan-logo-symbol::after {
        content: "";

        position: absolute;

        background: white;

        border-radius: 4px;
    }

    .esan-logo-symbol::before {
        width: 9px;
        height: 42px;

        left: 7px;
        top: 4px;
    }

    .esan-logo-symbol::after {
        width: 34px;
        height: 9px;

        left: 7px;
        top: 4px;

        box-shadow:
            0 16px 0 white,
            0 33px 0 white;
    }

    /*
       Small agricultural accent
    */

    .esan-logo-leaf {
        position: absolute;

        width: 15px;
        height: 27px;

        right: 13px;
        bottom: 15px;

        background: #d8eec2;

        border-radius: 100% 0 100% 0;

        transform: rotate(25deg);
    }

    /* ==========================================
       ESAN WORDMARK
       ========================================== */

    .esan-wordmark {
        font-family:
            Arial,
            Helvetica,
            sans-serif;

        font-size: 42px;

        font-weight: 800;

        letter-spacing: 4px;

        color: #174f35;

        margin-bottom: 4px;
    }

    .esan-login-tagline {
        font-family:
            Arial,
            Helvetica,
            sans-serif;

        font-size: 11px;

        font-weight: 600;

        letter-spacing: 3px;

        color: #7a7a7a;

        margin-bottom: 35px;
    }

    /* ==========================================
       LOGIN INPUT AREA
       ========================================== */

    div[data-testid="stTextInput"] label {
        font-weight: 600;
    }

    div[data-testid="stTextInput"] input {
        border-radius: 10px;
        padding: 12px;
    }

    /* ==========================================
       LOGIN BUTTON
       ========================================== */

    div[data-testid="stButton"] > button {
        border-radius: 10px;
        min-height: 46px;
        font-weight: 700;
    }

    /* ==========================================
       LOGIN FOOTER
       ========================================== */

    .esan-login-footer {
        margin-top: 35px;

        color: #999;

        font-size: 11px;

        letter-spacing: 0.5px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ==================================================
# SAFE IMPORT SYSTEM
# ==================================================

module_errors = []


def safe_import(module_path, function_name):
    """
    Safely import a module function.

    If the module fails to load, the application continues
    running and records the error for diagnostics.
    """

    try:

        module = __import__(
            module_path,
            fromlist=[function_name],
        )

        if hasattr(module, function_name):

            return getattr(
                module,
                function_name,
            )

        error = (
            f"{module_path}: missing function "
            f"'{function_name}'"
        )

        module_errors.append(error)

        logging.error(error)

        return None

    except Exception as e:

        error = (
            f"{module_path}: "
            f"{type(e).__name__}: {e}"
        )

        module_errors.append(error)

        logging.exception(
            f"Failed loading {module_path}"
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
                User.username == "admin"
            )
            .first()
        )

        if not admin:

            from auth import hash_password

            admin = User(
                username="admin",
                full_name="System Administrator",
                email="admin@nileharvest.com",
                password_hash=hash_password(
                    "admin123"
                ),
                role="Administrator",
                active=True,
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
# MODULE REGISTRY
# ==================================================

# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

dashboard_home = safe_import(
    "modules.dashboard.home",
    "dashboard_home",
)


# --------------------------------------------------
# PROCUREMENT
# --------------------------------------------------

procurement_dashboard = safe_import(
    "modules.procurement.dashboard",
    "procurement_dashboard",
)

procurement_suppliers = safe_import(
    "modules.procurement.suppliers",
    "suppliers_page",
)

procurement_purchases = safe_import(
    "modules.procurement.purchases",
    "purchases_page",
)

procurement_purchase_orders = safe_import(
    "modules.procurement.purchase_orders",
    "purchase_orders_page",
)


# --------------------------------------------------
# WAREHOUSE
# --------------------------------------------------

warehouse_dashboard = safe_import(
    "modules.warehouse.dashboard",
    "warehouse_dashboard",
)

warehouse_inventory = safe_import(
    "modules.warehouse.inventory",
    "inventory_page",
)


# --------------------------------------------------
# MILLING
# --------------------------------------------------

milling_dashboard = safe_import(
    "modules.milling.dashboard",
    "milling_dashboard",
)


# --------------------------------------------------
# PACKAGING
# --------------------------------------------------

packaging_dashboard = safe_import(
    "modules.packaging.dashboard",
    "packaging_dashboard",
)


# --------------------------------------------------
# SALES & DISTRIBUTION
# --------------------------------------------------

sales_dashboard = safe_import(
    "modules.sales.dashboard",
    "sales_dashboard",
)

sales_customers = safe_import(
    "modules.sales.customers",
    "customers_page",
)

sales_quotations = safe_import(
    "modules.sales.quotations",
    "quotations_page",
)

sales_orders = safe_import(
    "modules.sales.orders",
    "sales_orders_page",
)

sales_deliveries = safe_import(
    "modules.sales.deliveries",
    "deliveries_page",
)

sales_invoices = safe_import(
    "modules.sales.invoices",
    "invoices_page",
)

sales_payments = safe_import(
    "modules.sales.payments",
    "payments_page",
)


# --------------------------------------------------
# FINANCE
# --------------------------------------------------

finance_dashboard = safe_import(
    "modules.finance.dashboard",
    "finance_dashboard",
)


# --------------------------------------------------
# REPORTS
# --------------------------------------------------

reports_dashboard = safe_import(
    "modules.reports.dashboard",
    "reports_dashboard",
)


# ==================================================
# FALLBACK PAGE
# ==================================================

def _fallback_page(title):

    def _render():

        st.info(
            f"{title} – This section is currently "
            "being prepared."
        )

    return _render


# Procurement fallbacks

procurement_suppliers = (
    procurement_suppliers
    or _fallback_page("Suppliers")
)

procurement_purchases = (
    procurement_purchases
    or _fallback_page("Purchases")
)

procurement_purchase_orders = (
    procurement_purchase_orders
    or _fallback_page("Purchase Orders")
)


# Warehouse fallback

warehouse_inventory = (
    warehouse_inventory
    or _fallback_page("Inventory")
)


# ==================================================
# DATABASE INITIALIZATION
# ==================================================

def initialize_database():

    try:

        inspector = inspect(engine)

        existing_tables = (
            inspector.get_table_names()
        )

        missing_tables = [
            table
            for table in Base.metadata.tables
            if table not in existing_tables
        ]

        if missing_tables:

            logging.info(
                "Creating missing tables: %s",
                missing_tables,
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
                    "Seed data failed: %s",
                    e,
                )

    except Exception:

        logging.exception(
            "Database initialization failed"
        )

        st.error(
            "Database initialization failed. "
            "Please check esan_erp.log."
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

        if (
            user
            and user.active
            and verify_password(
                password,
                user.password_hash,
            )
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


# ==================================================
# LOGIN SCREEN
# ==================================================

if not st.session_state.logged_in:

    # ----------------------------------------------
    # ESAN BRANDING
    # ----------------------------------------------

    st.markdown(
        """
        <div class="esan-login-page">

            <div class="esan-login-container">

                <div class="esan-logo-mark">

                    <div class="esan-logo-ring"></div>

                    <div class="esan-logo-symbol"></div>

                    <div class="esan-logo-leaf"></div>

                </div>

                <div class="esan-wordmark">
                    Esan
                </div>

                <div class="esan-login-tagline">
                    ENTERPRISE MANAGEMENT SYSTEM
                </div>

            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


    # ----------------------------------------------
    # LOGIN FORM
    # ----------------------------------------------

    col1, col2, col3 = st.columns(
        [1, 2, 1]
    )

    with col2:

        username = st.text_input(
            "Username",
            placeholder="Enter your username",
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password",
        )

        if st.button(
            "Login",
            use_container_width=True,
            type="primary",
        ):

            if login(
                username,
                password,
            ):

                st.success(
                    "Login successful"
                )

                st.rerun()

            else:

                st.error(
                    "Invalid username or password"
                )


        st.info(
            "Default administrator: "
            "admin / admin123"
        )


    # ----------------------------------------------
    # LOGIN FOOTER
    # ----------------------------------------------

    st.markdown(
        """
        <div class="esan-login-footer"
             style="text-align:center">

            Nile Harvest Foods Ltd.
            <br>
            Esan ERP Enterprise Platform

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.stop()


# ==================================================
# MAIN HEADER
# ==================================================

st.title("🌾 Esan ERP")

st.caption(
    f"{COMPANY_NAME} | Version {VERSION}"
)


# ==================================================
# SIDEBAR NAVIGATION
# ==================================================

with st.sidebar:

    st.markdown(
        """
        <h2 style="text-align:center">
        🌾 Esan ERP
        </h2>
        """,
        unsafe_allow_html=True,
    )

    st.divider()


    def nav_button(label):

        if st.button(
            label,
            use_container_width=True,
        ):

            st.session_state.current_page = (
                label
            )


    # MAIN

    nav_button(
        "🏠 Overview"
    )


    # OPERATIONS

    st.markdown(
        "**OPERATIONS**"
    )

    nav_button(
        "🌾 Procurement"
    )

    nav_button(
        "📦 Warehouse"
    )

    nav_button(
        "🏭 Milling"
    )

    nav_button(
        "📦 Packaging"
    )


    # COMMERCIAL

    st.markdown(
        "**COMMERCIAL**"
    )

    nav_button(
        "🚚 Sales & Distribution"
    )


    # FINANCE

    st.markdown(
        "**FINANCE**"
    )

    nav_button(
        "💰 Finance"
    )


    # REPORTING

    st.markdown(
        "**REPORTING**"
    )

    nav_button(
        "📊 Reports"
    )


    st.divider()


    # USER PANEL

    st.markdown(
        "### 👤 User Panel"
    )

    st.write(
        f"User: **{st.session_state.username}**"
    )

    st.write(
        f"Role: **{st.session_state.role}**"
    )


    if st.button(
        "🚪 Logout",
        use_container_width=True,
    ):

        st.session_state.logged_in = False

        st.session_state.username = None

        st.session_state.role = None

        st.session_state.current_page = (
            "🏠 Overview"
        )

        st.rerun()


# ==================================================
# CURRENT PAGE
# ==================================================

menu = st.session_state.current_page


# ==================================================
# ERP ROUTER
# ==================================================

if menu == "🏠 Overview":

    if dashboard_home:

        dashboard_home()

    else:

        st.warning(
            "Overview dashboard could not be loaded."
        )


# ==================================================
# PROCUREMENT
# ==================================================

elif menu == "🌾 Procurement":

    st.header(
        "🌾 Procurement"
    )

    procurement_menu = st.radio(
        "Procurement Module",
        [
            "Dashboard",
            "Suppliers",
            "Purchase Orders",
            "Purchases",
        ],
        horizontal=True,
    )


    if procurement_menu == "Dashboard":

        if procurement_dashboard:

            procurement_dashboard()

        else:

            st.warning(
                "Procurement dashboard unavailable."
            )


    elif procurement_menu == "Suppliers":

        procurement_suppliers()


    elif procurement_menu == "Purchase Orders":

        procurement_purchase_orders()


    elif procurement_menu == "Purchases":

        procurement_purchases()


# ==================================================
# WAREHOUSE
# ==================================================

elif menu == "📦 Warehouse":

    st.header(
        "📦 Warehouse"
    )

    warehouse_menu = st.radio(
        "Warehouse Module",
        [
            "Dashboard",
            "Inventory",
        ],
        horizontal=True,
    )


    if warehouse_menu == "Dashboard":

        if warehouse_dashboard:

            warehouse_dashboard()

        else:

            st.warning(
                "Warehouse dashboard unavailable."
            )


    elif warehouse_menu == "Inventory":

        warehouse_inventory()


# ==================================================
# MILLING
# ==================================================

elif menu == "🏭 Milling":

    if milling_dashboard:

        milling_dashboard()

    else:

        st.warning(
            "Milling module unavailable."
        )


# ==================================================
# PACKAGING
# ==================================================

elif menu == "📦 Packaging":

    if packaging_dashboard:

        packaging_dashboard()

    else:

        st.warning(
            "Packaging module unavailable."
        )


# ==================================================
# SALES & DISTRIBUTION
# ==================================================

elif menu == "🚚 Sales & Distribution":

    st.header(
        "🚚 Sales & Distribution"
    )

    sales_menu = st.radio(
        "Sales Module",
        [
            "Dashboard",
            "Customers",
            "Quotations",
            "Sales Orders",
            "Deliveries",
            "Invoices",
            "Payments",
        ],
        horizontal=True,
    )


    sales_pages = {

        "Dashboard":
            sales_dashboard,

        "Customers":
            sales_customers,

        "Quotations":
            sales_quotations,

        "Sales Orders":
            sales_orders,

        "Deliveries":
            sales_deliveries,

        "Invoices":
            sales_invoices,

        "Payments":
            sales_payments,

    }


    page_func = sales_pages.get(
        sales_menu
    )


    if page_func:

        page_func()

    else:

        st.warning(
            f"{sales_menu} page unavailable."
        )


# ==================================================
# FINANCE
# ==================================================

elif menu == "💰 Finance":

    if finance_dashboard:

        finance_dashboard()

    else:

        st.warning(
            "Finance module unavailable."
        )


# ==================================================
# REPORTS
# ==================================================

elif menu == "📊 Reports":

    if reports_dashboard:

        reports_dashboard()

    else:

        st.warning(
            "Reports module unavailable."
        )


# ==================================================
# MODULE LOADING INFORMATION
# ==================================================

if module_errors:

    with st.expander(
        "⚠️ Module Loading Information"
    ):

        st.warning(
            "The following modules could not be loaded:"
        )

        for error in module_errors:

            st.write(
                f"• {error}"
            )


# ==================================================
# FOOTER
# ==================================================

st.divider()

st.caption(
    "© Nile Harvest Foods Ltd. | "
    "Esan ERP Enterprise Platform"
)