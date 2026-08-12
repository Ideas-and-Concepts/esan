"""
Nile Harvest Foods Ltd.
Enterprise Resource Planning System

Version 1.4.0 Alpha
Full Repository Integration

Robust Streamlit Controller
"""

import io
import logging

import streamlit as st
from sqlalchemy import inspect, text

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
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# OPTIONAL USER MODEL
# ============================================================
#
# IMPORTANT:
# models.py must NOT prevent the entire Streamlit application
# from starting.
#
# We therefore load User safely.
# ============================================================

User = None
MODEL_IMPORT_ERROR = None

try:
    from models import User as _User

    User = _User

except Exception as exc:
    MODEL_IMPORT_ERROR = (
        f"{type(exc).__name__}: {exc}"
    )

    logging.exception(
        "Unable to import User model from models.py"
    )


# ============================================================
# CREATE NILE HARVEST LOGO
# ============================================================

def create_logo():
    """
    Generate the Nile Harvest Foods logo as a PNG
    entirely in memory.

    No external image file is required.
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

        for x, y in [
            (95, 315),
            (125, 300),
            (155, 320),
            (265, 320),
            (295, 300),
            (325, 315),
        ]:

            draw.ellipse(
                (x, y, x + 18, y + 30),
                fill=(242, 190, 45, 255),
            )

        # ----------------------------------------------------
        # Convert to PNG
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
# ERP UI
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
    }

    div[data-testid="stSidebar"] {
        border-right: 1px solid rgba(128,128,128,0.25);
    }

    .login-logo-container {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
        margin-top: 30px;
        margin-bottom: 20px;
    }

    .sidebar-logo-container {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
        margin-top: 5px;
        margin-bottom: 15px;
    }

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

    div[data-testid="stSidebar"] div[data-testid="stButton"] > button {
        text-align: left;
        border-radius: 9px;
    }

    div[data-testid="stSidebar"] h3 {
        margin-top: 0.5rem;
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
    """
    Safely import a module function.

    A broken module will not crash the entire ERP.
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

        if function is not None:

            return function

        error = (
            f"{module_path}: "
            f"missing function '{function_name}'"
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
# SEED DATA
# ============================================================

load_seed_data = None

try:

    from seed.seed_data import load_seed_data

except Exception as exc:

    logging.warning(
        "Seed data module unavailable: %s",
        exc,
    )


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
            f"{title} – "
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
    """
    Initialize database safely.

    This function does not require models.py to be
    successfully imported just to start Streamlit.
    """

    try:

        inspector = inspect(engine)

        existing_tables = (
            inspector.get_table_names()
        )

        logging.info(
            "Existing database tables: %s",
            existing_tables,
        )

        # ----------------------------------------------------
        # Create registered SQLAlchemy tables.
        # ----------------------------------------------------

        try:

            Base.metadata.create_all(
                bind=engine
            )

        except Exception as exc:

            logging.warning(
                "Base metadata initialization warning: %s",
                exc,
            )

        # ----------------------------------------------------
        # Ensure users table exists.
        #
        # This is intentionally independent of models.py.
        # ----------------------------------------------------

        if "users" not in existing_tables:

            try:

                with engine.begin() as connection:

                    connection.execute(
                        text(
                            """
                            CREATE TABLE IF NOT EXISTS users (
                                id INTEGER PRIMARY KEY,
                                username VARCHAR(100) UNIQUE NOT NULL,
                                password_hash VARCHAR(255) NOT NULL,
                                role VARCHAR(100),
                                email VARCHAR(255),
                                active BOOLEAN DEFAULT 1,
                                created_at DATETIME
                            )
                            """
                        )
                    )

                logging.info(
                    "Created users table using fallback schema."
                )

            except Exception as exc:

                logging.warning(
                    "Unable to create fallback users table: %s",
                    exc,
                )

        # ----------------------------------------------------
        # Create default admin.
        # ----------------------------------------------------

        ensure_admin_user()

        # ----------------------------------------------------
        # Seed data.
        # ----------------------------------------------------

        if load_seed_data:

            try:

                load_seed_data()

            except TypeError:

                # Some seed functions expect a database session.
                try:

                    db = SessionLocal()

                    try:
                        load_seed_data(db)

                    finally:
                        db.close()

                except Exception as exc:

                    logging.warning(
                        "Seed data could not be loaded: %s",
                        exc,
                    )

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
            "Database initialization encountered an error."
        )

        st.caption(
            f"{type(exc).__name__}: {exc}"
        )


# ============================================================
# ADMIN USER
# ============================================================

def ensure_admin_user():
    """
    Create the default administrator if one does not exist.

    Uses the ORM User model when available.
    Falls back to direct SQL when models.py cannot load.
    """

    # --------------------------------------------------------
    # ORM method
    # --------------------------------------------------------

    if User is not None:

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

                    from auth import hash_password

                    admin = User(
                        username="admin",
                        password_hash=hash_password(
                            "admin123"
                        ),
                        role="Administrator",
                        email="admin@nileharvest.com",
                        active=True,
                    )

                    # ------------------------------------------------
                    # Some versions of the User model may contain
                    # full_name, while others do not.
                    # ------------------------------------------------

                    if hasattr(
                        User,
                        "full_name",
                    ):

                        admin.full_name = (
                            "System Administrator"
                        )

                    db.add(admin)

                    db.commit()

                    logging.info(
                        "Default administrator created."
                    )

                return

            finally:

                db.close()

        except Exception as exc:

            logging.warning(
                "ORM admin creation failed. "
                "Using SQL fallback: %s",
                exc,
            )

    # --------------------------------------------------------
    # SQL fallback method
    # --------------------------------------------------------

    try:

        from auth import hash_password

        password_hash = hash_password(
            "admin123"
        )

        with engine.begin() as connection:

            result = connection.execute(
                text(
                    """
                    SELECT id
                    FROM users
                    WHERE username = :username
                    """
                ),
                {
                    "username": "admin",
                },
            )

            existing_admin = result.first()

            if existing_admin is None:

                connection.execute(
                    text(
                        """
                        INSERT INTO users
                        (
                            username,
                            password_hash,
                            role,
                            email,
                            active
                        )
                        VALUES
                        (
                            :username,
                            :password_hash,
                            :role,
                            :email,
                            :active
                        )
                        """
                    ),
                    {
                        "username": "admin",
                        "password_hash": password_hash,
                        "role": "Administrator",
                        "email": "admin@nileharvest.com",
                        "active": 1,
                    },
                )

                logging.info(
                    "Default administrator created using SQL fallback."
                )

    except Exception as exc:

        logging.error(
            "Unable to create administrator: %s",
            exc,
        )


