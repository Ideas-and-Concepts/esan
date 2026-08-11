"""
Esan ERP Controller
Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Version 1.4.0 Alpha

Architecture
------------
streamlit_app.py
    ├── Authentication
    ├── Database initialization
    ├── ERP sidebar navigation
    ├── Dynamic module header
    ├── Module registry
    ├── Safe module imports
    ├── Safe module rendering
    └── Module diagnostics

modules/
    ├── dashboard/
    ├── procurement/
    ├── warehouse/
    ├── milling/
    ├── packaging/
    ├── sales/
    ├── finance/
    └── reports/

The pages/ directory is NOT required.
"""

# ============================================================
# STANDARD LIBRARY
# ============================================================

import html
import logging
from typing import Callable, Optional


# ============================================================
# THIRD-PARTY
# ============================================================

import streamlit as st
from sqlalchemy import inspect


# ============================================================
# ESAN CORE
# ============================================================

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

logger = logging.getLogger("esan_erp")


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Esan ERP",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# GLOBAL ERP UI
# ============================================================

st.markdown(
    """
    <style>

    /* ======================================================
       STREAMLIT CLEANUP
       ====================================================== */

    #MainMenu {
        visibility: hidden;
    }

    header {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        max-width: 1600px;
    }


    /* ======================================================
       SIDEBAR
       ====================================================== */

    section[data-testid="stSidebar"] {
        background: transparent;
        border: none;
    }

    section[data-testid="stSidebar"] > div {
        background: #f8faf9;
        border-right: 1px solid #dfe5e1;
        box-shadow: 5px 0 20px rgba(0, 0, 0, 0.05);
    }


    /* ======================================================
       SIDEBAR BRAND
       ====================================================== */

    .esan-brand {
        text-align: center;
        padding: 10px 5px 18px 5px;
    }

    .esan-logo {
        font-size: 2.3rem;
        line-height: 1;
    }

    .esan-title {
        font-size: 1.35rem;
        font-weight: 750;
        color: #263238;
        margin-top: 6px;
    }

    .esan-company {
        font-size: 0.72rem;
        color: #718096;
        margin-top: 3px;
    }

    .esan-version {
        display: inline-block;
        margin-top: 8px;
        padding: 3px 9px;
        border-radius: 20px;
        background: #e8f5e9;
        color: #2e7d32;
        font-size: 0.65rem;
        font-weight: 700;
    }


    /* ======================================================
       SIDEBAR SECTION LABELS
       ====================================================== */

    .nav-section {
        margin: 17px 5px 6px 5px;
        color: #7b817d;
        font-size: 0.67rem;
        font-weight: 750;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }


    /* ======================================================
       SIDEBAR BUTTONS
       ====================================================== */

    section[data-testid="stSidebar"] .stButton > button {
        width: 100%;
        text-align: left;
        background: transparent;
        color: #374151;
        border: 1px solid transparent;
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


    /* ======================================================
       ACTIVE MODULE
       ====================================================== */

    .esan-active-module {
        background: #e8f5e9;
        border: 1px solid #c8e6c9;
        border-radius: 9px;
        color: #1b5e20;
        font-weight: 700;
        padding: 9px 12px;
        margin: 2px 0;
        font-size: 0.88rem;
    }


    /* ======================================================
       USER PANEL
       ====================================================== */

    .esan-user {
        background: white;
        border: 1px solid #e2e8e4;
        border-radius: 10px;
        padding: 11px;
        margin-top: 16px;
    }

    .esan-user-name {
        font-size: 0.86rem;
        font-weight: 700;
        color: #263238;
    }

    .esan-user-role {
        font-size: 0.7rem;
        color: #718096;
        margin-top: 3px;
    }


    /* ======================================================
       MAIN ERP HEADER
       ====================================================== */

    .esan-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: white;
        border: 1px solid #e3e8e5;
        border-radius: 14px;
        padding: 15px 20px;
        margin-bottom: 18px;
        box-shadow: 0 3px 14px rgba(0, 0, 0, 0.035);
    }

    .esan-header-title {
        font-size: 1.45rem;
        font-weight: 750;
        color: #263238;
    }

    .esan-header-subtitle {
        color: #718096;
        font-size: 0.76rem;
        margin-top: 3px;
    }

    .esan-header-module {
        background: #e8f5e9;
        color: #2e7d32;
        padding: 7px 12px;
        border-radius: 20px;
        font-size: 0.74rem;
        font-weight: 700;
        white-space: nowrap;
    }


    /* ======================================================
       MODULE TITLE
       ====================================================== */

    .module-title {
        color: #263238;
        font-size: 1.35rem;
        font-weight: 750;
        margin-bottom: 2px;
    }

    .module-subtitle {
        color: #718096;
        font-size: 0.78rem;
        margin-bottom: 15px;
    }


    /* ======================================================
       SUBNAVIGATION
       ====================================================== */

    .esan-subnav {
        margin-bottom: 18px;
    }


    /* ======================================================
       LOGIN
       ====================================================== */

    .esan-login-card {
        max-width: 520px;
        margin: 70px auto 20px auto;
        text-align: center;
    }

    .esan-login-logo {
        font-size: 4rem;
        line-height: 1;
    }

    .esan-login-title {
        color: #263238;
        margin: 10px 0 3px 0;
        font-size: 2.1rem;
        font-weight: 750;
    }

    .esan-login-company {
        color: #4a5568;
        margin: 0;
        font-size: 1.1rem;
        font-weight: 600;
    }

    .esan-login-description {
        color: #718096;
        font-size: 0.9rem;
        margin-top: 7px;
    }


    /* ======================================================
       FOOTER
       ====================================================== */

    .esan-footer {
        text-align: center;
        color: #9ca3af;
        font-size: 0.7rem;
        margin-top: 30px;
        padding-bottom: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

DEFAULT_SESSION = {
    "logged_in": False,
    "username": None,
    "full_name": None,
    "role": None,
    "current_page": "🏠 Overview",
    "current_subpage": "Dashboard",
    "seed_loaded": False,
}

for key, value in DEFAULT_SESSION.items():

    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# MODULE ERROR REGISTRY
# ============================================================

module_errors = []


# ============================================================
# SAFE MODULE IMPORT
# ============================================================

def safe_import(
    module_path: str,
    function_name: str,
) -> Optional[Callable]:
    """
    Safely import a module function.

    A broken optional module must not prevent
    the rest of Esan ERP from starting.
    """

    try:

        module = __import__(
            module_path,
            fromlist=[function_name],
        )

        function = getattr(
            module,
            function_name,
            None,
        )

        if function is None:

            error = (
                f"{module_path}: "
                f"function '{function_name}' "
                f"not found"
            )

            module_errors.append(error)

            logger.warning(error)

            return None

        return function

    except Exception as exc:

        error = (
            f"{module_path}: "
            f"{type(exc).__name__}: {exc}"
        )

        module_errors.append(error)

        logger.exception(
            "Module import failed: %s",
            error,
        )

        return None


# ============================================================
# ADMIN CREATION
# ============================================================

try:

    from services.user_service import create_admin

except Exception as exc:

    logger.warning(
        "Could not import services.user_service: %s",
        exc,
    )

    create_admin = None


def create_fallback_admin(db):
    """
    Create the default administrator without assuming
    optional User model fields.

    This prevents errors such as:
        TypeError: 'full_name' is an invalid keyword argument
    """

    try:

        existing_admin = (
            db.query(User)
            .filter(User.username == "admin")
            .first()
        )

        if existing_admin:

            return existing_admin

        from auth import hash_password

        # Build only fields that actually exist
        # in the current User model.
        user_columns = set(
            User.__table__.columns.keys()
        )

        admin_data = {
            "username": "admin",
            "password_hash": hash_password("admin123"),
            "role": "Administrator",
        }

        optional_values = {
            "full_name": "System Administrator",
            "email": "admin@nileharvest.com",
            "active": True,
        }

        for field, value in optional_values.items():

            if field in user_columns:
                admin_data[field] = value

        admin = User(**admin_data)

        db.add(admin)
        db.commit()

        logger.info(
            "Default administrator created."
        )

        return admin

    except Exception:

        db.rollback()

        logger.exception(
            "Fallback administrator creation failed."
        )

        raise


# ============================================================
# OPTIONAL SEED DATA
# ============================================================

try:

    from seed.seed_data import load_seed_data

except Exception as exc:

    logger.warning(
        "Seed module unavailable: %s",
        exc,
    )

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
# Sales & Distribution
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
# ERP MODULE CONFIGURATION
# ============================================================

MODULES = {

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

@st.cache_resource
def initialize_database():
    """
    Initialize database tables and ensure that an
    administrator account exists.
    """

    try:

        inspector = inspect(engine)

        existing_tables = set(
            inspector.get_table_names()
        )

        required_tables = set(
            Base.metadata.tables.keys()
        )

        missing_tables = (
            required_tables
            - existing_tables
        )

        if missing_tables:

            logger.info(
                "Missing ERP tables detected: %s",
                ", ".join(
                    sorted(missing_tables)
                ),
            )

        # Create only missing tables.
        Base.metadata.create_all(
            bind=engine
        )

        db = SessionLocal()

        try:

            if create_admin:

                try:

                    create_admin(db)

                except TypeError as exc:

                    # Protect against an old user_service
                    # having an incompatible User model.
                    logger.warning(
                        "Repository create_admin failed "
                        "with TypeError: %s",
                        exc,
                    )

                    db.rollback()

                    create_fallback_admin(db)

            else:

                create_fallback_admin(db)

        finally:

            db.close()

        return True, None

    except Exception as exc:

        logger.exception(
            "Database initialization failed."
        )

        return False, str(exc)


# ============================================================
# START DATABASE
# ============================================================

db_ok, db_error = initialize_database()


if not db_ok:

    st.error(
        "❌ Esan ERP could not initialize the database."
    )

    with st.expander(
        "Technical details"
    ):

        st.code(
            db_error or "Unknown database error"
        )

    st.stop()


# ============================================================
# SEED DATA
# ============================================================

if (
    load_seed_data
    and not st.session_state.seed_loaded
):

    try:

        load_seed_data()

        st.session_state.seed_loaded = True

        logger.info(
            "Seed data loaded successfully."
        )

    except Exception as exc:

        # Do not stop the ERP if seed data fails.
        st.session_state.seed_loaded = True

        logger.warning(
            "Seed data failed: %s",
            exc,
        )


# ============================================================
# AUTHENTICATION
# ============================================================

def login(
    username: str,
    password: str,
) -> bool:
    """
    Authenticate an ERP user.
    """

    if not username or not password:
        return False

    db = SessionLocal()

    try:

        user = (
            db.query(User)
            .filter(
                User.username == username
            )
            .first()
        )

        if not user:
            return False

        if not verify_password(
            password,
            user.password_hash,
        ):
            return False

        # Respect active status when present.
        if hasattr(user, "active"):

            if user.active is False:
                return False

        st.session_state.logged_in = True

        st.session_state.username = (
            user.username
        )

        st.session_state.full_name = (
            getattr(
                user,
                "full_name",
                None,
            )
            or user.username
        )

        st.session_state.role = (
            getattr(
                user,
                "role",
                None,
            )
            or "user"
        )

        logger.info(
            "User '%s' logged in.",
            username,
        )

        return True

    except Exception as exc:

        logger.exception(
            "Login error: %s",
            exc,
        )

        return False

    finally:

        db.close()


# ============================================================
# LOGOUT
# ============================================================

def logout():

    logger.info(
        "User '%s' logged out.",
        st.session_state.username,
    )

    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.full_name = None
    st.session_state.role = None

    st.session_state.current_page = (
        "🏠 Overview"
    )

    st.session_state.current_subpage = (
        "Dashboard"
    )

    st.rerun()


# ============================================================
# LOGIN SCREEN
# ============================================================

if not st.session_state.logged_in:

    st.markdown(
        """
        <div class="esan-login-card">

            <div class="esan-login-logo">
                🌾
            </div>

            <div class="esan-login-title">
                Esan ERP
            </div>

            <div class="esan-login-company">
                Nile Harvest Foods Ltd.
            </div>

            <div class="esan-login-description">
                Enterprise Milling & Packaging
                Management System
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    left, center, right = st.columns(
        [1, 1.4, 1]
    )

    with center:

        st.markdown(
            "### 🔐 Sign in"
        )

        username = st.text_input(
            "Username",
            placeholder="Enter username",
            key="login_username",
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter password",
            key="login_password",
        )

        if st.button(
            "Login",
            type="primary",
            use_container_width=True,
            key="login_button",
        ):

            if login(
                username.strip(),
                password,
            ):

                st.success(
                    "Login successful."
                )

                st.rerun()

            else:

                st.error(
                    "Invalid username or password."
                )

        st.caption(
            "Default administrator: "
            "admin / admin123"
        )

    st.stop()


# ============================================================
# NAVIGATION
# ============================================================

def navigate(page: str):

    if page not in MODULES:

        logger.warning(
            "Unknown navigation page: %s",
            page,
        )

        return

    st.session_state.current_page = page

    st.session_state.current_subpage = (
        "Dashboard"
    )


def navigate_subpage(subpage: str):

    st.session_state.current_subpage = (
        subpage
    )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    # --------------------------------------------------------
    # BRAND
    # --------------------------------------------------------

    company_safe = html.escape(
        str(COMPANY_NAME)
    )

    version_safe = html.escape(
        str(VERSION)
    )

    st.markdown(
        f"""
        <div class="esan-brand">

            <div class="esan-logo">
                🌾
            </div>

            <div class="esan-title">
                Esan ERP
            </div>

            <div class="esan-company">
                {company_safe}
            </div>

            <div class="esan-version">
                Version {version_safe}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


    # --------------------------------------------------------
    # MAIN
    # --------------------------------------------------------

    st.markdown(
        '<div class="nav-section">Main</div>',
        unsafe_allow_html=True,
    )

    overview_page = "🏠 Overview"

    if (
        st.session_state.current_page
        == overview_page
    ):

        st.markdown(
            '<div class="esan-active-module">'
            '🏠 &nbsp; Overview'
            '</div>',
            unsafe_allow_html=True,
        )

    else:

        if st.button(
            "🏠  Overview",
            key="sidebar_overview",
            use_container_width=True,
        ):

            navigate(overview_page)
            st.rerun()


    # --------------------------------------------------------
    # OPERATIONS
    # --------------------------------------------------------

    st.markdown(
        '<div class="nav-section">Operations</div>',
        unsafe_allow_html=True,
    )

    operation_pages = [
        (
            "🌾 Procurement",
            "sidebar_procurement",
        ),
        (
            "📦 Warehouse",
            "sidebar_warehouse",
        ),
        (
            "🏭 Milling",
            "sidebar_milling",
        ),
        (
            "📦 Packaging",
            "sidebar_packaging",
        ),
    ]

    for page, key in operation_pages:

        if (
            st.session_state.current_page
            == page
        ):

            st.markdown(
                f'<div class="esan-active-module">'
                f'{html.escape(page)}'
                f'</div>',
                unsafe_allow_html=True,
            )

        else:

            if st.button(
                page,
                key=key,
                use_container_width=True,
            ):

                navigate(page)
                st.rerun()


    # --------------------------------------------------------
    # COMMERCIAL
    # --------------------------------------------------------

    st.markdown(
        '<div class="nav-section">Commercial</div>',
        unsafe_allow_html=True,
    )

    sales_page = "🚚 Sales & Distribution"

    if (
        st.session_state.current_page
        == sales_page
    ):

        st.markdown(
            '<div class="esan-active-module">'
            '🚚 &nbsp; Sales & Distribution'
            '</div>',
            unsafe_allow_html=True,
        )

    else:

        if st.button(
            sales_page,
            key="sidebar_sales",
            use_container_width=True,
        ):

            navigate(sales_page)
            st.rerun()


    # --------------------------------------------------------
    # FINANCE
    # --------------------------------------------------------

    st.markdown(
        '<div class="nav-section">Finance</div>',
        unsafe_allow_html=True,
    )

    finance_page = "💰 Finance"

    if (
        st.session_state.current_page
        == finance_page
    ):

        st.markdown(
            '<div class="esan-active-module">'
            '💰 &nbsp; Finance'
            '</div>',
            unsafe_allow_html=True,
        )

    else:

        if st.button(
            finance_page,
            key="sidebar_finance",
            use_container_width=True,
        ):

            navigate(finance_page)
            st.rerun()


    # --------------------------------------------------------
    # REPORTING
    # --------------------------------------------------------

    st.markdown(
        '<div class="nav-section">Reporting</div>',
        unsafe_allow_html=True,
    )

    reports_page = "📊 Reports"

    if (
        st.session_state.current_page
        == reports_page
    ):

        st.markdown(
            '<div class="esan-active-module">'
            '📊 &nbsp; Reports'
            '</div>',
            unsafe_allow_html=True,
        )

    else:

        if st.button(
            reports_page,
            key="sidebar_reports",
            use_container_width=True,
        ):

            navigate(reports_page)
            st.rerun()


    # --------------------------------------------------------
    # ADMINISTRATION
    # --------------------------------------------------------

    if (
        str(
            st.session_state.role
        ).lower()
        == "administrator"
    ):

        st.markdown(
            '<div class="nav-section">'
            'Administration'
            '</div>',
            unsafe_allow_html=True,
        )

        st.caption(
            "🔐 Administrator access"
        )


    # --------------------------------------------------------
    # USER PANEL
    # --------------------------------------------------------

    user_name = html.escape(
        str(
            st.session_state.full_name
            or st.session_state.username
            or "User"
        )
    )

    user_role = html.escape(
        str(
            st.session_state.role
            or "user"
        )
    )

    st.markdown(
        f"""
        <div class="esan-user">

            <div class="esan-user-name">
                👤 {user_name}
            </div>

            <div class="esan-user-role">
                {user_role}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    if st.button(
        "🚪  Logout",
        key="sidebar_logout",
        use_container_width=True,
    ):

        logout()


# ============================================================
# CURRENT MODULE
# ============================================================

current_page = (
    st.session_state.current_page
)

current_module = MODULES.get(
    current_page
)


# ============================================================
# ERP HEADER
# ============================================================

if current_module:

    module_title = html.escape(
        str(
            current_module["title"]
        )
    )

    st.markdown(
        f"""
        <div class="esan-header">

            <div>

                <div class="esan-header-title">
                    🌾 Esan ERP
                </div>

                <div class="esan-header-subtitle">
                    {company_safe}
                    &nbsp;|&nbsp;
                    Enterprise Milling & Packaging
                    Management System
                </div>

            </div>

            <div class="esan-header-module">
                {module_title}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# MODULE TITLE
# ============================================================

if current_module:

    module_title = html.escape(
        str(
            current_module["title"]
        )
    )

    st.markdown(
        f"""
        <div class="module-title">
            {module_title}
        </div>

        <div class="module-subtitle">
            {module_title} module
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# SUB-NAVIGATION
# ============================================================

children = None

if current_module:

    children = (
        current_module.get(
            "children"
        )
    )


if children:

    subpages = list(
        children.keys()
    )

    current_subpage = (
        st.session_state.current_subpage
    )

    if (
        current_subpage
        not in subpages
    ):

        current_subpage = (
            subpages[0]
        )

        st.session_state.current_subpage = (
            current_subpage
        )


    st.markdown(
        '<div class="esan-subnav">',
        unsafe_allow_html=True,
    )

    columns = st.columns(
        len(subpages)
    )

    for index, subpage in enumerate(
        subpages
    ):

        with columns[index]:

            is_active = (
                st.session_state.current_subpage
                == subpage
            )

            button_label = (
                f"✓ {subpage}"
                if is_active
                else subpage
            )

            if st.button(
                button_label,
                key=(
                    "subpage_"
                    f"{current_page}_"
                    f"{subpage}"
                ),
                use_container_width=True,
                type=(
                    "primary"
                    if is_active
                    else "secondary"
                ),
            ):

                navigate_subpage(
                    subpage
                )

                st.rerun()

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )


# ============================================================
# MODULE RENDERER
# ============================================================

def render_module(
    function: Optional[Callable],
    name: str,
):
    """
    Render an ERP module safely.

    A failure inside one module is contained so
    the main ERP shell remains available.
    """

    if function is None:

        st.warning(
            f"⚠️ {name} is not available."
        )

        return

    try:

        function()

    except Exception as exc:

        logger.exception(
            "Error rendering module '%s': %s",
            name,
            exc,
        )

        st.error(
            f"⚠️ {name} encountered an error."
        )

        with st.expander(
            "Technical details"
        ):

            st.code(
                f"{type(exc).__name__}: {exc}"
            )


# ============================================================
# ERP ROUTER
# ============================================================

if current_module is None:

    st.error(
        f"Module '{current_page}' "
        "was not found."
    )

    if st.button(
        "Return to Overview",
        key="return_overview",
    ):

        navigate("🏠 Overview")
        st.rerun()

else:

    if children:

        selected_subpage = (
            st.session_state.current_subpage
        )

        selected_function = (
            children.get(
                selected_subpage
            )
        )

        render_module(
            selected_function,
            (
                f"{current_module['title']} / "
                f"{selected_subpage}"
            ),
        )

    else:

        render_module(
            current_module["function"],
            current_module["title"],
        )


# ============================================================
# MODULE DIAGNOSTICS
# ============================================================

if module_errors:

    with st.expander(
        "⚠️ Module Loading Information"
    ):

        st.caption(
            "Some optional modules could not be "
            "loaded. The rest of the ERP remains "
            "available."
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

        © {company_safe}
        &nbsp;|&nbsp;
        Esan ERP Enterprise Platform
        &nbsp;|&nbsp;
        Version {version_safe}

    </div>
    """,
    unsafe_allow_html=True,
)