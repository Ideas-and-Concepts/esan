"""
Esan ERP Controller
Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Version 1.4.0 Alpha – Full Repository Integration
"""

import logging
from typing import Callable, Optional

import streamlit as st
from sqlalchemy import inspect

from config import COMPANY_NAME, VERSION
from database import Base, engine, SessionLocal
from models import User
from auth import verify_password

# ---------- Logging ----------
logging.basicConfig(
    filename="esan_erp.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("esan_erp")

# ---------- Page config ----------
st.set_page_config(
    page_title="Esan ERP",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Global UI (polished from first version) ----------
st.markdown(
    """
    <style>
    #MainMenu { visibility: hidden; }
    header { visibility: hidden; }
    footer { visibility: hidden; }
    .block-container { padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1600px; }

    section[data-testid="stSidebar"] > div {
        background: #f8faf9;
        border-right: 1px solid #dfe5e1;
    }
    .esan-brand { text-align: center; padding: 10px 5px 18px 5px; }
    .esan-logo { font-size: 2.3rem; line-height: 1; }
    .esan-title { font-size: 1.35rem; font-weight: 750; color: #263238; margin-top: 6px; }
    .esan-company { font-size: 0.72rem; color: #718096; margin-top: 3px; }
    .esan-version { display: inline-block; margin-top: 8px; padding: 3px 9px; border-radius: 20px; background: #e8f5e9; color: #2e7d32; font-size: 0.65rem; font-weight: 700; }
    .esan-header { display: flex; justify-content: space-between; align-items: center; background: white; border: 1px solid #e3e8e5; border-radius: 14px; padding: 15px 20px; margin-bottom: 18px; box-shadow: 0 3px 14px rgba(0,0,0,0.035); }
    .esan-header-title { font-size: 1.45rem; font-weight: 750; color: #263238; }
    .esan-header-subtitle { color: #718096; font-size: 0.76rem; margin-top: 3px; }
    .esan-header-module { background: #e8f5e9; color: #2e7d32; padding: 7px 12px; border-radius: 20px; font-size: 0.74rem; font-weight: 700; }
    .esan-footer { text-align: center; color: #9ca3af; font-size: 0.7rem; margin-top: 30px; padding-bottom: 10px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Session state ----------
for key, val in {
    "logged_in": False,
    "username": None,
    "full_name": None,
    "role": None,
    "current_page": "🏠 Overview",
    "current_subpage": "Dashboard",
    "seed_loaded": False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

module_diagnostics = []

def safe_import(module_path, function_name):
    try:
        mod = __import__(module_path, fromlist=[function_name])
        fn = getattr(mod, function_name, None)
        if fn is None:
            module_diagnostics.append(f"{module_path}: missing {function_name}")
            return None
        return fn
    except Exception as e:
        module_diagnostics.append(f"{module_path}: {e}")
        return None

# ---------- Admin creation ----------
try:
    from services.user_service import create_admin
except ImportError:
    def create_admin(db):
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            from auth import hash_password
            admin = User(username="admin", password_hash=hash_password("admin123"), role="Administrator")
            db.add(admin)
            db.commit()

# ---------- Seed data ----------
try:
    from seed.seed_data import load_seed_data
except ImportError:
    load_seed_data = None

# ---------- Module registry (matching actual repo files) ----------
dashboard_home = safe_import("modules.dashboard.home", "dashboard_home")
procurement_dashboard = safe_import("modules.procurement.dashboard", "procurement_dashboard")
procurement_suppliers = safe_import("modules.procurement.suppliers", "suppliers_page")
procurement_purchase_orders = safe_import("modules.procurement.purchase_orders", "purchase_orders_page")
warehouse_dashboard = safe_import("modules.warehouse.dashboard", "warehouse_dashboard")
warehouse_inventory = safe_import("modules.warehouse.inventory", "inventory_page")
milling_dashboard = safe_import("modules.milling.dashboard", "milling_dashboard")
packaging_dashboard = safe_import("modules.packaging.dashboard", "packaging_dashboard")
sales_dashboard = safe_import("modules.sales.dashboard", "sales_dashboard")
sales_customers = safe_import("modules.sales.customers", "customers_page")
sales_quotations = safe_import("modules.sales.quotations", "quotations_page")
sales_orders = safe_import("modules.sales.orders", "sales_orders_page")
sales_delivery = safe_import("modules.sales.delivery", "delivery_page")
sales_payments = safe_import("modules.sales.payments", "payments_page")

# Inline invoice page (uses invoicing service)
def sales_invoice_page():
    st.subheader("🧾 Invoice Management")
    try:
        from database import SessionLocal
        from models import Invoice, SalesOrder
        db = SessionLocal()
        try:
            orders = db.query(SalesOrder).order_by(SalesOrder.created_at.desc()).all()
            invoices = db.query(Invoice).order_by(Invoice.created_at.desc()).all()
            tab1, tab2 = st.tabs(["Create Invoice", "Invoices"])
            with tab1:
                if not orders:
                    st.info("No sales orders available.")
                else:
                    order_map = {f"{o.order_number} | {o.status} | {o.total_amount:,.2f}": o.id for o in orders}
                    selected = st.selectbox("Sales Order", list(order_map.keys()))
                    if st.button("Create Invoice", type="primary"):
                        from modules.sales.invoicing import create_invoice
                        create_invoice(order_map[selected])
                        st.success("Invoice created.")
                        st.rerun()
            with tab2:
                if not invoices:
                    st.info("No invoices found.")
                else:
                    data = [{"Invoice": getattr(inv, "invoice_number", "N/A"), "Amount": getattr(inv, "amount", 0), "Status": getattr(inv, "status", "N/A")} for inv in invoices]
                    import pandas as pd
                    st.dataframe(pd.DataFrame(data), use_container_width=True)
        finally:
            db.close()
    except Exception as e:
        st.error(f"Invoice module failed: {e}")

finance_dashboard = safe_import("modules.finance.dashboard", "finance_dashboard")
reports_dashboard = safe_import("modules.reports.dashboard", "reports_dashboard")

MODULES = {
    "🏠 Overview": {"title": "Overview", "function": dashboard_home, "children": None},
    "🌾 Procurement": {"title": "Procurement", "function": procurement_dashboard, "children": {"Dashboard": procurement_dashboard, "Suppliers": procurement_suppliers, "Purchase Orders": procurement_purchase_orders}},
    "📦 Warehouse": {"title": "Warehouse", "function": warehouse_dashboard, "children": {"Dashboard": warehouse_dashboard, "Inventory": warehouse_inventory}},
    "🏭 Milling": {"title": "Milling", "function": milling_dashboard, "children": None},
    "📦 Packaging": {"title": "Packaging", "function": packaging_dashboard, "children": None},
    "🚚 Sales & Distribution": {"title": "Sales & Distribution", "function": sales_dashboard, "children": {"Dashboard": sales_dashboard, "Customers": sales_customers, "Quotations": sales_quotations, "Sales Orders": sales_orders, "Deliveries": sales_delivery, "Invoices": sales_invoice_page, "Payments": sales_payments}},
    "💰 Finance": {"title": "Finance", "function": finance_dashboard, "children": None},
    "📊 Reports": {"title": "Reports", "function": reports_dashboard, "children": None},
}

# ---------- Database init ----------
@st.cache_resource
def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        create_admin(db)
        db.close()
        return True, None
    except Exception as e:
        return False, str(e)

db_ok, db_err = init_db()
if not db_ok:
    st.error("Database initialization failed")
    st.code(db_err)
    st.stop()

if load_seed_data and not st.session_state.seed_loaded:
    try:
        load_seed_data()
        st.session_state.seed_loaded = True
    except Exception as e:
        logger.warning(f"Seed failed: {e}")

# ---------- Login ----------
def login(username, password):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user and verify_password(password, user.password_hash):
            if hasattr(user, "active") and user.active is False:
                return False
            st.session_state.logged_in = True
            st.session_state.username = user.username
            st.session_state.full_name = getattr(user, "full_name", None) or user.username
            st.session_state.role = user.role or "user"
            return True
        return False
    finally:
        db.close()

def logout():
    for k in ["logged_in", "username", "full_name", "role"]:
        st.session_state[k] = None
    st.session_state.logged_in = False
    st.session_state.current_page = "🏠 Overview"
    st.session_state.current_subpage = "Dashboard"
    st.rerun()

# ---------- Login screen ----------
if not st.session_state.logged_in:
    st.markdown("""
    <div style="text-align:center; margin-top:8vh;">
        <div style="font-size:4rem;">🌾</div>
        <h1 style="color:#263238;">Esan ERP</h1>
        <h3 style="color:#4a5568;">Nile Harvest Foods Ltd.</h3>
        <p style="color:#718096;">Enterprise Milling & Packaging Management System</p>
    </div>
    """, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("### 🔐 Sign in")
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True, type="primary"):
            if login(u.strip(), p):
                st.success("Login successful")
                st.rerun()
            else:
                st.error("Invalid credentials")
        st.caption("Default: admin / admin123")
    st.stop()

# ---------- Sidebar with buttons (reliable navigation) ----------
with st.sidebar:
    st.markdown(f"""
    <div class="esan-brand">
        <div class="esan-logo">🌾</div>
        <div class="esan-title">Esan ERP</div>
        <div class="esan-company">{COMPANY_NAME}</div>
        <div class="esan-version">Version {VERSION}</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.markdown("### 📋 Navigation")

    # Define navigation button function
    def nav_button(label):
        if st.button(label, use_container_width=True):
            st.session_state.current_page = label
            st.session_state.current_subpage = "Dashboard"
            st.rerun()

    # MAIN
    st.markdown("**MAIN**")
    nav_button("🏠 Overview")

    # OPERATIONS
    st.markdown("**OPERATIONS**")
    nav_button("🌾 Procurement")
    nav_button("📦 Warehouse")
    nav_button("🏭 Milling")
    nav_button("📦 Packaging")

    # COMMERCIAL
    st.markdown("**COMMERCIAL**")
    nav_button("🚚 Sales & Distribution")

    # FINANCE
    st.markdown("**FINANCE**")
    nav_button("💰 Finance")

    # REPORTING
    st.markdown("**REPORTING**")
    nav_button("📊 Reports")

    st.divider()
    st.markdown(f"**👤 {st.session_state.full_name}**")
    st.caption(f"Role: {st.session_state.role}")
    if st.button("🚪 Logout", use_container_width=True):
        logout()

# ---------- Main header ----------
current_page = st.session_state.current_page
cur_mod = MODULES.get(current_page)
if cur_mod:
    st.markdown(f"""
    <div class="esan-header">
        <div>
            <div class="esan-header-title">🌾 Esan ERP</div>
            <div class="esan-header-subtitle">{COMPANY_NAME} | Enterprise Milling & Packaging</div>
        </div>
        <div class="esan-header-module">{cur_mod['title']}</div>
    </div>
    """, unsafe_allow_html=True)

# ---------- Sub-navigation (for modules with children) ----------
children = cur_mod.get("children") if cur_mod else None
if children:
    subpages = list(children.keys())
    cur_sub = st.session_state.current_subpage
    if cur_sub not in subpages:
        cur_sub = subpages[0]
        st.session_state.current_subpage = cur_sub
    cols = st.columns(len(subpages))
    for i, sp in enumerate(subpages):
        with cols[i]:
            if st.button(sp, key=f"sub_{sp}", use_container_width=True,
                         type="primary" if cur_sub == sp else "secondary"):
                st.session_state.current_subpage = sp
                st.rerun()

# ---------- Render module ----------
def render(fn, name):
    if fn is None:
        st.warning(f"⚠️ {name} is not available")
        return
    try:
        fn()
    except Exception as e:
        st.error(f"⚠️ {name} error")
        st.code(str(e))

if cur_mod is None:
    st.error("Module not found")
else:
    if children:
        sel_fn = children.get(st.session_state.current_subpage)
        render(sel_fn, f"{cur_mod['title']} / {st.session_state.current_subpage}")
    else:
        render(cur_mod["function"], cur_mod["title"])

# ---------- Diagnostics (admin only) ----------
if module_diagnostics and st.session_state.role == "Administrator":
    with st.expander("🔧 Diagnostics"):
        for msg in module_diagnostics:
            st.write(f"• {msg}")

# ---------- Footer ----------
st.markdown(f"""
<div class="esan-footer">
    © {COMPANY_NAME} | Esan ERP Enterprise Platform | Version {VERSION}
</div>
""", unsafe_allow_html=True)