# ============================================================
# INITIALIZE DATABASE
# ============================================================

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
# LOGIN
# ============================================================

def login(username, password):
    """
    Authenticate user.

    ORM is preferred.
    SQL fallback is used if models.py is unavailable.
    """

    username = (username or "").strip()

    if not username or not password:

        return False

    # --------------------------------------------------------
    # ORM authentication
    # --------------------------------------------------------

    if User is not None:

        try:

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
                    and getattr(
                        user,
                        "active",
                        True,
                    )
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
                        getattr(
                            user,
                            "role",
                            "User",
                        )
                    )

                    return True

            finally:

                db.close()

        except Exception as exc:

            logging.warning(
                "ORM login failed. "
                "Using SQL authentication: %s",
                exc,
            )

    # --------------------------------------------------------
    # SQL fallback authentication
    # --------------------------------------------------------

    try:

        with engine.connect() as connection:

            result = connection.execute(
                text(
                    """
                    SELECT
                        username,
                        password_hash,
                        role,
                        active
                    FROM users
                    WHERE username = :username
                    LIMIT 1
                    """
                ),
                {
                    "username": username,
                },
            )

            user = result.mappings().first()

            if not user:

                return False

            active = user.get(
                "active",
                True,
            )

            if not active:

                return False

            stored_hash = user.get(
                "password_hash"
            )

            if not stored_hash:

                return False

            if verify_password(
                password,
                stored_hash,
            ):

                st.session_state.logged_in = True

                st.session_state.username = (
                    user.get(
                        "username",
                        username,
                    )
                )

                st.session_state.role = (
                    user.get(
                        "role",
                        "User",
                    )
                )

                return True

    except Exception as exc:

        logging.exception(
            "SQL authentication failed."
        )

        st.error(
            "Unable to access the user database."
        )

        st.caption(
            f"{type(exc).__name__}: {exc}"
        )

    return False


# ============================================================
# LOGOUT
# ============================================================

def logout():

    st.session_state.logged_in = False

    st.session_state.username = None

    st.session_state.role = None

    st.session_state.current_page = (
        "🏠 Overview"
    )

    st.rerun()


# ============================================================
# LOGIN PAGE
# ============================================================

if not st.session_state.logged_in:

    st.markdown(
        """
        <div class="login-logo-container"></div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # Logo
    # --------------------------------------------------------

    if LOGO_IMAGE is not None:

        logo_col1, logo_col2, logo_col3 = st.columns(
            [1, 1, 1]
        )

        with logo_col2:

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
                margin-bottom:20px;
            ">
                🌱
            </div>
            """,
            unsafe_allow_html=True,
        )

    # --------------------------------------------------------
    # Login form
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
    # Logo
    # --------------------------------------------------------

    st.markdown(
        """
        <div class="sidebar-logo-container"></div>
        """,
        unsafe_allow_html=True,
    )

    if LOGO_IMAGE is not None:

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
            ">
                🌱
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    # --------------------------------------------------------
    # Navigation helper
    # --------------------------------------------------------

    def nav_button(label):

        if st.button(
            label,
            use_container_width=True,
            key=f"nav_{label}",
        ):

            st.session_state.current_page = label

    # --------------------------------------------------------
    # Overview
    # --------------------------------------------------------

    nav_button(
        "🏠 Overview"
    )

    # --------------------------------------------------------
    # Operations
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
    # Commercial
    # --------------------------------------------------------

    st.markdown(
        "**COMMERCIAL**"
    )

    nav_button(
        "🚚 Sales & Distribution"
    )

    # --------------------------------------------------------
    # Finance
    # --------------------------------------------------------

    st.markdown(
        "**FINANCE**"
    )

    nav_button(
        "💰 Finance"
    )

    # --------------------------------------------------------
    # Reporting
    # --------------------------------------------------------

    st.markdown(
        "**REPORTING**"
    )

    nav_button(
        "📊 Reports"
    )

    st.divider()

    # --------------------------------------------------------
    # User Panel
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

        logout()


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
# MODULE LOADING INFORMATION
# ============================================================

if module_errors:

    with st.expander(
        "⚠️ Module Loading Information"
    ):

        st.warning(
            "Some optional ERP modules could not be loaded."
        )

        for error in module_errors:

            st.write(
                f"• {error}"
            )


# ============================================================
# MODEL WARNING
# ============================================================

if MODEL_IMPORT_ERROR:

    with st.expander(
        "⚠️ Model Loading Information"
    ):

        st.warning(
            "The ORM models.py could not be loaded."
        )

        st.write(
            MODEL_IMPORT_ERROR
        )

        st.info(
            "The ERP controller is running using "
            "its database fallback where possible. "
            "The models.py issue should be corrected "
            "before all ORM-dependent modules are used."
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