"""
Esan ERP
Nile Harvest Foods Ltd.
Enterprise Resource Planning System

Version 1.4.0 Alpha
Full Repository Integration

Main Modules
-------------
- Overview
- Procurement
- Warehouse
- Milling
- Packaging
- Sales & Distribution
- Finance
- Reports
- Administration

Sales & Distribution Workflow
------------------------------
Customers
    ↓
Quotations
    ↓
Sales Orders
    ↓
Stock Reservation
    ↓
Deliveries
    ↓
Invoices
    ↓
Payments
    ↓
Finance / General Ledger
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
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# GLOBAL UI
# ============================================================

st.markdown(
    """
    <style>

    /* ======================================================
       STREAMLIT CLEANUP
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

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }

    div[data-testid="stSidebar"] {
        border-right: 1px solid #dddddd;
    }

    /* ======================================================
       LOGIN
       ====================================================== */

    .login-page {
        min-height: 80vh;
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
        width: 112px;
        height: 112px;
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

    .esan-sidebar-logo {
        width: 82px;
        height: 82px;
        margin: 0 auto 12px auto;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .esan-sidebar-logo svg {
        width: 100%;
        height: 100%;
        display: block;
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
        min-height: 44px;
        font-weight: 700;
    }

    /* ======================================================
       ERP HEADERS
       ====================================================== */

    .erp-title {
        font-size: 1.8rem;
        font-weight: 750;
        margin-bottom: 0.15rem;
    }

    .erp-subtitle {
        color: #777777;
        font-size: 0.95rem;
        margin-bottom: 1rem;
    }

    /* ======================================================
       SIDEBAR
       ====================================================== */

    .sidebar-section {
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.06em;
        color: #777777;
        margin-top: 0.8rem;
        margin-bottom: 0.25rem;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# ESAN LOGO
# ============================================================

def render_logo(size="normal"):
    """
    Render the Esan ERP logo as inline SVG.

    size:
        normal  -> Login screen
        sidebar -> Sidebar
    """

    if size == "sidebar":
        css_class = "esan-sidebar-logo"
    else:
        css_class = "esan-logo"

    st.markdown(
        f"""
        <div class="{css_class}">

            <svg
                viewBox="0 0 200 200"
                xmlns="http://www.w3.org/2000/svg"
                role="img"
                aria-label="Esan ERP"
            >

                <!-- Main rounded square -->
                <rect
                    x="8"
                    y="8"
                    width="184"
                    height="184"
                    rx="48"
                    fill="#2E7D32"
                />

                <!-- Inner green highlight -->
                <rect
                    x="18"
                    y="18"
                    width="164"
                    height="164"
                    rx="40"
                    fill="#388E3C"
                    opacity="0.35"
                />

                <!-- Ground / soil -->
                <path
                    d="
                        M8 142
                        Q55 126 100 142
                        Q145 158 192 140
                        L192 192
                        L8 192
                        Z
                    "
                    fill="#4E342E"
                />

                <!-- Stem -->
                <path
                    d="
                        M100 145
                        C98 125 98 105 100 80
                    "
                    stroke="#AED581"
                    stroke-width="8"
                    stroke-linecap="round"
                    fill="none"
                />

                <!-- Left leaf -->
                <path
                    d="
                        M98 105
                        C76 103 58 91 52 72
                        C73 70 92 80 100 96
                        Z
                    "
                    fill="#81C784"
                />

                <!-- Right leaf -->
                <path
                    d="
                        M102 94
                        C113 72 133 62 154 66
                        C151 87 132 101 104 102
                        Z
                    "
                    fill="#A5D66A"
                />

                <!-- Grain / seed -->
                <circle
                    cx="100"
                    cy="57"
                    r="8"
                    fill="#DCE775"
                />

            </svg>

        </div>
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

    Missing or broken optional modules are recorded rather
    than crashing the entire ERP application.
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
            "Failed loading module %s",
            module_path,
        )

        return None


# ============================================================
# ADMIN USER CREATION
# ============================================================

try:

    from services.user_service import create_admin

except Exception:

    def create_admin(db):
        """
        Fallback administrator creation.
        """

        admin = (
            db.query(User)
            .filter(
                User.username == "admin"
            )
            .first()
        )

        if admin:
            return

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
    """
    Generic fallback for unavailable modules.
    """

    def render():

        st.warning(
            f"{title} module is currently unavailable."
        )

        st.caption(
            "Check the Module Loading Information "
            "section below for details."
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

administration_dashboard = (
    administration_dashboard
    or fallback_page("Administration")
)


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def initialize_database():
    """
    Initialize database tables and administrator account.
    """

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
                "Missing database tables detected: %s",
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

        logging.exception(
            "Database initialization failed"
        )

        st.error(
            "Database initialization failed."
        )

        st.caption(
            "Check esan_erp.log for the full error."
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
    """
    Authenticate an ERP user.
    """

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

            logging.info(
                "Successful login: %s",
                user.username,
            )

            return True

        logging.warning(
            "Failed login attempt: %s",
            username,
        )

        return False

    except Exception:

        logging.exception(
            "Login error"
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
        <div class="login-page">
            <div class="login-container">
        """,
        unsafe_allow_html=True,
    )

    render_logo("normal")

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

        login_clicked = st.button(
            "Login",
            use_container_width=True,
            type="primary",
        )

        if login_clicked:

            if login(
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

    # --------------------------------------------------------
    # LOGO
    # --------------------------------------------------------

    render_logo("sidebar")

    st.divider()

    # --------------------------------------------------------
    # NAVIGATION FUNCTION
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
    # OVERVIEW
    # --------------------------------------------------------

    nav_button(
        "🏠 Overview"
    )

    # --------------------------------------------------------
    # OPERATIONS
    # --------------------------------------------------------

    st.markdown(
        '<div class="sidebar-section">'
        "OPERATIONS"
        "</div>",
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
        '<div class="sidebar-section">'
        "COMMERCIAL"
        "</div>",
        unsafe_allow_html=True,
    )

    nav_button(
        "🚚 Sales & Distribution"
    )

    # --------------------------------------------------------
    # FINANCE
    # --------------------------------------------------------

    st.markdown(
        '<div class="sidebar-section">'
        "FINANCE"
        "</div>",
        unsafe_allow_html=True,
    )

    nav_button(
        "💰 Finance"
    )

    # --------------------------------------------------------
    # REPORTING
    # --------------------------------------------------------

    st.markdown(
        '<div class="sidebar-section">'
        "REPORTING"
        "</div>",
        unsafe_allow_html=True,
    )

    nav_button(
        "📊 Reports"
    )

    # --------------------------------------------------------
    # ADMINISTRATION
    # --------------------------------------------------------

    if st.session_state.role in [
        "Administrator",
        "Administrator ",
        "Admin",
        "admin",
    ]:

        st.markdown(
            '<div class="sidebar-section">'
            "ADMINISTRATION"
            "</div>",
            unsafe_allow_html=True,
        )

        nav_button(
            "🔐 Administration"
        )

    # --------------------------------------------------------
    # USER PANEL
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

    st.caption(
        "Suppliers → Purchase Orders → Purchases"
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

    st.caption(
        "Inventory → Stock Movements → "
        "Stock Reservation → Dispatch"
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

    st.header(
        "🏭 Milling"
    )

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

    st.header(
        "📦 Packaging"
    )

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
        "Customers → Quotations → Sales Orders → "
        "Stock Reservation → Deliveries → "
        "Invoices → Payments → Finance"
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

    selected_page = sales_pages.get(
        sales_menu
    )

    if selected_page:

        selected_page()

    else:

        st.warning(
            f"{sales_menu} page is unavailable."
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

    st.header(
        "📊 Reports"
    )

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
        "Administrator ",
        "Admin",
        "admin",
    ]:

        st.error(
            "You do not have permission "
            "to access Administration."
        )

    elif administration_dashboard:

        st.header(
            "🔐 Administration"
        )

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
# FOOTER
# ============================================================

st.divider()

st.caption(
    f"© {COMPANY_NAME} | "
    f"Esan ERP {VERSION} | "
    f"Enterprise Resource Planning Platform"
)