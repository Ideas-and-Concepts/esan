"""
Esan ERP
Nile Harvest Foods Ltd.
Enterprise Resource Planning System

Version 1.4.0 Alpha
Full Repository Integration
"""

import logging
import importlib

import streamlit as st


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
# GLOBAL ERROR COLLECTION
# ============================================================

module_errors = []
system_errors = []


# ============================================================
# SAFE CONFIG IMPORT
# ============================================================

COMPANY_NAME = "Nile Harvest Foods Ltd."
VERSION = "1.4.0 Alpha"

try:
    config_module = importlib.import_module("config")

    COMPANY_NAME = getattr(
        config_module,
        "COMPANY_NAME",
        COMPANY_NAME,
    )

    VERSION = getattr(
        config_module,
        "VERSION",
        VERSION,
    )

except Exception as exc:

    logging.warning(
        "Config module could not be loaded: %s",
        exc,
    )


# ============================================================
# SAFE DATABASE IMPORT
# ============================================================

Base = None
engine = None
SessionLocal = None

try:

    database_module = importlib.import_module(
        "database"
    )

    Base = getattr(
        database_module,
        "Base",
        None,
    )

    engine = getattr(
        database_module,
        "engine",
        None,
    )

    SessionLocal = getattr(
        database_module,
        "SessionLocal",
        None,
    )

    if Base is None:
        system_errors.append(
            "database.py: Base was not found."
        )

    if engine is None:
        system_errors.append(
            "database.py: engine was not found."
        )

    if SessionLocal is None:
        system_errors.append(
            "database.py: SessionLocal was not found."
        )

except Exception as exc:

    error = (
        f"database.py: "
        f"{type(exc).__name__}: {exc}"
    )

    system_errors.append(error)

    logging.exception(
        "Database module failed to load."
    )


# ============================================================
# SAFE AUTH IMPORT
# ============================================================

verify_password = None
hash_password = None

try:

    auth_module = importlib.import_module(
        "auth"
    )

    verify_password = getattr(
        auth_module,
        "verify_password",
        None,
    )

    hash_password = getattr(
        auth_module,
        "hash_password",
        None,
    )

    if verify_password is None:

        system_errors.append(
            "auth.py: verify_password was not found."
        )

except Exception as exc:

    error = (
        f"auth.py: "
        f"{type(exc).__name__}: {exc}"
    )

    system_errors.append(error)

    logging.exception(
        "Auth module failed to load."
    )


# ============================================================
# SAFE USER MODEL IMPORT
# ============================================================

User = None

try:

    models_module = importlib.import_module(
        "models"
    )

    User = getattr(
        models_module,
        "User",
        None,
    )

    if User is None:

        system_errors.append(
            "models.py: User model was not found."
        )

except Exception as exc:

    error = (
        f"models.py: "
        f"{type(exc).__name__}: {exc}"
    )

    system_errors.append(error)

    logging.exception(
        "Models module failed to load."
    )


# ============================================================
# GLOBAL UI
# ============================================================

