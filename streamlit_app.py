"""
Nile Harvest Foods Ltd.
Enterprise Resource Planning System

Esan ERP
Version 1.4.0 Alpha
"""

import io
import logging
import os
from datetime import datetime

import streamlit as st
from sqlalchemy import inspect

from config import COMPANY_NAME, VERSION
from database import Base, engine, SessionLocal

# ============================================================
# OPTIONAL MODEL IMPORT
# ============================================================

try:
    from models import User
except Exception as exc:
    User = None
    MODEL_IMPORT_ERROR = str(exc)
else:
    MODEL_IMPORT_ERROR = None


# ============================================================
# AUTH IMPORT
# ============================================================

try:
    from auth import verify_password, hash_password
except Exception as exc:
    verify_password = None
    hash_password = None
    AUTH_IMPORT_ERROR = str(exc)
else:
    AUTH_IMPORT_ERROR = None


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
# CUSTOM NILE HARVEST LOGO
# ============================================================

@st.cache_resource
def create_logo():
    """
    Creates the Nile Harvest Foods corporate logo in memory.

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
        # Corporate colors
        # ----------------------------------------------------

        dark_green = (24, 92, 52, 255)
        green = (46, 125, 50, 255)
        light_green = (129, 199, 132, 255)
        gold = (232, 181, 45, 255)
        brown = (92, 64, 45, 255)
        blue = (38, 111, 145, 255)
        white = (255, 255, 255, 255)

        # ----------------------------------------------------
        # Outer emblem
        # ----------------------------------------------------

        draw.rounded_rectangle(
            (25, 25, 575, 575),
            radius=125,
            fill=dark_green,
        )

        # ----------------------------------------------------
        # Inner emblem
        # ----------------------------------------------------

        draw.rounded_rectangle(
            (45, 45, 555, 555),
            radius=105,
            fill=green,
        )

        # ----------------------------------------------------
        # Golden sun
        # ----------------------------------------------------

        draw.ellipse(
            (185, 105, 415, 335),
            fill=gold,
        )

        # ----------------------------------------------------
        # Nile river
        # ----------------------------------------------------

        river_points = [
            (75, 375),
            (165, 340),
            (245, 365),
            (330, 345),
            (425, 370),
            (525, 335),
            (525, 420),
            (430, 450),
            (335, 425),
            (250, 450),
            (165, 425),
            (75, 455),
        ]

        draw.polygon(
            river_points,
            fill=blue,
        )

        # ----------------------------------------------------
        # Soil
        # ----------------------------------------------------

        draw.rounded_rectangle(
            (45, 445, 555, 555),
            radius=70,
            fill=brown,
        )

        # ----------------------------------------------------
        # Main plant stem
        # ----------------------------------------------------

        draw.rounded_rectangle(
            (292, 235, 308, 475),
            radius=8,
            fill=light_green,
        )

        # ----------------------------------------------------
        # Left leaf
        # ----------------------------------------------------

        draw.ellipse(
            (125, 225, 305, 350),
            fill=light_green,
        )

        # ----------------------------------------------------
        # Right leaf
        # ----------------------------------------------------

        draw.ellipse(
            (295, 225, 475, 350),
            fill=light_green,
        )

        # ----------------------------------------------------
        # Leaf veins
        # ----------------------------------------------------

        draw.line(
            (185, 280, 295, 360),
            fill=green,
            width=9,
        )

        draw.line(
            (415, 280, 305, 360),
            fill=green,
            width=9,
        )

        # ----------------------------------------------------
        # Grain symbols
        # ----------------------------------------------------

        grain_positions = [
            (115, 420),
            (155, 400),
            (195, 430),
            (405, 430),
            (445, 400),
            (485, 420),
        ]

        for x, y in grain_positions:
            draw.ellipse(
                (x, y, x + 22, y + 38),
                fill=gold,
            )

        # ----------------------------------------------------
        # Small central gold seed
        # ----------------------------------------------------

        draw.ellipse(
            (285, 425, 315, 470),
            fill=gold,
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


LOGO_IMAGE = create_logo()


# ============================================================
# UI CSS
# ============================================================

st.markdown(
    """
    <style>

    /* ======================================================
       REMOVE STREAMLIT DEFAULT UI
       ====================================================== */

    #MainMenu {
        visibility: hidden;
    }

    header {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }


    /* ======================================================
       MAIN CONTAINER
       ====================================================== */

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

    .sidebar-logo {
        width: 100%;
        text-align: center;
        padding-top: 8px;
        padding-bottom: 12px;
    }

    .sidebar-logo img {
        max-width: 115px;
        margin: auto;
    }


    /* ======================================================
       LOGIN
       ====================================================== */

    .login-wrapper {
        width: 100%;
        display: flex;
        justify-content: center;
        align-items: center;
        padding-top: 35px;
    }

    .login-logo {
        text-align: center;
        width: 100%;
    }

    .login-logo img {
        width: 185px;
        max-width: 60%;
        height: auto;
        margin: auto;
    }

    .login-title {
        text-align: center;
        font-size: 25px;
        font-weight: 800;
        margin-top: 8px;
        margin-bottom: 3px;
        color: #2e7d32;
    }

    .login-subtitle {
        text-align: center;
        font-size: 14px;
        opacity: 0.7;
        margin-bottom: 25px;
    }


    /* ======================================================
       INPUTS
       ====================================================== */

    div[data-testid="stTextInput"] label {
        font-weight: 600;
    }

    div[data-testid="stTextInput"] input {
        min-height: 46px;
        border-radius: 10px;
    }


    /* ======================================================
       BUTTONS
       ====================================================== */

    div[data-testid="stButton"] > button {
        min-height: 44px;
        border-radius: 10px;
        font-weight: 700;
    }


    /* ======================================================
       SIDEBAR BUTTONS
       ====================================================== */

    div[data-testid="stSidebar"]
    div[data-testid="stButton"]
    > button {

        text-align: left;
        border-radius: 9px;
        margin-bottom: 3px;
    }


    /* ======================================================
       SECTION HEADINGS
       ====================================================== */

    .module-title {
        font-size: 28px;
        font-weight: 800;
        margin-bottom: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SAFE IMPORT SYSTEM
# ============================================================

module_errors = []


def safe_import(module_path, function_name):

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
# PRODUCTION
# ============================================================

milling_dashboard = safe_import(
    "modules.milling.dashboard",
    "milling_dashboard",
)

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
# FALLBACK
# ============================================================

def fallback_page(title):

    def render():

        st.info(
            f"{title} is currently being prepared."
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

        Base.metadata.create_all(
            bind=engine
        )

        if User is None:

            logging.warning(
                "User model could not be imported."
            )

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

                password_hash_value = None

                if hash_password:

                    password_hash_value = (
                        hash_password("admin123")
                    )

                else:

                    logging.error(
                        "hash_password unavailable."
                    )

                    return

                # ------------------------------------------
                # Build User safely.
                #
                # Different versions of models.py may have
                # different User columns.
                # ------------------------------------------

                user_columns = {
                    column.name
                    for column in User.__table__.columns
                }

                user_data = {}

                if "username" in user_columns:
                    user_data["username"] = "admin"

                if "password_hash" in user_columns:
                    user_data["password_hash"] = (
                        password_hash_value
                    )

                if "role" in user_columns:
                    user_data["role"] = "Administrator"

                if "email" in user_columns:
                    user_data["email"] = (
                        "admin@nileharvest.com"
                    )

                if "active" in user_columns:
                    user_data["active"] = True

                if "full_name" in user_columns:
                    user_data["full_name"] = (
                        "System Administrator"
                    )

                if "created_at" in user_columns:
                    user_data["created_at"] = datetime.utcnow()

                admin = User(
                    **user_data
                )

                db.add(admin)
                db.commit()

                logging.info(
                    "Default administrator account created."
                )

        except Exception as exc:

            db.rollback()

            logging.exception(
                "Administrator initialization failed: %s",
                exc,
            )

        finally:

            db.close()

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
# SEED DATA
# ============================================================

try:

    from seed.seed_data import load_seed_data

except Exception:

    load_seed_data = None


if load_seed_data:

    try:

        load_seed_data()

    except Exception as exc:

        logging.warning(
            "Seed data loading failed: %s",
            exc,
        )


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
# LOGIN FUNCTION
# ============================================================

def login(username, password):

    if User is None:

        st.error(
            "The User database model could not be loaded."
        )

        return False

    if verify_password is None:

        st.error(
            "Authentication system could not be loaded."
        )

        return False

    username = (username or "").strip()
    password = password or ""

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
                "Login failed: unknown user '%s'",
                username,
            )

            return False

        active = getattr(
            user,
            "active",
            True,
        )

        if not active:

            logging.warning(
                "Login failed: inactive user '%s'",
                username,
            )

            return False

        password_hash_value = getattr(
            user,
            "password_hash",
            None,
        )

        if not password_hash_value:

            logging.error(
                "User '%s' has no password hash.",
                username,
            )

            return False

        try:

            valid_password = verify_password(
                password,
                password_hash_value,
            )

        except Exception as exc:

            logging.exception(
                "Password verification failed: %s",
                exc,
            )

            return False

        if valid_password:

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
                "Successful login: %s",
                username,
            )

            return True

        logging.warning(
            "Invalid password for user '%s'",
            username,
        )

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
        '<div class="login-wrapper">',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="login-logo">',
        unsafe_allow_html=True,
    )

    if LOGO_IMAGE is not None:

        st.image(
            LOGO_IMAGE,
            width=185,
        )

    else:

        st.markdown(
            """
            <div style="
                text-align:center;
                font-size:90px;
                padding:20px;
            ">
                🌾
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="login-title">
            Nile Harvest Foods Ltd.
        </div>

        <div class="login-subtitle">
            Esan Enterprise Resource Planning System
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        "</div>",
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

    st.stop()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    # --------------------------------------------------------
    # CENTERED LOGO
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
                font-size:65px;
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
    # NAVIGATION
    # --------------------------------------------------------

    def nav_button(label):

        if st.button(
            label,
            use_container_width=True,
            key=f"nav_{label}",
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

    st.markdown(
        '<div class="module-title">🌾 Procurement</div>',
        unsafe_allow_html=True,
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

    st.markdown(
        '<div class="module-title">📦 Warehouse</div>',
        unsafe_allow_html=True,
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

    st.markdown(
        '<div class="module-title">🚚 Sales & Distribution</div>',
        unsafe_allow_html=True,
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
# MODULE ERRORS
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