"""
Esan ERP Controller
Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Version 1.4.0 Alpha – Full Repository Integration

Architecture
------------
streamlit_app.py
    ├── Authentication
    ├── Database initialization
    ├── Login window
    ├── ERP sidebar navigation
    ├── Module router
    └── Module error isolation

The pages/ directory is NOT required.
"""

# ============================================================
# STANDARD LIBRARY
# ============================================================

import logging


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


    /* ======================================================
       LOGIN WINDOW
       ====================================================== */

    .esan-login-card {
        text-align: center;
        padding-top: 55px;
        padding-bottom: 25px;
    }

    .esan-login-logo {
        font-size: 4.8rem;
        line-height: 1;
        margin-bottom: 12px;
    }

    .esan-login-title {
        font-size: 2.5rem;
        font-weight: 800;
        color: #263238;
        line-height: 1.1;
    }

    .esan-login-company {
        font-size: 1rem;
        font-weight: 600;
        color: #4a5568;
        margin-top: 8px;
    }

    .esan-login-description {
        font-size: 0.85rem;
        color: #718096;
        margin-top: 7px;
    }

    .esan-login-box {
        background: white;
        border: 1px solid #e2e8e4;
        border-radius: 16px;
        padding: 25px;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.06);
        margin-top: 10px;
    }


    /* ======================================================
       SIDEBAR
       ====================================================== */

    div[data-testid="stSidebar"] {
        border-right: 1px solid #dfe5e1;
    }

    section[data-testid="stSidebar"] > div {
        background: #f8faf9;
    }


    /* ======================================================
       SIDEBAR BRAND
       ====================================================== */

    .esan-sidebar-brand {
        text-align: center;
        padding: 10px 5px 15px 5px;
    }

    .esan-sidebar-logo {
        font-size: 2.3rem;
        line-height: 1;
    }

    .esan-sidebar-title {
        font-size: 1.35rem;
        font-weight: 800;
        color: #263238;
        margin-top: 6px;
    }

    .esan-sidebar-company {
        font-size: 0.7rem;
        color: #718096;
        margin-top: 3px;
    }


    /* ======================================================
       SIDEBAR SECTION LABELS
       ====================================================== */

    .nav-section {
        margin: 16px 5px 6px 5px;
        color: #7b817d;
        font-size: 0.68rem;
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
    }

    section[data-testid="stSidebar"] .stButton > button:hover {
        background: #e8f5e9;
        border-color: #c8e6c9;
        color: #1b5e20;
    }


    /* ======================================================
       USER PANEL
       ====================================================== */

    .esan-user-panel {
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
       MAIN HEADER
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
# SESSION MANAGEMENT
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
# SAFE IMPORT SYSTEM
# ============================================================

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

            error = (
                f"{module_path}: "
                f"missing function '{function_name}'"
            )

            module_errors.append(error)

            logger.warning(error)

            return None

        return function

    except Exception as exc:

        error = f"{module_path}: {exc}"

        module_errors.append(error)

        logger.error(error)

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
            .filter(
                User.username == "admin"
            )
            .first()
        )

        if admin:
            return

        from auth import hash_password

        # Build the administrator using fields
        # available in the current User model.

        admin_data = {
            "username": "admin",
            "password_hash": hash_password(
                "admin123"
            ),
            "role": "Administrator",
        }

        # Optional model fields

        if hasattr(User, "full_name"):
            admin_data["full_name"] = (
                "System Administrator"
            )

        if hasattr(User, "email"):
            admin_data["email"] = (
                "admin@nileharvest.com"
            )

        if hasattr(User, "active"):
            admin_data["active"] = True

        admin = User(**admin_data)

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
# DATABASE INITIALIZATION
# ============================================================

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
                "Creating missing tables: %s",
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

        return True

    except Exception as exc:

        logger.exception(
            "Database initialization failed"
        )

        st.error(
            "❌ Database initialization failed."
        )

        with st.expander(
            "Technical details"
        ):

            st.code(
                str(exc)
            )

        return False


# Run database initialization

database_ready = initialize_database()

if not database_ready:
    st.stop()


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

        if not user:
            return False

        if not verify_password(
            password,
            user.password_hash,
        ):
            return False

        # Respect active status if available

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
# LOGIN SCREEN
# ============================================================

