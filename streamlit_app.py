"""
Nile Harvest Foods Ltd.
Enterprise Resource Planning System

Version 1.4.0 Alpha – Full Repository Integration
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
    page_title="Nile Harvest ERP",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# ERP UI
# ============================================================

st.markdown(
    """
    <style>

    /* ========================================================
       HIDE STREAMLIT DEFAULT UI
       ======================================================== */

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


    /* ========================================================
       SIDEBAR
       ======================================================== */

    div[data-testid="stSidebar"] {
        border-right: 1px solid rgba(100, 100, 100, 0.20);
    }

    div[data-testid="stSidebar"] > div:first-child {
        padding-top: 1rem;
    }


    /* ========================================================
       LOGIN PAGE
       ======================================================== */

    .login-page {
        min-height: 82vh;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 20px;
    }

    .login-container {
        width: 430px;
        max-width: 100%;
        text-align: center;
    }


    /* ========================================================
       NILE HARVEST LOGO
       ======================================================== */

    .nh-logo {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 100%;
    }

    .nh-logo-login {
        margin: 0 auto 24px auto;
    }

    .nh-logo-sidebar {
        margin: 4px auto 12px auto;
    }

    .nh-logo svg {
        display: block;
        width: 100%;
        height: auto;
    }

    .nh-logo-login svg {
        width: 230px;
        max-width: 90%;
    }

    .nh-logo-sidebar svg {
        width: 175px;
        max-width: 90%;
    }


    /* ========================================================
       LOGIN INPUTS
       ======================================================== */

    div[data-testid="stTextInput"] label {
        font-weight: 600;
    }

    div[data-testid="stTextInput"] input {
        border-radius: 10px;
        min-height: 45px;
        padding-left: 14px;
    }


    /* ========================================================
       BUTTONS
       ======================================================== */

    div[data-testid="stButton"] > button {
        border-radius: 10px;
        min-height: 44px;
        font-weight: 700;
    }


    /* ========================================================
       NAVIGATION BUTTONS
       ======================================================== */

    div[data-testid="stSidebar"] div[data-testid="stButton"] > button {
        border-radius: 9px;
        text-align: left;
        padding-left: 14px;
        margin-bottom: 3px;
    }


    /* ========================================================
       USER PANEL
       ======================================================== */

    .user-panel {
        padding: 12px;
        border-radius: 12px;
        background: rgba(128, 128, 128, 0.08);
        margin-top: 10px;
        margin-bottom: 10px;
    }

    .user-panel-title {
        font-weight: 700;
        margin-bottom: 7px;
    }

    .user-panel-text {
        font-size: 13px;
        line-height: 1.7;
    }


    /* ========================================================
       MODULE HEADERS
       ======================================================== */

    .module-header {
        padding: 8px 0 15px 0;
    }


    /* ========================================================
       RESPONSIVE
       ======================================================== */

    @media (max-width: 768px) {

        .nh-logo-login svg {
            width: 200px;
        }

        .nh-logo-sidebar svg {
            width: 150px;
        }

        .block-container {
            padding-top: 1rem;
        }

    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# NILE HARVEST LOGO
# ============================================================

def render_nile_harvest_logo(location="login"):
    """
    Render the Nile Harvest Foods Ltd. logo using inline SVG.

    Using SVG instead of CSS shapes makes the logo much more
    reliable across Streamlit browsers and deployments.
    """

    if location == "sidebar":
        logo_class = "nh-logo nh-logo-sidebar"
    else:
        logo_class = "nh-logo nh-logo-login"

    logo_html = f"""
    <div class="{logo_class}">
        <svg
            viewBox="0 0 520 190"
            xmlns="http://www.w3.org/2000/svg"
            role="img"
            aria-label="Nile Harvest Foods Ltd."
        >

            <!-- =================================================
                 ICON BACKGROUND
                 ================================================= -->

            <defs>

                <linearGradient
                    id="nhGreen"
                    x1="0%"
                    y1="0%"
                    x2="100%"
                    y2="100%"
                >
                    <stop
                        offset="0%"
                        stop-color="#2E7D32"
                    />

                    <stop
                        offset="100%"
                        stop-color="#145A32"
                    />
                </linearGradient>

                <linearGradient
                    id="nhGold"
                    x1="0%"
                    y1="0%"
                    x2="100%"
                    y2="100%"
                >
                    <stop
                        offset="0%"
                        stop-color="#F4C542"
                    />

                    <stop
                        offset="100%"
                        stop-color="#C99A1A"
                    />
                </linearGradient>

            </defs>


            <!-- =================================================
                 LOGO EMBLEM
                 ================================================= -->

            <rect
                x="12"
                y="12"
                width="166"
                height="166"
                rx="42"
                fill="url(#nhGreen)"
            />


            <!-- =================================================
                 WATER / NILE
                 ================================================= -->

            <path
                d="
                    M32 132
                    C58 119, 80 145, 105 132
                    C130 119, 148 141, 160 132
                "
                fill="none"
                stroke="#42A5F5"
                stroke-width="8"
                stroke-linecap="round"
            />

            <path
                d="
                    M32 149
                    C58 136, 80 162, 105 149
                    C130 136, 148 158, 160 149
                "
                fill="none"
                stroke="#90CAF9"
                stroke-width="5"
                stroke-linecap="round"
            />


            <!-- =================================================
                 HARVEST STEM
                 ================================================= -->

            <path
                d="
                    M95 129
                    C94 103, 94 80, 96 53
                "
                fill="none"
                stroke="#AED581"
                stroke-width="7"
                stroke-linecap="round"
            />


            <!-- =================================================
                 LEFT LEAF
                 ================================================= -->

            <path
                d="
                    M96 88
                    C70 86, 51 70, 47 49
                    C69 50, 91 62, 96 88
                    Z
                "
                fill="#81C784"
            />


            <!-- =================================================
                 RIGHT LEAF
                 ================================================= -->

            <path
                d="
                    M96 76
                    C112 50, 134 43, 153 46
                    C147 68, 128 82, 96 76
                    Z
                "
                fill="#A5D66A"
            />


            <!-- =================================================
                 GRAIN
                 ================================================= -->

            <ellipse
                cx="78"
                cy="62"
                rx="8"
                ry="14"
                transform="rotate(-25 78 62)"
                fill="url(#nhGold)"
            />

            <ellipse
                cx="73"
                cy="76"
                rx="8"
                ry="14"
                transform="rotate(-25 73 76)"
                fill="url(#nhGold)"
            />

            <ellipse
                cx="116"
                cy="54"
                rx="8"
                ry="14"
                transform="rotate(25 116 54)"
                fill="url(#nhGold)"
            />

            <ellipse
                cx="122"
                cy="67"
                rx="8"
                ry="14"
                transform="rotate(25 122 67)"
                fill="url(#nhGold)"
            />


            <!-- =================================================
                 GOLD HARVEST LINE
                 ================================================= -->

            <path
                d="
                    M38 115
                    C67 102, 117 102, 153 115
                "
                fill="none"
                stroke="#F4C542"
                stroke-width="4"
                stroke-linecap="round"
            />


            <!-- =================================================
                 COMPANY NAME
                 ================================================= -->

            <text
                x="202"
                y="78"
                font-family="Arial, Helvetica, sans-serif"
                font-size="42"
                font-weight="700"
                fill="#1B5E20"
                letter-spacing="1"
            >
                NILE HARVEST
            </text>

            <text
                x="204"
                y="113"
                font-family="Arial, Helvetica, sans-serif"
                font-size="25"
                font-weight="600"
                fill="#4E342E"
                letter-spacing="3"
            >
                FOODS LTD.
            </text>


            <!-- =================================================
                 TAGLINE
                 ================================================= -->

            <text
                x="205"
                y="143"
                font-family="Arial, Helvetica, sans-serif"
                font-size="13"
                fill="#1976D2"
                letter-spacing="1.5"
            >
                HARVEST • PROCESS • DELIVER
            </text>

        </svg>
    </div>
    """

    st.markdown(
        logo_html,
        unsafe_allow_html=True,
    )


# ============================================================
# SAFE IMPORT SYSTEM
# ============================================================

module_errors = []


def safe_import(module_path, function_name):
    """
    Safely import a module function.

    Failed modules do not crash the entire ERP application.
    """

    try:

        module = __import__(
            module_path,
            fromlist=[function_name],
        )

        if hasattr(module, function_name):
            return getattr(module, function_name)

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

        logging.exception(
            "Failed loading %s",
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

        admin = (
            db.query(User)
            .filter(User.username == "admin")
            .first()
        )

        if not admin:

            from auth import hash_password

            admin = User(
                username="admin",
                full_name="System Administrator",
                email="admin@nileharvest.com",
                password_hash=hash_password("admin123"),
                role="Administrator",
                active=True,
            )

            db.add(admin)
            db.commit()


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


# ============================================================
# SESSION MANAGEMENT
# ============================================================

if "logged_in" not in st.session_state:

    st.session_state.logged_in = False

    st.session_state.username = None

    st.session_state.role = None

    st.session_state.current_page = (
        "🏠 Overview"
    )


# ============================================================
# LOGIN FUNCTION
# ============================================================

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

            st.session_state.role = (
                user.role
            )

            return True

        return False

    finally:

        db.close()


# ============================================================
# LOGIN SCREEN
# ============================================================

if not st.session_state.logged_in:

    st.markdown(
        '<div class="login-page">',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="login-container">',
        unsafe_allow_html=True,
    )

    # NEW NILE HARVEST LOGO
    render_nile_harvest_logo(
        location="login"
    )

    st.markdown(
        "</div></div>",
        unsafe_allow_html=True,
    )


    # --------------------------------------------------------
    # LOGIN FORM
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


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    # --------------------------------------------------------
    # NEW NILE HARVEST LOGO
    # --------------------------------------------------------

    render_nile_harvest_logo(
        location="sidebar"
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

            st.session_state.current_page = (
                label
            )


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


    # --------------------------------------------------------
    # USER PANEL
    # --------------------------------------------------------

    st.divider()

    st.markdown(
        """
        <div class="user-panel">

            <div class="user-panel-title">
                👤 User Panel
            </div>

        </div>
        """,
        unsafe_allow_html=True,
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

menu = (
    st.session_state.current_page
)


# ============================================================
# ERP ROUTER
# ============================================================

# ------------------------------------------------------------
# OVERVIEW
# ------------------------------------------------------------

if menu == "🏠 Overview":

    if dashboard_home:

        dashboard_home()

    else:

        st.warning(
            "Overview dashboard could not be loaded."
        )


# ------------------------------------------------------------
# PROCUREMENT
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# WAREHOUSE
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# MILLING
# ------------------------------------------------------------

elif menu == "🏭 Milling":

    if milling_dashboard:

        milling_dashboard()

    else:

        st.warning(
            "Milling module unavailable."
        )


# ------------------------------------------------------------
# PACKAGING
# ------------------------------------------------------------

elif menu == "📦 Packaging":

    if packaging_dashboard:

        packaging_dashboard()

    else:

        st.warning(
            "Packaging module unavailable."
        )


# ------------------------------------------------------------
# SALES & DISTRIBUTION
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# FINANCE
# ------------------------------------------------------------

elif menu == "💰 Finance":

    if finance_dashboard:

        finance_dashboard()

    else:

        st.warning(
            "Finance module unavailable."
        )


# ------------------------------------------------------------
# REPORTS
# ------------------------------------------------------------

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
            "The following modules could not be loaded:"
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
    "Enterprise Resource Planning Platform"
)