"""
Esan ERP Controller
Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Version 1.4.0 Alpha
"""

import logging
from typing import Callable, Optional

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
# GLOBAL UI
# ============================================================

st.markdown(
    """
    <style>

    /* -------------------------------------------------------
       STREAMLIT CLEANUP
    ------------------------------------------------------- */

    #MainMenu {
        display: none;
    }

    header {
        display: none;
    }

    footer {
        display: none;
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1600px;
    }


    /* -------------------------------------------------------
       SIDEBAR
    ------------------------------------------------------- */

    section[data-testid="stSidebar"] {
        background: #f8faf9;
        border-right: 1px solid #dfe5e1;
    }


    /* -------------------------------------------------------
       SIDEBAR BRAND
    ------------------------------------------------------- */

    .esan-brand {
        text-align: center;
        padding: 12px 5px 18px 5px;
    }

    .esan-logo {
        font-size: 3rem;
        line-height: 1;
        margin-bottom: 8px;
    }

    .esan-title {
        font-size: 1.35rem;
        font-weight: 750;
        color: #263238;
    }

    .esan-company {
        font-size: 0.72rem;
        color: #718096;
        margin-top: 4px;
    }

    .esan-version {
        display: inline-block;
        margin-top: 8px;
        padding: 4px 10px;
        border-radius: 20px;
        background: #e8f5e9;
        color: #2e7d32;
        font-size: 0.65rem;
        font-weight: 700;
    }


    /* -------------------------------------------------------
       SIDEBAR NAVIGATION
    ------------------------------------------------------- */

    .nav-section {
        margin: 17px 5px 7px 5px;
        color: #7b817d;
        font-size: 0.67rem;
        font-weight: 750;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

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
    }

    section[data-testid="stSidebar"] .stButton > button:hover {
        background: #e8f5e9;
        border-color: #c8e6c9;
        color: #1b5e20;
    }

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


    /* -------------------------------------------------------
       USER PANEL
    ------------------------------------------------------- */

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


    /* -------------------------------------------------------
       LOGIN WINDOW
    ------------------------------------------------------- */

    .esan-login-container {
        max-width: 520px;
        margin: 55px auto 20px auto;
        text-align: center;
    }

    .esan-login-logo {
        font-size: 5rem;
        line-height: 1;
        margin-bottom: 10px;
    }

    .esan-login-title {
        font-size: 2.4rem;
        font-weight: 800;
        color: #263238;
        margin-bottom: 5px;
    }

    .esan-login-company {
        font-size: 1rem;
        font-weight: 600;
        color: #4a5568;
    }

    .esan-login-description {
        font-size: 0.85rem;
        color: #718096;
        margin-top: 7px;
        line-height: 1.5;
    }

    .esan-login-badge {
        display: inline-block;
        margin-top: 12px;
        padding: 5px 12px;
        border-radius: 20px;
        background: #e8f5e9;
        color: #2e7d32;
        font-size: 0.7rem;
        font-weight: 700;
    }


    /* -------------------------------------------------------
       MAIN HEADER
    ------------------------------------------------------- */

    .esan-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: white;
        border: 1px solid #e3e8e5;
        border-radius: 14px;
        padding: 15px 20px;
        margin-bottom: 18px;
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
    }


    /* -------------------------------------------------------
       MODULE TITLE
    ------------------------------------------------------- */

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


    /* -------------------------------------------------------
       FOOTER
    ------------------------------------------------------- */

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
                f"function '{function_name}' not found"
            )

            module_errors.append(error)
            logger.warning(error)

            return None

        return function

    except Exception as exc:

        error = f"{module_path}: {exc}"

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

except ImportError:

    def create_admin(db):

        admin = (
            db.query(User)
            .filter(User.username == "admin")
            .first()
        )

        if admin:
            return

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

        logger.info(
            "Default administrator created."
        )


# ============================================================
# OPTIONAL SEED DATA
# ============================================================

try:
    from seed.seed_data import load_seed_data
except ImportError:
    load_seed_data = None


# ============================================================
# MODULE REGISTRY
# ============================================================

dashboard_home = safe_import(
    "modules.dashboard.home",
    "dashboard_home",
)

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

warehouse_dashboard = safe_import(
    "modules.warehouse.dashboard",
    "warehouse_dashboard",
)

warehouse_inventory = safe_import(
    "modules.warehouse.inventory",
    "inventory_page",
)

milling_dashboard = safe_import(
    "modules.milling.dashboard",
    "milling_dashboard",
)

packaging_dashboard = safe_import(
    "modules.packaging.dashboard",
    "packaging_dashboard",
)

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

finance_dashboard = safe_import(
    "modules.finance.dashboard",
    "finance_dashboard",
)

reports_dashboard = safe_import(
    "modules.reports.dashboard",
    "reports_dashboard",
)


# ============================================================
# MODULE DEFINITIONS
# ============================================================

MODULES = {

    "🏠 Overview": {
        "title": "Overview",
        "function": dashboard_home,
        "children": None,
    },

    "🌾 Procurement": {
        "title": "Procurement",
        "function": procurement_dashboard,
        "children": {
            "Dashboard": procurement_dashboard,
            "Suppliers": procurement_suppliers,
            "Purchase Orders": procurement_purchases,
        },
    },

    "📦 Warehouse": {
        "title": "Warehouse",
        "function": warehouse_dashboard,
        "children": {
            "Dashboard": warehouse_dashboard,
            "Inventory": warehouse_inventory,
        },
    },

    "🏭 Milling": {
        "title": "Milling",
        "function": milling_dashboard,
        "children": None,
    },

    "📦 Packaging": {
        "title": "Packaging",
        "function": packaging_dashboard,
        "children": None,
    },

    "🚚 Sales & Distribution": {
        "title": "Sales & Distribution",
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
        "function": finance_dashboard,
        "children": None,
    },

    "📊 Reports": {
        "title": "Reports",
        "function": reports_dashboard,
        "children": None,
    },
}


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

@st.cache_resource
def initialize_database():

    try:

        inspect(engine)

        Base.metadata.create_all(
            bind=engine
        )

        db = SessionLocal()

        try:
            create_admin(db)

        finally:
            db.close()

        return True, None

    except Exception as exc:

        logger.exception(
            "Database initialization failed"
        )

        return False, str(exc)


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
# LOGIN FUNCTION
# ============================================================

def login(
    username: str,
    password: str,
) -> bool:

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

        # Check active status if available
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
            user.role or "User"
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
# LOGIN SCREEN
# ============================================================

if not st.session_state.logged_in:

    # --------------------------------------------------------
    # LOGIN BRANDING
    #
    # IMPORTANT:
    # The entire HTML must be inside st.markdown().
    # Do not place <div> elements directly in Python.
    # --------------------------------------------------------

    st.markdown(
        """
        <div class="esan-login-container">

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
                Enterprise Milling &amp; Packaging
                Management System
            </div>

            <div class="esan-login-badge">
                ERP VERSION 1.4.0 ALPHA
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


    # --------------------------------------------------------
    # LOGIN FORM
    # --------------------------------------------------------

    left, center, right = st.columns(
        [1, 1.5, 1]
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

        login_clicked = st.button(
            "Login",
            type="primary",
            use_container_width=True,
            key="login_button",
        )

        if login_clicked:

            username_value = (
                username.strip()
            )

            if not username_value:

                st.error(
                    "Please enter your username."
                )

            elif not password:

                st.error(
                    "Please enter your password."
                )

            elif login(
                username_value,
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

        st.info(
            "Default administrator: "
            "admin / admin123"
        )

    st.stop()


# ============================================================
# NAVIGATION FUNCTIONS
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


def navigate_subpage(
    subpage: str
):

    st.session_state.current_subpage = (
        subpage
    )


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
# SIDEBAR
# ============================================================

with st.sidebar:

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
                {COMPANY_NAME}
            </div>

            <div class="esan-version">
                Version {VERSION}
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

    if st.session_state.current_page == "🏠 Overview":

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

            navigate("🏠 Overview")
            st.rerun()


    # --------------------------------------------------------
    # OPERATIONS
    # --------------------------------------------------------

    st.markdown(
        '<div class="nav-section">Operations</div>',
        unsafe_allow_html=True,
    )

    operation_pages = [
        ("🌾 Procurement", "sidebar_procurement"),
        ("📦 Warehouse", "sidebar_warehouse"),
        ("🏭 Milling", "sidebar_milling"),
        ("📦 Packaging", "sidebar_packaging"),
    ]

    for page, key in operation_pages:

        if st.session_state.current_page == page:

            st.markdown(
                f'<div class="esan-active-module">'
                f'{page}'
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

    page = "🚚 Sales & Distribution"

    if st.session_state.current_page == page:

        st.markdown(
            '<div class="esan-active-module">'
            '🚚 &nbsp; Sales & Distribution'
            '</div>',
            unsafe_allow_html=True,
        )

    else:

        if st.button(
            page,
            key="sidebar_sales",
            use_container_width=True,
        ):

            navigate(page)
            st.rerun()


    # --------------------------------------------------------
    # FINANCE
    # --------------------------------------------------------

    st.markdown(
        '<div class="nav-section">Finance</div>',
        unsafe_allow_html=True,
    )

    page = "💰 Finance"

    if st.session_state.current_page == page:

        st.markdown(
            '<div class="esan-active-module">'
            '💰 &nbsp; Finance'
            '</div>',
            unsafe_allow_html=True,
        )

    else:

        if st.button(
            page,
            key="sidebar_finance",
            use_container_width=True,
        ):

            navigate(page)
            st.rerun()


    # --------------------------------------------------------
    # REPORTING
    # --------------------------------------------------------

    st.markdown(
        '<div class="nav-section">Reporting</div>',
        unsafe_allow_html=True,
    )

    page = "📊 Reports"

    if st.session_state.current_page == page:

        st.markdown(
            '<div class="esan-active-module">'
            '📊 &nbsp; Reports'
            '</div>',
            unsafe_allow_html=True,
        )

    else:

        if st.button(
            page,
            key="sidebar_reports",
            use_container_width=True,
        ):

            navigate(page)
            st.rerun()


    # --------------------------------------------------------
    # USER
    # --------------------------------------------------------

    st.markdown(
        f"""
        <div class="esan-user">

            <div class="esan-user-name">
                👤 {st.session_state.full_name}
            </div>

            <div class="esan-user-role">
                {st.session_state.role}
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
                    Enterprise Milling &amp; Packaging
                    Management System
                </div>

            </div>

            <div class="esan-header-module">
                {current_module["title"]}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# MODULE TITLE
# ============================================================

if current_module:

    st.markdown(
        f"""
        <div class="module-title">
            {current_module["title"]}
        </div>

        <div class="module-subtitle">
            {current_module["title"]} module
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# SUB-NAVIGATION
# ============================================================

children = None

if current_module:

    children = current_module.get(
        "children"
    )


if children:

    subpages = list(
        children.keys()
    )

    current_subpage = (
        st.session_state.current_subpage
    )

    if current_subpage not in subpages:

        current_subpage = subpages[0]

        st.session_state.current_subpage = (
            current_subpage
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

            if st.button(
                f"✓ {subpage}"
                if is_active
                else subpage,
                key=(
                    f"subpage_"
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


# ============================================================
# MODULE RENDERER
# ============================================================

def render_module(
    function: Optional[Callable],
    name: str,
):

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
                str(exc)
            )


# ============================================================
# ERP ROUTER
# ============================================================

if current_module is None:

    st.error(
        f"Module '{current_page}' "
        "was not found."
    )

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

# Only display this section when there are REAL import
# problems. It will NOT appear simply because a module is
# optional or because the application loaded successfully.

if module_errors:

    with st.expander(
        "⚠️ Module Loading Information"
    ):

        st.caption(
            "The following modules could not be loaded. "
            "Other ERP modules remain available."
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

        © {COMPANY_NAME}
        &nbsp;|&nbsp;
        Esan ERP Enterprise Platform
        &nbsp;|&nbsp;
        Version {VERSION}

    </div>
    """,
    unsafe_allow_html=True,
)