"""
Nile Harvest Foods Ltd.
Enterprise Resource Planning System

Version 1.4.0 Alpha
Full Repository Integration
"""

import io
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

core_errors = []


try:
    from config import COMPANY_NAME, VERSION
except Exception as exc:
    COMPANY_NAME = "Nile Harvest Foods Ltd."
    VERSION = "1.4.0 Alpha"

    core_errors.append(
        f"config: {type(exc).__name__}: {exc}"
    )

    logging.exception(
        "Unable to import config"
    )


# ------------------------------------------------------------
# DATABASE
# ------------------------------------------------------------

try:
    from database import Base, engine, SessionLocal

except Exception as exc:

    Base = None
    engine = None
    SessionLocal = None

    core_errors.append(
        f"database: {type(exc).__name__}: {exc}"
    )

    logging.exception(
        "Unable to import database"
    )


# ------------------------------------------------------------
# MODELS
#
# IMPORTANT:
# We import the models module first instead of directly doing:
#
#     from models import User
#
# This prevents the application from crashing immediately
# when models.py has another model/import issue.
# ------------------------------------------------------------

models_module = None
User = None

try:

    import models as models_module

    User = getattr(
        models_module,
        "User",
        None,
    )

    if User is None:

        core_errors.append(
            "models: User model was not found."
        )

        logging.error(
            "User model was not found in models.py"
        )

except Exception as exc:

    core_errors.append(
        f"models: {type(exc).__name__}: {exc}"
    )

    logging.exception(
        "Unable to import models.py"
    )


# ------------------------------------------------------------
# AUTH
# ------------------------------------------------------------

try:

    from auth import verify_password

except Exception as exc:

    verify_password = None

    core_errors.append(
        f"auth: {type(exc).__name__}: {exc}"
    )

    logging.exception(
        "Unable to import auth"
    )


# ============================================================
# LOGO GENERATOR
# ============================================================

def create_logo():
    """
    Generate the Nile Harvest Foods logo as a PNG image
    entirely in memory.

    This avoids relying on an external image file.
    """

    try:

        from PIL import Image, ImageDraw

        size = 420

        image = Image.new(
            "RGBA",
            (size, size),
            (0, 0, 0, 0),
        )

        draw = ImageDraw.Draw(image)

        # ----------------------------------------------------
        # Outer rounded square
        # ----------------------------------------------------

        draw.rounded_rectangle(
            (15, 15, size - 15, size - 15),
            radius=85,
            fill=(30, 100, 55, 255),
        )

        # ----------------------------------------------------
        # Inner green area
        # ----------------------------------------------------

        draw.rounded_rectangle(
            (30, 30, size - 30, size - 30),
            radius=70,
            fill=(46, 125, 50, 255),
        )

        # ----------------------------------------------------
        # Gold sunrise
        # ----------------------------------------------------

        draw.ellipse(
            (135, 70, 285, 220),
            fill=(242, 190, 45, 255),
        )

        # ----------------------------------------------------
        # Soil
        # ----------------------------------------------------

        draw.rounded_rectangle(
            (30, 285, size - 30, size - 30),
            radius=60,
            fill=(91, 62, 45, 255),
        )

        # ----------------------------------------------------
        # Plant stem
        # ----------------------------------------------------

        draw.rounded_rectangle(
            (202, 145, 218, 310),
            radius=8,
            fill=(174, 213, 129, 255),
        )

        # ----------------------------------------------------
        # Left leaf
        # ----------------------------------------------------

        draw.ellipse(
            (95, 145, 215, 230),
            fill=(129, 199, 132, 255),
        )

        # ----------------------------------------------------
        # Right leaf
        # ----------------------------------------------------

        draw.ellipse(
            (205, 145, 325, 230),
            fill=(129, 199, 132, 255),
        )

        # ----------------------------------------------------
        # Leaf veins
        # ----------------------------------------------------

        draw.line(
            (155, 190, 205, 230),
            fill=(46, 125, 50, 255),
            width=6,
        )

        draw.line(
            (265, 190, 215, 230),
            fill=(46, 125, 50, 255),
            width=6,
        )

        # ----------------------------------------------------
        # Gold grain symbols
        # ----------------------------------------------------

        grains = [
            (95, 315),
            (125, 300),
            (155, 320),
            (265, 320),
            (295, 300),
            (325, 315),
        ]

        for x, y in grains:

            draw.ellipse(
                (
                    x,
                    y,
                    x + 18,
                    y + 30,
                ),
                fill=(242, 190, 45, 255),
            )

        # ----------------------------------------------------
        # PNG buffer
        # ----------------------------------------------------

        buffer = io.BytesIO()

        image.save(
            buffer,
            format="PNG",
        )

        buffer.seek(0)

        return buffer

    except Exception as exc:

        logging.exception(
            "Unable to generate Nile Harvest logo: %s",
            exc,
        )

        return None


# ============================================================
# CACHE LOGO
# ============================================================

@st.cache_resource
def get_logo():
    return create_logo()


LOGO_IMAGE = get_logo()


