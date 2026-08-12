"""
Esan ERP
Nile Harvest Foods Ltd.
Enterprise Resource Planning System

Version 1.4.0 Alpha
Full Repository Integration
"""

import logging
import os

import streamlit as st
from sqlalchemy import (
    inspect,
    text,
    MetaData,
    Table,
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
)
from sqlalchemy.exc import SQLAlchemyError

from config import COMPANY_NAME, VERSION
from database import Base, engine, SessionLocal


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


# ============================================================
# ESAN UI
# ============================================================

st.markdown(
    """
    <style>

    /* =====================================================
       HIDE STREAMLIT DEFAULT ELEMENTS
       ===================================================== */

    #MainMenu {
        visibility: hidden;
    }

    header {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    /* =====================================================
       MAIN CONTENT
       ===================================================== */

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }

    /* =====================================================
       LOGIN PAGE
       ===================================================== */

    .esan-login-page {
        min-height: 35vh;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        margin-bottom: 0.5rem;
    }

    .esan-login-brand {
        text-align: center;
        margin-bottom: 10px;
    }

    .esan-login-brand .esan-name {
        font-size: 68px;
        font-weight: 900;
        letter-spacing: 8px;
        line-height: 1;
        color: #2e7d32;
        text-shadow:
            0 3px 12px rgba(46, 125, 50, 0.20);
    }

    .esan-login-brand .esan-subtitle {
        margin-top: 12px;
        font-size: 13px;
        letter-spacing: 2px;
        font-weight: 600;
        opacity: 0.70;
        text-transform: uppercase;
    }

    .esan-login-form {
        max-width: 440px;
        margin: auto;
    }

    /* =====================================================
       INPUTS
       ===================================================== */

    div[data-testid="stTextInput"] label {
        font-weight: 600;
    }

    div[data-testid="stTextInput"] input {
        min-height: 46px;
        border-radius: 10px;
    }

    /* =====================================================
       BUTTONS
       ===================================================== */

    div[data-testid="stButton"] > button {
        min-height: 44px;
        border-radius: 10px;
        font-weight: 700;
    }

    /* =====================================================
       SIDEBAR
       ===================================================== */

    div[data-testid="stSidebar"] {
        border-right: 1px solid rgba(128, 128, 128, 0.25);
    }

    .sidebar-esan {
        width: 100%;
        text-align: center;
        padding: 8px 0 4px 0;
    }

    .sidebar-esan-name {
        font-size: 34px;
        font-weight: 900;
        letter-spacing: 5px;
        color: #2e7d32;
        line-height: 1;
    }

    .sidebar-esan-subtitle {
        margin-top: 7px;
        font-size: 9px;
        letter-spacing: 1.5px;
        opacity: 0.65;
        font-weight: 600;
    }

    /* =====================================================
       SIDEBAR NAVIGATION
       ===================================================== */

    div[data-testid="stSidebar"]
    div[data-testid="stButton"] > button {
        text-align: left;
        border-radius: 9px;
        margin-bottom: 3px;
    }

    /* =====================================================
       SECTION HEADINGS
       ===================================================== */

    div[data-testid="stSidebar"] p {
        margin-bottom: 4px;
    }

    /* =====================================================
       MOBILE
       ===================================================== */

    @media (max-width: 768px) {

        .esan-login-brand .esan-name {
            font-size: 52px;
            letter-spacing: 5px;
        }

        .esan-login-brand .esan-subtitle {
            font-size: 10px;
        }

    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SAFE MODULE IMPORT
# ============================================================

module_errors = []


def safe_import(module_path, function_name):
    """
    Safely import a module function.

    A broken optional module will not crash
    the entire ERP application.
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
# PASSWORD SYSTEM
# ============================================================

def verify_user_password(password, password_hash):
    """
    Uses the existing Esan auth system when available.

    Falls back to bcrypt when necessary.
    """

    if not password_hash:
        return False

    # --------------------------------------------------------
    # Existing Esan authentication
    # --------------------------------------------------------

    try:

        from auth import verify_password

        return bool(
            verify_password(
                password,
                password_hash,
            )
        )

    except Exception as exc:

        logging.warning(
            "auth.verify_password unavailable: %s",
            exc,
        )

    # --------------------------------------------------------
    # bcrypt fallback
    # --------------------------------------------------------

    try:

        import bcrypt

        return bool(
            bcrypt.checkpw(
                password.encode("utf-8"),
                password_hash.encode("utf-8"),
            )
        )

    except Exception as exc:

        logging.warning(
            "bcrypt fallback failed: %s",
            exc,
        )

    return False


def create_password_hash(password):
    """
    Creates a password hash using the existing
    Esan auth system or bcrypt.
    """

    try:

        from auth import hash_password

        return hash_password(password)

    except Exception:

        pass

    try:

        import bcrypt

        return bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt(),
        ).decode("utf-8")

    except Exception as exc:

        logging.error(
            "Unable to create password hash: %s",
            exc,
        )

        return None


