"""
Esan ERP Controller
Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Version 1.3.0 Alpha
"""

import streamlit as st
import os
import logging
from datetime import datetime
from sqlalchemy import inspect

from config import COMPANY_NAME, VERSION
from database import Base, engine, SessionLocal, DATABASE_URL
from models import User
from auth import verify_password


# ==================================================
# LOGGING
# ==================================================

logging.basicConfig(
    filename="esan_erp.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Esan ERP",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==================================================
# CLEAN UI
# ==================================================

st.markdown(
    """
    <style>

    #MainMenu {
        display:none;
    }

    footer {
        display:none;
    }

    header {
        display:none;
    }

    .block-container {
        padding-top:2rem;
        padding-bottom:1rem;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ==================================================
# SAFE MODULE IMPORT SYSTEM
# ==================================================

module_errors = []


def safe_import(module_path, function_name):

    try:

        module = __import__(
            module_path,
            fromlist=[function_name]
        )

        if hasattr(module, function_name):

            return getattr(
                module,
                function_name
            )

        module_errors.append(
            f"{module_path}: Missing {function_name}"
        )

        return None


    except Exception as e:

        module_errors.append(
            f"{module_path}: {str(e)}"
        )

        logging.error(
            f"{module_path} failed: {e}"
        )

        return None



# ==================================================
# ADMIN CREATION
# ==================================================

try:

    from services.user_service import create_admin


except ImportError:


    def create_admin(db):

        admin = (
            db.query(User)
            .filter(
                User.username=="admin"
            )
            .first()
        )


        if not admin:

            from auth import hash_password


            admin = User(

                username="admin",

                password_hash=
                hash_password(
                    "admin123"
                ),

                role="Administrator",

                full_name=
                "System Administrator",

                email=
                "admin@nileharvest.com"

            )


            db.add(admin)

            db.commit()



# ==================================================
# SEED DATA
# ==================================================

try:

    from seed.seed_data import load_seed_data


except ImportError:

    load_seed_data = None



# ==================================================
# MODULE REGISTRY
# ==================================================

dashboard_home = safe_import(
    "modules.dashboard.home",
    "dashboard_home"
)


procurement_dashboard = safe_import(
    "modules.procurement.dashboard",
    "procurement_dashboard"
)


warehouse_dashboard = safe_import(
    "modules.warehouse.dashboard",
    "warehouse_dashboard"
)


milling_dashboard = safe_import(
    "modules.milling.dashboard",
    "milling_dashboard"
)


packaging_dashboard = safe_import(
    "modules.packaging.dashboard",
    "packaging_dashboard"
)


sales_dashboard = safe_import(
    "modules.sales.dashboard",
    "sales_dashboard"
)


customers_page = safe_import(
    "modules.sales.customers",
    "customers_page"
)


quotations_page = safe_import(
    "modules.sales.quotations",
    "quotations_page"
)


sales_orders_page = safe_import(
    "modules.sales.orders",
    "sales_orders_page"
)


delivery_page = safe_import(
    "modules.sales.delivery",
    "delivery_page"
)


dispatch_page = safe_import(
    "modules.sales.dispatch",
    "dispatch_page"
)


finance_dashboard = safe_import(
    "modules.finance.dashboard",
    "finance_dashboard"
)


invoices_page = safe_import(
    "modules.finance.invoices",
    "invoices_page"
)


payments_page = safe_import(
    "modules.finance.payments",
    "payments_page"
)


reports_dashboard = safe_import(
    "modules.reports.dashboard",
    "reports_dashboard"
)


logistics_dashboard = safe_import(
    "modules.logistics.dashboard",
    "logistics_dashboard"
)


hr_dashboard = safe_import(
    "modules.hr.dashboard",
    "hr_dashboard"
)


maintenance_dashboard = safe_import(
    "modules.maintenance.dashboard",
    "maintenance_dashboard"
)


ai_assistant_page = safe_import(
    "modules.ai_assistant.ai_page",
    "ai_assistant_page"
)


user_management_page = safe_import(
    "modules.administration.user_management",
    "user_management_page"
)


change_password_page = safe_import(
    "modules.administration.change_password",
    "change_password_page"
)

# ==================================================
# DATABASE INITIALIZATION
# ==================================================

def initialize_database():

    try:

        inspector = inspect(engine)

        existing_tables = (
            inspector.get_table_names()
        )


        missing_tables = []

        for table_name in Base.metadata.tables:

            if table_name not in existing_tables:

                missing_tables.append(
                    table_name
                )


        if missing_tables:

            st.warning(
                "🔄 Creating missing ERP database tables..."
            )

            Base.metadata.create_all(
                bind=engine
            )


        else:

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
                    f"Seed loading failed: {e}"
                )


    except Exception as e:

        logging.error(
            f"Database initialization error: {e}"
        )

        st.error(
            "Database initialization failed"
        )



initialize_database()



# ==================================================
# SESSION MANAGEMENT
# ==================================================

if "logged_in" not in st.session_state:

    st.session_state.logged_in = False

    st.session_state.username = None

    st.session_state.role = None



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


        if user and verify_password(
            password,
            user.password_hash
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



# ==================================================
# LOGIN SCREEN
# ==================================================

if not st.session_state.logged_in:


    st.markdown(
        """
        <div style="text-align:center">

        <h1>🌾 Esan ERP</h1>

        <h3>Nile Harvest Foods Ltd.</h3>

        <p>
        Enterprise Milling & Packaging Management System
        </p>

        </div>
        """,
        unsafe_allow_html=True
    )


    col1, col2, col3 = st.columns(
        [1,2,1]
    )


    with col2:

        username = st.text_input(
            "Username"
        )


        password = st.text_input(
            "Password",
            type="password"
        )


        if st.button(
            "Login",
            use_container_width=True
        ):


            if login(
                username,
                password
            ):

                st.success(
                    "Login successful"
                )

                st.rerun()


            else:

                st.error(
                    "Invalid username or password"
                )


        st.info(
            "Default administrator: admin / admin123"
        )


    st.stop()



# ==================================================
# MAIN APPLICATION
# ==================================================

st.title(
    "🌾 Esan ERP"
)

st.caption(
    f"{COMPANY_NAME} | Version {VERSION}"
)


# ==================================================
# SIDEBAR NAVIGATION PANEL
# ==================================================

with st.sidebar:

    st.markdown(
        """
        <h2 style="text-align:center;">
        🌾 Esan ERP
        </h2>
        """,
        unsafe_allow_html=True
    )

    st.divider()


    # Initialize menu state

    if "current_page" not in st.session_state:

        st.session_state.current_page = "Overview"



    # -------------------------
    # Navigation Helper
    # -------------------------

    def nav_button(label):

        if st.button(
            label,
            use_container_width=True
        ):

            st.session_state.current_page = label



    # -------------------------
    # MAIN MENU
    # -------------------------

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



    # -------------------------
    # ADMINISTRATION
    # -------------------------

    if st.session_state.role == "Administrator":

        st.markdown(
            "**ADMINISTRATION**"
        )


        nav_button(
            "🔐 Administration"
        )



    st.divider()


    # -------------------------
    # USER PANEL
    # -------------------------

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
        use_container_width=True
    ):

        st.session_state.logged_in = False

        st.session_state.username = None

        st.session_state.role = None

        st.session_state.current_page = "Overview"

        st.rerun()
 


    



# ==================================================
# ROUTER
# ==================================================

if menu == "Overview":

    if dashboard_home:

        dashboard_home()

    else:

        st.info(
            "Overview dashboard not available"
        )



elif menu == "🌾 Procurement":

    if procurement_dashboard:

        procurement_dashboard()

    else:

        st.warning(
            "Procurement module unavailable"
        )



elif menu == "📦 Warehouse":

    if warehouse_dashboard:

        warehouse_dashboard()

    else:

        st.warning(
            "Warehouse module unavailable"
        )



elif menu == "🏭 Milling":

    if milling_dashboard:

        milling_dashboard()

    else:

        st.warning(
            "Milling module unavailable"
        )



elif menu == "📦 Packaging":

    if packaging_dashboard:

        packaging_dashboard()

    else:

        st.warning(
            "Packaging module unavailable"
        )



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
            "Dispatch",
            "Deliveries",
            "Invoices",
            "Payments"
        ]
    )


    sales_pages = {

        "Dashboard": sales_dashboard,

        "Customers": customers_page,

        "Quotations": quotations_page,

        "Sales Orders": sales_orders_page,

        "Dispatch": dispatch_page,

        "Deliveries": delivery_page,

        "Invoices": invoices_page,

        "Payments": payments_page

    }


    page = sales_pages.get(
        sales_menu
    )


    if page:

        page()

    else:

        st.warning(
            "Sales module unavailable"
        )



elif menu == "💰 Finance":

    if finance_dashboard:

        finance_dashboard()

    else:

        st.warning(
            "Finance module unavailable"
        )



elif menu == "📊 Reports":

    if reports_dashboard:

        reports_dashboard()

    else:

        st.warning(
            "Reports module unavailable"
        )



elif menu == "🚚 Logistics":

    if logistics_dashboard:

        logistics_dashboard()

    else:

        st.info(
            "Logistics module will be added"
        )



elif menu == "👥 HR & Employees":

    if hr_dashboard:

        hr_dashboard()

    else:

        st.info(
            "HR module will be added"
        )



elif menu == "🔧 Maintenance":

    if maintenance_dashboard:

        maintenance_dashboard()

    else:

        st.info(
            "Maintenance module will be added"
        )



elif menu == "🤖 AI Assistant":

    if ai_assistant_page:

        ai_assistant_page()

    else:

        st.info(
            "AI Assistant module will be added"
        )



elif menu == "🔐 Administration":


    if st.session_state.role != "Administrator":

        st.error(
            "Access denied"
        )


    else:


        st.header(
            "🔐 Administration"
        )


        admin_menu = st.radio(

            "Administration",

            [
                "User Management",
                "Change Password"
            ]

        )


        if admin_menu == "User Management":

            if user_management_page:

                user_management_page()



        elif admin_menu == "Change Password":

            if change_password_page:

                change_password_page()



# ==================================================
# FOOTER
# ==================================================

st.divider()

st.caption(
    "© Nile Harvest Foods Ltd. | Esan ERP Enterprise Platform"
)