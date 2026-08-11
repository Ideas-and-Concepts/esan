"""
Esan ERP Controller
Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Version 1.4.0 Alpha
"""

import logging
import importlib

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
# CLEAN ERP UI
# ============================================================

st.markdown(
    """
    <style>
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

        div[data-testid="stSidebar"] {
            border-right: 1px solid #ddd;
        }

        .esan-login {
            max-width: 480px;
            margin: 5rem auto 0 auto;
            padding: 2.5rem;
            border: 1px solid #e5e5e5;
            border-radius: 18px;
            text-align: center;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        }

        .esan-logo {
            font-size: 4rem;
            margin-bottom: 0.5rem;
        }

        .esan-title {
            font-size: 2.2rem;
            font-weight: 700;
            margin-bottom: 0.2rem;
        }

        .esan-company {
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }

        .esan-description {
            color: #666;
            margin-bottom: 1.5rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# MODULE REGISTRY
# ============================================================

module_errors = []


def safe_import(module_path, function_name):
    """
    Safely import a module function.

    Returns:
        function if available
        None if unavailable

    Technical errors are logged instead of being dumped
    onto the user interface.
    """

    try:
        module = importlib.import_module(module_path)

    except ModuleNotFoundError as exc:
        message = f"Module not found: {module_path}"

        logger.warning(message)

        module_errors.append(
            {
                "type": "missing_module",
                "module": module_path,
                "function": function_name,
                "message": message,
            }
        )

        return None

    except Exception as exc:
        message = (
            f"Error importing {module_path}: "
            f"{type(exc).__name__}: {exc}"
        )

        logger.exception(message)

        module_errors.append(
            {
                "type": "import_error",
                "module": module_path,
                "function": function_name,
                "message": message,
            }
        )

        return None

    if not hasattr(module, function_name):

        message = (
            f"Function '{function_name}' not found "
            f"in module '{module_path}'"
        )

        logger.warning(message)

        module_errors.append(
            {
                "type": "missing_function",
                "module": module_path,
                "function": function_name,
                "message": message,
            }
        )

        return None

    return getattr(module, function_name)


# ============================================================
# FALLBACK PAGE
# ============================================================

def fallback_page(title, description=None):
    """
    Creates a safe placeholder page for modules that have
    not yet been implemented.
    """

    def render():

        st.subheader(title)

        if description:
            st.info(description)
        else:
            st.info(
                f"{title} is not yet available. "
                "The module can be added without changing "
                "the main ERP controller."
            )

    return render


# ============================================================
# ADMIN CREATION
# ============================================================

try:

    from services.user_service import create_admin

except Exception:

    logger.warning(
        "services.user_service.create_admin could not be imported. "
        "Using controller fallback."
    )

    def create_admin(db):

        from auth import hash_password

        admin = (
            db.query(User)
            .filter(User.username == "admin")
            .first()
        )

        if admin:
            return

        admin = User(
            username="admin",
            password_hash=hash_password("admin123"),
            role="Administrator",
        )

        # Only populate fields if they exist on the model.
        if hasattr(User, "full_name"):
            admin.full_name = "System Administrator"

        if hasattr(User, "email"):
            admin.email = "admin@nileharvest.com"

        if hasattr(User, "active"):
            admin.active = True

        db.add(admin)
        db.commit()

        logger.info("Default administrator account created.")


# ============================================================
# OPTIONAL SEED DATA
# ============================================================

try:

    from seed.seed_data import load_seed_data

except Exception:

    load_seed_data = None
    logger.info("Seed data module not available.")


# ============================================================
# MODULE REGISTRY
# ============================================================

# -------------------------
# Dashboard
# -------------------------

dashboard_home = safe_import(
    "modules.dashboard.home",
    "dashboard_home",
)


# -------------------------
# Procurement
# -------------------------

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


# -------------------------
# Warehouse
# -------------------------

warehouse_dashboard = safe_import(
    "modules.warehouse.dashboard",
    "warehouse_dashboard",
)

warehouse_inventory = safe_import(
    "modules.warehouse.inventory",
    "inventory_page",
)


# -------------------------
# Milling
# -------------------------

milling_dashboard = safe_import(
    "modules.milling.dashboard",
    "milling_dashboard",
)


# -------------------------
# Packaging
# -------------------------

packaging_dashboard = safe_import(
    "modules.packaging.dashboard",
    "packaging_dashboard",
)


# -------------------------
# Sales
# -------------------------

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


# -------------------------
# Finance
# -------------------------

finance_dashboard = safe_import(
    "modules.finance.dashboard",
    "finance_dashboard",
)


# -------------------------
# Reports
# -------------------------

reports_dashboard = safe_import(
    "modules.reports.dashboard",
    "reports_dashboard",
)


# ============================================================
# FALLBACKS
# ============================================================

dashboard_home = dashboard_home or fallback_page(
    "🏠 Overview",
    "The ERP overview dashboard is not available yet.",
)

procurement_dashboard = procurement_dashboard or fallback_page(
    "🌾 Procurement Dashboard"
)

procurement_suppliers = procurement_suppliers or fallback_page(
    "👥 Suppliers",
    "Supplier management will be available here.",
)

procurement_purchases = procurement_purchases or fallback_page(
    "📋 Purchase Orders",
    "Purchase order management will be available here.",
)

warehouse_dashboard = warehouse_dashboard or fallback_page(
    "📦 Warehouse Dashboard"
)

warehouse_inventory = warehouse_inventory or fallback_page(
    "📦 Inventory",
    "Warehouse inventory management will be available here.",
)

milling_dashboard = milling_dashboard or fallback_page(
    "🏭 Milling",
    "Milling production management will be available here.",
)

packaging_dashboard = packaging_dashboard or fallback_page(
    "📦 Packaging",
    "Packaging production management will be available here.",
)

sales_dashboard = sales_dashboard or fallback_page(
    "🚚 Sales Dashboard"
)

sales_customers = sales_customers or fallback_page(
    "👥 Customers",
    "Customer management will be available here.",
)

sales_quotations = sales_quotations or fallback_page(
    "📝 Quotations",
    "Quotation management will be available here.",
)

sales_orders = sales_orders or fallback_page(
    "🛒 Sales Orders",
    "Sales order management will be available here.",
)

sales_deliveries = sales_deliveries or fallback_page(
    "🚚 Deliveries",
    "Delivery management will be available here.",
)

sales_invoices = sales_invoices or fallback_page(
    "🧾 Invoices",
    "Invoice management will be available here.",
)

sales_payments = sales_payments or fallback_page(
    "💳 Payments",
    "Payment management will be available here.",
)

finance_dashboard = finance_dashboard or fallback_page(
    "💰 Finance",
    "Finance management will be available here.",
)

reports_dashboard = reports_dashboard or fallback_page(
    "📊 Reports",
    "ERP reports will be available here.",
)


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def initialize_database():

    try:

        inspector = inspect(engine)

        existing_tables = inspector.get_table_names()

        missing_tables = [
            table_name
            for table_name in Base.metadata.tables
            if table_name not in existing_tables
        ]

        if missing_tables:

            logger.info(
                "Creating missing database tables: %s",
                ", ".join(missing_tables),
            )

        Base.metadata.create_all(bind=engine)

        db = SessionLocal()

        try:

            create_admin(db)

        finally:

            db.close()

        # Seed data is optional.
        if load_seed_data:

            try:

                load_seed_data()

            except Exception as exc:

                logger.exception(
                    "Seed data failed: %s",
                    exc,
                )

    except Exception as exc:

        logger.exception(
            "Database initialization failed: %s",
            exc,
        )

        st.error(
            "⚠️ Esan ERP could not initialize the database."
        )

        st.stop()


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

    st.session_state.current_page = "🏠 Overview"


# ============================================================
# LOGIN FUNCTION
# ============================================================

def login(username, password):

    username = username.strip()

    if not username or not password:
        return False

    db = SessionLocal()

    try:

        user = (
            db.query(User)
            .filter(User.username == username)
            .first()
        )

        if not user:
            return False

        # Respect the active field when the model has one.
        if hasattr(user, "active") and not user.active:
            return False

        if not verify_password(
            password,
            user.password_hash,
        ):
            return False

        st.session_state.logged_in = True
        st.session_state.username = user.username
        st.session_state.role = user.role

        logger.info(
            "Successful login: %s",
            user.username,
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

    st.markdown(
        """
        <div class="esan-login">

            <div class="esan-logo">🌾</div>

            <div class="esan-title">
                Esan ERP
            </div>

            <div class="esan-company">
                Nile Harvest Foods Ltd.
            </div>

            <div class="esan-description">
                Enterprise Milling &amp; Packaging
                Management System
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:

        username = st.text_input(
            "Username",
            placeholder="Enter username",
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter password",
        )

        login_clicked = st.button(
            "🔐 Login",
            use_container_width=True,
            type="primary",
        )

        if login_clicked:

            if login(username, password):

                st.success("Login successful.")

                st.rerun()

            else:

                st.error(
                    "Invalid username or password."
                )

        st.caption(
            "Default administrator: admin / admin123"
        )

    st.stop()


# ============================================================
# MAIN HEADER
# ============================================================

st.title("🌾 Esan ERP")

st.caption(
    f"{COMPANY_NAME} | Version {VERSION}"
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div style="text-align:center;">
            <div style="font-size:2.5rem;">🌾</div>
            <h2 style="margin-top:0;">Esan ERP</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    def nav_button(label):

        if st.button(
            label,
            use_container_width=True,
        ):

            st.session_state.current_page = label
            st.rerun()


    # -------------------------
    # MAIN
    # -------------------------

    nav_button("🏠 Overview")


    # -------------------------
    # OPERATIONS
    # -------------------------

    st.markdown("**OPERATIONS**")

    nav_button("🌾 Procurement")
    nav_button("📦 Warehouse")
    nav_button("🏭 Milling")
    nav_button("📦 Packaging")


    # -------------------------
    # COMMERCIAL
    # -------------------------

    st.markdown("**COMMERCIAL**")

    nav_button("🚚 Sales & Distribution")


    # -------------------------
    # FINANCE
    # -------------------------

    st.markdown("**FINANCE**")

    nav_button("💰 Finance")


    # -------------------------
    # REPORTING
    # -------------------------

    st.markdown("**REPORTING**")

    nav_button("📊 Reports")


    st.divider()


    # -------------------------
    # USER
    # -------------------------

    st.markdown("### 👤 User Panel")

    st.write(
        f"User: **{st.session_state.username}**"
    )

    st.write(
        f"Role: **{st.session_state.role}**"
    )


    # -------------------------
    # LOGOUT
    # -------------------------

    if st.button(
        "🚪 Logout",
        use_container_width=True,
    ):

        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.role = None
        st.session_state.current_page = "🏠 Overview"

        st.rerun()


# ============================================================
# CURRENT PAGE
# ============================================================

menu = st.session_state.current_page


# ============================================================
# ERP ROUTER
# ============================================================

if menu == "🏠 Overview":

    dashboard_home()


# ============================================================
# PROCUREMENT
# ============================================================

elif menu == "🌾 Procurement":

    st.header("🌾 Procurement")

    procurement_menu = st.radio(
        "Procurement Module",
        [
            "Dashboard",
            "Suppliers",
            "Purchase Orders",
        ],
        horizontal=True,
    )

    if procurement_menu == "Dashboard":
        procurement_dashboard()

    elif procurement_menu == "Suppliers":
        procurement_suppliers()

    elif procurement_menu == "Purchase Orders":
        procurement_purchases()


# ============================================================
# WAREHOUSE
# ============================================================

elif menu == "📦 Warehouse":

    st.header("📦 Warehouse")

    warehouse_menu = st.radio(
        "Warehouse Module",
        [
            "Dashboard",
            "Inventory",
        ],
        horizontal=True,
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

    st.header("🚚 Sales & Distribution")

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

    page_func = sales_pages.get(sales_menu)

    if page_func:
        page_func()
    else:
        st.error(
            f"Unable to load {sales_menu}."
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
# DEVELOPER MODULE STATUS
# ============================================================

# Technical import errors are logged but are NOT displayed
# to normal users.
#
# If you need to inspect them during development, uncomment
# the block below.

# if module_errors:
#
#     with st.expander("🛠 Developer: Module Loading Information"):
#
#         for error in module_errors:
#             st.write(error)


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "© Nile Harvest Foods Ltd. | "
    "Esan ERP Enterprise Platform"
)