# ============================================================
# DATABASE TABLE COMPATIBILITY
# ============================================================

def ensure_users_table():
    """
    Ensures a basic users table exists.

    This deliberately does NOT import models.User.
    Therefore a broken models.py will not prevent login.
    """

    try:

        inspector = inspect(engine)

        tables = inspector.get_table_names()

        if "users" in tables:
            return True

        metadata = MetaData()

        Table(
            "users",
            metadata,
            Column(
                "id",
                Integer,
                primary_key=True,
            ),
            Column(
                "username",
                String(100),
                unique=True,
                nullable=False,
            ),
            Column(
                "full_name",
                String(200),
                nullable=True,
            ),
            Column(
                "email",
                String(200),
                nullable=True,
            ),
            Column(
                "password_hash",
                String(255),
                nullable=False,
            ),
            Column(
                "role",
                String(100),
                nullable=True,
            ),
            Column(
                "active",
                Boolean,
                default=True,
            ),
            Column(
                "created_at",
                DateTime,
                nullable=True,
            ),
        )

        metadata.create_all(
            bind=engine,
            checkfirst=True,
        )

        logging.info(
            "Created users table."
        )

        return True

    except Exception as exc:

        logging.exception(
            "Unable to ensure users table."
        )

        return False


# ============================================================
# ADMIN USER
# ============================================================

def ensure_admin_user():
    """
    Creates the default administrator only when
    an admin account does not already exist.

    Default credentials:

        Username: admin
        Password: admin123
    """

    try:

        ensure_users_table()

        db = SessionLocal()

        try:

            result = db.execute(
                text(
                    """
                    SELECT id
                    FROM users
                    WHERE username = :username
                    LIMIT 1
                    """
                ),
                {
                    "username": "admin"
                },
            )

            admin = result.fetchone()

            if admin:

                return True

            password_hash = create_password_hash(
                "admin123"
            )

            if not password_hash:

                logging.error(
                    "Could not create admin password hash."
                )

                return False

            db.execute(
                text(
                    """
                    INSERT INTO users
                    (
                        username,
                        full_name,
                        email,
                        password_hash,
                        role,
                        active
                    )
                    VALUES
                    (
                        :username,
                        :full_name,
                        :email,
                        :password_hash,
                        :role,
                        :active
                    )
                    """
                ),
                {
                    "username": "admin",
                    "full_name": "System Administrator",
                    "email": "admin@nileharvest.com",
                    "password_hash": password_hash,
                    "role": "Administrator",
                    "active": True,
                },
            )

            db.commit()

            logging.info(
                "Default administrator created."
            )

            return True

        finally:

            db.close()

    except Exception as exc:

        logging.exception(
            "Admin initialization failed: %s",
            exc,
        )

        return False


# ============================================================
# LOGIN
# ============================================================

