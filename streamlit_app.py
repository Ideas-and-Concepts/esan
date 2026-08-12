"""
Nile Harvest Foods Ltd.
Enterprise Resource Planning System

Esan ERP
Version 1.4.0 Alpha – Full Repository Integration
"""

import logging

import streamlit as st
from sqlalchemy import inspect

from config import COMPANY_NAME, VERSION
from database import Base, engine, SessionLocal
from models import User
from auth import verify_password


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    filename="esan_erp.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Nile Harvest ERP",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# ERP UI STYLES
# ============================================================

st.markdown(
    """
    <style>

    /* ========================================================
       HIDE STREAMLIT DEFAULT UI
       ======================================================== */

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
        padding-bottom: 2rem;
    }


    /* ========================================================
       SIDEBAR
       ======================================================== */

    div[data-testid="stSidebar"] {
        border-right: 1px solid #dddddd;
    }

    div[data-testid="stSidebar"] > div:first-child {
        padding-top: 1rem;
    }


    /* ========================================================
       ORIGINAL NILE HARVEST LOGO
       ======================================================== */

    .logo {
        width: 112px;
        height: 112px;

        margin: 0 auto 18px auto;

        border-radius: 32px;

        background:
            linear-gradient(
                145deg,
                #2e7d32,
                #1b5e20
            );

        display: flex;
        align-items: center;
        justify-content: center;

        position: relative;

        overflow: hidden;

        box-shadow:
            0 18px 45px
            rgba(20, 90, 55, 0.25);
    }


    /* ========================================================
       SOIL / GROUND
       ======================================================== */

    .logo::before {
        content: "";

        position: absolute;

        left: 0;
        bottom: 0;

        width: 100%;
        height: 28px;

        background: #4e342e;

        border-radius:
            0 0 28px 28px;

        z-index: 1;
    }


    /* ========================================================
       STEM
       ======================================================== */

    .logo-stem {
        position: absolute;

        bottom: 28px;
        left: 50%;

        transform:
            translateX(-50%);

        width: 6px;
        height: 40px;

        background: #aed581;

        border-radius:
            3px 3px 0 0;

        z-index: 2;
    }


    /* ========================================================
       LEAVES
       ======================================================== */

    .logo-leaf {
        position: absolute;

        bottom: 52px;

        width: 18px;
        height: 18px;

        background: #81c784;

        border-radius: 50%;

        z-index: 3;
    }


    .logo-leaf.left {
        left: 24px;

        transform:
            rotate(-30deg);
    }


    .logo-leaf.right {
        right: 24px;

        transform:
            rotate(30deg);
    }


    /* ========================================================
       LOGIN PAGE
       ======================================================== */

    .login-page {
        min-height: 32vh;

        display: flex;
        align-items: center;
        justify-content: center;

        padding: 20px 20px 5px 20px;
    }


    .login-container {
        width: 420px;
        max-width: 100%;

        text-align: center;
    }


    .login-logo-container {
        width: 100%;

        display: flex;
        align-items: center;
        justify-content: center;

        margin-top: 20px;
        margin-bottom: 5px;
    }


    /* ========================================================
       LOGIN INPUTS
       ======================================================== */

    div[data-testid="stTextInput"] label {
        font-weight: 600;
    }


    div[data-testid="stTextInput"] input {
        border-radius: 10px;

        min-height: 45px;

        padding-left: 14px;
    }


    /* ========================================================
       BUTTONS
       ======================================================== */

    div[data-testid="stButton"] > button {
        border-radius: 10px;

        min-height: 46px;

        font-weight: 700;
    }


    /* ========================================================
       SIDEBAR LOGO CONTAINER
       ======================================================== */

    .sidebar-logo-container {
        width: 100%;

        display: flex;
        align-items: center;
        justify-content: center;

        margin-top: 5px;
        margin-bottom: 15px;
    }


    /* ========================================================
       SIDEBAR NAVIGATION
       ======================================================== */

    div[data-testid="stSidebar"] div.stButton > button {
        text-align: left;

        border-radius: 9px;

        margin-bottom: 4px;

        min-height: 42px;
    }


    /* ========================================================
       SECTION LABELS
       ======================================================== */

    .sidebar-section {
        font-size: 0.72rem;

        font-weight: 800;

        letter-spacing: 0.08em;

        margin-top: 14px;
        margin-bottom: 6px;

        opacity: 0.65;
    }


    /* ========================================================
       USER PANEL
       ======================================================== */

    .user-panel {
        padding: 12px;

        border-radius: 12px;

        background:
            rgba(128, 128, 128, 0.08);

        margin-top: 10px;

        margin-bottom: 10px;
    }


    /* ========================================================
       MOBILE
       ======================================================== */

    @media (max-width: 768px) {

        .logo {
            width: 92px;
            height: 92px;

            border-radius: 26px;
        }

        .login-page {
            min-height: 25vh;
        }

        .block-container {
            padding-top: 1rem;
        }
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SAFE MODULE IMPORT SYSTEM
# ============================================================

module_errors = []


def safe_import(module_path, function_name):
    """
    Safely import a module function.

    Returns:
        callable or None
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
            f"{module_path}: "
            f"missing function '{function_name}'"
        )

        module_errors.append(error)

        logging.error(error)

        return None

    except Exception as exc:

        error = (
            f"{module_path}: "
            f"{type(exc).__name__}: {exc}"
        )

        module_errors.append(error)

        logging.exception(
            "Failed loading %s",
            module_path,
        )

        return None


