"""
Nile Harvest Foods Ltd.
Enterprise Resource Planning System

Esan ERP
Version 1.4.0 Alpha

Full Repository Integration
"""

import io
import logging
import importlib

import streamlit as st
from sqlalchemy import inspect

from config import COMPANY_NAME, VERSION
from database import Base, engine, SessionLocal
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
# SAFE MODEL LOADING
# ============================================================

User = None
MODEL_ERROR = None

try:
    models_module = importlib.import_module("models")

    User = getattr(
        models_module,
        "User",
        None,
    )

    if User is None:
        MODEL_ERROR = (
            "The models.py file was loaded, "
            "but it does not contain a User model."
        )

except Exception as exc:
    MODEL_ERROR = (
        f"Unable to load models.py: "
        f"{type(exc).__name__}: {exc}"
    )

    logging.exception(
        "Unable to load models.py"
    )


# ============================================================
# NEW NILE HARVEST LOGO
# ============================================================

def create_logo():
    """
    Generate the Nile Harvest Foods logo completely in memory.

    No external image file is required.
    """

    try:
        from PIL import Image, ImageDraw

        size = 600

        image = Image.new(
            "RGBA",
            (size, size),
            (0, 0, 0, 0),
        )

        draw = ImageDraw.Draw(image)

        # ----------------------------------------------------
        # Outer badge
        # ----------------------------------------------------

        draw.rounded_rectangle(
            (15, 15, 585, 585),
            radius=125,
            fill=(27, 94, 32, 255),
        )

        # ----------------------------------------------------
        # Inner badge
        # ----------------------------------------------------

        draw.rounded_rectangle(
            (35, 35, 565, 565),
            radius=105,
            fill=(46, 125, 50, 255),
        )

        # ----------------------------------------------------
        # Golden sun
        # ----------------------------------------------------

        draw.ellipse(
            (190, 85, 410, 305),
            fill=(242, 190, 45, 255),
        )

        # ----------------------------------------------------
        # Horizon
        # ----------------------------------------------------

        draw.rectangle(
            (55, 275, 545, 330),
            fill=(129, 199, 132, 255),
        )

        # ----------------------------------------------------
        # Nile water
        # ----------------------------------------------------

        draw.rounded_rectangle(
            (55, 310, 545, 400),
            radius=35,
            fill=(30, 105, 150, 255),
        )

        # ----------------------------------------------------
        # Water highlights
        # ----------------------------------------------------

        for y in (335, 365):

            draw.line(
                (100, y, 500, y),
                fill=(144, 202, 249, 255),
                width=7,
            )

        # ----------------------------------------------------
        # Soil
        # ----------------------------------------------------

        draw.rounded_rectangle(
            (55, 395, 545, 545),
            radius=45,
            fill=(91, 62, 45, 255),
        )

        # ----------------------------------------------------
        # Plant stem
        # ----------------------------------------------------

        draw.rounded_rectangle(
            (292, 205, 308, 440),
            radius=8,
            fill=(174, 213, 129, 255),
        )

        # ----------------------------------------------------
        # Left leaf
        # ----------------------------------------------------

        draw.ellipse(
            (145, 220, 310, 335),
            fill=(129, 199, 132, 255),
        )

        # ----------------------------------------------------
        # Right leaf
        # ----------------------------------------------------

        draw.ellipse(
            (290, 220, 455, 335),
            fill=(129, 199, 132, 255),
        )

        # ----------------------------------------------------
        # Left leaf vein
        # ----------------------------------------------------

        draw.line(
            (180, 275, 300, 335),
            fill=(46, 125, 50, 255),
            width=9,
        )

        # ----------------------------------------------------
        # Right leaf vein
        # ----------------------------------------------------

        draw.line(
            (420, 275, 300, 335),
            fill=(46, 125, 50, 255),
            width=9,
        )

        # ----------------------------------------------------
        # Grain symbols
        # ----------------------------------------------------

        grain_positions = [
            (120, 440),
            (165, 415),
            (205, 450),
            (395, 450),
            (435, 415),
            (480, 440),
        ]

        for x, y in grain_positions:

            draw.ellipse(
                (x, y, x + 22, y + 38),
                fill=(242, 190, 45, 255),
            )

        # ----------------------------------------------------
        # Small gold center
        # ----------------------------------------------------

        draw.ellipse(
            (280, 430, 320, 470),
            fill=(242, 190, 45, 255),
        )

        # ----------------------------------------------------
        # Export PNG
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
            "Logo generation failed: %s",
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
# ERP UI
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

    header {
        display: none;
    }

    footer {
        display: none;
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }


    /* ======================================================
       SIDEBAR
       ====================================================== */

    div[data-testid="stSidebar"] {
        border-right: 1px solid rgba(128,128,128,0.25);
    }


    /* ======================================================
       LOGIN PAGE
       ====================================================== */

    .login-page {
        width: 100%;
        min-height: 78vh;

        display: flex;
        flex-direction: column;

        justify-content: flex-start;
        align-items: center;

        padding-top: 35px;
    }


    .login-logo {
        display: flex;
        justify-content: center;
        align-items: center;

        width: 100%;

        margin-bottom: 25px;
    }


    .login-form {
        width: 100%;
        max-width: 430px;

        margin-left: auto;
        margin-right: auto;
    }


    /* ======================================================
       SIDEBAR LOGO
       ====================================================== */

    .sidebar-logo {
        display: flex;
        justify-content: center;
        align-items: center;

        width: 100%;

        padding-top: 8px;
        padding-bottom: 10px;
    }


    /* ======================================================
       INPUTS
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
    div[data-testid="stButton"] > button {

        text-align: left;
        border-radius: 9px;

        margin-bottom: 2px;
    }


    /* ======================================================
       SIDEBAR SECTION HEADINGS
       ====================================================== */

    div[data-testid="stSidebar"] h3 {
        margin-top: 0.5rem;
    }


    /* ======================================================
       LOGIN TITLE
       ====================================================== */

    .login-title {
        text-align: center;

        font-size: 28px;
        font-weight: 800;

        margin-top: 5px;
        margin-bottom: 4px;
    }


    .login-subtitle {
        text-align: center;

        font-size: 14px;

        opacity: 0.7;

        margin-bottom: 22px;
    }


    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SAFE IMPORT SYSTEM