st.markdown(
    """
    <style>

    /* ======================================================
       HIDE STREAMLIT DEFAULT UI
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

    /* ======================================================
       MAIN CONTENT
       ====================================================== */

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

    /* ======================================================
       LOGIN PAGE
       ====================================================== */

    .login-page {
        min-height: 38vh;
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

        box-shadow:
            0 18px 45px
            rgba(20, 90, 55, 0.25);

        overflow: hidden;
    }

    /* ======================================================
       SOIL
       ====================================================== */

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
    }

    /* ======================================================
       STEM
       ====================================================== */

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

    /* ======================================================
       LEAVES
       ====================================================== */

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
    div[data-testid="stButton"]
    > button {

        text-align: left;
        border-radius: 9px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SAFE MODULE IMPORT SYSTEM
# ============================================================

def safe_import(
    module_path,
    function_name,
):
    """
    Safely import a module function.

    If a module is broken or unavailable,
    the ERP continues running.
    """

    try:

        module = importlib.import_module(
            module_path
        )

        function = getattr(
            module,
            function_name,
            None,
        )

        if function is None:

            error = (
                f"{module_path}: missing function "
                f"'{function_name}'"
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
# ADMIN CREATION SERVICE
# ============================================================

create_admin_service = None

try:

    user_service = importlib.import_module(
        "services.user_service"
    )

    create_admin_service = getattr(
        user_service,
        "create_admin",
        None,
    )

except Exception as exc:

    logging.warning(
        "User service unavailable: %s",
        exc,
    )


# ============================================================
# CREATE DEFAULT ADMINISTRATOR
# ============================================================

def ensure_admin_user(db):
    """
    Create the default administrator if one does
    not already exist.

    Default credentials:

        Username: admin
        Password: admin123
    """

    if User is None:
        raise RuntimeError(
            "User model is unavailable."
        )

    # --------------------------------------------------------
    # Use existing service first
    # --------------------------------------------------------

    if create_admin_service is not None:

        try:

            create_admin_service(db)

            return

        except Exception as exc:

            logging.warning(
                "Existing create_admin service failed: %s",
                exc,
            )

    # --------------------------------------------------------
    # Check for existing admin
    # --------------------------------------------------------

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
            "Could not query User model: %s",
            exc,
        )

        raise

    if admin is not None:
        return

    # --------------------------------------------------------
    # Password hashing
    # --------------------------------------------------------

    if hash_password is None:

        raise RuntimeError(
            "hash_password is unavailable."
        )

    password_hash = hash_password(
        "admin123"
    )

    # --------------------------------------------------------
    # Detect actual User columns
    # --------------------------------------------------------

    try:

        user_columns = {
            column.name
            for column in User.__table__.columns
        }

    except Exception:

        user_columns = set()

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
        values["password_hash"] = (
            password_hash
        )

    elif "password" in user_columns:
        values["password"] = (
            password_hash
        )

    if "role" in user_columns:
        values["role"] = "Administrator"

    if "active" in user_columns:
        values["active"] = True

    if not values.get("username"):

        raise RuntimeError(
            "User model does not contain "
            "a username field."
        )

    admin = User(**values)

    db.add(admin)
    db.commit()

    logging.info(
        "Default administrator created."
    )


# ============================================================
# SEED DATA
# ============================================================

load_seed_data = None

try:

    seed_module = importlib.import_module(
        "seed.seed_data"
    )

    load_seed_data = getattr(
        seed_module,
        "load_seed_data",
        None,
    )

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
# SALES
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


# ------------------------------------------------------------
# ADMINISTRATION
# ------------------------------------------------------------

administration_dashboard = safe_import(
    "modules.admin.dashboard",
    "admin_dashboard",
)


# ============================================================
# FALLBACK PAGE
# ============================================================

def fallback_page(title):

    def render():

        st.info(
            f"{title} is currently unavailable."
        )

        st.caption(
            "The module could not be loaded. "
            "Check Module Loading Information "
            "below."
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

administration_dashboard = (
    administration_dashboard
    or fallback_page("Administration")
)


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def initialize_database():

    if engine is None:
        return

    try:

        # ----------------------------------------------------
        # Inspect database
        # ----------------------------------------------------

        if Base is not None:

            try:

                inspector = inspect(
                    engine
                )

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

            # ------------------------------------------------
            # Create missing tables
            # ------------------------------------------------

            Base.metadata.create_all(
                bind=engine
            )

        # ----------------------------------------------------
        # Create administrator
        # ----------------------------------------------------

        if (
            SessionLocal is not None
            and User is not None
        ):

            db = SessionLocal()

            try:

                ensure_admin_user(db)

            except Exception as exc:

                logging.exception(
                    "Admin initialization failed: %s",
                    exc,
                )

                system_errors.append(
                    "Administrator initialization: "
                    f"{type(exc).__name__}: {exc}"
                )

            finally:

                db.close()

        # ----------------------------------------------------
        # Seed data
        # ----------------------------------------------------

        if load_seed_data is not None:

            try:

                load_seed_data()

            except Exception as exc:

                logging.warning(
                    "Seed data failed: %s",
                    exc,
                )

    except Exception as exc:

        error = (
            "Database initialization failed: "
            f"{type(exc).__name__}: {exc}"
        )

        system_errors.append(error)

        logging.exception(
            "Database initialization failed."
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

    st.session_state.current_page = (
        "🏠 Overview"
    )


# ============================================================
# LOGIN FUNCTION
# ============================================================

def login(username, password):

    if not username:
        return False

    if not password:
        return False

    if User is None:
        return False

    if SessionLocal is None:
        return False

    if verify_password is None:
        return False

    db = SessionLocal()

    try:

        user = (
            db.query(User)
            .filter(
                User.username
                == username.strip()
            )
            .first()
        )

        if user is None:

            logging.warning(
                "Login failed. "
                "Unknown username: %s",
                username,
            )

            return False

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
                "No password hash for user: %s",
                username,
            )

            return False

        try:

            password_valid = (
                verify_password(
                    password,
                    password_hash,
                )
            )

        except Exception as exc:

            logging.exception(
                "Password verification error: %s",
                exc,
            )

            return False

        if not password_valid:

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
            "Successful login: %s",
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
# LOGIN PAGE
# ============================================================

if not st.session_state.logged_in:

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
            key="login_button",
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

                if User is None:

                    st.error(
                        "Login system could not "
                        "load the User model."
                    )

                elif SessionLocal is None:

                    st.error(
                        "Database connection is "
                        "not available."
                    )

                elif verify_password is None:

                    st.error(
                        "Password verification "
                        "system is unavailable."
                    )

                else:

                    st.error(
                        "Invalid username or password."
                    )

    # --------------------------------------------------------
    # Diagnostics
    # --------------------------------------------------------

    if system_errors or module_errors:

        with st.expander(
            "⚠️ System Diagnostics"
        ):

            if system_errors:

                st.warning(
                    "System information:"
                )

                for error in system_errors:

                    st.write(
                        f"• {error}"
                    )

            if module_errors:

                st.warning(
                    "Module information:"
                )

                for error in module_errors:

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
            width:100%;
            text-align:center;
            margin-top:5px;
            margin-bottom:15px;
        ">

            <div class="logo"
                 style="
                    width:88px;
                    height:88px;
                    margin:0 auto;
                    border-radius:25px;
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
    # Navigation function
    # --------------------------------------------------------

    def nav_button(label):

        if st.button(
            label,
            use_container_width=True,
            key=f"nav_{label}",
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
    # Administration
    # --------------------------------------------------------

    if st.session_state.role in [
        "Administrator",
        "Admin",
        "admin",
    ]:

        st.markdown(
            "**ADMINISTRATION**"
        )

        nav_button(
            "🔐 Administration"
        )

    # --------------------------------------------------------
    # User panel
    # --------------------------------------------------------

    st.divider()

    st.markdown(
        "### 👤 User Panel"
    )

    st.write(
        f"User: "
        f"**{st.session_state.username}**"
    )

    st.write(
        f"Role: "
        f"**{st.session_state.role}**"
    )

    if st.button(
        "🚪 Logout",
        use_container_width=True,
        key="logout_button",
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

    st.caption(
        "Customer → Quotation → Sales Order → "
        "Delivery → Invoice → Payment"
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

    st.header(
        "💰 Finance"
    )

    st.caption(
        "Accounts Receivable → Cash / Bank → "
        "General Ledger"
    )

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
# ADMINISTRATION
# ============================================================

elif menu == "🔐 Administration":

    if st.session_state.role not in [
        "Administrator",
        "Admin",
        "admin",
    ]:

        st.error(
            "You do not have permission "
            "to access Administration."
        )

    elif administration_dashboard:

        administration_dashboard()

    else:

        st.warning(
            "Administration module unavailable."
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
# SYSTEM INFORMATION
# ============================================================

if system_errors:

    with st.expander(
        "⚠️ System Information"
    ):

        for error in system_errors:

            st.write(
                f"• {error}"
            )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    f"© {COMPANY_NAME} | "
    f"Esan ERP {VERSION} | "
    f"Enterprise Resource Planning Platform"
)