# ============================================================
# ADMIN CREATION
# ============================================================

try:

    from services.user_service import create_admin

except ImportError:

    def create_admin(db):
        """
        Fallback admin creation.
        """

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


# ============================================================
# SEED DATA
# ============================================================

try:

    from seed.seed_data import load_seed_data

except ImportError:

    load_seed_data = None


# ============================================================
# MODULE REGISTRY
# ============================================================

# ------------------------------------------------------------
# Dashboard
# ------------------------------------------------------------

dashboard_home = safe_import(
    "modules.dashboard.home",
    "dashboard_home",
)


# ------------------------------------------------------------
# Procurement
# ------------------------------------------------------------

procurement_dashboard = safe_import(
    "modules.procurement.dashboard",
    "procurement_dashboard",
)

procurement_suppliers = safe_import(
    "modules.procurement.suppliers",
    "suppliers_page",
)

procurement_purchase_orders = safe_import(
    "modules.procurement.purchase_orders",
    "purchase_orders_page",
)

procurement_purchases = safe_import(
    "modules.procurement.purchases",
    "purchases_page",
)


# ------------------------------------------------------------
# Warehouse
# ------------------------------------------------------------

warehouse_dashboard = safe_import(
    "modules.warehouse.dashboard",
    "warehouse_dashboard",
)

warehouse_inventory = safe_import(
    "modules.warehouse.inventory",
    "inventory_page",
)


# ------------------------------------------------------------
# Milling
# ------------------------------------------------------------

milling_dashboard = safe_import(
    "modules.milling.dashboard",
    "milling_dashboard",
)


# ------------------------------------------------------------
# Packaging
# ------------------------------------------------------------

packaging_dashboard = safe_import(
    "modules.packaging.dashboard",
    "packaging_dashboard",
)


# ------------------------------------------------------------
# Sales
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# Finance
# ------------------------------------------------------------

finance_dashboard = safe_import(
    "modules.finance.dashboard",
    "finance_dashboard",
)


# ------------------------------------------------------------
# Reports
# ------------------------------------------------------------

reports_dashboard = safe_import(
    "modules.reports.dashboard",
    "reports_dashboard",
)


# ============================================================
# FALLBACK PAGE
# ============================================================

def _fallback_page(title):

    def _render():

        st.info(
            f"{title} – "
            "This section is currently being prepared."
        )

    return _render


procurement_suppliers = (
    procurement_suppliers
    or _fallback_page("Suppliers")
)

procurement_purchase_orders = (
    procurement_purchase_orders
    or _fallback_page("Purchase Orders")
)

procurement_purchases = (
    procurement_purchases
    or _fallback_page("Purchases")
)

