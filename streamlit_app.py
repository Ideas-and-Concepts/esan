"""
Esan ERP
Nile Harvest Foods Ltd.
Enterprise Resource Planning System

Version 1.4.0 Alpha
Full Repository Integration
"""

import logging
import streamlit as st
from sqlalchemy import inspect

from config import COMPANY_NAME, VERSION
from database import Base, engine, SessionLocal
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
# GLOBAL VARIABLES
# ============================================================

module_errors = []
database_errors = []

User = None


# ============================================================
# LOAD USER MODEL SAFELY
# ============================================================

try:
    import models

    User = getattr(models, "User", None)

    if User is None:
        module_errors.append(
            "models: User model was not found."
        )

except Exception as exc:
    error = (
        f"models: {type(exc).__name__}: {exc}"
    )

    module_errors.append(error)

    logging.exception(
        "Unable to load models module"
    )


# ============================================================
# GLOBAL UI
# ============================================================

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
        padding-bottom: 2rem;
    }

    div[data-testid="stSidebar"] {
        border-right: 1px solid #ddd;
    }

    /* ======================================================
       LOGIN
       ====================================================== */

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

    /* ======================================================
       LOGO
       ====================================================== */

    .logo {
        width: 112px;
        height: 112px;
        margin: 0 auto 18px auto;
        border-radius: 32px;
        background: linear-gradient(
            145deg,
            #2e7d32,
            #1b5e20
        );
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
        box-shadow:
            0 18px 45px
            rgba(20, 90, 55, 0.25);
    }

    .logo::before {
        content: "";
        position: absolute;
        bottom: 0;
        left: 0;
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

    /* ======================================================
       LOGIN INPUTS
       ====================================================== */

    div[data-testid="stTextInput"] label {
        font-weight: 600;
    }

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


# ============================================================
# SAFE MODULE IMPORT
# ============================================================

def safe_import(module_path, function_name):
    """
    Safely import a module function.

    A failed optional module will not crash
    the entire ERP application.
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

create_admin = None

try:
    from services.user_service import create_admin

except Exception as exc:

    logging.warning(
        "services.user_service.create_admin unavailable: %s",
        exc,
    )


def ensure_admin_user(db):
    """
    Creates the default administrator if possible.

    This function is intentionally defensive because
    different versions of the User model may have
    different fields.
    """

    if User is None:
        raise RuntimeError(
            "User model is unavailable."
        )

    # --------------------------------------------------------
    # Use project's create_admin service if available
    # --------------------------------------------------------

    if create_admin is not None:

        try:
            create_admin(db)
            return
        except Exception as exc:
            logging.warning(
                "create_admin service failed: %s",
                exc,
            )

    # --------------------------------------------------------
    # Check existing admin
    # --------------------------------------------------------

    admin = (
        db.query(User)
        .filter(
            User.username == "admin"
        )
        .first()
    )

    if admin:
        return

    # --------------------------------------------------------
    # Password hashing
    # --------------------------------------------------------

    try:
        from auth import hash_password
    except Exception as exc:
        raise RuntimeError(
            f"Unable to import hash_password: {exc}"
        )

    password_hash = hash_password(
        "admin123"
    )

    # --------------------------------------------------------
    # Build user using only fields that exist
    # --------------------------------------------------------

    user_columns = {
        column.name
        for column in User.__table__.columns
    }

    values = {}

    if "username" in user_columns:
        values["username"] = "admin"

    if "full_name" in user_columns:
        values["full_name"] = (
            "System Administrator"
        )

    if "name" in user_columns:
        values["name"] = (
            "System Administrator"
        )

    if "email" in user_columns:
        values["email"] = (
            "admin@nileharvest.com"
        )

    if "password_hash" in user_columns:
        values["password_hash"] = password_hash

    if "password" in user_columns:
        values["password"] = password_hash

    if "role" in user_columns:
        values["role"] = "Administrator"

    if "active" in user_columns:
        values["active"] = True

    admin = User(**values)

    db.add(admin)
    db.commit()

    logging.info(
        "Default administrator account created."
    )


# ============================================================
# SEED DATA
# ============================================================

load_seed_data = None

try:
    from seed.seed_data import load_seed_data

except Exception as exc:

    logging.info(
        "Seed data module unavailable: %s",
        exc,
    )


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
# MILLING
# ------------------------------------------------------------

milling_dashboard = safe_import(
    "modules.milling.dashboard",
    "milling_dashboard",
)


# ------------------------------------------------------------
# PACKAGING
# ------------------------------------------------------------

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

        if engine is None:
            raise RuntimeError(
                "Database engine is unavailable."
            )

        # ----------------------------------------------------
        # Inspect database
        # ----------------------------------------------------

        try:

            inspector = inspect(engine)

            existing_tables = (
                inspector.get_table_names()
            )

            missing_tables = [
                table_name
                for table_name
                in Base.metadata.tables
                if table_name
                not in existing_tables
            ]

            if missing_tables:

                logging.info(
                    "Missing database tables: %s",
                    missing_tables,
                )

        except Exception as exc:

            logging.warning(
                "Database inspection failed: %s",
                exc,
            )

        # ----------------------------------------------------
        # Create missing tables
        # ----------------------------------------------------

        Base.metadata.create_all(
            bind=engine
        )

        # ----------------------------------------------------
        # Create administrator
        # ----------------------------------------------------

        if User is not None:

            db = SessionLocal()

            try:

                ensure_admin_user(db)

            finally:

                db.close()

        else:

            database_errors.append(
                "User model could not be loaded."
            )

        # ----------------------------------------------------
        # Seed data
        # ----------------------------------------------------

        if load_seed_data:

            try:

                load_seed_data()

            except Exception as exc:

                logging.warning(
                    "Seed data failed: %s",
                    exc,
                )

    except Exception as exc:

        error = (
            f"Database initialization failed: "
            f"{type(exc).__name__}: {exc}"
        )

        database_errors.append(error)

        logging.exception(
            "Database initialization failed"
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

    if not username or not password:
        return False

    if User is None:

        logging.error(
            "Login failed because User model "
            "is unavailable."
        )

        return False

    db = SessionLocal()

    try:

        user = (
            db.query(User)
            .filter(
                User.username == username.strip()
            )
            .first()
        )

        if user is None:

            logging.warning(
                "Login failed. User not found: %s",
                username,
            )

            return False

        # ----------------------------------------------------
        # Active status
        # ----------------------------------------------------

        active = getattr(
            user,
            "active",
            True,
        )

        if active is False:

            logging.warning(
                "Inactive user attempted login: %s",
                username,
            )

            return False

        # ----------------------------------------------------
        # Password hash
        # ----------------------------------------------------

        password_hash = getattr(
            user,
            "password_hash",
            None,
        )

        if not password_hash:

            password_hash = getattr(
                user,
                "password",
                None,
            )

        if not password_hash:

            logging.error(
                "User %s has no password hash.",
                username,
            )

            return False

        # ----------------------------------------------------
        # Verify password
        # ----------------------------------------------------

        try:

            valid_password = verify_password(
                password,
                password_hash,
            )

        except Exception as exc:

            logging.exception(
                "Password verification failed: %s",
                exc,
            )

            return False

        if not valid_password:

            logging.warning(
                "Invalid password for user: %s",
                username,
            )

            return False

        # ----------------------------------------------------
        # Successful login
        # ----------------------------------------------------

        st.session_state.logged_in = True

        st.session_state.username = getattr(
            user,
            "username",
            username,
        )

        st.session_state.role = getattr(
            user,
            "role",
            "User",
        )

        logging.info(
            "User logged in successfully: %s",
            username,
        )

        return True

    except Exception as exc:

        logging.exception(
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
    # Centered logo
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Login form
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

                if User is None:

                    st.error(
                        "Login system is unavailable "
                        "because the User model could not "
                        "be loaded. Check the module "
                        "loading information below."
                    )

                else:

                    st.error(
                        "Invalid username or password."
                    )

    # --------------------------------------------------------
    # Diagnostic information
    # --------------------------------------------------------

    if module_errors or database_errors:

        with st.expander(
            "⚠️ System Diagnostics"
        ):

            if module_errors:

                st.warning(
                    "Module loading information:"
                )

                for error in module_errors:

                    st.write(
                        f"• {error}"
                    )

            if database_errors:

                st.warning(
                    "Database information:"
                )

                for error in database_errors:

                    st.write(
                        f"• {error}"
                    )

    st.stop()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    # --------------------------------------------------------
    # Logo
    # --------------------------------------------------------

    st.markdown(
        """
        <div style="
            text-align:center;
            margin-bottom:1rem;
        ">

            <div class="logo"
                 style="
                    margin:0 auto;
                    width:88px;
                    height:88px;
                 ">

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
    # Navigation
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
    # Overview
    # --------------------------------------------------------

    nav_button(
        "🏠 Overview"
    )

    # --------------------------------------------------------
    # Operations
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
    # Commercial
    # --------------------------------------------------------

    st.markdown(
        "**COMMERCIAL**"
    )

    nav_button(
        "🚚 Sales & Distribution"
    )

    # --------------------------------------------------------
    # Finance
    # --------------------------------------------------------

    st.markdown(
        "**FINANCE**"
    )

    nav_button(
        "💰 Finance"
    )

    # --------------------------------------------------------
    # Reporting
    # --------------------------------------------------------

    st.markdown(
        "**REPORTING**"
    )

    nav_button(
        "📊 Reports"
    )

    # --------------------------------------------------------
    # User panel
    # --------------------------------------------------------

    st.divider()

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

        logging.info(
            "User logged out: %s",
            st.session_state.username,
        )

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
            "Some optional modules could not "
            "be loaded."
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