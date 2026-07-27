"""
Esan ERP Controller
Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Version 1.2.0 Alpha
"""

import streamlit as st
from config import COMPANY_NAME, VERSION
from database import Base, engine, SessionLocal
from models import User
from auth import verify_password

# =====================================
# CRITICAL SERVICE / COMPONENT IMPORTS
# =====================================
try:
    from services.user_service import create_admin
except ImportError:
    def create_admin(db):
        """Fallback: create default admin if missing."""
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            from auth import hash_password
            admin = User(
                username="admin",
                password_hash=hash_password("admin123"),
                role="admin",
                email="admin@nileharvest.com"
            )
            db.add(admin)
            db.commit()

try:
    from components.themes import esan_theme
except ImportError:
    def esan_theme(theme):
        pass

# =====================================
# OPTIONAL SEED DATA
# =====================================
try:
    from seed.seed_data import load_seed_data
except ImportError:
    load_seed_data = None

# =====================================
# MODULE IMPORTS (with fallbacks)
# =====================================
module_functions = {
    "Overview": None,
    "🌾 Procurement": None,
    "📦 Warehouse": None,
    "🏭 Milling": None,
    "📦 Packaging": None,
    "🚚 Sales": None,
    "💰 Finance": None,
    "📊 Reports": None,
}

try:
    from modules.dashboard.home import dashboard_home
    module_functions["Overview"] = dashboard_home
except ImportError:
    pass

try:
    from modules.procurement.dashboard import procurement_dashboard
    module_functions["🌾 Procurement"] = procurement_dashboard
except ImportError:
    pass

try:
    from modules.warehouse.dashboard import warehouse_dashboard
    module_functions["📦 Warehouse"] = warehouse_dashboard
except ImportError:
    pass

try:
    from modules.milling.dashboard import milling_dashboard
    module_functions["🏭 Milling"] = milling_dashboard
except ImportError:
    pass

try:
    from modules.packaging.dashboard import packaging_dashboard
    module_functions["📦 Packaging"] = packaging_dashboard
except ImportError:
    pass

# Sales has sub‑modules – we'll keep a simplified entry
try:
    from modules.sales.dashboard import sales_dashboard
    module_functions["🚚 Sales"] = sales_dashboard
except ImportError:
    pass

try:
    from modules.finance.dashboard import finance_dashboard
    module_functions["💰 Finance"] = finance_dashboard
except ImportError:
    pass

try:
    from modules.reports.dashboard import reports_dashboard
    module_functions["📊 Reports"] = reports_dashboard
except ImportError:
    pass

# =====================================
# PAGE CONFIGURATION
# =====================================
st.set_page_config(page_title="Esan ERP", page_icon="🌾", layout="wide")

# Clean Streamlit UI
st.markdown("""
<style>
#MainMenu {display:none;}
footer {display:none;}
header {display:none;}

/* Make room for the bottom navigation bar */
.main > div {
    padding-bottom: 90px;
}

/* Bottom navigation container */
.bottom-nav {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background-color: #f0f2f6;
    padding: 10px 20px;
    box-shadow: 0px -2px 5px rgba(0,0,0,0.1);
    z-index: 999;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.bottom-nav button {
    font-size: 14px !important;
    padding: 8px 10px !important;
    border-radius: 8px !important;
    background: none !important;
    border: none !important;
    color: #333 !important;
    transition: 0.2s;
}
.bottom-nav button:hover {
    background: #e0e4e8 !important;
}
.bottom-nav .active {
    background: #d0d5dd !important;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# =====================================
# DATABASE INITIALIZATION
# =====================================
try:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        create_admin(db)
    finally:
        db.close()
    if load_seed_data:
        load_seed_data()
except Exception as e:
    st.error("Database initialization failed")
    st.exception(e)

# =====================================
# SESSION STATE
# =====================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None
    st.session_state.page = "Overview"  # default page

# =====================================
# LOGIN FUNCTION
# =====================================
def login(username, password):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user and verify_password(password, user.password_hash):
            st.session_state.logged_in = True
            st.session_state.username = user.username
            st.session_state.role = user.role
            return True
        return False
    finally:
        db.close()

# =====================================
# LOGIN SCREEN
# =====================================
if not st.session_state.logged_in:
    st.markdown("""
    <div style="text-align:center">
    <h1>🌾 Esan ERP</h1>
    <h3>Nile Harvest Foods Ltd.</h3>
    <p>Enterprise Milling & Packaging Management System</p>
    </div>
    """, unsafe_allow_html=True)

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if login(username, password):
            st.success("Login successful")
            st.rerun()
        else:
            st.error("Invalid username or password")

    st.info("Default administrator: admin / admin123")
    st.stop()

# =====================================
# APPLICATION HEADER (after login)
# =====================================
st.title("🌾 Esan ERP")
st.caption(f"{COMPANY_NAME} | Version {VERSION}")

# =====================================
# SIDEBAR: USER & THEME (still in sidebar, not bottom)
# =====================================
st.sidebar.success(f"User: {st.session_state.username}")
st.sidebar.info(f"Role: {st.session_state.role}")

theme = st.sidebar.selectbox("Appearance", ["Light", "Dark"])
esan_theme(theme)

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None
    st.rerun()

# =====================================
# ROUTING BASED ON CURRENT PAGE
# =====================================
current_page = st.session_state.page
func = module_functions.get(current_page)
if func:
    func()
else:
    if current_page == "🚚 Sales":
        # Sales might have sub‑modules; we can integrate later
        st.header("🚚 Sales & Distribution")
        st.info("Sales module is under development.")
    else:
        st.info(f"{current_page} module not available yet.")

# =====================================
# BOTTOM NAVIGATION BAR
# =====================================
st.markdown('<div class="bottom-nav">', unsafe_allow_html=True)

# Define menu items (label, icon)
menu_items = [
    ("Overview", "🏠"),
    ("🌾 Procurement", "🌾"),
    ("📦 Warehouse", "📦"),
    ("🏭 Milling", "🏭"),
    ("📦 Packaging", "📦"),
    ("🚚 Sales", "🚚"),
    ("💰 Finance", "💰"),
    ("📊 Reports", "📊"),
]

cols = st.columns(len(menu_items))
for i, (label, icon) in enumerate(menu_items):
    # Highlight active page
    if st.session_state.page == label:
        cols[i].markdown(f'<button class="active">{icon} {label.split()[-1]}</button>', unsafe_allow_html=True)
    else:
        if cols[i].button(f"{icon} {label.split()[-1]}"):
            st.session_state.page = label
            st.rerun()

st.markdown('</div>', unsafe_allow_html=True)