# ============================================================
# UI CSS
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
    }


    /* ======================================================
       SIDEBAR
       ====================================================== */

    div[data-testid="stSidebar"] {
        border-right: 1px solid rgba(128,128,128,0.25);
    }

    div[data-testid="stSidebar"] div[data-testid="stButton"] > button {
        text-align: left;
        border-radius: 9px;
        min-height: 42px;
        font-weight: 600;
    }


    /* ======================================================
       LOGO CONTAINERS
       ====================================================== */

    .login-logo-container {

        width: 100%;

        display: flex;

        justify-content: center;

        align-items: center;

        margin-top: 20px;

        margin-bottom: 15px;
    }

    .sidebar-logo-container {

        width: 100%;

        display: flex;

        justify-content: center;

        align-items: center;

        margin-top: 5px;

        margin-bottom: 15px;
    }


    /* ======================================================
       LOGIN
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
       SIDEBAR USER PANEL
       ====================================================== */

    .user-panel {

        padding: 12px;

        border-radius: 12px;

        border: 1px solid rgba(128,128,128,0.20);

        margin-top: 10px;

        margin-bottom: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SAFE MODULE IMPORT SYSTEM
# ============================================================

module_errors = []


def safe_import(module_path, function_name):
    """
    Safely import a module function.

    If a module fails, the entire ERP will continue running.
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
# MODULE REGISTRY
# ============================================================

# ------------------------------------------------------------
# DASHBOARD
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
            f"{title} – "
            "This section is currently being prepared."
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
# ADMIN CREATION
# ============================================================

def create_default_admin(db):
    """
    Creates the default administrator if the User model
    is available and the user does not already exist.
    """

    if User is None:

        logging.warning(
            "User model unavailable. "
            "Administrator creation skipped."
        )

        return

    try:

        admin = (
            db.query(User)
            .filter(
                User.username == "admin"
            )
            .first()
        )

        if admin:

            return

        try:

            from auth import hash_password

        except Exception as exc:

            logging.exception(
                "Unable to import hash_password"
            )

            return

        # ----------------------------------------------------
        # Build only fields that actually exist in User.
        #
        # This prevents errors such as:
        # "full_name is an invalid keyword argument for User"
        # ----------------------------------------------------

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

        if "email" in user_columns:
            values["email"] = (
                "admin@nileharvest.com"
            )

        if "password_hash" in user_columns:
            values["password_hash"] = (
                hash_password("admin123")
            )

        if "role" in user_columns:
            values["role"] = "Administrator"

        if "active" in user_columns:
            values["active"] = True

        admin = User(**values)

        db.add(admin)

        db.commit()

        logging.info(
            "Default administrator created."
        )

    except Exception as exc:

        db.rollback()

        logging.exception(
            "Unable to create default administrator: %s",
            exc,
        )


# ============================================================
# SEED DATA
# ============================================================

try:

    from seed.seed_data import load_seed_data

except Exception as exc:

    load_seed_data = None

    logging.warning(
        "Seed data unavailable: %s",
        exc,
    )


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def initialize_database():

    if engine is None or Base is None:

        logging.error(
            "Database engine/Base unavailable."
        )

        return

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
                "Missing database tables: %s",
                missing_tables,
            )

        Base.metadata.create_all(
            bind=engine
        )

        if SessionLocal is not None:

            db = SessionLocal()

            try:

                create_default_admin(db)

            finally:

                db.close()

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
            "Database initialization failed. "
            "Please check esan_erp.log."
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

    if (
        SessionLocal is None
        or User is None
        or verify_password is None
    ):

        logging.error(
            "Login unavailable because "
            "database/User/auth components are missing."
        )

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

        if not user:

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

        if (
            active
            and password_hash
            and verify_password(
                password,
                password_hash,
            )
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
        '<div class="login-logo-container"></div>',
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # LOGO
    # --------------------------------------------------------

    if LOGO_IMAGE is not None:

        logo_left, logo_center, logo_right = st.columns(
            [1, 1, 1]
        )

        with logo_center:

            st.image(
                LOGO_IMAGE,
                width=145,
            )

    else:

        st.markdown(
            """
            <div style="
                text-align:center;
                font-size:80px;
                margin:20px;
            ">
                🌱
            </div>
            """,
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

        login_clicked = st.button(
            "Login",
            use_container_width=True,
            type="primary",
        )

        if login_clicked:

            if not username or not password:

                st.warning(
                    "Please enter your username "
                    "and password."
                )

            elif login(
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

    st.stop()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    # --------------------------------------------------------
    # LOGO
    # --------------------------------------------------------

    st.markdown(
        '<div class="sidebar-logo-container"></div>',
        unsafe_allow_html=True,
    )

    if LOGO_IMAGE is not None:

        logo_col1, logo_col2, logo_col3 = st.columns(
            [0.6, 1.8, 0.6]
        )

        with logo_col2:

            st.image(
                LOGO_IMAGE,
                width=105,
            )

    else:

        st.markdown(
            """
            <div style="
                text-align:center;
                font-size:60px;
                margin:10px;
            ">
                🌱
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    # --------------------------------------------------------
    # NAVIGATION FUNCTION
    # --------------------------------------------------------

    def nav_button(label):

        if st.button(
            label,
            use_container_width=True,
        ):

            st.session_state.current_page = label

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
# CORE SYSTEM WARNINGS
# ============================================================

if core_errors:

    with st.expander(
        "⚠️ Core System Diagnostics"
    ):

        st.warning(
            "One or more core components "
            "could not be loaded."
        )

        for error in core_errors:

            st.code(
                error
            )


# ============================================================
# MODULE LOADING INFORMATION
# ============================================================

if module_errors:

    with st.expander(
        "⚠️ Module Loading Information"
    ):

        st.warning(
            "Some ERP modules could not be loaded."
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