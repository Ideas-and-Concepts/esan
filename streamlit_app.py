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
    ├── Sidebar navigation
    └── ERP module router

modules/
    ├── dashboard/
    ├── procurement/
    ├── warehouse/
    ├── milling/
    ├── packaging/
    ├── sales/
    ├── finance/
    └── reports/

NOTE
----
The pages/ directory is NOT required.
All application navigation is handled from this controller.
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
# ERP GLOBAL CSS
# ============================================================

st.markdown(
    """
    <style>

    /* Remove Streamlit branding */
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


    /* ================================================
       SIDEBAR
       ================================================ */

    section[data-testid="stSidebar"] {
        background: #f7faf8;
        border-right: 1px solid #dfe6e1;
    }

    section[data-testid="stSidebar"] > div {
        padding-top: 1rem;
    }

    .esan-sidebar-brand {
        text-align: center;
        padding: 5px 5px 15px 5px;
    }

    .esan-sidebar-logo {
        font-size: 2.4rem;
        line-height: 1;
    }

    .esan-sidebar-title {
        font-size: 1.35rem;
        font-weight: 750;
        color: #263238;
        margin-top: 7px;
    }

    .esan-sidebar-company {
        font-size: 0.72rem;
        color: #718096;
        margin-top: 3px;
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

    .esan-nav-section {
        margin: 18px 4px 7px 4px;
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
        border-radius: 8px;
        padding: 9px 11px;
        margin: 2px 0;
        font-size: 0.88rem;
        transition: all 0.15s ease;
    }

    section[data-testid="stSidebar"] .stButton > button:hover {
        background: #e8f5e9;
        border-color: #c8e6c9;
        color: #1b5e20;
    }

    .esan-user-card {
        background: white;
        border: 1px solid #e2e8e4;
        border-radius: 10px;
        padding: 11px;
        margin-top: 15px;
    }

    .esan-user-name {
        font-size: 0.86rem;
        font-weight: 700;
        color: #263238;
    }

    .esan-user-role {
        font-size: 0.70rem;
        color: #718096;
        margin-top: 3px;
    }


    /* ================================================
       MAIN HEADER
       ================================================ */

    .esan-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: white;
        border: 1px solid #e3e8e5;
        border-radius: 14px;
        padding: 15px 20px;
        margin-bottom: 18px;
        box-shadow: 0 3px 14px rgba(0,0,0,0.035);
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


    /* ================================================
       SUB NAVIGATION
       ================================================ */

    .esan-subnav-title {
        color: #718096;
        font-size: 0.70rem;
        font-weight: 700;
        margin: 5px 0 7px 0;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }


    /* ================================================
       FOOTER
       ================================================ */

    .esan-footer {
        text-align: center;
        color: #9ca3af;
        font-size: 0.70rem;
        margin-top: 35px;
        padding-bottom: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


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
# SAFE IMPORT
# ============================================================

module_errors = []


def safe_import(module_path, function_name):

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

            message = (
                f"{module_path}: "
                f"missing function "
                f"'{function_name}'"
            )

            module_errors.append(message)

            logger.warning(message)

            return None

        return function

    except Exception as exc:

        message = (
            f"{module_path}: {exc}"
        )

        module_errors.append(message)

        logger.exception(
            "Module import failed: %s",
            message,
        )

        return None


# ============================================================
# MODULE IMPORTS
# ============================================================

# ---------------- Dashboard ----------------

dashboard_home = safe_import(
    "modules.dashboard.home",
    "dashboard_home",
)


# ---------------- Procurement ----------------

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


# ---------------- Warehouse ----------------

warehouse_dashboard = safe_import(
    "modules.warehouse.dashboard",
    "warehouse_dashboard",
)


# ---------------- Milling ----------------

milling_dashboard = safe_import(
    "modules.milling.dashboard",
    "milling_dashboard",
)


# ---------------- Packaging ----------------

packaging_dashboard = safe_import(
    "modules.packaging.dashboard",
    "packaging_dashboard",
)


# ---------------- Sales ----------------

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

sales_dispatch = safe_import(
    "modules.sales.dispatch",
    "dispatch_page",
)

sales_delivery = safe_import(
    "modules.sales.delivery",
    "delivery_page",
)

sales_payments = safe_import(
    "modules.sales.payments",
    "payments_page",
)


# ---------------- Finance ----------------

finance_dashboard = safe_import(
    "modules.finance.dashboard",
    "finance_dashboard",
)


# ---------------- Reports ----------------

reports_dashboard = safe_import(
    "modules.reports.dashboard",
    "reports_dashboard",
)


# ============================================================
# ADMIN CREATION
# ============================================================

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

        if admin:
            return

        from auth import hash_password

        admin = User(
            username="admin",
            password_hash=hash_password(
                "admin123"
            ),
            role="Administrator",
            full_name="System Administrator",
            email="admin@nileharvest.com",
            active=True,
        )

        db.add(admin)
        db.commit()

        logger.info(
            "Default administrator created."
        )


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

@st.cache_resource
def initialize_database():

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
                "Creating missing ERP tables: %s",
                ", ".join(
                    sorted(missing_tables)
                ),
            )

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


database_ok, database_error = (
    initialize_database()
)


if not database_ok:

    st.error(
        "❌ Esan ERP could not initialize "
        "the database."
    )

    with st.expander(
        "Technical details"
    ):

        st.code(
            str(database_error)
        )

    st.stop()


# ============================================================
# LOGIN
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

        if not user:
            return False

        if not verify_password(
            password,
            user.password_hash,
        ):
            return False

        if hasattr(user, "active"):

            if user.active is False:
                return False

        st.session_state.logged_in = True
        st.session_state.username = (
            user.username
        )
        st.session_state.role = (
            user.role
        )
        st.session_state.current_page = (
            "🏠 Overview"
        )
        st.session_state.current_subpage = (
            "Dashboard"
        )

        logger.info(
            "User logged in: %s",
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


def logout():

    logger.info(
        "User logged out: %s",
        st.session_state.username,
    )

    st.session_state.logged_in = False
    st.session_state.username = None
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
        <div style="
            max-width:520px;
            margin:65px auto 20px auto;
            text-align:center;
        ">

            <div style="
                font-size:4rem;
                line-height:1;
            ">
                🌾
            </div>

            <h1 style="
                color:#263238;
                margin:10px 0 3px 0;
            ">
                Esan ERP
            </h1>

            <h3 style="
                color:#4a5568;
                margin:0;
            ">
                Nile Harvest Foods Ltd.
            </h3>

            <p style="
                color:#718096;
                font-size:0.9rem;
                margin-top:7px;
            ">
                Enterprise Milling & Packaging
                Management System
            </p>

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
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter password",
        )

        if st.button(
            "Login",
            type="primary",
            use_container_width=True,
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
# NAVIGATION HELPERS
# ============================================================

def set_page(page):

    st.session_state.current_page = page

    st.session_state.current_subpage = (
        "Dashboard"
    )


def set_subpage(subpage):

    st.session_state.current_subpage = (
        subpage
    )


# ============================================================
# SIDEBAR NAVIGATION
# ============================================================

with st.sidebar:

    # --------------------------------------------------------
    # BRAND
    # --------------------------------------------------------

    st.markdown(
        f"""
        <div class="esan-sidebar-brand">

            <div class="esan-sidebar-logo">
                🌾
            </div>

            <div class="esan-sidebar-title">
                Esan ERP
            </div>

            <div class="esan-sidebar-company">
                {COMPANY_NAME}
            </div>

            <div class="esan-version">
                v{VERSION}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()


    # --------------------------------------------------------
    # MAIN
    # --------------------------------------------------------

    st.markdown(
        '<div class="esan-nav-section">'
        'Main'
        '</div>',
        unsafe_allow_html=True,
    )

    if st.button(
        "🏠  Overview",
        key="sidebar_overview",
        use_container_width=True,
    ):

        set_page(
            "🏠 Overview"
        )

        st.rerun()


    # --------------------------------------------------------
    # OPERATIONS
    # --------------------------------------------------------

    st.markdown(
        '<div class="esan-nav-section">'
        'Operations'
        '</div>',
        unsafe_allow_html=True,
    )

    if st.button(
        "🌾  Procurement",
        key="sidebar_procurement",
        use_container_width=True,
    ):

        set_page(
            "🌾 Procurement"
        )

        st.rerun()


    if st.button(
        "📦  Warehouse",
        key="sidebar_warehouse",
        use_container_width=True,
    ):

        set_page(
            "📦 Warehouse"
        )

        st.rerun()


    if st.button(
        "🏭  Milling",
        key="sidebar_milling",
        use_container_width=True,
    ):

        set_page(
            "🏭 Milling"
        )

        st.rerun()


    if st.button(
        "📦  Packaging",
        key="sidebar_packaging",
        use_container_width=True,
    ):

        set_page(
            "📦 Packaging"
        )

        st.rerun()


    # --------------------------------------------------------
    # COMMERCIAL
    # --------------------------------------------------------

    st.markdown(
        '<div class="esan-nav-section">'
        'Commercial'
        '</div>',
        unsafe_allow_html=True,
    )

    if st.button(
        "🚚  Sales & Distribution",
        key="sidebar_sales",
        use_container_width=True,
    ):

        set_page(
            "🚚 Sales & Distribution"
        )

        st.rerun()


    # --------------------------------------------------------
    # FINANCE
    # --------------------------------------------------------

    st.markdown(
        '<div class="esan-nav-section">'
        'Finance'
        '</div>',
        unsafe_allow_html=True,
    )

    if st.button(
        "💰  Finance",
        key="sidebar_finance",
        use_container_width=True,
    ):

        set_page(
            "💰 Finance"
        )

        st.rerun()


    # --------------------------------------------------------
    # REPORTING
    # --------------------------------------------------------

    st.markdown(
        '<div class="esan-nav-section">'
        'Reporting'
        '</div>',
        unsafe_allow_html=True,
    )

    if st.button(
        "📊  Reports",
        key="sidebar_reports",
        use_container_width=True,
    ):

        set_page(
            "📊 Reports"
        )

        st.rerun()


    # --------------------------------------------------------
    # ADMINISTRATION
    # --------------------------------------------------------

    if (
        st.session_state.role
        == "Administrator"
    ):

        st.markdown(
            '<div class="esan-nav-section">'
            'Administration'
            '</div>',
            unsafe_allow_html=True,
        )

        st.caption(
            "🔐 Administrator"
        )


    # --------------------------------------------------------
    # USER
    # --------------------------------------------------------

    st.divider()

    st.markdown(
        f"""
        <div class="esan-user-card">

            <div class="esan-user-name">
                👤 {st.session_state.username}
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
# MODULE DEFINITIONS
# ============================================================

MODULES = {

    "🏠 Overview": {
        "title": "Overview",
        "function": dashboard_home,
        "subpages": None,
    },

    "🌾 Procurement": {
        "title": "Procurement",
        "function": procurement_dashboard,
        "subpages": {
            "Dashboard": procurement_dashboard,
            "Suppliers": procurement_suppliers,
            "Purchase Orders": procurement_purchase_orders,
        },
    },

    "📦 Warehouse": {
        "title": "Warehouse",
        "function": warehouse_dashboard,
        "subpages": {
            "Dashboard": warehouse_dashboard,
        },
    },

    "🏭 Milling": {
        "title": "Milling",
        "function": milling_dashboard,
        "subpages": None,
    },

    "📦 Packaging": {
        "title": "Packaging",
        "function": packaging_dashboard,
        "subpages": None,
    },

    "🚚 Sales & Distribution": {
        "title": "Sales & Distribution",
        "function": sales_dashboard,
        "subpages": {
            "Dashboard": sales_dashboard,
            "Customers": sales_customers,
            "Quotations": sales_quotations,
            "Sales Orders": sales_orders,
            "Dispatch": sales_dispatch,
            "Deliveries": sales_delivery,
            "Payments": sales_payments,
        },
    },

    "💰 Finance": {
        "title": "Finance",
        "function": finance_dashboard,
        "subpages": None,
    },

    "📊 Reports": {
        "title": "Reports",
        "function": reports_dashboard,
        "subpages": None,
    },
}


# ============================================================
# MAIN HEADER
# ============================================================

current_page = (
    st.session_state.current_page
)

module = MODULES.get(
    current_page
)

if module:

    module_title = module["title"]

else:

    module_title = "Overview"


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
# MODULE RENDERER
# ============================================================

def render_module(function, title):

    if function is None:

        st.info(
            f"ℹ️ {title} is not available yet."
        )

        return

    try:

        function()

    except Exception as exc:

        logger.exception(
            "Error in module: %s",
            title,
        )

        st.error(
            f"❌ Error loading {title}."
        )

        with st.expander(
            "Technical details"
        ):

            st.code(
                str(exc)
            )


# ============================================================
# ROUTER
# ============================================================

if not module:

    st.error(
        "The selected ERP module "
        "could not be found."
    )

else:

    subpages = module["subpages"]


    # --------------------------------------------------------
    # MODULE WITH SUBPAGES
    # --------------------------------------------------------

    if subpages:

        available_subpages = list(
            subpages.keys()
        )

        current_subpage = (
            st.session_state.current_subpage
        )

        if (
            current_subpage
            not in available_subpages
        ):

            current_subpage = (
                available_subpages[0]
            )

            st.session_state.current_subpage = (
                current_subpage
            )


        st.markdown(
            '<div class="esan-subnav-title">'
            'Module Navigation'
            '</div>',
            unsafe_allow_html=True,
        )


        # ----------------------------------------------------
        # SUB NAVIGATION
        # ----------------------------------------------------

        columns = st.columns(
            len(available_subpages)
        )


        for index, subpage in enumerate(
            available_subpages
        ):

            with columns[index]:

                if st.button(
                    subpage,
                    key=(
                        "subpage_"
                        + current_page
                        + "_"
                        + subpage
                    ),
                    type=(
                        "primary"
                        if subpage
                        == current_subpage
                        else "secondary"
                    ),
                    use_container_width=True,
                ):

                    set_subpage(
                        subpage
                    )

                    st.rerun()


        # ----------------------------------------------------
        # SELECTED SUBMODULE
        # ----------------------------------------------------

        selected_function = (
            subpages.get(
                current_subpage
            )
        )

        render_module(
            selected_function,
            (
                module_title
                + " / "
                + current_subpage
            ),
        )


    # --------------------------------------------------------
    # SIMPLE MODULE
    # --------------------------------------------------------

    else:

        render_module(
            module["function"],
            module_title,
        )


# ============================================================
# MODULE IMPORT DIAGNOSTICS
# ============================================================

if module_errors:

    with st.expander(
        "⚠️ Module Loading Information"
    ):

        st.caption(
            "These warnings identify modules "
            "that could not be loaded. "
            "The rest of the ERP can continue "
            "running."
        )

        for error in module_errors:

            st.write(
                "• " + error
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
