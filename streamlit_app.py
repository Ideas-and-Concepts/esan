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
import hashlib
import hmac

import streamlit as st
from sqlalchemy import inspect, text

from config import COMPANY_NAME, VERSION
from database import Base, engine, SessionLocal


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
# SAFE USER MODEL IMPORT
# ============================================================

User = None
USER_MODEL_ERROR = None

try:
    from models import User

except Exception as exc:
    USER_MODEL_ERROR = (
        f"models.User could not be imported: "
        f"{type(exc).__name__}: {exc}"
    )

    logging.exception(
        "Unable to import User model"
    )


# ============================================================
# SAFE AUTH IMPORT
# ============================================================

try:
    from auth import verify_password

except Exception as exc:

    verify_password = None

    logging.exception(
        "Unable to import verify_password"
    )


try:
    from auth import hash_password

except Exception as exc:

    hash_password = None

    logging.exception(
        "Unable to import hash_password"
    )


# ============================================================
# INLINE ESAN LOGO
# ============================================================

def esan_logo_svg(size=150):
    """
    Returns the Esan / Nile Harvest SVG logo.

    This is deliberately inline SVG so the logo does not depend
    on CSS pseudo-elements, PIL, image files, or static folders.
    """

    size = int(size)

    return f"""
    <div style="
        width:100%;
        display:flex;
        justify-content:center;
        align-items:center;
    ">
        <svg
            width="{size}"
            height="{size}"
            viewBox="0 0 420 420"
            xmlns="http://www.w3.org/2000/svg"
            role="img"
            aria-label="Esan ERP"
        >

            <!-- Outer rounded square -->
            <rect
                x="12"
                y="12"
                width="396"
                height="396"
                rx="82"
                fill="#1B5E20"
            />

            <!-- Main green field -->
            <rect
                x="27"
                y="27"
                width="366"
                height="366"
                rx="68"
                fill="#2E7D32"
            />

            <!-- Gold sunrise -->
            <circle
                cx="210"
                cy="145"
                r="72"
                fill="#F2BE2D"
            />

            <!-- Soil -->
            <path
                d="
                    M27 292
                    Q80 270 135 292
                    Q190 314 245 292
                    Q300 270 393 292
                    L393 325
                    Q393 393 325 393
                    L95 393
                    Q27 393 27 325
                    Z
                "
                fill="#5D4037"
            />

            <!-- Stem -->
            <rect
                x="202"
                y="145"
                width="16"
                height="170"
                rx="8"
                fill="#AED581"
            />

            <!-- Left leaf -->
            <path
                d="
                    M207 220
                    C165 165 108 148 78 181
                    C108 229 159 245 207 220
                    Z
                "
                fill="#81C784"
            />

            <!-- Right leaf -->
            <path
                d="
                    M213 220
                    C255 165 312 148 342 181
                    C312 229 261 245 213 220
                    Z
                "
                fill="#81C784"
            />

            <!-- Leaf veins -->
            <path
                d="M205 220 L120 185"
                stroke="#2E7D32"
                stroke-width="7"
                stroke-linecap="round"
            />

            <path
                d="M215 220 L300 185"
                stroke="#2E7D32"
                stroke-width="7"
                stroke-linecap="round"
            />

            <!-- Gold grain -->
            <ellipse
                cx="95"
                cy="315"
                rx="9"
                ry="16"
                fill="#F2BE2D"
            />

            <ellipse
                cx="125"
                cy="300"
                rx="9"
                ry="16"
                fill="#F2BE2D"
            />

            <ellipse
                cx="155"
                cy="318"
                rx="9"
                ry="16"
                fill="#F2BE2D"
            />

            <ellipse
                cx="265"
                cy="318"
                rx="9"
                ry="16"
                fill="#F2BE2D"
            />

            <ellipse
                cx="295"
                cy="300"
                rx="9"
                ry="16"
                fill="#F2BE2D"
            />

            <ellipse
                cx="325"
                cy="315"
                rx="9"
                ry="16"
                fill="#F2BE2D"
            />

        </svg>
    </div>
    """


def render_logo(size=150):
    """
    Render the logo directly in Streamlit.
    """

    st.markdown(
        esan_logo_svg(size),
        unsafe_allow_html=True,
    )


# ============================================================
# GLOBAL UI
# ============================================================