if not st.session_state.logged_in:

    # --------------------------------------------------------
    # BRANDING
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # LOGIN FORM
    # --------------------------------------------------------

    left, center, right = st.columns(
        [1, 1.4, 1]
    )

    with center:

        st.markdown(
            '<div class="esan-login-box">',
            unsafe_allow_html=True,
        )

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
            "🔐 Login",
            use_container_width=True,
            type="primary",
            key="login_button",
        ):

            clean_username = username.strip()

            if not clean_username:

                st.warning(
                    "Please enter your username."
                )

            elif not password:

                st.warning(
                    "Please enter your password."
                )

            elif login(
                clean_username,
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

        st.markdown(
            """
            <div style="
                text-align:center;
                margin-top:15px;
                color:#718096;
                font-size:0.75rem;
            ">
                Default administrator:
                <strong>admin / admin123</strong>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

    st.stop()


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

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()


    # --------------------------------------------------------
    # NAVIGATION HELPER
    # --------------------------------------------------------

    def nav_button(label):

        if st.button(
            label,
            use_container_width=True,
        ):

            st.session_state.current_page = (
                label
            )

            st.session_state.current_subpage = (
                "Dashboard"
            )

            st.rerun()


    # --------------------------------------------------------
    # MAIN
    # --------------------------------------------------------

    st.markdown(
        "**MAIN**"
    )

    nav_button(
        "🏠 Overview"
    )


    # --------------------------------------------------------
    # OPERATIONS
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # COMMERCIAL
    # --------------------------------------------------------

    st.markdown(
        "**COMMERCIAL**"
    )

    nav_button(
        "🚚 Sales & Distribution"
    )


    # --------------------------------------------------------
    # FINANCE
    # --------------------------------------------------------

    st.markdown(
        "**FINANCE**"
    )

    nav_button(
        "💰 Finance"
    )


    # --------------------------------------------------------
    # REPORTING
    # --------------------------------------------------------

    st.markdown(
        "**REPORTING**"
    )

    nav_button(
        "📊 Reports"
    )


    # --------------------------------------------------------
    # USER PANEL
    # --------------------------------------------------------

    st.divider()

    st.markdown(
        f"""
        <div class="esan-user-panel">

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
        "🚪 Logout",
        use_container_width=True,
        key="logout_button",
    ):

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
# CURRENT PAGE
# ============================================================

menu = st.session_state.current_page


# ============================================================
# ERP HEADER
# ============================================================

page_titles = {
    "🏠 Overview": "Overview",
    "🌾 Procurement": "Procurement",
    "📦 Warehouse": "Warehouse",
    "🏭 Milling": "Milling",
    "📦 Packaging": "Packaging",
    "🚚 Sales & Distribution": "Sales & Distribution",
    "💰 Finance": "Finance",
    "📊 Reports": "Reports",
}

current_title = page_titles.get(
    menu,
    "Overview"
)

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
            {current_title}
        </div>

    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# ERP ROUTER
# ============================================================

if menu == "🏠 Overview":

    if dashboard_home:
        dashboard_home()
    else:
        st.info(
            "Overview dashboard not available."
        )


# ============================================================
# PROCUREMENT
# ============================================================

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
        ],
        horizontal=True,
        key="procurement_menu",
    )

    if procurement_menu == "Dashboard":

        if procurement_dashboard:
            procurement_dashboard()
        else:
            st.warning(
                "Procurement dashboard unavailable."
            )

    elif procurement_menu == "Suppliers":

        if procurement_suppliers:
            procurement_suppliers()
        else:
            st.warning(
                "Suppliers page unavailable."
            )

    elif procurement_menu == "Purchase Orders":

        if procurement_purchases:
            procurement_purchases()
        else:
            st.warning(
                "Purchase orders page unavailable."
            )


# ============================================================
# WAREHOUSE
# ============================================================

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
        key="warehouse_menu",
    )

    if warehouse_menu == "Dashboard":

        if warehouse_dashboard:
            warehouse_dashboard()
        else:
            st.warning(
                "Warehouse dashboard unavailable."
            )

    elif warehouse_menu == "Inventory":

        if warehouse_inventory:
            warehouse_inventory()
        else:
            st.warning(
                "Inventory page unavailable."
            )


# ============================================================
# MILLING
# ============================================================

elif menu == "🏭 Milling":

    if milling_dashboard:
        milling_dashboard()
    else:
        st.warning(
            "Milling module unavailable."
        )


# ============================================================
# PACKAGING
# ============================================================

elif menu == "📦 Packaging":

    if packaging_dashboard:
        packaging_dashboard()
    else:
        st.warning(
            "Packaging module unavailable."
        )


# ============================================================
# SALES & DISTRIBUTION
# ============================================================

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
        key="sales_menu",
    )

    sales_pages = {
        "Dashboard": sales_dashboard,
        "Customers": sales_customers,
        "Quotations": sales_quotations,
        "Sales Orders": sales_orders,
        "Deliveries": sales_deliveries,
        "Invoices": sales_invoices,
        "Payments": sales_payments,
    }

    page_func = sales_pages.get(
        sales_menu
    )

    if page_func:

        try:
            page_func()

        except Exception as exc:

            logger.exception(
                "Sales module error: %s",
                exc,
            )

            st.error(
                "An error occurred while loading "
                f"{sales_menu}."
            )

            with st.expander(
                "Technical details"
            ):

                st.code(
                    str(exc)
                )

    else:

        st.warning(
            f"{sales_menu} page unavailable."
        )


# ============================================================
# FINANCE
# ============================================================

elif menu == "💰 Finance":

    if finance_dashboard:
        finance_dashboard()
    else:
        st.warning(
            "Finance module unavailable."
        )


# ============================================================
# REPORTS
# ============================================================

elif menu == "📊 Reports":

    if reports_dashboard:
        reports_dashboard()
    else:
        st.warning(
            "Reports module unavailable."
        )


# ============================================================
# MODULE IMPORT WARNINGS
# ============================================================

if module_errors:

    with st.expander(
        "⚠️ Module Loading Information"
    ):

        st.caption(
            "The ERP is running, but some optional "
            "modules could not be loaded."
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
    f"Esan ERP Enterprise Platform | "
    f"Version {VERSION}"
)