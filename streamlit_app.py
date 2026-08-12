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
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Esan ERP | Nile Harvest Foods Ltd.",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    filename="esan_erp.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


# ============================================================
# GLOBAL ERROR COLLECTION
# ============================================================

module_errors = []
system_errors = []


# ============================================================
# CONFIGURATION
# ============================================================

try:
    from config import COMPANY_NAME, VERSION
except Exception:
    COMPANY_NAME = "Nile Harvest Foods Ltd."
    VERSION = "1.4.0 Alpha"


# ============================================================
# DATABASE IMPORT
# ============================================================

try:
    from database import Base, engine, SessionLocal
except Exception as exc:

    Base = None
    engine = None
    SessionLocal = None

    system_errors.append(
        f"Database import failed: {type(exc).__name__}: {exc}"
    )

    logging.exception("Database import failed")


# ============================================================
# AUTH IMPORT
# ============================================================

try:
    from auth import verify_password
except Exception as exc:

    verify_password = None

    system_errors.append(
        f"Authentication import failed: {type(exc).__name__}: {exc}"
    )

    logging.exception("Authentication import failed")


# ============================================================
# USER MODEL
# ============================================================

User = None

try:

    models_module = importlib.import_module("models")

    User = getattr(
        models_module,
        "User",
        None,
    )

    if User is None:

        logging.warning(
            "User model was not found in models.py"
        )

except Exception as exc:

    system_errors.append(
        f"Models import failed: {type(exc).__name__}: {exc}"
    )

    logging.exception("Models import failed")


# ============================================================
# OPTIONAL PASSWORD HASH
# ============================================================

try:
    from auth import hash_password
except Exception:
    hash_password = None


# ============================================================
# UI STYLE
# ============================================================