warehouse_inventory = (
    warehouse_inventory
    or _fallback_page("Inventory")
)


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def initialize_database():

    try:

        inspector = inspect(engine)

        existing_tables = (
            inspector.get_table_names()
        )

        missing_tables = [
            table_name
            for table_name in Base.metadata.tables
            if table_name not in existing_tables
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

            except Exception as exc:

                logging.warning(
                    "Seed data failed: %s",
                    exc,
                )

    except Exception as exc:

        logging.exception(
            "Database initialization failed"
        )

        st.error(
            "Database initialization failed. "
            "Please check esan_erp.log."
        )


initialize_database()


# ============================================================
# SESSION MANAGEMENT
# ============================================================

if "logged_in" not in st.session_state:

    st.session_state.logged_in = False

if "username" not in st.session_state:

    st.session_state.username = None

if "role" not in st.session_state:

    st.session_state.role = None

if "current_page" not in st.session_state:

    st.session_state.current_page = (
        "🏠 Overview"
    )


# ============================================================
# LOGIN FUNCTION
# ============================================================

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

    except Exception:

        logging.exception(
            "Login error"
        )

        return False

    finally:

        db.close()


# ============================================================
# LOGIN SCREEN
# ============================================================

if not st.session_state.logged_in:

    # --------------------------------------------------------
    # Original Nile Harvest Logo
    # --------------------------------------------------------

    st.markdown(
        """
        <div class="login-page">

            <div class="login-container">

                <div class="login-logo-container">

                    <div class="logo">

                        <div class="logo-stem"></div>

                        <div class="logo-leaf left"></div>

                        <div class="logo-leaf right"></div>

                    </div>

                </div>

            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


    # --------------------------------------------------------
    # Login Form
    # --------------------------------------------------------

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

    st.stop()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    # --------------------------------------------------------
    # ORIGINAL NILE HARVEST LOGO
    # --------------------------------------------------------

    st.markdown(
        """
        <div class="sidebar-logo-container">

            <div class="logo">

                <div class="logo-stem"></div>

                <div class="logo-leaf left"></div>

                <div class="logo-leaf right"></div>

            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


    st.divider()


    # --------------------------------------------------------
    # Navigation Button
    # --------------------------------------------------------

    def nav_button(label):

        if st.button(
            label,
            use_container_width=True,
            key=f"nav_{label}",
        ):

            st.session_state.current_page = label

            st.rerun()


    # --------------------------------------------------------
    # Overview
    # --------------------------------------------------------

    nav_button(
        "🏠 Overview"
    )


    # --------------------------------------------------------
    # Operations
    # --------------------------------------------------------

    st.markdown(
        '<div class="sidebar-section">'
        'OPERATIONS'
        '</div>',
        unsafe_allow_html=True,
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


    # --------------------------------------------------------
    # Commercial
    # --------------------------------------------------------

    st.markdown(
        '<div class="sidebar-section">'
        'COMMERCIAL'
        '</div>',
        unsafe_allow_html=True,
    )

    nav_button(
        "🚚 Sales & Distribution"
    )


    # --------------------------------------------------------
    # Finance
    # --------------------------------------------------------

    st.markdown(
        '<div class="sidebar-section">'
        'FINANCE'
        '</div>',
        unsafe_allow_html=True,
    )

    nav_button(
        "💰 Finance"
    )


    # --------------------------------------------------------
    # Reporting
    # --------------------------------------------------------

    st.markdown(
        '<div class="sidebar-section">'
        'REPORTING'
        '</div>',
        unsafe_allow_html=True,
    )

    nav_button(
        "📊 Reports"
    )


    st.divider()


    # --------------------------------------------------------
    # User Panel
    # --------------------------------------------------------

    st.markdown(
        '<div class="user-panel">',
        unsafe_allow_html=True,
    )

    st.markdown(
        "### 👤 User Panel"
    )

    st.write(
        f"User: **{st.session_state.username}**"
    )

    st.write(
        f"Role: **{st.session_state.role}**"
    )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )


    # --------------------------------------------------------
    # Logout
    # --------------------------------------------------------

    if st.button(
        "🚪 Logout",
        use_container_width=True,
        key="logout_button",
    ):

        st.session_state.logged_in = False

        st.session_state.username = None

        st.session_state.role = None

        st.session_state.current_page = (
            "🏠 Overview"
        )

        st.rerun()


# ============================================================
# CURRENT PAGE
# ============================================================

menu = st.session_state.current_page


# ============================================================
# ERP ROUTER
# ============================================================

# ------------------------------------------------------------
# OVERVIEW
# ------------------------------------------------------------

if menu == "🏠 Overview":

    if dashboard_home:

        dashboard_home()

    else:

        st.warning(
            "Overview dashboard could not be loaded."
        )


# ------------------------------------------------------------
# PROCUREMENT
# ------------------------------------------------------------

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
        key="procurement_navigation",
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


# ------------------------------------------------------------
# WAREHOUSE
# ------------------------------------------------------------

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
        key="warehouse_navigation",
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


# ------------------------------------------------------------
# MILLING
# ------------------------------------------------------------

elif menu == "🏭 Milling":

    if milling_dashboard:

        milling_dashboard()

    else:

        st.warning(
            "Milling module unavailable."
        )


# ------------------------------------------------------------
# PACKAGING
# ------------------------------------------------------------

elif menu == "📦 Packaging":

    if packaging_dashboard:

        packaging_dashboard()

    else:

        st.warning(
            "Packaging module unavailable."
        )


# ------------------------------------------------------------
# SALES & DISTRIBUTION
# ------------------------------------------------------------

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
        key="sales_navigation",
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


# ------------------------------------------------------------
# FINANCE
# ------------------------------------------------------------

elif menu == "💰 Finance":

    if finance_dashboard:

        finance_dashboard()

    else:

        st.warning(
            "Finance module unavailable."
        )


# ------------------------------------------------------------
# REPORTS
# ------------------------------------------------------------

elif menu == "📊 Reports":

    if reports_dashboard:

        reports_dashboard()

    else:

        st.warning(
            "Reports module unavailable."
        )


# ============================================================
# MODULE LOADING INFORMATION
# ============================================================

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


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    f"© {COMPANY_NAME} | "
    f"Enterprise Resource Planning Platform | "
    f"Version {VERSION}"
)