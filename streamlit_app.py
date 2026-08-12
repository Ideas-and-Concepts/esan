"""
Esan ERP
Nile Harvest Foods Ltd.
Enterprise Resource Planning System

Version 1.4.0 Alpha
Full Repository Integration

Main Modules:
- Overview
- Procurement
- Warehouse
- Milling
- Packaging
- Sales & Distribution
- Finance
- Reports
- Administration
"""

import logging

import streamlit as st
from sqlalchemy import inspect


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
# LOGGING
# ============================================================

logging.basicConfig(
    filename="esan_erp.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


# ============================================================
# SAFE CORE IMPORTS
# ============================================================

database_error = None
auth_error = None
models_error = None

Base = None
engine = None
SessionLocal = None
verify_password = None
hash_password = None
User = None


# ------------------------------------------------------------
# DATABASE
# ------------------------------------------------------------

try:

    from database import Base, engine, SessionLocal

except Exception as exc:

    database_error = (
        f"database.py: "
        f"{type(exc).__name__}: {exc}"
    )

    logging.exception(
        "Unable to import database"
    )


# ------------------------------------------------------------
# MODELS
# ------------------------------------------------------------

try:

    from models import User

except Exception as exc:

    models_error = (
        f"models.py: "
        f"{type(exc).__name__}: {exc}"
    )

    logging.exception(
        "Unable to import User from models.py"
    )


# ------------------------------------------------------------
# AUTH
# ------------------------------------------------------------

try:

    from auth import verify_password

except Exception as exc:

    auth_error = (
        f"auth.py: "
        f"{type(exc).__name__}: {exc}"
    )

    logging.exception(
        "Unable to import verify_password"
    )


try:

    from auth import hash_password

except Exception:

    hash_password = None


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
        border-right: 1px solid rgba(128,128,128,0.25);
    }

    /* ======================================================
       LOGIN
       ====================================================== */

    .login-page {
        min-height: 78vh;
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
       ESAN LOGO
       ====================================================== */

    .esan-logo {
        width: 120px;
        height: 120px;
        margin: 0 auto 25px auto;
        border-radius: 34px;
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
            rgba(20,90,55,0.25);
        overflow: hidden;
    }

    .esan-logo-text {
        color: white;
        font-size: 34px;
        font-weight: 800;
        letter-spacing: 2px;
        position: relative;
        z-index: 5;
    }

    .esan-logo::after {
        content: "";
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 25px;
        background: #4e342e;
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

    div[data-testid="stButton"] > button {
        border-radius: 10px;
        min-height: 44px;
        font-weight: 700;
    }

    /* ======================================================
       SIDEBAR
       ====================================================== */

    div[data-testid="stSidebar"] .esan-sidebar-logo {
        text-align: center;
        margin-top: 5px;
        margin-bottom: 15px;
    }

    div[data-testid="stSidebar"] .esan-sidebar-logo-box {
        width: 82px;
        height: 82px;
        margin: auto;
        border-radius: 24px;
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
        overflow: hidden;
        box-shadow:
            0 10px 25px
            rgba(20,90,55,0.20);
    }

    div[data-testid="stSidebar"]
    .esan-sidebar-logo-box::after {
        content: "";
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 18px;
        background: #4e342e;
    }

    div[data-testid="stSidebar"]
    .esan-sidebar-logo-text {
        color: white;
        font-size: 24px;
        font-weight: 800;
        letter-spacing: 1px;
        position: relative;
        z-index: 5;
    }

    div[data-testid="stSidebar"]
    div[data-testid="stButton"] > button {
        text-align: left;
        border-radius: 9px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# CONFIG
# ============================================================

try:

    from config import COMPANY_NAME, VERSION

except Exception:

    COMPANY_NAME = "Nile Harvest Foods Ltd."

    VERSION = "1.4.0 Alpha"


# ============================================================
# SAFE MODULE IMPORT
# ============================================================

module_errors = []


def safe_import(module_path, function_name):

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

procurement_purchase_orders = safe_import(
    "modules.procurement.purchase_orders",
    "purchase_orders_page",
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
            "The module could not be loaded."
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

    if Base is None or engine is None:

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
            "Database initialization failed"
        )

        st.error(
            "Database initialization failed."
        )

        st.caption(
            str(exc)
        )


initialize_database()


# ============================================================
# SESSION STATE
# ============================================================

if "logged_in" not in st.session_state:

    st.session_state.logged_in = False

    st.session_state.username = None

    st.session_state.role = None

    st.session_state.current_page = (
        "🏠 Overview"
    )


# ============================================================
# ADMIN CREATION
# ============================================================

def ensure_admin():

    if (
        SessionLocal is None
        or User is None
        or hash_password is None
    ):

        return

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

            # ------------------------------------------------
            # Add optional fields only when the model supports
            # them. This prevents the old full_name error.
            # ------------------------------------------------

            if hasattr(User, "full_name"):

                admin.full_name = (
                    "System Administrator"
                )

            if hasattr(User, "email"):

                admin.email = (
                    "admin@nileharvest.com"
                )

            db.add(admin)

            db.commit()

            logging.info(
                "Default administrator created."
            )

    except Exception as exc:

        db.rollback()

        logging.exception(
            "Unable to create administrator."
        )

    finally:

        db.close()


ensure_admin()


# ============================================================
# LOGIN FUNCTION
# ============================================================

def login(username, password):

    if (
        SessionLocal is None
        or User is None
        or verify_password is None
    ):

        st.error(
            "Login system is unavailable. "
            "Check database.py, models.py and auth.py."
        )

        return False

    username = (username or "").strip()

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

        if user is None:

            logging.warning(
                "Login failed: unknown user %s",
                username,
            )

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

        if not active or not password_hash:

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
                "User logged in: %s",
                username,
            )

            return True

        logging.warning(
            "Invalid password for user: %s",
            username,
        )

        return False

    except Exception as exc:

        logging.exception(
            "Login error: %s",
            exc,
        )

        st.error(
            "Unable to process login. "
            "Check esan_erp.log."
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

                <div class="esan-logo">

                    <div class="esan-logo-text">
                        ESAN
                    </div>

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
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password",
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

    # --------------------------------------------------------
    # Database/model diagnostics
    # --------------------------------------------------------

    if database_error or models_error or auth_error:

        with st.expander(
            "⚠️ System Diagnostics"
        ):

            if database_error:

                st.error(
                    database_error
                )

            if models_error:

                st.error(
                    models_error
                )

            if auth_error:

                st.error(
                    auth_error
                )

    st.stop()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    # --------------------------------------------------------
    # ESAN LOGO
    # --------------------------------------------------------

    st.markdown(
        """
        <div class="esan-sidebar-logo">

            <div class="esan-sidebar-logo-box">

                <div class="esan-sidebar-logo-text">
                    ESAN
                </div>

            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()


    # --------------------------------------------------------
    # NAVIGATION
    # --------------------------------------------------------

    def nav_button(label):

        if st.button(
            label,
            use_container_width=True,
        ):

            st.session_state.current_page = label

            st.rerun()


    nav_button(
        "🏠 Overview"
    )


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


    st.markdown(
        "**COMMERCIAL**"
    )

    nav_button(
        "🚚 Sales & Distribution"
    )


    st.markdown(
        "**FINANCE**"
    )

    nav_button(
        "💰 Finance"
    )


    st.markdown(
        "**REPORTING**"
    )

    nav_button(
        "📊 Reports"
    )


    # --------------------------------------------------------
    # ADMINISTRATION
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

    st.caption(
        "Customer → Quotation → Sales Order → "
        "Stock Reservation → Delivery → Invoice → Payment"
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
            "Some optional modules could not be loaded."
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
    f"Esan ERP {VERSION} | "
    f"Enterprise Resource Planning Platform"
)