"""
Esan ERP Controller
Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Version 1.4.0 Alpha – Full Repository Integration

Architecture
------------
streamlit_app.py
    ├── Authentication
    ├── Database initialization
    ├── Sidebar navigation
    ├── Module router
    └── Safe module loading

The Streamlit pages/ directory is NOT required.
All ERP screens are loaded from modules/.
"""

import logging
from typing import Callable, Optional

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
# GLOBAL ERP UI
# ============================================================

st.markdown(
    """
    <style>

    /* ======================================================
       STREAMLIT CLEANUP
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

    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        max-width: 1600px;
    }


    /* ======================================================
       SIDEBAR
       ====================================================== */

    section[data-testid="stSidebar"] {
        background: transparent;
        border: none;
    }

    section[data-testid="stSidebar"] > div {
        background: #f8faf9;
        border-right: 1px solid #dfe5e1;
        box-shadow: 5px 0 20px rgba(0, 0, 0, 0.05);
    }


    /* ======================================================
       SIDEBAR BRAND
       ====================================================== */

    .esan-brand {
        text-align: center;
        padding: 10px 5px 18px 5px;
    }

    .esan-logo {
        font-size: 2.3rem;
        line-height: 1;
    }

    .esan-title {
        font-size: 1.35rem;
        font-weight: 750;
        color: #263238;
        margin-top: 6px;
    }

    .esan-company {
        font-size: 0.72rem;
        color: #718096;
        margin-top: 3px;
    }

    .esan-version {
        display: inline-block;
        margin-top: 8px;
        padding: 3px 9px;
        border-radius: 20px;
        background: #e8f5e9;
        color: #2e7d32;
        font-size: 0.65rem;
        font-weight: 700;
    }


    /* ======================================================
       NAVIGATION
       ====================================================== */

    .nav-section {
        margin: 17px 5px 6px 5px;
        color: #7b817d;
        font-size: 0.67rem;
        font-weight: 750;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    section[data-testid="stSidebar"] .stButton > button {
        width: 100%;
        text-align: left;
        background: transparent;
        color: #374151;
        border: 1px solid transparent;
        border-radius: 9px;
        padding: 9px 12px;
        margin: 2px 0;
        font-size: 0.88rem;
        transition: all 0.15s ease;
    }

    section[data-testid="stSidebar"] .stButton > button:hover {
        background: #e8f5e9;
        border-color: #c8e6c9;
        color: #1b5e20;
    }

    .esan-active-module {
        background: #e8f5e9;
        border: 1px solid #c8e6c9;
        border-radius: 9px;
        color: #1b5e20;
        font-weight: 700;
        padding: 9px 12px;
        margin: 2px 0;
        font-size: 0.88rem;
    }


    /* ======================================================
       USER PANEL
       ====================================================== */

    .esan-user {
        background: white;
        border: 1px solid #e2e8e4;
        border-radius: 10px;
        padding: 11px;
        margin-top: 16px;
    }

    .esan-user-name {
        font-size: 0.86rem;
        font-weight: 700;
        color: #263238;
    }

    .esan-user-role {
        font-size: 0.7rem;
        color: #718096;
        margin-top: 3px;
    }


    /* ======================================================
       MAIN HEADER
       ====================================================== */

    .esan-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: white;
        border: 1px solid #e3e8e5;
        border-radius: 14px;
        padding: 15px 20px;
        margin-bottom: 18px;
        box-shadow: 0 3px 14px rgba(0, 0, 0, 0.035);
    }

    .esan-header-title {
        font-size: 1.45rem;
        font-weight: 750;
        color: #263238;
    }

    .esan-header-subtitle {
        color: #718096;
        font-size: 0.76rem;
        margin-top: 3px;
    }

    .esan-header-module {
        background: #e8f5e9;
        color: #2e7d32;
        padding: 7px 12px;
        border-radius: 20px;
        font-size: 0.74rem;
        font-weight: 700;
        white-space: nowrap;
    }


    /* ======================================================
       MODULE TITLE
       ====================================================== */

    .module-title {
        color: #263238;
        font-size: 1.35rem;
        font-weight: 750;
        margin-bottom: 2px;
    }

    .module-subtitle {
        color: #718096;
        font-size: 0.78rem;
        margin-bottom: 15px;
    }


    /* ======================================================
       LOGIN
       ====================================================== */

    .esan-login-card {
        max-width: 520px;
        margin: 70px auto 20px auto;
        text-align: center;
    }

    .esan-login-logo {
        font-size: 4rem;
        line-height: 1;
    }

    .esan-login-title {
        color: #263238;
        margin: 10px 0 3px 0;
        font-size: 2.1rem;
        font-weight: 750;
    }

    .esan-login-company {
        color: #4a5568;
        margin: 0;
        font-size: 1.15rem;
        font-weight: 600;
    }

    .esan-login-description {
        color: #718096;
        font-size: 0.9rem;
        margin-top: 7px;
    }


    /* ======================================================
       FOOTER
       ====================================================== */

    .esan-footer {
        text-align: center;
        color: #9ca3af;
        font-size: 0.7rem;
        margin-top: 30px;
        padding-bottom: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

DEFAULT_SESSION = {
    "logged_in": False,
    "username": None,
    "full_name": None,
    "role": None,
    "current_page": "🏠 Overview",
    "current_subpage": "Dashboard",
    "seed_loaded": False,
}

for key, value in DEFAULT_SESSION.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# MODULE DIAGNOSTICS
# ============================================================

module_diagnostics = []


# ============================================================
# SAFE MODULE IMPORT
# ============================================================

def safe_import(
    module_path: str,
    function_name: str,
) -> Optional[Callable]:

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
            message = (
                f"{module_path}: "
                f"function '{function_name}' "
                f"was not found"
            )
            module_diagnostics.append(message)
            logger.warning(message)
            return None
        return function
    except Exception as exc:
        message = (
            f"{module_path}: "
            f"{type(exc).__name__}: {exc}"
        )
        module_diagnostics.append(message)
        logger.exception(
            "Optional module failed to load: %s",
            message,
        )
        return None


# ============================================================
# ADMIN SERVICE
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
        if admin:
            return admin
        from auth import hash_password
        admin = User(
            username="admin",
            password_hash=hash_password("admin123"),
            role="Administrator",
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        logger.info("Default administrator created.")
        return admin


# ============================================================
# OPTIONAL SEED DATA
# ============================================================

try:
    from seed.seed_data import load_seed_data
except ImportError:
    load_seed_data = None


# ============================================================
# MODULE REGISTRY
# ============================================================

# --- Dashboard ---
dashboard_home = safe_import(
    "modules.dashboard.home",
    "dashboard_home",
)

# --- Procurement ---
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

# --- Warehouse ---
warehouse_dashboard = safe_import(
    "modules.warehouse.dashboard",
    "warehouse_dashboard",
)
warehouse_inventory = safe_import(
    "modules.warehouse.inventory",
    "inventory_page",
)

# --- Milling & Packaging ---
milling_dashboard = safe_import(
    "modules.milling.dashboard",
    "milling_dashboard",
)
packaging_dashboard = safe_import(
    "modules.packaging.dashboard",
    "packaging_dashboard",
)

# --- Sales ---
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
sales_delivery = safe_import(
    "modules.sales.delivery",
    "delivery_page",
)
sales_payments = safe_import(
    "modules.sales.payments",
    "payments_page",
)

# --- Inline Invoice Page (uses service, not a Streamlit page) ---
def sales_invoice_page():
    st.subheader("🧾 Invoice Management")
    try:
        from database import SessionLocal
        from models import Invoice, SalesOrder

        db = SessionLocal()
        try:
            orders = (
                db.query(SalesOrder)
                .order_by(SalesOrder.created_at.desc())
                .all()
            )
            invoices = (
                db.query(Invoice)
                .order_by(Invoice.created_at.desc())
                .all()
            )

            tab1, tab2 = st.tabs(["Create Invoice", "Invoices"])

            with tab1:
                if not orders:
                    st.info("No sales orders are available.")
                else:
                    order_map = {
                        f"{o.order_number} | {o.status} | {o.total_amount:,.2f}": o.id
                        for o in orders
                    }
                    selected = st.selectbox("Sales Order", list(order_map.keys()))
                    if st.button("Create Invoice", type="primary", key="create_invoice_button"):
                        try:
                            from modules.sales.invoicing import create_invoice
                            invoice = create_invoice(order_map[selected])
                            st.success("Invoice created successfully.")
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Invoice creation failed: {exc}")

            with tab2:
                if not invoices:
                    st.info("No invoices found.")
                else:
                    data = []
                    for inv in invoices:
                        data.append({
                            "Invoice": getattr(inv, "invoice_number", "N/A"),
                            "Customer": getattr(inv, "customer_id", "N/A"),
                            "Amount": getattr(inv, "amount", 0),
                            "Status": getattr(inv, "status", "N/A"),
                            "Date": (
                                inv.created_at.strftime("%Y-%m-%d")
                                if getattr(inv, "created_at", None)
                                else "N/A"
                            ),
                        })
                    import pandas as pd
                    st.dataframe(pd.DataFrame(data), use_container_width=True)
        finally:
            db.close()
    except Exception as exc:
        logger.exception("Invoice module error")
        st.error("Invoice module could not be loaded.")
        with st.expander("Technical details"):
            st.code(str(exc))

# --- Finance ---
finance_dashboard = safe_import(
    "modules.finance.dashboard",
    "finance_dashboard",
)

# --- Reports ---
reports_dashboard = safe_import(
    "modules.reports.dashboard",
    "reports_dashboard",
)


# ============================================================
# MODULE REGISTRY (full definitions)
# ============================================================

MODULES = {
    "🏠 Overview": {
        "title": "Overview",
        "section": "MAIN",
        "function": dashboard_home,
        "children": None,
    },
    "🌾 Procurement": {
        "title": "Procurement",
        "section": "OPERATIONS",
        "function": procurement_dashboard,
        "children": {
            "Dashboard": procurement_dashboard,
            "Suppliers": procurement_suppliers,
            "Purchase Orders": procurement_purchase_orders,
        },
    },
    "📦 Warehouse": {
        "title": "Warehouse",
        "section": "OPERATIONS",
        "function": warehouse_dashboard,
        "children": {
            "Dashboard": warehouse_dashboard,
            "Inventory": warehouse_inventory,
        },
    },
    "🏭 Milling": {
        "title": "Milling",
        "section": "OPERATIONS",
        "function": milling_dashboard,
        "children": None,
    },
    "📦 Packaging": {
        "title": "Packaging",
        "section": "OPERATIONS",
        "function": packaging_dashboard,
        "children": None,
    },
    "🚚 Sales & Distribution": {
        "title": "Sales & Distribution",
        "section": "COMMERCIAL",
        "function": sales_dashboard,
        "children": {
            "Dashboard": sales_dashboard,
            "Customers": sales_customers,
            "Quotations": sales_quotations,
            "Sales Orders": sales_orders,
            "Deliveries": sales_delivery,
            "Invoices": sales_invoice_page,
            "Payments": sales_payments,
        },
    },
    "💰 Finance": {
        "title": "Finance",
        "section": "FINANCE",
        "function": finance_dashboard,
        "children": None,
    },
    "📊 Reports": {
        "title": "Reports",
        "section": "REPORTING",
        "function": reports_dashboard,
        "children": None,
    },
}


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

@st.cache_resource
def initialize_database():
    try:
        inspector = inspect(engine)
        existing_tables = set(inspector.get_table_names())
        required_tables = set(Base.metadata.tables.keys())
        missing_tables = required_tables - existing_tables
        if missing_tables:
            logger.info(
                "Missing ERP tables detected: %s",
                ", ".join(sorted(missing_tables)),
            )
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            create_admin(db)
        finally:
            db.close()
        return True, None
    except Exception as exc:
        logger.exception("Database initialization failed")
        return False, str(exc)


db_ok, db_error = initialize_database()

if not db_ok:
    st.error("❌ Esan ERP could not initialize the database.")
    with st.expander("Technical details"):
        st.code(db_error or "Unknown database error")
    st.stop()


# ============================================================
# SEED DATA (run once)
# ============================================================

if load_seed_data and not st.session_state.seed_loaded:
    try:
        load_seed_data()
        st.session_state.seed_loaded = True
        logger.info("Seed data loaded successfully.")
    except Exception as exc:
        st.session_state.seed_loaded = True
        logger.warning("Seed data failed: %s", exc)


# ============================================================
# AUTHENTICATION
# ============================================================

def login(username: str, password: str) -> bool:
    db = SessionLocal()
    try:
        user = (
            db.query(User)
            .filter(User.username == username)
            .first()
        )
        if not user:
            return False
        if not verify_password(password, user.password_hash):
            return False
        if hasattr(user, "active") and user.active is False:
            return False
        st.session_state.logged_in = True
        st.session_state.username = user.username
        st.session_state.full_name = (
            getattr(user, "full_name", None) or user.username
        )
        st.session_state.role = user.role or "user"
        logger.info("User '%s' logged in.", username)
        return True
    except Exception as exc:
        logger.exception("Login error: %s", exc)
        return False
    finally:
        db.close()


def logout():
    logger.info("User '%s' logged out.", st.session_state.username)
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.full_name = None
    st.session_state.role = None
    st.session_state.current_page = "🏠 Overview"
    st.session_state.current_subpage = "Dashboard"
    st.rerun()


# ============================================================
# LOGIN SCREEN
# ============================================================

if not st.session_state.logged_in:
    st.markdown(
        """
        <div class="esan-login-card">
            <div class="esan-login-logo">🌾</div>
            <div class="esan-login-title">Esan ERP</div>
            <div class="esan-login-company">Nile Harvest Foods Ltd.</div>
            <div class="esan-login-description">
                Enterprise Milling & Packaging Management System
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, center, right = st.columns([1, 1.4, 1])
    with center:
        st.markdown("### 🔐 Sign in")
        username = st.text_input("Username", placeholder="Enter username", key="login_username")
        password = st.text_input("Password", type="password", placeholder="Enter password", key="login_password")
        if st.button("Login", type="primary", use_container_width=True, key="login_button"):
            if login(username.strip(), password):
                st.success("Login successful.")
                st.rerun()
            else:
                st.error("Invalid username or password.")
        st.caption("Default administrator: admin / admin123")
    st.stop()


# ============================================================
# NAVIGATION HELPERS
# ============================================================

def navigate(page: str):
    if page not in MODULES:
        logger.warning("Unknown navigation page: %s", page)
        return
    st.session_state.current_page = page
    st.session_state.current_subpage = "Dashboard"


def navigate_subpage(subpage: str):
    st.session_state.current_subpage = subpage


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown(
        f"""
        <div class="esan-brand">
            <div class="esan-logo">🌾</div>
            <div class="esan-title">Esan ERP</div>
            <div class="esan-company">{COMPANY_NAME}</div>
            <div class="esan-version">Version {VERSION}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # MAIN
    st.markdown('<div class="nav-section">Main</div>', unsafe_allow_html=True)
    current = st.session_state.current_page
    if current == "🏠 Overview":
        st.markdown('<div class="esan-active-module">🏠 &nbsp; Overview</div>', unsafe_allow_html=True)
    else:
        if st.button("🏠  Overview", key="sidebar_overview", use_container_width=True):
            navigate("🏠 Overview")
            st.rerun()

    # OPERATIONS
    st.markdown('<div class="nav-section">Operations</div>', unsafe_allow_html=True)
    for page, key in [("🌾 Procurement", "sidebar_procurement"), ("📦 Warehouse", "sidebar_warehouse"), ("🏭 Milling", "sidebar_milling"), ("📦 Packaging", "sidebar_packaging")]:
        if current == page:
            st.markdown(f'<div class="esan-active-module">{page}</div>', unsafe_allow_html=True)
        else:
            if st.button(page, key=key, use_container_width=True):
                navigate(page)
                st.rerun()

    # COMMERCIAL
    st.markdown('<div class="nav-section">Commercial</div>', unsafe_allow_html=True)
    page = "🚚 Sales & Distribution"
    if current == page:
        st.markdown('<div class="esan-active-module">🚚 &nbsp; Sales & Distribution</div>', unsafe_allow_html=True)
    else:
        if st.button(page, key="sidebar_sales", use_container_width=True):
            navigate(page)
            st.rerun()

    # FINANCE
    st.markdown('<div class="nav-section">Finance</div>', unsafe_allow_html=True)
    page = "💰 Finance"
    if current == page:
        st.markdown('<div class="esan-active-module">💰 &nbsp; Finance</div>', unsafe_allow_html=True)
    else:
        if st.button(page, key="sidebar_finance", use_container_width=True):
            navigate(page)
            st.rerun()

    # REPORTING
    st.markdown('<div class="nav-section">Reporting</div>', unsafe_allow_html=True)
    page = "📊 Reports"
    if current == page:
        st.markdown('<div class="esan-active-module">📊 &nbsp; Reports</div>', unsafe_allow_html=True)
    else:
        if st.button(page, key="sidebar_reports", use_container_width=True):
            navigate(page)
            st.rerun()

    # ADMINISTRATION
    if st.session_state.role == "Administrator":
        st.markdown('<div class="nav-section">Administration</div>', unsafe_allow_html=True)
        st.caption("🔐 Administrator access")

    # USER PANEL
    st.markdown(
        f"""
        <div class="esan-user">
            <div class="esan-user-name">👤 {st.session_state.full_name}</div>
            <div class="esan-user-role">{st.session_state.role}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    if st.button("🚪  Logout", key="sidebar_logout", use_container_width=True):
        logout()


# ============================================================
# CURRENT MODULE
# ============================================================

current_page = st.session_state.current_page
current_module = MODULES.get(current_page)


# ============================================================
# ERP HEADER
# ============================================================

if current_module:
    st.markdown(
        f"""
        <div class="esan-header">
            <div>
                <div class="esan-header-title">🌾 Esan ERP</div>
                <div class="esan-header-subtitle">
                    {COMPANY_NAME} &nbsp;|&nbsp; Enterprise Milling & Packaging Management System
                </div>
            </div>
            <div class="esan-header-module">{current_module["title"]}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# MODULE TITLE
# ============================================================

if current_module:
    st.markdown(
        f"""
        <div class="module-title">{current_module["title"]}</div>
        <div class="module-subtitle">{current_module["title"]} module</div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# SUB-NAVIGATION
# ============================================================

children = current_module.get("children") if current_module else None

if children:
    subpages = list(children.keys())
    current_subpage = st.session_state.current_subpage
    if current_subpage not in subpages:
        current_subpage = subpages[0]
        st.session_state.current_subpage = current_subpage

    columns = st.columns(len(subpages))
    for idx, subpage in enumerate(subpages):
        with columns[idx]:
            is_active = st.session_state.current_subpage == subpage
            if st.button(
                f"✓ {subpage}" if is_active else subpage,
                key=f"subpage_{current_page}_{subpage}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                navigate_subpage(subpage)
                st.rerun()


# ============================================================
# MODULE RENDERER
# ============================================================

def render_module(function: Optional[Callable], name: str):
    if function is None:
        st.warning(f"⚠️ {name} is currently unavailable.")
        return
    try:
        function()
    except Exception as exc:
        logger.exception("Error rendering module '%s': %s", name, exc)
        st.error(f"⚠️ {name} encountered an error.")
        with st.expander("Technical details"):
            st.code(str(exc))


# ============================================================
# ERP ROUTER
# ============================================================

if current_module is None:
    st.error(f"Module '{current_page}' was not found.")
else:
    if children:
        selected_subpage = st.session_state.current_subpage
        selected_function = children.get(selected_subpage)
        render_module(selected_function, f"{current_module['title']} / {selected_subpage}")
    else:
        render_module(current_module["function"], current_module["title"])


# ============================================================
# ADMIN DIAGNOSTICS (hidden from normal users)
# ============================================================

if module_diagnostics and st.session_state.role == "Administrator":
    with st.expander("🔧 Administrator Diagnostics"):
        st.caption("Optional module diagnostics. These do not stop Esan ERP.")
        for msg in module_diagnostics:
            st.write(f"• {msg}")


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    f"""
    <div class="esan-footer">
        © {COMPANY_NAME} &nbsp;|&nbsp; Esan ERP Enterprise Platform &nbsp;|&nbsp; Version {VERSION}
    </div>
    """,
    unsafe_allow_html=True,
)