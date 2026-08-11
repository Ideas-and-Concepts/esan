"""
Esan ERP Controller
Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Version 1.4.0 Alpha
Module-Driven Architecture

Architecture
------------
streamlit_app.py
      |
      +-- modules/
      |     +-- dashboard/
      |     +-- procurement/
      |     +-- warehouse/
      |     +-- milling/
      |     +-- packaging/
      |     +-- sales/
      |     +-- finance/
      |     +-- reports/
      |
      +-- database.py
      +-- models.py
      +-- auth.py
      +-- seed/
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
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("esan_erp")


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Esan ERP",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# ERP UI STYLING
# ============================================================

st.markdown(
    """
    <style>

    /* ------------------------------------------------------
       STREAMLIT CHROME
    ------------------------------------------------------ */

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    header {
        visibility: hidden;
    }

    /* ------------------------------------------------------
       GLOBAL PAGE
    ------------------------------------------------------ */

    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        max-width: 1600px;
    }

    /* ------------------------------------------------------
       FLOATING SIDEBAR
    ------------------------------------------------------ */

    section[data-testid="stSidebar"] {
        background: transparent;
        border: none;
    }

    section[data-testid="stSidebar"] > div {
        background: #f8faf9;
        border-right: 1px solid #dfe5e1;
        box-shadow: 6px 0 24px rgba(0, 0, 0, 0.05);
    }

    /* ------------------------------------------------------
       SIDEBAR BRAND
    ------------------------------------------------------ */

    .esan-brand {
        padding: 10px 8px 18px 8px;
        text-align: center;
    }

    .esan-brand-icon {
        font-size: 2.2rem;
        margin-bottom: 3px;
    }

    .esan-brand-title {
        font-size: 1.35rem;
        font-weight: 750;
        color: #1f2937;
        letter-spacing: -0.5px;
    }

    .esan-brand-company {
        font-size: 0.72rem;
        color: #6b7280;
        margin-top: 3px;
    }

    .esan-version {
        display: inline-block;
        margin-top: 8px;
        padding: 3px 8px;
        border-radius: 20px;
        background: #e8f5e9;
        color: #2e7d32;
        font-size: 0.65rem;
        font-weight: 600;
    }

    /* ------------------------------------------------------
       SIDEBAR SECTION HEADINGS
    ------------------------------------------------------ */

    .nav-section {
        color: #7a827d;
        font-size: 0.68rem;
        font-weight: 750;
        letter-spacing: 0.08em;
        margin: 18px 6px 6px 6px;
        text-transform: uppercase;
    }

    /* ------------------------------------------------------
       STREAMLIT SIDEBAR BUTTONS
    ------------------------------------------------------ */

    section[data-testid="stSidebar"] .stButton > button {
        width: 100%;
        border: 1px solid transparent;
        background: transparent;
        color: #374151;
        text-align: left;
        border-radius: 9px;
        padding: 9px 12px;
        margin: 2px 0;
        font-size: 0.88rem;
        transition: all 0.15s ease;
    }

    section[data-testid="stSidebar"] .stButton > button:hover {
        background: #e8f5e9;
        border-color: #c8e6c9;
        color: #1b5e20;
    }

    /* ------------------------------------------------------
       USER CARD
    ------------------------------------------------------ */

    .user-card {
        margin-top: 18px;
        padding: 12px;
        background: white;
        border: 1px solid #e2e8e4;
        border-radius: 10px;
    }

    .user-card-name {
        font-size: 0.88rem;
        font-weight: 700;
        color: #263238;
    }

    .user-card-role {
        font-size: 0.72rem;
        color: #718096;
        margin-top: 2px;
    }

    /* ------------------------------------------------------
       MAIN HEADER
    ------------------------------------------------------ */

    .esan-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: white;
        border: 1px solid #e3e8e5;
        border-radius: 14px;
        padding: 16px 20px;
        margin-bottom: 18px;
        box-shadow: 0 3px 14px rgba(0, 0, 0, 0.035);
    }

    .esan-header-title {
        font-size: 1.55rem;
        font-weight: 750;
        color: #263238;
    }

    .esan-header-subtitle {
        font-size: 0.78rem;
        color: #718096;
        margin-top: 3px;
    }

    .esan-header-module {
        padding: 7px 12px;
        background: #e8f5e9;
        color: #2e7d32;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 650;
    }

    /* ------------------------------------------------------
       MODULE HEADER
    ------------------------------------------------------ */

    .module-header {
        margin-bottom: 15px;
    }

    .module-title {
        font-size: 1.45rem;
        font-weight: 750;
        color: #263238;
    }

    .module-description {
        color: #718096;
        font-size: 0.82rem;
        margin-top: 3px;
    }

    /* ------------------------------------------------------
       KPI CARDS
    ------------------------------------------------------ */

    .kpi-card {
        background: white;
        border: 1px solid #e5e9e6;
        border-radius: 12px;
        padding: 18px;
        box-shadow: 0 3px 12px rgba(0,0,0,0.035);
    }

    .kpi-label {
        color: #718096;
        font-size: 0.76rem;
        font-weight: 600;
    }

    .kpi-value {
        color: #263238;
        font-size: 1.55rem;
        font-weight: 750;
        margin-top: 5px;
    }

    /* ------------------------------------------------------
       FOOTER
    ------------------------------------------------------ */

    .esan-footer {
        text-align: center;
        color: #9ca3af;
        font-size: 0.7rem;
        padding: 18px 0 4px 0;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# SAFE IMPORT SYSTEM
# ============================================================

module_errors = []


def safe_import(module_path, function_name):
    """
    Safely imports a module function.

    This prevents one incomplete ERP module from crashing
    the entire application.
    """
    try:
        module = __import__(module_path, fromlist=[function_name])

        if hasattr(module, function_name):
            return getattr(module, function_name)

        message = f"{module_path}: missing function '{function_name}'"
        module_errors.append(message)
        logger.warning(message)
        return None

    except Exception as exc:
        message = f"{module_path}: {exc}"
        module_errors.append(message)
        logger.exception(message)
        return None


# ============================================================
# ADMIN CREATION
# ============================================================

try:
    from services.user_service import create_admin

except ImportError:

    def create_admin(db):
        """
        Fallback administrator creation.
        """

        admin = (
            db.query(User)
            .filter(User.username == "admin")
            .first()
        )

        if not admin:
            from auth import hash_password

            admin = User(
                username="admin",
                password_hash=hash_password("admin123"),
                role="Administrator"
            )

            db.add(admin)
            db.commit()

            logger.info("Default administrator created.")


# ============================================================
# OPTIONAL SEED DATA
# ============================================================

try:
    from seed.seed_data import load_seed_data
except ImportError:
    load_seed_data = None


# ============================================================
# MODULE IMPORTS
#
# IMPORTANT:
# The application now depends on modules/ only.
# No pages/ directory is required.
# ============================================================

# ------------------------------------------------------------
# Dashboard
# ------------------------------------------------------------

dashboard_home = safe_import(
    "modules.dashboard.home",
    "dashboard_home"
)


# ------------------------------------------------------------
# Procurement
# ------------------------------------------------------------

procurement_dashboard = safe_import(
    "modules.procurement.dashboard",
    "procurement_dashboard"
)

procurement_suppliers = safe_import(
    "modules.procurement.suppliers",
    "suppliers_page"
)

procurement_purchases = safe_import(
    "modules.procurement.purchases",
    "purchases_page"
)


# ------------------------------------------------------------
# Warehouse
# ------------------------------------------------------------

warehouse_dashboard = safe_import(
    "modules.warehouse.dashboard",
    "warehouse_dashboard"
)

warehouse_inventory = safe_import(
    "modules.warehouse.inventory",
    "inventory_page"
)


# ------------------------------------------------------------
# Milling
# ------------------------------------------------------------

milling_dashboard = safe_import(
    "modules.milling.dashboard",
    "milling_dashboard"
)


# ------------------------------------------------------------
# Packaging
# ------------------------------------------------------------

packaging_dashboard = safe_import(
    "modules.packaging.dashboard",
    "packaging_dashboard"
)


# ------------------------------------------------------------
# Sales & Distribution
# ------------------------------------------------------------

sales_dashboard = safe_import(
    "modules.sales.dashboard",
    "sales_dashboard"
)

sales_customers = safe_import(
    "modules.sales.customers",
    "customers_page"
)

sales_quotations = safe_import(
    "modules.sales.quotations",
    "quotations_page"
)

sales_orders = safe_import(
    "modules.sales.orders",
    "sales_orders_page"
)

sales_deliveries = safe_import(
    "modules.sales.deliveries",
    "deliveries_page"
)

sales_invoices = safe_import(
    "modules.sales.invoices",
    "invoices_page"
)

sales_payments = safe_import(
    "modules.sales.payments",
    "payments_page"
)


# ------------------------------------------------------------
# Finance
# ------------------------------------------------------------

finance_dashboard = safe_import(
    "modules.finance.dashboard",
    "finance_dashboard"
)


# ------------------------------------------------------------
# Reports
# ------------------------------------------------------------

reports_dashboard = safe_import(
    "modules.reports.dashboard",
    "reports_dashboard"
)


# ============================================================
# MODULE REGISTRY
#
# Central definition of the ERP navigation.
# ============================================================

MODULE_REGISTRY = {

    "🏠 Overview": {
        "title": "Overview",
        "section": "MAIN",
        "function": dashboard_home,
        "children": None,
    },

    "🌾 Procurement": {
        "title": "Procurement",
        "section": "OPERATIONS",
        "function": procurement_dashboard,
        "children": {
            "Dashboard": procurement_dashboard,
            "Suppliers": procurement_suppliers,
            "Purchase Orders": procurement_purchases,
        },
    },

    "📦 Warehouse": {
        "title": "Warehouse",
        "section": "OPERATIONS",
        "function": warehouse_dashboard,
        "children": {
            "Dashboard": warehouse_dashboard,
            "Inventory": warehouse_inventory,
        },
    },

    "🏭 Milling": {
        "title": "Milling",
        "section": "OPERATIONS",
        "function": milling_dashboard,
        "children": None,
    },

    "📦 Packaging": {
        "title": "Packaging",
        "section": "OPERATIONS",
        "function": packaging_dashboard,
        "children": None,
    },

    "🚚 Sales & Distribution": {
        "title": "Sales & Distribution",
        "section": "COMMERCIAL",
        "function": sales_dashboard,
        "children": {
            "Dashboard": sales_dashboard,
            "Customers": sales_customers,
            "Quotations": sales_quotations,
            "Sales Orders": sales_orders,
            "Deliveries": sales_deliveries,
            "Invoices": sales_invoices,
            "Payments": sales_payments,
        },
    },

    "💰 Finance": {
        "title": "Finance",
        "section": "FINANCE",
        "function": finance_dashboard,
        "children": None,
    },

    "📊 Reports": {
        "title": "Reports",
        "section": "REPORTING",
        "function": reports_dashboard,
        "children": None,
    },
}


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def initialize_database():
    """
    Creates missing database tables and ensures that the
    administrator account exists.
    """

    try:

        inspector = inspect(engine)

        existing_tables = inspector.get_table_names()

        missing_tables = [
            table_name
            for table_name in Base.metadata.tables
            if table_name not in existing_tables
        ]

        if missing_tables:
            logger.info(
                "Creating missing tables: %s",
                ", ".join(missing_tables)
            )

        Base.metadata.create_all(bind=engine)

        db = SessionLocal()

        try:
            create_admin(db)

        finally:
            db.close()

        # Seed data is optional.
        if load_seed_data:

            try:
                load_seed_data()
                logger.info("Seed data loaded.")

            except Exception as exc:
                logger.warning(
                    "Seed data failed: %s",
                    exc
                )

    except Exception as exc:

        logger.exception(
            "Database initialization failed: %s",
            exc
        )

        st.error(
            "Database initialization failed. "
            "Check esan_erp.log for details."
        )


initialize_database()


# ============================================================
# SESSION STATE
# ============================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = None

if "role" not in st.session_state:
    st.session_state.role = None

if "current_page" not in st.session_state:
    st.session_state.current_page = "🏠 Overview"

if "current_subpage" not in st.session_state:
    st.session_state.current_subpage = "Dashboard"


# ============================================================
# AUTHENTICATION
# ============================================================

def login(username, password):

    db = SessionLocal()

    try:

        user = (
            db.query(User)
            .filter(User.username == username)
            .first()
        )

        if user and verify_password(
            password,
            user.password_hash
        ):

            st.session_state.logged_in = True
            st.session_state.username = user.username
            st.session_state.role = user.role

            logger.info(
                "User '%s' logged in.",
                username
            )

            return True

        logger.warning(
            "Failed login attempt for '%s'.",
            username
        )

        return False

    finally:
        db.close()


def logout():

    logger.info(
        "User '%s' logged out.",
        st.session_state.username
    )

    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None
    st.session_state.current_page = "🏠 Overview"
    st.session_state.current_subpage = "Dashboard"

    st.rerun()


# ============================================================
# LOGIN SCREEN
# ============================================================

if not st.session_state.logged_in:

    st.markdown(
        """
        <div style="
            max-width:520px;
            margin:80px auto 20px auto;
            text-align:center;
        ">
            <div style="font-size:4rem;">🌾</div>

            <h1 style="
                margin-bottom:4px;
                color:#263238;
            ">
                Esan ERP
            </h1>

            <h3 style="
                color:#4a5568;
                margin-bottom:5px;
            ">
                Nile Harvest Foods Ltd.
            </h3>

            <p style="
                color:#718096;
                font-size:0.9rem;
            ">
                Enterprise Milling & Packaging Management System
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([1, 1.4, 1])

    with col2:

        st.markdown("### 🔐 Sign in")

        username = st.text_input(
            "Username",
            placeholder="Enter username"
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter password"
        )

        if st.button(
            "Login",
            type="primary",
            use_container_width=True
        ):

            if login(username, password):

                st.success("Login successful.")
                st.rerun()

            else:

                st.error(
                    "Invalid username or password."
                )

        st.caption(
            "Default administrator: admin / admin123"
        )

    st.stop()


# ============================================================
# SIDEBAR HELPERS
# ============================================================

def select_page(page):

    st.session_state.current_page = page
    st.session_state.current_subpage = "Dashboard"


def select_subpage(page, subpage):

    st.session_state.current_page = page
    st.session_state.current_subpage = subpage


# ============================================================
# FLOATING ERP SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        f"""
        <div class="esan-brand">

            <div class="esan-brand-icon">
                🌾
            </div>

            <div class="esan-brand-title">
                Esan ERP
            </div>

            <div class="esan-brand-company">
                {COMPANY_NAME}
            </div>

            <div class="esan-version">
                Version {VERSION}
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # MAIN
    # --------------------------------------------------------

    st.markdown(
        '<div class="nav-section">Main</div>',
        unsafe_allow_html=True
    )

    if st.button(
        "🏠  Overview",
        use_container_width=True,
        key="nav_overview"
    ):
        select_page("🏠 Overview")
        st.rerun()


    # --------------------------------------------------------
    # OPERATIONS
    # --------------------------------------------------------

    st.markdown(
        '<div class="nav-section">Operations</div>',
        unsafe_allow_html=True
    )

    if st.button(
        "🌾  Procurement",
        use_container_width=True,
        key="nav_procurement"
    ):
        select_page("🌾 Procurement")
        st.rerun()

    if st.button(
        "📦  Warehouse",
        use_container_width=True,
        key="nav_warehouse"
    ):
        select_page("📦 Warehouse")
        st.rerun()

    if st.button(
        "🏭  Milling",
        use_container_width=True,
        key="nav_milling"
    ):
        select_page("🏭 Milling")
        st.rerun()

    if st.button(
        "📦  Packaging",
        use_container_width=True,
        key="nav_packaging"
    ):
        select_page("📦 Packaging")
        st.rerun()


    # --------------------------------------------------------
    # COMMERCIAL
    # --------------------------------------------------------

    st.markdown(
        '<div class="nav-section">Commercial</div>',
        unsafe_allow_html=True
    )

    if st.button(
        "🚚  Sales & Distribution",
        use_container_width=True,
        key="nav_sales"
    ):
        select_page("🚚 Sales & Distribution")
        st.rerun()


    # --------------------------------------------------------
    # FINANCE
    # --------------------------------------------------------

    st.markdown(
        '<div class="nav-section">Finance</div>',
        unsafe_allow_html=True
    )

    if st.button(
        "💰  Finance",
        use_container_width=True,
        key="nav_finance"
    ):
        select_page("💰 Finance")
        st.rerun()


    # --------------------------------------------------------
    # REPORTING
    # --------------------------------------------------------

    st.markdown(
        '<div class="nav-section">Reporting</div>',
        unsafe_allow_html=True
    )

    if st.button(
        "📊  Reports",
        use_container_width=True,
        key="nav_reports"
    ):
        select_page("📊 Reports")
        st.rerun()


    # --------------------------------------------------------
    # ADMINISTRATION
    # --------------------------------------------------------

    if st.session_state.role == "Administrator":

        st.markdown(
            '<div class="nav-section">Administration</div>',
            unsafe_allow_html=True
        )

        st.info(
            "Administrator access enabled."
        )


    # --------------------------------------------------------
    # USER PANEL
    # --------------------------------------------------------

    st.markdown(
        f"""
        <div class="user-card">

            <div class="user-card-name">
                👤 {st.session_state.username}
            </div>

            <div class="user-card-role">
                {st.session_state.role}
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    st.write("")

    if st.button(
        "🚪  Logout",
        use_container_width=True,
        key="logout_button"
    ):
        logout()


# ============================================================
# CURRENT MODULE
# ============================================================

current_page = st.session_state.current_page

module = MODULE_REGISTRY.get(current_page)


# ============================================================
# MAIN ERP HEADER
# ============================================================

if module:

    st.markdown(
        f"""
        <div class="esan-header">

            <div>

                <div class="esan-header-title">
                    🌾 Esan ERP
                </div>

                <div class="esan-header-subtitle">
                    {COMPANY_NAME}
                    &nbsp;|&nbsp;
                    Enterprise Milling & Packaging Management System
                </div>

            </div>

            <div class="esan-header-module">
                {module["title"]}
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# MODULE HEADER
# ============================================================

if module:

    st.markdown(
        f"""
        <div class="module-header">

            <div class="module-title">
                {current_page}
            </div>

            <div class="module-description">
                {module["title"]} module
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# SUB-NAVIGATION
#
# Instead of nested radio buttons, use compact horizontal
# buttons for modules with child pages.
# ============================================================

if module and module["children"]:

    children = module["children"]

    child_names = list(children.keys())

    # Keep current subpage valid.
    if st.session_state.current_subpage not in child_names:
        st.session_state.current_subpage = child_names[0]

    cols = st.columns(len(child_names))

    for index, child_name in enumerate(child_names):

        with cols[index]:

            if st.button(
                child_name,
                use_container_width=True,
                key=f"subnav_{current_page}_{child_name}"
            ):

                st.session_state.current_subpage = child_name
                st.rerun()


# ============================================================
# MODULE ROUTER
# ============================================================

def render_module(function, module_name):

    """
    Executes an ERP module safely.

    Modules remain independent files inside modules/.
    A failure inside one module will not crash the
    entire ERP controller.
    """

    if function is None:

        st.warning(
            f"{module_name} is currently unavailable."
        )

        return

    try:

        function()

    except Exception as exc:

        logger.exception(
            "Module '%s' failed: %s",
            module_name,
            exc
        )

        st.error(
            f"{module_name} could not be loaded."
        )

        with st.expander(
            "Technical information"
        ):

            st.code(
                str(exc)
            )


# ============================================================
# ROUTE CURRENT PAGE
# ============================================================

if current_page == "🏠 Overview":

    render_module(
        dashboard_home,
        "Overview"
    )


elif current_page == "🌾 Procurement":

    selected = st.session_state.current_subpage

    render_module(
        MODULE_REGISTRY[current_page]["children"].get(selected),
        f"Procurement / {selected}"
    )


elif current_page == "📦 Warehouse":

    selected = st.session_state.current_subpage

    render_module(
        MODULE_REGISTRY[current_page]["children"].get(selected),
        f"Warehouse / {selected}"
    )


elif current_page == "🏭 Milling":

    render_module(
        milling_dashboard,
        "Milling"
    )


elif current_page == "📦 Packaging":

    render_module(
        packaging_dashboard,
        "Packaging"
    )


elif current_page == "🚚 Sales & Distribution":

    selected = st.session_state.current_subpage

    render_module(
        MODULE_REGISTRY[current_page]["children"].get(selected),
        f"Sales & Distribution / {selected}"
    )


elif current_page == "💰 Finance":

    render_module(
        finance_dashboard,
        "Finance"
    )


elif current_page == "📊 Reports":

    render_module(
        reports_dashboard,
        "Reports"
    )


else:

    st.error(
        "ERP module not found."
    )


# ============================================================
# MODULE LOADING INFORMATION
# ============================================================

if module_errors:

    with st.expander(
        "⚠️ Module Loading Information"
    ):

        st.caption(
            "These messages identify modules that could not "
            "be imported. They do not necessarily prevent "
            "the rest of Esan ERP from running."
        )

        for error in module_errors:

            st.write(
                f"• {error}"
            )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    f"""
    <div class="esan-footer">
        © Nile Harvest Foods Ltd.
        &nbsp;|&nbsp;
        Esan ERP Enterprise Platform
        &nbsp;|&nbsp;
        Version {VERSION}
    </div>
    """,
    unsafe_allow_html=True
    )