st.markdown(
    """
    <style>

    /* ======================================================
       HIDE STREAMLIT DEFAULT UI
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


    /* ======================================================
       MAIN CONTENT
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

    div[data-testid="stSidebar"] > div:first-child {
        padding-top: 1rem;
    }


    /* ======================================================
       LOGIN PAGE
       ====================================================== */

    .esan-login-wrapper {
        width: 100%;
        min-height: 30vh;
        display: flex;
        justify-content: center;
        align-items: center;
        flex-direction: column;
        text-align: center;
    }

    .esan-login-brand {
        text-align: center;
        font-size: 2rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        margin-top: 8px;
        margin-bottom: 4px;
    }

    .esan-login-company {
        text-align: center;
        color: #777;
        font-size: 0.9rem;
        margin-bottom: 1.5rem;
    }


    /* ======================================================
       LOGIN INPUTS
       ====================================================== */

    div[data-testid="stTextInput"] label {
        font-weight: 600;
    }

    div[data-testid="stTextInput"] input {
        border-radius: 10px;
        min-height: 46px;
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

    div[data-testid="stSidebar"] div[data-testid="stButton"] > button {
        text-align: left;
        border-radius: 9px;
    }


    /* ======================================================
       SECTION HEADERS
       ====================================================== */

    .erp-title {
        font-size: 1.8rem;
        font-weight: 750;
    }

    .erp-subtitle {
        color: #777;
        font-size: 0.95rem;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# MODULE ERROR REGISTRY
# ============================================================

module_errors = []


if USER_MODEL_ERROR:
    logging.warning(USER_MODEL_ERROR)


# ============================================================
# SAFE MODULE IMPORT
# ============================================================

def safe_import(module_path, function_name):
    """
    Safely import an optional ERP module.
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
            "Failed loading %s",
            module_path,
        )

        return None


# ============================================================
# ADMIN CREATION
# ============================================================

def create_admin_safely():
    """
    Creates the default administrator.

    First attempts to use the User ORM model.
    If the model cannot be imported, attempts a raw SQL
    fallback against the users table.
    """

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # ORM METHOD
        # ----------------------------------------------------

        if User is not None:

            try:

                admin = (
                    db.query(User)
                    .filter(
                        User.username == "admin"
                    )
                    .first()
                )

                if admin is None:

                    if hash_password is None:

                        logging.error(
                            "hash_password is unavailable."
                        )

                        return

                    admin = User(
                        username="admin",
                        password_hash=hash_password(
                            "admin123"
                        ),
                        role="Administrator",
                        active=True,
                    )

                    # Add optional fields only if they
                    # actually exist on the model.

                    if hasattr(
                        User,
                        "full_name",
                    ):

                        admin.full_name = (
                            "System Administrator"
                        )

                    if hasattr(
                        User,
                        "email",
                    ):

                        admin.email = (
                            "admin@nileharvest.com"
                        )

                    db.add(admin)
                    db.commit()

                    logging.info(
                        "Default admin user created."
                    )

                return

            except Exception as exc:

                db.rollback()

                logging.exception(
                    "ORM admin creation failed: %s",
                    exc,
                )

        # ----------------------------------------------------
        # RAW SQL FALLBACK
        # ----------------------------------------------------

        if hash_password is None:

            logging.error(
                "Cannot create fallback admin because "
                "hash_password is unavailable."
            )

            return

        password_hash = hash_password(
            "admin123"
        )

        result = db.execute(
            text(
                "SELECT id FROM users "
                "WHERE username = :username "
                "LIMIT 1"
            ),
            {
                "username": "admin",
            },
        )

        existing_admin = result.first()

        if existing_admin is None:

            db.execute(
                text(
                    """
                    INSERT INTO users
                    (
                        username,
                        password_hash,
                        role,
                        active
                    )
                    VALUES
                    (
                        :username,
                        :password_hash,
                        :role,
                        :active
                    )
                    """
                ),
                {
                    "username": "admin",
                    "password_hash": password_hash,
                    "role": "Administrator",
                    "active": True,
                },
            )

            db.commit()

            logging.info(
                "Fallback admin user created."
            )

    except Exception as exc:

        db.rollback()

        logging.exception(
            "Admin initialization failed: %s",
            exc,
        )

    finally:

        db.close()


# ============================================================
# SEED DATA
# ============================================================

try:

    from seed.seed_data import load_seed_data

except Exception:

    load_seed_data = None

    logging.warning(
        "Seed data module unavailable."
    )


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
# MILLING
# ============================================================

milling_dashboard = safe_import(
    "modules.milling.dashboard",
    "milling_dashboard",
)


# ============================================================
# PACKAGING
# ============================================================

packaging_dashboard = safe_import(
    "modules.packaging.dashboard",
    "packaging_dashboard",
)