# ============================================================

module_errors = []


def safe_import(
    module_path,
    function_name,
):
    """
    Safely import a module function.

    A broken module will not crash
    the entire ERP application.
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

        if function is not None:

            return function

        error = (
            f"{module_path}: "
            f"missing function "
            f"'{function_name}'"
        )

        module_errors.append(error)

        logging.error(error)

        return None

    except Exception as exc:

        error = (
            f"{module_path}: "
            f"{type(exc).__name__}: "
            f"{exc}"
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

def create_default_admin(db):
    """
    Creates the default administrator.

    The function checks which User fields actually exist
    before passing values to SQLAlchemy.
    """

    if User is None:
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

        from auth import hash_password

        password_hash = hash_password(
            "admin123"
        )

        user_columns = {
            column.name
            for column in User.__table__.columns
        }

        user_data = {}

        if "username" in user_columns:
            user_data["username"] = "admin"

        if "password_hash" in user_columns:
            user_data["password_hash"] = (
                password_hash
            )

        if "full_name" in user_columns:
            user_data["full_name"] = (
                "System Administrator"
            )

        if "email" in user_columns:
            user_data["email"] = (
                "admin@nileharvest.com"
            )

        if "role" in user_columns:
            user_data["role"] = (
                "Administrator"
            )

        if "active" in user_columns:
            user_data["active"] = True

        admin = User(
            **user_data
        )

        db.add(admin)

        db.commit()

        logging.info(
            "Default administrator created."
        )

    except Exception as exc:

        db.rollback()

        logging.exception(
            "Admin creation failed: %s",
            exc,
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

    logging.warning(
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

def fallback_page(title):

    def render():

        st.info(
            f"{title} - "
            "This section is currently being prepared."
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


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def initialize_database():

    try:

        if engine is None:

            logging.error(
                "Database engine is unavailable."
            )

            return

        inspector = inspect(
            engine
        )

        existing_tables = (
            inspector.get_table_names()
        )

        missing_tables = [
            table_name
            for table_name in Base.metadata.tables
            if table_name
            not in existing_tables
        ]

        if missing_tables:

            logging.info(
                "Creating missing tables: %s",
                missing_tables,
            )

        Base.metadata.create_all(
            bind=engine
        )

        if User is not None:

            db = SessionLocal()

            try:

                create_default_admin(
                    db
                )

            finally:

                db.close()

        if load_seed_data:

            try:

                load_seed_data()

            except TypeError:

                # Some seed functions accept a database
                # session while others do not.
                db = SessionLocal()

                try:

                    load_seed_data(db)

                finally:

                    db.close()

            except Exception as exc:

                logging.warning(
                    "Seed data failed: %s",
                    exc,
                )

    except Exception as exc:

        logging.exception(
            "Database initialization failed."
        )

        st.error(
            "Database initialization failed."
        )

        with st.expander(
            "Database Error Details"
        ):

            st.code(
                str(exc)
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

def login(
    username,
    password,
):
    """
    Authenticate a user safely.
    """

    if User is None:

        logging.error(
            "Login attempted but User model "
            "is unavailable."
        )

        return False, (
            "User model could not be loaded."
        )

    if not username or not password:

        return False, (
            "Please enter your username "
            "and password."
        )

    db = SessionLocal()

    try:

        user = (
            db.query(User)
            .filter(
                User.username == username.strip()
            )
            .first()
        )

        if user is None:

            logging.warning(
                "Login failed for unknown user: %s",
                username,
            )

            return False, (
                "Invalid username or password."
            )

        active = getattr(
            user,
            "active",
            True,
        )

        if not active:

            return False, (
                "This user account is inactive."
            )

        stored_hash = getattr(
            user,
            "password_hash",
            None,
        )

        if not stored_hash:

            logging.error(
                "User %s has no password_hash.",
                username,
            )

            return False, (
                "This user does not have "
                "a valid password configured."
            )

        try:

            valid_password = verify_password(
                password,
                stored_hash,
            )

        except Exception as exc:

            logging.exception(
                "Password verification failed."
            )

            return False, (
                f"Password verification error: "
                f"{exc}"
            )

        if not valid_password:

            logging.warning(
                "Invalid password for user: %s",
                username,
            )

            return False, (
                "Invalid username or password."
            )

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

        return True, "Login successful."

    except Exception as exc:

        logging.exception(
            "Login error."
        )

        return False, (
            f"Login error: {exc}"
        )

    finally:

        db.close()


# ============================================================
# LOGIN PAGE
# ============================================================

if not st.session_state.logged_in:

    # --------------------------------------------------------
    # CENTERED LOGIN AREA
    # --------------------------------------------------------

    st.markdown(
        '<div class="login-page">',
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # CENTERED LOGO
    # --------------------------------------------------------

    st.markdown(
        '<div class="login-logo">',
        unsafe_allow_html=True,
    )

    if LOGO_IMAGE is not None:

        st.image(
            LOGO_IMAGE,
            width=180,
        )

    else:

        st.markdown(
            """
            <div style="
                text-align:center;
                font-size:90px;
            ">
                🌾
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # LOGIN TITLE
    # --------------------------------------------------------

    st.markdown(
        """
        <div class="login-title">
            Esan ERP
        </div>

        <div class="login-subtitle">
            Nile Harvest Foods Ltd.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # LOGIN FORM
    # --------------------------------------------------------

    login_left, login_center, login_right = st.columns(
        [1, 2, 1]
    )

    with login_center:

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

            success, message = login(
                username,
                password,
            )

            if success:

                st.success(
                    message
                )

                st.rerun()

            else:

                st.error(
                    message
                )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # MODEL ERROR INFORMATION
    # --------------------------------------------------------

    if MODEL_ERROR:

        with st.expander(
            "⚠️ System Configuration"
        ):

            st.warning(
                MODEL_ERROR
            )

    st.stop()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    # --------------------------------------------------------
    # CENTERED SIDEBAR LOGO
    # --------------------------------------------------------

    st.markdown(
        '<div class="sidebar-logo">',
        unsafe_allow_html=True,
    )

    if LOGO_IMAGE is not None:

        st.image(
            LOGO_IMAGE,
            width=115,
        )

    else:

        st.markdown(
            """
            <div style="
                text-align:center;
                font-size:60px;
            ">
                🌾
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        "</div>",
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

    page_function = sales_pages.get(
        sales_menu
    )

    if page_function:

        page_function()

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