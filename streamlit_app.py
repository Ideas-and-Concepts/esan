"""
Nile Harvest Foods Ltd.
Enterprise Resource Planning System

Version 1.4.0 Alpha – Full Repository Integration
"""

import logging
import os

import streamlit as st
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
    format="%(asctime)s - %(levelname)s - %(message)s",
)


# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Nile Harvest ERP",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==================================================
# CLEAN ERP UI
# ==================================================

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
    }

    div[data-testid="stSidebar"] {
        border-right: 1px solid #ddd;
    }


    /* ==========================================
       LOGIN PAGE
       ========================================== */

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


    /* ==========================================
       ESAN ERP SVG LOGO
       ========================================== */

    .esan-logo {
        width: 118px;
        height: 118px;
        margin: 0 auto 20px auto;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .esan-logo svg {
        width: 100%;
        height: 100%;
        display: block;
    }


    /* ==========================================
       SIDEBAR LOGO
       ========================================== */

    .esan-sidebar-logo {
        width: 82px;
        height: 82px;
        margin: 0 auto 10px auto;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .esan-sidebar-logo svg {
        width: 100%;
        height: 100%;
        display: block;
    }


    /* ==========================================
       LOGIN INPUTS & BUTTON
       ========================================== */

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


# ==================================================
# ESAN ERP LOGO
# ==================================================

def render_esan_logo(size="normal"):
    """
    Render the Esan ERP logo as inline SVG.

    size:
        normal  -> login page
        sidebar -> sidebar
    """

    if size == "sidebar":
        logo_class = "esan-sidebar-logo"
    else:
        logo_class = "esan-logo"

    st.markdown(
        f"""
        <div class="{logo_class}">

            <svg
                viewBox="0 0 200 200"
                xmlns="http://www.w3.org/2000/svg"
                role="img"
                aria-label="Esan ERP"
            >

                <!-- =================================================
                     MAIN GREEN EMBLEM
                     ================================================= -->

                <rect
                    x="7"
                    y="7"
                    width="186"
                    height="186"
                    rx="48"
                    fill="#2E7D32"
                />

                <!-- =================================================
                     INNER GREEN GLOW
                     ================================================= -->

                <rect
                    x="18"
                    y="18"
                    width="164"
                    height="164"
                    rx="40"
                    fill="#388E3C"
                    opacity="0.45"
                />

                <!-- =================================================
                     SOIL
                     ================================================= -->

                <path
                    d="
                        M8 143
                        C42 132 69 132 100 143
                        C132 154 157 153 192 139
                        L192 192
                        L8 192
                        Z
                    "
                    fill="#4E342E"
                />

                <!-- =================================================
                     STEM
                     ================================================= -->

                <path
                    d="
                        M100 146
                        C99 130 99 111 100 88
                    "
                    stroke="#AED581"
                    stroke-width="8"
                    stroke-linecap="round"
                    fill="none"
                />

                <!-- =================================================
                     LEFT LEAF
                     ================================================= -->

                <path
                    d="
                        M98 108
                        C78 105 58 94 51 74
                        C72 71 91 82 100 99
                        Z
                    "
                    fill="#81C784"
                />

                <!-- =================================================
                     RIGHT LEAF
                     ================================================= -->

                <path
                    d="
                        M102 98
                        C113 76 133 64 154 68
                        C151 89 133 103 104 105
                        Z
                    "
                    fill="#A5D66A"
                />

                <!-- =================================================
                     CENTRAL GRAIN
                     ================================================= -->

                <ellipse
                    cx="100"
                    cy="61"
                    rx="8"
                    ry="11"
                    fill="#DCE775"
                />

                <!-- =================================================
                     SMALL GRAIN DETAILS
                     ================================================= -->

                <circle
                    cx="75"
                    cy="129"
                    r="3"
                    fill="#795548"
                    opacity="0.8"
                />

                <circle
                    cx="91"
                    cy="137"
                    r="3"
                    fill="#795548"
                    opacity="0.8"
                />

                <circle
                    cx="119"
                    cy="139"
                    r="3"
                    fill="#795548"
                    opacity="0.8"
                />

                <circle
                    cx="138"
                    cy="132"
                    r="3"
                    fill="#795548"
                    opacity="0.8"
                />

            </svg>

        </div>
        """,
        unsafe_allow_html=True,
    )


# ==================================================
# SAFE IMPORT SYSTEM
# ==================================================

module_errors = []


def safe_import(module_path, function_name):
    """Safely import a module function."""

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

    except Exception as e:

        error = (
            f"{module_path}: "
            f"{type(e).__name__}: {e}"
        )

        module_errors.append(error)

        logging.exception(
            f"Failed loading {module_path}"
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
                active=True,
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


# ==================================================
# FALLBACK PAGE
# ==================================================

def _fallback_page(title):

    def _render():

        st.info(
            f"{title} – "
            "This section is currently being prepared."
        )

    return _render


procurement_suppliers = (
    procurement_suppliers
    or _fallback_page("Suppliers")
)

procurement_purchases = (
    procurement_purchases
    or _fallback_page("Purchases")
)

procurement_purchase_orders = (
    procurement_purchase_orders
    or _fallback_page("Purchase Orders")
)

warehouse_inventory = (
    warehouse_inventory
    or _fallback_page("Inventory")
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

        missing_tables = [
            t
            for t in Base.metadata.tables
            if t not in existing_tables
        ]

        if missing_tables:

            logging.info(
                "Creating missing tables: %s",
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

            except Exception as e:

                logging.warning(
                    "Seed data failed: %s",
                    e,
                )

    except Exception:

        logging.exception(
            "Database initialization failed"
        )

        st.error(
            "Database initialization failed. "
            "Please check esan_erp.log."
        )


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
                user.password_hash,
            )
        ):

            st.session_state.logged_in = True
            st.session_state.username = (
                user.username
            )
            st.session_state.role = user.role

            return True

        return False

    finally:

        db.close()


# ==================================================
# LOGIN SCREEN
# ==================================================

if not st.session_state.logged_in:

    st.markdown(
        """
        <div class="login-page">
            <div class="login-container">
        """,
        unsafe_allow_html=True,
    )

    # NEW SVG LOGO
    render_esan_logo("normal")

    st.markdown(
        """
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
                    "Login successful"
                )

                st.rerun()

            else:

                st.error(
                    "Invalid username or password"
                )

    st.stop()


# ==================================================
# SIDEBAR
# ==================================================

with st.sidebar:

    # NEW SVG LOGO
    render_esan_logo("sidebar")

    st.divider()

    def nav_button(label):

        if st.button(
            label,
            use_container_width=True,
        ):

            st.session_state.current_page = label

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

if menu == "🏠 Overview":

    if dashboard_home:

        dashboard_home()

    else:

        st.warning(
            "Overview dashboard could not be loaded."
        )


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


elif menu == "🏭 Milling":

    if milling_dashboard:

        milling_dashboard()

    else:

        st.warning(
            "Milling module unavailable."
        )


elif menu == "📦 Packaging":

    if packaging_dashboard:

        packaging_dashboard()

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


# ==================================================
# FINANCE
# ==================================================

elif menu == "💰 Finance":

    if finance_dashboard:

        finance_dashboard()

    else:

        st.warning(
            "Finance module unavailable."
        )


# ==================================================
# REPORTS
# ==================================================

elif menu == "📊 Reports":

    if reports_dashboard:

        reports_dashboard()

    else:

        st.warning(
            "Reports module unavailable."
        )


# ==================================================
# MODULE LOADING INFORMATION
# ==================================================

if module_errors:

    with st.expander(
        "⚠️ Module Loading Information"
    ):

        st.warning(
            "The following modules could not be loaded:"
        )

        for error in module_errors:

            st.write(
                f"• {error}"
            )


# ==================================================
# FOOTER
# ==================================================

st.divider()

st.caption(
    f"© {COMPANY_NAME} | "
    f"Enterprise Resource Planning Platform"
)