st.markdown(
    """
    <style>

    /* =====================================================
       STREAMLIT CLEANUP
       ===================================================== */

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    header {
        visibility: hidden;
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }


    /* =====================================================
       ESAN BRAND
       ===================================================== */

    .esan-login-brand {
        text-align: center;
        margin-top: 7vh;
        margin-bottom: 30px;
    }

    .esan-login-title {
        font-size: 64px;
        font-weight: 800;
        letter-spacing: 3px;
        line-height: 1;
        margin-bottom: 12px;
    }

    .esan-login-subtitle {
        font-size: 15px;
        opacity: 0.70;
        letter-spacing: 1px;
    }


    /* =====================================================
       LOGIN CARD
       ===================================================== */

    .login-card {
        max-width: 460px;
        margin: auto;
        padding: 30px;
        border-radius: 18px;
        border: 1px solid rgba(128,128,128,0.20);
        box-shadow: 0 15px 40px rgba(0,0,0,0.08);
    }


    /* =====================================================
       SIDEBAR BRAND
       ===================================================== */

    .esan-sidebar-brand {
        text-align: center;
        padding: 12px 0 18px 0;
    }

    .esan-sidebar-title {
        font-size: 32px;
        font-weight: 800;
        letter-spacing: 2px;
        line-height: 1;
    }

    .esan-sidebar-subtitle {
        font-size: 11px;
        opacity: 0.65;
        margin-top: 8px;
    }


    /* =====================================================
       SIDEBAR
       ===================================================== */

    div[data-testid="stSidebar"] {
        border-right: 1px solid rgba(128,128,128,0.22);
    }

    div[data-testid="stSidebar"] div[data-testid="stButton"] button {
        border-radius: 9px;
        min-height: 42px;
        text-align: left;
        font-weight: 600;
    }


    /* =====================================================
       INPUTS
       ===================================================== */

    div[data-testid="stTextInput"] input {
        border-radius: 10px;
        min-height: 45px;
    }


    /* =====================================================
       BUTTONS
       ===================================================== */

    div[data-testid="stButton"] button {
        border-radius: 10px;
        min-height: 44px;
        font-weight: 700;
    }


    /* =====================================================
       SECTION LABELS
       ===================================================== */

    .module-section {
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 1px;
        opacity: 0.60;
        margin-top: 14px;
        margin-bottom: 5px;
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
    Safely imports a module function.

    A failed module will not crash the ERP.
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
# FALLBACK PAGE
# ============================================================

def fallback_page(title):

    def render():

        st.info(
            f"{title} is currently unavailable."
        )

        st.caption(
            "The module could not be loaded. "
            "Check the Module Loading Information section below."
        )

    return render


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
# MILLING
# ============================================================

milling_dashboard = safe_import(
    "modules.milling.dashboard",
    "milling_dashboard",
)


# ============================================================
# PACKAGING
# ============================================================

packaging_dashboard = safe_import(
    "modules.packaging.dashboard",
    "packaging_dashboard",
)


# ============================================================
# SALES
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
# APPLY FALLBACKS
# ============================================================

dashboard_home = (
    dashboard_home
    or fallback_page("Overview")
)

procurement_dashboard = (
    procurement_dashboard
    or fallback_page("Procurement Dashboard")
)

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

warehouse_dashboard = (
    warehouse_dashboard
    or fallback_page("Warehouse Dashboard")
)

warehouse_inventory = (
    warehouse_inventory
    or fallback_page("Inventory")
)

milling_dashboard = (
    milling_dashboard
    or fallback_page("Milling")
)

packaging_dashboard = (
    packaging_dashboard
    or fallback_page("Packaging")
)

sales_dashboard = (
    sales_dashboard
    or fallback_page("Sales Dashboard")
)

sales_customers = (
    sales_customers
    or fallback_page("Customers")
)

sales_quotations = (
    sales_quotations
    or fallback_page("Quotations")
)

sales_orders = (
    sales_orders
    or fallback_page("Sales Orders")
)

sales_deliveries = (
    sales_deliveries
    or fallback_page("Deliveries")
)

sales_invoices = (
    sales_invoices
    or fallback_page("Invoices")
)

sales_payments = (
    sales_payments
    or fallback_page("Payments")
)

finance_dashboard = (
    finance_dashboard
    or fallback_page("Finance")
)

reports_dashboard = (
    reports_dashboard
    or fallback_page("Reports")
)


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def initialize_database():

    if engine is None or Base is None:

        logging.warning(
            "Database initialization skipped because "
            "database components are unavailable."
        )

        return

    try:

        Base.metadata.create_all(
            bind=engine
        )

        logging.info(
            "Database tables initialized."
        )

    except Exception as exc:

        logging.exception(
            "Database initialization failed."
        )

        system_errors.append(
            f"Database initialization failed: "
            f"{type(exc).__name__}: {exc}"
        )


initialize_database()


# ============================================================
# ADMIN CREATION
# ============================================================

def ensure_admin_user():

    if (
        SessionLocal is None
        or User is None
    ):
        return

    try:

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

                if hash_password is None:

                    logging.warning(
                        "Admin user could not be created "
                        "because hash_password is unavailable."
                    )

                    return

                # ------------------------------------------------
                # Build only fields that actually exist
                # ------------------------------------------------

                user_fields = {
                    "username": "admin",
                    "password_hash": hash_password(
                        "admin123"
                    ),
                    "role": "Administrator",
                    "active": True,
                }

                # ------------------------------------------------
                # Optional model fields
                # ------------------------------------------------

                model_columns = {
                    column.name
                    for column in User.__table__.columns
                }

                if "email" in model_columns:
                    user_fields["email"] = (
                        "admin@nileharvest.com"
                    )

                if "full_name" in model_columns:
                    user_fields["full_name"] = (
                        "System Administrator"
                    )

                admin = User(
                    **user_fields
                )

                db.add(admin)
                db.commit()

                logging.info(
                    "Default administrator created."
                )

        finally:

            db.close()

    except Exception as exc:

        logging.exception(
            "Admin initialization failed."
        )

        system_errors.append(
            f"Admin initialization failed: "
            f"{type(exc).__name__}: {exc}"
        )


ensure_admin_user()


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

    if (
        SessionLocal is None
        or User is None
        or verify_password is None
    ):

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

        if user is None:

            return False

        active = getattr(
            user,
            "active",
            True,
        )

        password_hash = getattr(
            user,
            "password_hash",
            None,
        )

        if not active:
            return False

        if not password_hash:
            return False

        if verify_password(
            password,
            password_hash,
        ):

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

            return True

        return False

    except Exception as exc:

        logging.exception(
            "Login error."
        )

        st.error(
            f"Login error: {type(exc).__name__}"
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
            <div class="esan-login-title">
                Esan
            </div>

            <div class="esan-login-subtitle">
                Enterprise Resource Planning
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(
        [1, 2, 1]
    )

    with col2:

        st.markdown(
            '<div class="login-card">',
            unsafe_allow_html=True,
        )

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

        login_button = st.button(
            "Login",
            use_container_width=True,
            type="primary",
        )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

        if login_button:

            if not username.strip():

                st.error(
                    "Please enter your username."
                )

            elif not password:

                st.error(
                    "Please enter your password."
                )

            elif login(
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

    st.stop()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div class="esan-sidebar-brand">
            <div class="esan-sidebar-title">
                Esan
            </div>

            <div class="esan-sidebar-subtitle">
                Nile Harvest Foods Ltd.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()


    # ========================================================
    # NAVIGATION BUTTON
    # ========================================================

    def nav_button(label):

        if st.button(
            label,
            use_container_width=True,
            key=f"nav_{label}",
        ):

            st.session_state.current_page = label

            st.rerun()


    # ========================================================
    # OVERVIEW
    # ========================================================

    nav_button(
        "🏠 Overview"
    )


    # ========================================================
    # OPERATIONS
    # ========================================================

    st.markdown(
        '<div class="module-section">OPERATIONS</div>',
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


    # ========================================================
    # COMMERCIAL
    # ========================================================

    st.markdown(
        '<div class="module-section">COMMERCIAL</div>',
        unsafe_allow_html=True,
    )

    nav_button(
        "🚚 Sales & Distribution"
    )


    # ========================================================
    # FINANCE
    # ========================================================

    st.markdown(
        '<div class="module-section">FINANCE</div>',
        unsafe_allow_html=True,
    )

    nav_button(
        "💰 Finance"
    )


    # ========================================================
    # REPORTING
    # ========================================================

    st.markdown(
        '<div class="module-section">REPORTING</div>',
        unsafe_allow_html=True,
    )

    nav_button(
        "📊 Reports"
    )


    # ========================================================
    # USER
    # ========================================================

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
        key="logout_button",
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

    dashboard_home()


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

        procurement_dashboard()

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

        warehouse_dashboard()

    elif warehouse_menu == "Inventory":

        warehouse_inventory()


# ============================================================
# MILLING
# ============================================================

elif menu == "🏭 Milling":

    milling_dashboard()


# ============================================================
# PACKAGING
# ============================================================

elif menu == "📦 Packaging":

    packaging_dashboard()


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
            f"{sales_menu} page is unavailable."
        )


# ============================================================
# FINANCE
# ============================================================

elif menu == "💰 Finance":

    finance_dashboard()


# ============================================================
# REPORTS
# ============================================================

elif menu == "📊 Reports":

    reports_dashboard()


# ============================================================
# SYSTEM DIAGNOSTICS
# ============================================================

if system_errors or module_errors:

    with st.expander(
        "⚠️ System Diagnostics",
        expanded=False,
    ):

        if system_errors:

            st.subheader(
                "System Errors"
            )

            for error in system_errors:

                st.error(error)

        if module_errors:

            st.subheader(
                "Module Loading Information"
            )

            for error in module_errors:

                st.warning(error)


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    f"© {COMPANY_NAME} | "
    f"Esan ERP | "
    f"Version {VERSION}"
)