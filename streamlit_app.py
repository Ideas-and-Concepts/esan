"""
Esan ERP Controller
Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Version 1.4.0 Alpha – Full Repository Integration
"""

import streamlit as st
import logging
from sqlalchemy import inspect

from config import COMPANY_NAME, VERSION
from database import Base, engine, SessionLocal
from models import User
from auth import verify_password


# ==================================================
# LOGGING
# ==================================================

logging.basicConfig(
    filename="esan_erp.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Esan ERP",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==================================================
# CLEAN ERP UI
# ==================================================

st.markdown(
    """
    <style>
    #MainMenu { display:none; }
    footer { display:none; }
    header { display:none; }
    .block-container { padding-top:1.5rem; }
    div[data-testid="stSidebar"] {
        border-right:1px solid #ddd;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# ==================================================
# SAFE IMPORT SYSTEM
# ==================================================

module_errors = []


def safe_import(module_path, function_name):
    """
    Safely import a module function.

    Returns:
        callable function if available
        None if import/function fails
    """

    try:

        module = __import__(
            module_path,
            fromlist=[function_name]
        )

        if hasattr(module, function_name):

            function = getattr(
                module,
                function_name
            )

            if callable(function):
                return function

            error = (
                f"{module_path}: "
                f"{function_name} exists but is not callable"
            )

            module_errors.append(error)
            logging.error(error)

            return None

        error = (
            f"{module_path}: "
            f"missing function '{function_name}'"
        )

        module_errors.append(error)
        logging.error(error)

        return None

    except Exception as e:

        error = (
            f"{module_path}: "
            f"{type(e).__name__}: {e}"
        )

        module_errors.append(error)

        logging.error(
            error,
            exc_info=True
        )

        return None


# ==================================================
# ADMIN CREATION
# ==================================================

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

        if not admin:

            from auth import hash_password

            admin = User(
                username="admin",
                full_name="System Administrator",
                email="admin@nileharvest.com",
                password_hash=hash_password(
                    "admin123"
                ),
                role="Administrator",
                active=True
            )

            db.add(admin)
            db.commit()


# ==================================================
# SEED DATA
# ==================================================

try:

    from seed.seed_data import load_seed_data

except ImportError:

    load_seed_data = None


# ==================================================
# MODULE REGISTRY
# ==================================================

# ==================================================
# DASHBOARD
# ==================================================

dashboard_home = safe_import(
    "modules.dashboard.home",
    "dashboard_home"
)


# ==================================================
# PROCUREMENT
# ==================================================

procurement_dashboard = safe_import(
    "modules.procurement.dashboard",
    "procurement_dashboard"
)

procurement_suppliers = safe_import(
    "modules.procurement.suppliers",
    "suppliers_page"
)

# IMPORTANT:
# The repository uses purchase_orders.py,
# not purchases.py.

procurement_purchases = safe_import(
    "modules.procurement.purchase_orders",
    "purchase_orders_page"
)


# ==================================================
# WAREHOUSE
# ==================================================

warehouse_dashboard = safe_import(
    "modules.warehouse.dashboard",
    "warehouse_dashboard"
)

warehouse_inventory = safe_import(
    "modules.warehouse.inventory",
    "inventory_page"
)


# ==================================================
# MILLING
# ==================================================

milling_dashboard = safe_import(
    "modules.milling.dashboard",
    "milling_dashboard"
)


# ==================================================
# PACKAGING
# ==================================================

packaging_dashboard = safe_import(
    "modules.packaging.dashboard",
    "packaging_dashboard"
)


# ==================================================
# SALES & DISTRIBUTION
# ==================================================

sales_dashboard = safe_import(
    "modules.sales.dashboard",
    "sales_dashboard"
)

sales_customers = safe_import(
    "modules.sales.customers",
    "customers_page"
)

sales_quotations = safe_import(
    "modules.sales.quotations",
    "quotations_page"
)

sales_orders = safe_import(
    "modules.sales.orders",
    "sales_orders_page"
)

sales_deliveries = safe_import(
    "modules.sales.deliveries",
    "deliveries_page"
)

sales_invoices = safe_import(
    "modules.sales.invoices",
    "invoices_page"
)

sales_payments = safe_import(
    "modules.sales.payments",
    "payments_page"
)


# ==================================================
# FINANCE
# ==================================================

finance_dashboard = safe_import(
    "modules.finance.dashboard",
    "finance_dashboard"
)


# ==================================================
# REPORTS
# ==================================================

reports_dashboard = safe_import(
    "modules.reports.dashboard",
    "reports_dashboard"
)


# ==================================================
# OPTIONAL MODULE FALLBACKS
# ==================================================

def _fallback_page(title):
    """
    Display a friendly placeholder for a module
    that has not yet been implemented.
    """

    def _render():

        st.info(
            f"{title} – "
            "This section will be available soon."
        )

    return _render


# Only use fallbacks for pages that are genuinely
# optional. We do NOT hide import errors for the
# main dashboards.

if procurement_suppliers is None:
    procurement_suppliers = _fallback_page(
        "Suppliers"
    )

if procurement_purchases is None:
    procurement_purchases = _fallback_page(
        "Purchase Orders"
    )

if warehouse_inventory is None:
    warehouse_inventory = _fallback_page(
        "Inventory"
    )

if sales_deliveries is None:
    sales_deliveries = _fallback_page(
        "Deliveries"
    )

if sales_invoices is None:
    sales_invoices = _fallback_page(
        "Invoices"
    )

if sales_payments is None:
    sales_payments = _fallback_page(
        "Payments"
    )


# ==================================================
# DATABASE INITIALIZATION
# ==================================================

def initialize_database():

    try:

        inspector = inspect(engine)

        existing_tables = (
            inspector.get_table_names()
        )

        missing_tables = []

        for table_name in Base.metadata.tables:

            if table_name not in existing_tables:

                missing_tables.append(
                    table_name
                )

        if missing_tables:

            logging.info(
                "Missing database tables: %s",
                missing_tables
            )

        # Create missing tables.
        Base.metadata.create_all(
            bind=engine
        )

        # Create administrator.
        db = SessionLocal()

        try:

            create_admin(db)

        finally:

            db.close()

        # Optional seed data.
        if load_seed_data:

            try:

                load_seed_data()

            except Exception as e:

                logging.warning(
                    "Seed data failed: %s",
                    e
                )

    except Exception as e:

        logging.error(
            "Database initialization error",
            exc_info=True
        )

        st.error(
            "Database initialization failed."
        )

        with st.expander(
            "Database Technical Information"
        ):

            st.exception(e)


initialize_database()


# ==================================================
# SESSION MANAGEMENT
# ==================================================

if "logged_in" not in st.session_state:

    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None
    st.session_state.current_page = (
        "🏠 Overview"
    )


# ==================================================
# LOGIN FUNCTION
# ==================================================

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

        if (
            user
            and user.active
            and verify_password(
                password,
                user.password_hash
            )
        ):

            st.session_state.logged_in = True
            st.session_state.username = (
                user.username
            )
            st.session_state.role = (
                user.role
            )

            return True

        return False

    finally:

        db.close()


# ==================================================
# LOGIN SCREEN
# DO NOT CHANGE
# ==================================================

if not st.session_state.logged_in:

    st.markdown(
        """
        <div style="text-align:center">
        <h1>🌾 Esan ERP</h1>
        <h3>Nile Harvest Foods Ltd.</h3>
        <p>Enterprise Milling & Packaging Management System</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(
        [1, 2, 1]
    )

    with col2:

        username = st.text_input(
            "Username"
        )

        password = st.text_input(
            "Password",
            type="password"
        )

        if st.button(
            "Login",
            use_container_width=True
        ):

            if login(
                username,
                password
            ):

                st.success(
                    "Login successful"
                )

                st.rerun()

            else:

                st.error(
                    "Invalid username or password"
                )

        st.info(
            "Default administrator: "
            "admin / admin123"
        )

    st.stop()


# ==================================================
# MAIN HEADER
# ==================================================

st.title("🌾 Esan ERP")

st.caption(
    f"{COMPANY_NAME} | Version {VERSION}"
)


# ==================================================
# SIDEBAR NAVIGATION
# DO NOT CHANGE
# ==================================================

with st.sidebar:

    st.markdown(
        """
        <h2 style="text-align:center">
        🌾 Esan ERP
        </h2>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    def nav_button(label):

        if st.button(
            label,
            use_container_width=True
        ):

            st.session_state.current_page = (
                label
            )

    # MAIN
    nav_button(
        "🏠 Overview"
    )

    # OPERATIONS
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

    # COMMERCIAL
    st.markdown(
        "**COMMERCIAL**"
    )

    nav_button(
        "🚚 Sales & Distribution"
    )

    # FINANCE
    st.markdown(
        "**FINANCE**"
    )

    nav_button(
        "💰 Finance"
    )

    # REPORTING
    st.markdown(
        "**REPORTING**"
    )

    nav_button(
        "📊 Reports"
    )

    st.divider()

    # USER PANEL
    st.markdown(
        "### 👤 User Panel"
    )

    st.write(
        f"User: **"
        f"{st.session_state.username}"
        f"**"
    )

    st.write(
        f"Role: **"
        f"{st.session_state.role}"
        f"**"
    )

    if st.button(
        "🚪 Logout",
        use_container_width=True
    ):

        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.role = None
        st.session_state.current_page = (
            "🏠 Overview"
        )

        st.rerun()


# ==================================================
# CURRENT PAGE
# ==================================================

menu = st.session_state.current_page


# ==================================================
# ERP ROUTER
# ==================================================

# ==================================================
# OVERVIEW
# ==================================================

if menu == "🏠 Overview":

    if dashboard_home:

        try:

            dashboard_home()

        except Exception as e:

            st.error(
                "Overview dashboard failed to load."
            )

            with st.expander(
                "Technical Information"
            ):

                st.exception(e)

    else:

        st.warning(
            "Overview dashboard unavailable."
        )


# ==================================================
# PROCUREMENT
# ==================================================

elif menu == "🌾 Procurement":

    st.header(
        "🌾 Procurement"
    )

    procurement_menu = st.radio(
        "Procurement Module",
        [
            "Dashboard",
            "Suppliers",
            "Purchase Orders"
        ],
        key="procurement_navigation"
    )

    if procurement_menu == "Dashboard":

        if procurement_dashboard:

            try:

                procurement_dashboard()

            except Exception as e:

                st.error(
                    "Procurement Dashboard failed "
                    "to load."
                )

                with st.expander(
                    "Technical Information"
                ):

                    st.exception(e)

        else:

            st.warning(
                "Procurement Dashboard unavailable."
            )

    elif procurement_menu == "Suppliers":

        try:

            procurement_suppliers()

        except Exception as e:

            st.error(
                "Suppliers module failed to load."
            )

            with st.expander(
                "Technical Information"
            ):

                st.exception(e)

    elif procurement_menu == "Purchase Orders":

        try:

            procurement_purchases()

        except Exception as e:

            st.error(
                "Purchase Orders module failed "
                "to load."
            )

            with st.expander(
                "Technical Information"
            ):

                st.exception(e)


# ==================================================
# WAREHOUSE
# ==================================================

elif menu == "📦 Warehouse":

    st.header(
        "📦 Warehouse"
    )

    warehouse_menu = st.radio(
        "Warehouse Module",
        [
            "Dashboard",
            "Inventory"
        ],
        key="warehouse_navigation"
    )

    if warehouse_menu == "Dashboard":

        if warehouse_dashboard:

            try:

                warehouse_dashboard()

            except Exception as e:

                st.error(
                    "Warehouse Dashboard failed "
                    "to load."
                )

                with st.expander(
                    "Technical Information"
                ):

                    st.exception(e)

        else:

            st.warning(
                "Warehouse Dashboard unavailable."
            )

    elif warehouse_menu == "Inventory":

        try:

            warehouse_inventory()

        except Exception as e:

            st.error(
                "Inventory module failed to load."
            )

            with st.expander(
                "Technical Information"
            ):

                st.exception(e)


# ==================================================
# MILLING
# ==================================================

elif menu == "🏭 Milling":

    if milling_dashboard:

        try:

            milling_dashboard()

        except Exception as e:

            st.error(
                "Milling module failed to load."
            )

            with st.expander(
                "Technical Information"
            ):

                st.exception(e)

    else:

        st.warning(
            "Milling module unavailable."
        )


# ==================================================
# PACKAGING
# ==================================================

elif menu == "📦 Packaging":

    if packaging_dashboard:

        try:

            packaging_dashboard()

        except Exception as e:

            st.error(
                "Packaging module failed to load."
            )

            with st.expander(
                "Technical Information"
            ):

                st.exception(e)

    else:

        st.warning(
            "Packaging module unavailable."
        )


# ==================================================
# SALES & DISTRIBUTION
# ==================================================

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
            "Payments"
        ],
        key="sales_navigation"
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

        try:

            page_func()

        except Exception as e:

            st.error(
                f"{sales_menu} module "
                "failed to load."
            )

            with st.expander(
                "Technical Information"
            ):

                st.exception(e)

    else:

        st.warning(
            f"{sales_menu} page unavailable."
        )


# ==================================================
# FINANCE
# ==================================================

elif menu == "💰 Finance":

    if finance_dashboard:

        try:

            finance_dashboard()

        except Exception as e:

            st.error(
                "Finance module failed to load."
            )

            with st.expander(
                "Technical Information"
            ):

                st.exception(e)

    else:

        st.warning(
            "Finance module unavailable."
        )


# ==================================================
# REPORTS
# ==================================================

elif menu == "📊 Reports":

    if reports_dashboard:

        try:

            reports_dashboard()

        except Exception as e:

            st.error(
                "Reports module failed to load."
            )

            with st.expander(
                "Technical Information"
            ):

                st.exception(e)

    else:

        st.warning(
            "Reports module unavailable."
        )


# ==================================================
# MODULE IMPORT WARNINGS
# ==================================================

if module_errors:

    with st.expander(
        "⚠️ Module Loading Information"
    ):

        st.warning(
            "One or more modules could not be "
            "imported. This does not prevent "
            "the rest of Esan ERP from running."
        )

        for error in module_errors:

            st.code(
                error
            )


# ==================================================
# FOOTER
# ==================================================

st.divider()

st.caption(
    "© Nile Harvest Foods Ltd. | "
    "Esan ERP Enterprise Platform"
)