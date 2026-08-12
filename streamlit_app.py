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
# GLOBAL UI
# ============================================================

st.markdown(
    """
    <style>

    /* ================================================
       STREAMLIT CLEANUP
       ================================================ */

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
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }


    /* ================================================
       ESAN BRAND
       ================================================ */

    .esan-brand {
        text-align: center;
        font-size: 42px;
        font-weight: 800;
        letter-spacing: 3px;
        margin-bottom: 5px;
    }

    .esan-subtitle {
        text-align: center;
        font-size: 14px;
        opacity: 0.65;
        margin-bottom: 30px;
    }


    /* ================================================
       LOGIN PAGE
       ================================================ */

    .login-wrapper {
        width: 100%;
        min-height: 72vh;

        display: flex;
        justify-content: center;
        align-items: center;
    }

    .login-card {
        width: 420px;
        max-width: 95%;
        padding: 35px;
        border-radius: 18px;
        border: 1px solid rgba(128, 128, 128, 0.22);
        box-shadow: 0 15px 45px rgba(0, 0, 0, 0.08);
        margin: auto;
    }

    .login-title {
        text-align: center;
        font-size: 34px;
        font-weight: 800;
        letter-spacing: 3px;
        margin-bottom: 5px;
    }

    .login-subtitle {
        text-align: center;
        opacity: 0.65;
        font-size: 14px;
        margin-bottom: 25px;
    }


    /* ================================================
       INPUTS
       ================================================ */

    div[data-testid="stTextInput"] label {
        font-weight: 600;
    }

    div[data-testid="stTextInput"] input {
        min-height: 46px;
        border-radius: 10px;
    }


    /* ================================================
       BUTTONS
       ================================================ */

    div[data-testid="stButton"] > button {
        min-height: 44px;
        border-radius: 10px;
        font-weight: 700;
    }


    /* ================================================
       SIDEBAR
       ================================================ */

    div[data-testid="stSidebar"] {
        border-right: 1px solid rgba(128, 128, 128, 0.25);
    }

    .sidebar-esan {
        text-align: center;
        font-size: 30px;
        font-weight: 800;
        letter-spacing: 3px;
        padding-top: 5px;
        padding-bottom: 3px;
    }

    .sidebar-company {
        text-align: center;
        font-size: 11px;
        opacity: 0.60;
        margin-bottom: 15px;
    }

    .sidebar-section {
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 1px;
        opacity: 0.60;
        margin-top: 15px;
        margin-bottom: 5px;
    }

    div[data-testid="stSidebar"] div[data-testid="stButton"] > button {
        text-align: left;
        border-radius: 9px;
    }


    /* ================================================
       FOOTER
       ================================================ */

    .esan-footer {
        text-align: center;
        opacity: 0.55;
        font-size: 12px;
        padding: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# MODULE ERROR TRACKING
# ============================================================

module_errors = []


# ============================================================
# SAFE IMPORT
# ============================================================

def safe_import(module_path, function_name):
    """
    Safely import a module and function.

    A broken optional module will not prevent
    the main Esan ERP application from loading.
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
# ADMIN ACCOUNT
# ============================================================

def ensure_admin_account():
    """
    Ensure the default administrator account exists.

    IMPORTANT:
    We only use fields that are expected in the User model.
    This avoids the previous 'invalid keyword argument'
    problem caused by fields such as full_name.
    """

    try:

        from auth import hash_password

        db = SessionLocal()

        try:

            admin = (
                db.query(User)
                .filter(
                    User.username == "admin"
                )
                .first()
            )

            if admin is None:

                admin = User(
                    username="admin",
                    password_hash=hash_password(
                        "admin123"
                    ),
                    role="Administrator",
                    active=True,
                )

                # ----------------------------------------
                # Add optional fields only if they exist
                # in the User model.
                # ----------------------------------------

                user_columns = {
                    column.name
                    for column in inspect(
                        User
                    ).columns
                }

                if (
                    "email"
                    in user_columns
                ):
                    admin.email = (
                        "admin@nileharvest.com"
                    )

                db.add(admin)
                db.commit()

                logging.info(
                    "Default administrator account created."
                )

            else:

                changed = False

                if hasattr(
                    admin,
                    "active",
                ) and not admin.active:

                    admin.active = True
                    changed = True

                if (
                    hasattr(
                        admin,
                        "role",
                    )
                    and not admin.role
                ):

                    admin.role = (
                        "Administrator"
                    )
                    changed = True

                if changed:

                    db.commit()

        finally:

            db.close()

        return True

    except Exception as exc:

        logging.exception(
            "Unable to initialize admin account: %s",
            exc,
        )

        return False


# ============================================================
# SEED DATA
# ============================================================

try:

    from seed.seed_data import load_seed_data

except Exception:

    load_seed_data = None


# ============================================================
# MODULE REGISTRY
# ============================================================

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

procurement_purchase_orders = safe_import(
    "modules.procurement.purchase_orders",
    "purchase_orders_page",
)

procurement_purchases = safe_import(
    "modules.procurement.purchases",
    "purchases_page",
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


# ============================================================
# FALLBACK PAGE
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

procurement_purchase_orders = (
    procurement_purchase_orders
    or fallback_page("Purchase Orders")
)

procurement_purchases = (
    procurement_purchases
    or fallback_page("Purchases")
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

        # --------------------------------------------
        # Create missing tables
        # --------------------------------------------

        inspector = inspect(engine)

        existing_tables = (
            inspector.get_table_names()
        )

        missing_tables = [
            table
            for table in Base.metadata.tables
            if table not in existing_tables
        ]

        if missing_tables:

            logging.info(
                "Creating missing tables: %s",
                missing_tables,
            )

        Base.metadata.create_all(
            bind=engine
        )

        # --------------------------------------------
        # Admin account
        # --------------------------------------------

        ensure_admin_account()

        # --------------------------------------------
        # Seed data
        # --------------------------------------------

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
            "The ERP database could not be initialized."
        )

        st.caption(
            "Check esan_erp.log for the detailed error."
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


# ============================================================
# LOGIN
# ============================================================

def login(username, password):

    username = (
        username or ""
    ).strip()

    password = (
        password or ""
    )

    if not username or not password:
        return False, "Enter username and password."

    db = SessionLocal()

    try:

        user = (
            db.query(User)
            .filter(
                User.username == username
            )
            .first()
        )

        if user is None:

            logging.warning(
                "Login failed: unknown user '%s'",
                username,
            )

            return False, "Invalid username or password."

        # --------------------------------------------
        # Check active account
        # --------------------------------------------

        if hasattr(
            user,
            "active",
        ):

            if not user.active:

                return False, (
                    "This user account is inactive."
                )

        # --------------------------------------------
        # Password hash
        # --------------------------------------------

        password_hash = getattr(
            user,
            "password_hash",
            None,
        )

        if not password_hash:

            logging.error(
                "User '%s' has no password_hash.",
                username,
            )

            return False, (
                "This account has no valid password."
            )

        # --------------------------------------------
        # Verify password
        # --------------------------------------------

        try:

            valid_password = verify_password(
                password,
                password_hash,
            )

        except Exception as exc:

            logging.exception(
                "Password verification error for '%s': %s",
                username,
                exc,
            )

            return False, (
                "Password verification failed."
            )

        if not valid_password:

            logging.warning(
                "Invalid password for user '%s'",
                username,
            )

            return False, (
                "Invalid username or password."
            )

        # --------------------------------------------
        # Successful login
        # --------------------------------------------

        st.session_state.logged_in = True

        st.session_state.username = (
            user.username
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

        return True, None

    except Exception as exc:

        logging.exception(
            "Login error: %s",
            exc,
        )

        return False, (
            "Unable to complete login. "
            "Check esan_erp.log."
        )

    finally:

        db.close()


# ============================================================
# LOGIN PAGE
# ============================================================

if not st.session_state.logged_in:

    st.markdown(
        '<div class="login-wrapper">',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="login-card">

            <div class="login-title">
                ESAN
            </div>

            <div class="login-subtitle">
                Enterprise Resource Planning System
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # Centered login form
    # --------------------------------------------------------

    left, center, right = st.columns(
        [1, 2, 1]
    )

    with center:

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

            success, error = login(
                username,
                password,
            )

            if success:

                st.success(
                    "Login successful."
                )

                st.rerun()

            else:

                st.error(
                    error
                    or "Invalid username or password."
                )

    st.markdown(
        """
        <div class="esan-footer">
            Esan ERP
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.stop()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    # --------------------------------------------------------
    # ESAN BRANDING
    # --------------------------------------------------------

    st.markdown(
        """
        <div class="sidebar-esan">
            ESAN
        </div>

        <div class="sidebar-company">
            Nile Harvest Foods Ltd.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    # --------------------------------------------------------
    # NAVIGATION BUTTON
    # --------------------------------------------------------

    def nav_button(label):

        if st.button(
            label,
            use_container_width=True,
        ):

            st.session_state.current_page = label

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

st.markdown(
    f"""
    <div class="esan-footer">
        © {COMPANY_NAME}
        &nbsp; | &nbsp;
        Esan ERP
        &nbsp; | &nbsp;
        Version {VERSION}
    </div>
    """,
    unsafe_allow_html=True,
)