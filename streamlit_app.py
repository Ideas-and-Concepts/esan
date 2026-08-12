"""
============================================================
ESAN ERP
Nile Harvest Foods Ltd.
Enterprise Resource Planning System

Version 1.4.0 Alpha
Full Repository Integration
============================================================
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
    page_title="Esan ERP",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# ESAN ERP UI
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


    /* ======================================================
       SIDEBAR
       ====================================================== */

    div[data-testid="stSidebar"] {
        border-right: 1px solid rgba(128, 128, 128, 0.25);
    }

    div[data-testid="stSidebar"] .block-container {
        padding-top: 1rem;
    }


    /* ======================================================
       ESAN BRAND
       ====================================================== */

    .esan-login-brand {
        text-align: center;
        width: 100%;
        margin-top: 35px;
        margin-bottom: 35px;
    }

    .esan-login-brand .esan-word {
        font-size: 58px;
        font-weight: 900;
        letter-spacing: 10px;
        line-height: 1;
        color: #2e7d32;
        font-family:
            Arial,
            Helvetica,
            sans-serif;
    }

    .esan-login-brand .esan-line {
        width: 90px;
        height: 4px;
        margin: 14px auto 0 auto;
        border-radius: 10px;
        background: #d4a72c;
    }


    /* ======================================================
       SIDEBAR BRAND
       ====================================================== */

    .esan-sidebar-brand {
        text-align: center;
        width: 100%;
        padding: 8px 0 12px 0;
    }

    .esan-sidebar-brand .esan-word {
        font-size: 34px;
        font-weight: 900;
        letter-spacing: 6px;
        line-height: 1;
        color: #2e7d32;
        font-family:
            Arial,
            Helvetica,
            sans-serif;
    }

    .esan-sidebar-brand .esan-line {
        width: 55px;
        height: 3px;
        margin: 9px auto 0 auto;
        border-radius: 10px;
        background: #d4a72c;
    }


    /* ======================================================
       LOGIN FORM
       ====================================================== */

    div[data-testid="stTextInput"] label {
        font-weight: 600;
    }

    div[data-testid="stTextInput"] input {
        border-radius: 10px;
        min-height: 45px;
        padding-left: 14px;
    }


    /* ======================================================
       BUTTONS
       ====================================================== */

    div[data-testid="stButton"] > button {
        border-radius: 10px;
        min-height: 44px;
        font-weight: 700;
    }


    /* ======================================================
       SIDEBAR BUTTONS
       ====================================================== */

    div[data-testid="stSidebar"]
    div[data-testid="stButton"] > button {

        text-align: left;
        border-radius: 9px;
        margin-bottom: 3px;
    }


    /* ======================================================
       SIDEBAR SECTION LABELS
       ====================================================== */

    .sidebar-section {
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        margin-top: 16px;
        margin-bottom: 5px;
        opacity: 0.7;
    }


    /* ======================================================
       LOGIN CONTAINER
       ====================================================== */

    .login-title {
        text-align: center;
        font-size: 1.05rem;
        font-weight: 600;
        margin-bottom: 15px;
        opacity: 0.75;
    }


    /* ======================================================
       USER PANEL
       ====================================================== */

    .user-panel {
        padding: 10px;
        border-radius: 10px;
        background: rgba(128, 128, 128, 0.08);
        margin-bottom: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SAFE IMPORT SYSTEM
# ============================================================

module_errors = []


def safe_import(module_path, function_name):
    """
    Safely import a module function.

    If a module fails to load, the rest of the ERP
    continues running and the error is displayed later.
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
                f"missing function '{function_name}'"
            )

            module_errors.append(error)

            logging.error(error)

            return None

        return function

    except Exception as exc:

        error = (
            f"{module_path}: "
            f"{type(exc).__name__}: {exc}"
        )

        module_errors.append(error)

        logging.exception(
            "Failed loading module %s",
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
        Create the default administrator if one does not exist.

        This fallback attempts to work with the existing User
        model without requiring the application to crash.
        """

        try:

            admin = (
                db.query(User)
                .filter(
                    User.username == "admin"
                )
                .first()
            )

        except Exception as exc:

            logging.exception(
                "Unable to query User model: %s",
                exc,
            )

            return

        if admin:
            return

        try:

            from auth import hash_password

            admin_data = {
                "username": "admin",
                "password_hash": hash_password(
                    "admin123"
                ),
                "role": "Administrator",
                "active": True,
            }

            # Add optional fields only when they exist
            user_columns = {
                column.name
                for column in User.__table__.columns
            }

            if "full_name" in user_columns:
                admin_data["full_name"] = (
                    "System Administrator"
                )

            if "email" in user_columns:
                admin_data["email"] = (
                    "admin@nileharvest.com"
                )

            admin = User(**admin_data)

            db.add(admin)
            db.commit()

            logging.info(
                "Default administrator created."
            )

        except Exception as exc:

            db.rollback()

            logging.exception(
                "Unable to create default admin: %s",
                exc,
            )


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
# OVERVIEW
# ------------------------------------------------------------

dashboard_home = safe_import(
    "modules.dashboard.home",
    "dashboard_home",
)


# ------------------------------------------------------------
# PROCUREMENT
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

procurement_purchase_orders = safe_import(
    "modules.procurement.purchase_orders",
    "purchase_orders_page",
)


# ------------------------------------------------------------
# WAREHOUSE
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
# PRODUCTION
# ------------------------------------------------------------

milling_dashboard = safe_import(
    "modules.milling.dashboard",
    "milling_dashboard",
)

packaging_dashboard = safe_import(
    "modules.packaging.dashboard",
    "packaging_dashboard",
)


# ------------------------------------------------------------
# SALES & DISTRIBUTION
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
# FINANCE
# ------------------------------------------------------------

finance_dashboard = safe_import(
    "modules.finance.dashboard",
    "finance_dashboard",
)


# ------------------------------------------------------------
# REPORTS
# ------------------------------------------------------------

reports_dashboard = safe_import(
    "modules.reports.dashboard",
    "reports_dashboard",
)


# ============================================================
# FALLBACK PAGE
# ============================================================

def fallback_page(title):

    def render():

        st.info(
            f"{title} – "
            "This section is currently being prepared."
        )

    return render


procurement_suppliers = (
    procurement_suppliers
    or fallback_page("Suppliers")
)

procurement_purchases = (
    procurement_purchases
    or fallback_page("Purchases")
)

procurement_purchase_orders = (
    procurement_purchase_orders
    or fallback_page("Purchase Orders")
)

warehouse_inventory = (
    warehouse_inventory
    or fallback_page("Inventory")
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
                "Missing database tables detected: %s",
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
            "Database initialization failed: %s",
            exc,
        )

        st.error(
            "Database initialization failed."
        )

        with st.expander(
            "Database Error Details"
        ):

            st.write(
                f"{type(exc).__name__}: {exc}"
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

    username = (username or "").strip()
    password = password or ""

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

            logging.warning(
                "Login failed: unknown username '%s'",
                username,
            )

            return False

        if not getattr(
            user,
            "active",
            True,
        ):

            logging.warning(
                "Login failed: inactive user '%s'",
                username,
            )

            return False

        password_hash = getattr(
            user,
            "password_hash",
            None,
        )

        if not password_hash:

            logging.error(
                "User '%s' has no password hash.",
                username,
            )

            return False

        try:

            password_valid = verify_password(
                password,
                password_hash,
            )

        except Exception as exc:

            logging.exception(
                "Password verification failed: %s",
                exc,
            )

            return False

        if password_valid:

            st.session_state.logged_in = True

            st.session_state.username = (
                getattr(
                    user,
                    "username",
                    username,
                )
            )

            st.session_state.role = (
                getattr(
                    user,
                    "role",
                    "User",
                )
            )

            logging.info(
                "Successful login for '%s'",
                username,
            )

            return True

        logging.warning(
            "Invalid password for '%s'",
            username,
        )

        return False

    except Exception as exc:

        logging.exception(
            "Login error: %s",
            exc,
        )

        return False

    finally:

        db.close()


# ============================================================
# LOGIN PAGE
# ============================================================

if not st.session_state.logged_in:

    st.markdown(
        """
        <div class="esan-login-brand">
            <div class="esan-word">ESAN</div>
            <div class="esan-line"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="login-title">
            Enterprise Resource Planning System
        </div>
        """,
        unsafe_allow_html=True,
    )

    login_col1, login_col2, login_col3 = st.columns(
        [1, 2, 1]
    )

    with login_col2:

        username = st.text_input(
            "Username",
            placeholder="Enter your username",
            key="login_username",
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password",
            key="login_password",
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
                    "Login successful."
                )

                st.rerun()

            else:

                st.error(
                    "Invalid username or password."
                )

    st.stop()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    # --------------------------------------------------------
    # ESAN BRAND
    # --------------------------------------------------------

    st.markdown(
        """
        <div class="esan-sidebar-brand">
            <div class="esan-word">ESAN</div>
            <div class="esan-line"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    # --------------------------------------------------------
    # NAVIGATION FUNCTION
    # --------------------------------------------------------

    def nav_button(label):

        if st.button(
            label,
            use_container_width=True,
        ):

            st.session_state.current_page = (
                label
            )

            st.rerun()


    # --------------------------------------------------------
    # OVERVIEW
    # --------------------------------------------------------

    nav_button(
        "🏠 Overview"
    )


    # --------------------------------------------------------
    # OPERATIONS
    # --------------------------------------------------------

    st.markdown(
        '<div class="sidebar-section">OPERATIONS</div>',
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
    # COMMERCIAL
    # --------------------------------------------------------

    st.markdown(
        '<div class="sidebar-section">COMMERCIAL</div>',
        unsafe_allow_html=True,
    )

    nav_button(
        "🚚 Sales & Distribution"
    )


    # --------------------------------------------------------
    # FINANCE
    # --------------------------------------------------------

    st.markdown(
        '<div class="sidebar-section">FINANCE</div>',
        unsafe_allow_html=True,
    )

    nav_button(
        "💰 Finance"
    )


    # --------------------------------------------------------
    # REPORTING
    # --------------------------------------------------------

    st.markdown(
        '<div class="sidebar-section">REPORTING</div>',
        unsafe_allow_html=True,
    )

    nav_button(
        "📊 Reports"
    )


    # --------------------------------------------------------
    # USER PANEL
    # --------------------------------------------------------

    st.divider()

    st.markdown(
        "### 👤 User Panel"
    )

    st.markdown(
        '<div class="user-panel">',
        unsafe_allow_html=True,
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
    # LOGOUT
    # --------------------------------------------------------

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


# ============================================================
# CURRENT PAGE
# ============================================================

menu = st.session_state.current_page


# ============================================================
# OVERVIEW
# ============================================================

if menu == "🏠 Overview":

    if dashboard_home:

        dashboard_home()

    else:

        st.warning(
            "Overview dashboard could not be loaded."
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
        key="sales_navigation",
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

        page_func()

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
# MODULE LOADING INFORMATION
# ============================================================

if module_errors:

    with st.expander(
        "⚠️ Module Loading Information"
    ):

        st.warning(
            "Some ERP modules could not be loaded."
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