# ============================================================
# SALES & DISTRIBUTION
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
# ADMINISTRATION
# ============================================================

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
            "The module could not be loaded. "
            "Check Module Loading Information "
            "below."
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

    try:

        # ----------------------------------------------------
        # Create missing tables
        # ----------------------------------------------------

        Base.metadata.create_all(
            bind=engine
        )

        # ----------------------------------------------------
        # Ensure admin exists
        # ----------------------------------------------------

        create_admin_safely()

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
            "Database initialization failed."
        )

        st.error(
            "Database initialization failed."
        )

        st.caption(
            f"{type(exc).__name__}: {exc}"
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
# PASSWORD VERIFICATION FALLBACK
# ============================================================

def fallback_verify_password(
    password,
    stored_password,
):
    """
    Fallback password verification.

    Supports common SHA-256 style hashes.
    The normal auth.verify_password function
    remains preferred when available.
    """

    if not stored_password:

        return False

    try:

        candidate = hashlib.sha256(
            password.encode("utf-8")
        ).hexdigest()

        return hmac.compare_digest(
            candidate,
            stored_password,
        )

    except Exception:

        return False


# ============================================================
# LOGIN FUNCTION
# ============================================================

def login(username, password):

    username = (
        username or ""
    ).strip()

    password = password or ""

    if not username or not password:

        return False

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # NORMAL ORM LOGIN
        # ----------------------------------------------------

        if User is not None:

            try:

                user = (
                    db.query(User)
                    .filter(
                        User.username == username
                    )
                    .first()
                )

                if user:

                    active = getattr(
                        user,
                        "active",
                        True,
                    )

                    stored_hash = getattr(
                        user,
                        "password_hash",
                        None,
                    )

                    if (
                        active
                        and stored_hash
                    ):

                        password_ok = False

                        if verify_password:

                            try:

                                password_ok = (
                                    verify_password(
                                        password,
                                        stored_hash,
                                    )
                                )

                            except Exception as exc:

                                logging.warning(
                                    "Normal password "
                                    "verification failed: %s",
                                    exc,
                                )

                        if not password_ok:

                            password_ok = (
                                fallback_verify_password(
                                    password,
                                    stored_hash,
                                )
                            )

                        if password_ok:

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

            except Exception as exc:

                db.rollback()

                logging.exception(
                    "ORM login failed: %s",
                    exc,
                )

        # ----------------------------------------------------
        # RAW SQL LOGIN FALLBACK
        # ----------------------------------------------------

        try:

            result = db.execute(
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

            row = result.mappings().first()

            if row:

                active = row.get(
                    "active",
                    True,
                )

                stored_hash = row.get(
                    "password_hash"
                )

                password_ok = False

                if (
                    active
                    and stored_hash
                ):

                    if verify_password:

                        try:

                            password_ok = (
                                verify_password(
                                    password,
                                    stored_hash,
                                )
                            )

                        except Exception:

                            password_ok = False

                    if not password_ok:

                        password_ok = (
                            fallback_verify_password(
                                password,
                                stored_hash,
                            )
                        )

                if password_ok:

                    st.session_state.logged_in = True

                    st.session_state.username = (
                        row.get(
                            "username",
                            username,
                        )
                    )

                    st.session_state.role = (
                        row.get(
                            "role",
                            "User",
                        )
                    )

                    logging.info(
                        "User logged in through "
                        "SQL fallback: %s",
                        username,
                    )

                    return True

        except Exception as exc:

            logging.exception(
                "SQL fallback login failed: %s",
                exc,
            )

        logging.warning(
            "Failed login attempt: %s",
            username,
        )

        return False

    finally:

        db.close()


# ============================================================
# LOGIN PAGE
# ============================================================

if not st.session_state.logged_in:

    # --------------------------------------------------------
    # Centered logo
    # --------------------------------------------------------

    st.markdown(
        '<div class="esan-login-wrapper">',
        unsafe_allow_html=True,
    )

    render_logo(145)

    st.markdown(
        '<div class="esan-login-brand">ESAN</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="esan-login-company">'
        'Nile Harvest Foods Ltd.'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '</div>',
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

    # --------------------------------------------------------
    # Authentication diagnostic
    # --------------------------------------------------------

    if USER_MODEL_ERROR:

        with st.expander(
            "Authentication diagnostics"
        ):

            st.warning(
                "The User ORM model could not be "
                "loaded. Esan is using its database "
                "authentication fallback."
            )

            st.caption(
                USER_MODEL_ERROR
            )

    st.stop()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    # --------------------------------------------------------
    # Centered Esan logo
    # --------------------------------------------------------

    render_logo(95)

    st.markdown(
        """
        <div style="
            text-align:center;
            font-size:1.35rem;
            font-weight:800;
            letter-spacing:0.08em;
            margin-top:-5px;
            margin-bottom:10px;
        ">
            ESAN
        </div>
        """,
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
    # ADMINISTRATION
    # --------------------------------------------------------

    administrator_roles = [
        "Administrator",
        "Admin",
        "admin",
    ]

    if (
        st.session_state.role
        in administrator_roles
    ):

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

    # --------------------------------------------------------
    # LOGOUT
    # --------------------------------------------------------

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

    if (
        st.session_state.role
        not in administrator_roles
    ):

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