def login(username, password):
    """
    Authenticate directly against the users table.

    No models.User import is required.
    """

    username = (username or "").strip()

    if not username or not password:
        return False

    try:

        ensure_users_table()

        db = SessionLocal()

        try:

            result = db.execute(
                text(
                    """
                    SELECT
                        username,
                        password_hash,
                        role,
                        active
                    FROM users
                    WHERE username = :username
                    LIMIT 1
                    """
                ),
                {
                    "username": username
                },
            )

            user = result.mappings().first()

            if not user:

                return False

            active = user.get("active")

            if active in (
                False,
                0,
                "0",
                "false",
                "False",
            ):
                return False

            valid = verify_user_password(
                password,
                user.get("password_hash"),
            )

            if not valid:

                return False

            st.session_state.logged_in = True

            st.session_state.username = (
                user.get("username")
                or username
            )

            st.session_state.role = (
                user.get("role")
                or "User"
            )

            return True

        finally:

            db.close()

    except Exception as exc:

        logging.exception(
            "Login error: %s",
            exc,
        )

        return False


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def initialize_database():

    try:

        # ----------------------------------------------------
        # Ensure database connection
        # ----------------------------------------------------

        with engine.connect() as connection:

            connection.execute(
                text("SELECT 1")
            )

        # ----------------------------------------------------
        # Try normal model metadata creation.
        #
        # Importantly, this does NOT import models here.
        # ----------------------------------------------------

        try:

            Base.metadata.create_all(
                bind=engine
            )

        except Exception as exc:

            logging.warning(
                "Normal metadata initialization skipped: %s",
                exc,
            )

        # ----------------------------------------------------
        # Ensure users table independently.
        # ----------------------------------------------------

        ensure_users_table()

        # ----------------------------------------------------
        # Ensure admin.
        # ----------------------------------------------------

        ensure_admin_user()

        # ----------------------------------------------------
        # Seed data
        # ----------------------------------------------------

        try:

            from seed.seed_data import load_seed_data

            if callable(load_seed_data):

                try:

                    load_seed_data()

                except Exception as exc:

                    logging.warning(
                        "Seed data failed: %s",
                        exc,
                    )

        except ImportError:

            pass

        except Exception as exc:

            logging.warning(
                "Seed system unavailable: %s",
                exc,
            )

    except Exception as exc:

        logging.exception(
            "Database initialization failed: %s",
            exc,
        )

        st.error(
            "Database connection could not be initialized. "
            "Please check esan_erp.log."
        )


initialize_database()


# ============================================================
# MODULE REGISTRY
# ============================================================

dashboard_home = safe_import(
    "modules.dashboard.home",
    "dashboard_home",
)


# ============================================================
# PROCUREMENT
# ============================================================

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


# ============================================================
# WAREHOUSE
# ============================================================

warehouse_dashboard = safe_import(
    "modules.warehouse.dashboard",
    "warehouse_dashboard",
)

warehouse_inventory = safe_import(
    "modules.warehouse.inventory",
    "inventory_page",
)


# ============================================================
# PRODUCTION
# ============================================================

milling_dashboard = safe_import(
    "modules.milling.dashboard",
    "milling_dashboard",
)

packaging_dashboard = safe_import(
    "modules.packaging.dashboard",
    "packaging_dashboard",
)


# ============================================================
# SALES & DISTRIBUTION
# ============================================================

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


# ============================================================
# FINANCE
# ============================================================

finance_dashboard = safe_import(
    "modules.finance.dashboard",
    "finance_dashboard",
)


# ============================================================
# REPORTS
# ============================================================

reports_dashboard = safe_import(
    "modules.reports.dashboard",
    "reports_dashboard",
)


# ============================================================
# FALLBACK PAGES
# ============================================================

def fallback_page(title):

    def render():

        st.info(
            f"{title} is currently unavailable."
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
# LOGIN PAGE
# ============================================================

if not st.session_state.logged_in:

    st.markdown(
        """
        <div class="esan-login-page">
            <div class="esan-login-brand">
                <div class="esan-name">ESAN</div>
                <div class="esan-subtitle">
                    Enterprise Resource Planning
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(
        [1, 2, 1]
    )

    with col2:

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

        login_clicked = st.button(
            "Login",
            use_container_width=True,
            type="primary",
        )

        if login_clicked:

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
        <div class="sidebar-esan">
            <div class="sidebar-esan-name">
                ESAN
            </div>

            <div class="sidebar-esan-subtitle">
                ERP PLATFORM
            </div>
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

            st.session_state.current_page = label

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

    st.divider()

    # --------------------------------------------------------
    # USER PANEL
    # --------------------------------------------------------

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
            "Some optional ERP modules could not be loaded."
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