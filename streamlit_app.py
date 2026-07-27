"""
Esan ERP Controller
Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Version 1.2.0 Alpha
"""


import streamlit as st
import os
from sqlalchemy import inspect


# =====================================
# CORE IMPORTS
# =====================================

from config import (
    COMPANY_NAME,
    VERSION
)


from database import (
    Base,
    engine,
    SessionLocal,
    DATABASE_URL
)


from models import User


from auth import verify_password


from services.user_service import create_admin


from components.navigation import esan_navigation


from components.themes import esan_theme




# =====================================
# OPTIONAL SEED DATA
# =====================================

try:

    from seed.seed_data import load_seed_data

except Exception:

    load_seed_data = None




# =====================================
# MODULE IMPORTS
# =====================================


try:

    from modules.dashboard.home import dashboard_home

except Exception:

    dashboard_home = None




# SALES

try:

    from modules.sales.dashboard import sales_dashboard

except Exception:

    sales_dashboard = None



try:

    from modules.sales.customers import customers_page

except Exception:

    customers_page = None



try:

    from modules.sales.orders import sales_orders_page

except Exception:

    sales_orders_page = None



try:

    from modules.sales.quotations import quotations_page

except Exception:

    quotations_page = None



try:

    from modules.sales.delivery import delivery_page

except Exception:

    delivery_page = None




# PROCUREMENT

try:

    from modules.procurement.dashboard import procurement_dashboard

except Exception:

    procurement_dashboard = None




# WAREHOUSE

try:

    from modules.warehouse.dashboard import warehouse_dashboard

except Exception:

    warehouse_dashboard = None




# MILLING

try:

    from modules.milling.dashboard import milling_dashboard

except Exception:

    milling_dashboard = None




# PACKAGING

try:

    from modules.packaging.dashboard import packaging_dashboard

except Exception:

    packaging_dashboard = None




# FINANCE

try:

    from modules.finance.dashboard import finance_dashboard

except Exception:

    finance_dashboard = None



try:

    from modules.finance.invoices import invoices_page

except Exception:

    invoices_page = None



try:

    from modules.finance.payments import payments_page

except Exception:

    payments_page = None




# REPORTS

try:

    from modules.reports.dashboard import reports_dashboard

except Exception:

    reports_dashboard = None




# =====================================
# PAGE CONFIGURATION
# =====================================

st.set_page_config(

    page_title="Esan ERP",

    page_icon="🌾",

    layout="wide"

)




# =====================================
# STREAMLIT CLEAN UI
# =====================================

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

</style>
""",

unsafe_allow_html=True

)



# =====================================
# DATABASE INITIALIZATION (with auto-repair)
# =====================================
try:
    needs_rebuild = False
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    if existing_tables:
        for table_name, table in Base.metadata.tables.items():
            if table_name in existing_tables:
                existing_cols = {col['name'] for col in inspector.get_columns(table_name)}
                model_cols = {c.name for c in table.columns}
                if model_cols - existing_cols:
                    needs_rebuild = True
                    break

    if needs_rebuild:
        st.warning("🔄 Database schema updated. Rebuilding with fresh tables...")
        try:
            if "sqlite:///" in DATABASE_URL:
                db_path = DATABASE_URL.replace("sqlite:///", "")
                if os.path.exists(db_path):
                    os.remove(db_path)
        except Exception:
            pass
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    create_admin(db)
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



if "username" not in st.session_state:

    st.session_state.username = None



if "role" not in st.session_state:

    st.session_state.role = None




# =====================================
# LOGIN FUNCTION
# =====================================

def login(username,password):


    db = SessionLocal()


    try:


        user = (

            db.query(User)

            .filter(
                User.username == username
            )

            .first()

        )



        if user:


            if verify_password(

                password,

                user.password_hash

            ):


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


    username = st.text_input(
        "Username"
    )


    password = st.text_input(
        "Password",
        type="password"
    )



    if st.button(
        "Login"
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




# =====================================
# APPLICATION HEADER
# =====================================

st.title(
    "🌾 Esan ERP"
)


st.caption(
    f"{COMPANY_NAME} | Version {VERSION}"
)




# =====================================
# THEME
# =====================================

theme = st.sidebar.selectbox(

    "Appearance",

    [
        "Light",
        "Dark"
    ]

)


esan_theme(theme)




# =====================================
# USER PANEL
# =====================================

st.sidebar.success(

    f"User: {st.session_state.username}"

)


st.sidebar.info(

    f"Role: {st.session_state.role}"

)



if st.sidebar.button(
    "Logout"
):


    st.session_state.logged_in = False

    st.session_state.username = None

    st.session_state.role = None

    st.rerun()




# =====================================
# NAVIGATION
# =====================================

menu = esan_navigation()




# =====================================
# ERP MODULE ROUTER
# =====================================


if menu == "Overview":


    if dashboard_home:

        dashboard_home()

    else:

        st.info(
            "Dashboard module not available."
        )




elif menu == "🌾 Procurement":


    if procurement_dashboard:

        procurement_dashboard()

    else:

        st.warning(
            "Procurement module not available."
        )




elif menu == "📦 Warehouse":


    if warehouse_dashboard:

        warehouse_dashboard()

    else:

        st.warning(
            "Warehouse module not available."
        )




elif menu == "🏭 Milling":


    if milling_dashboard:

        milling_dashboard()

    else:

        st.warning(
            "Milling module not available."
        )




elif menu == "📦 Packaging":


    if packaging_dashboard:

        packaging_dashboard()

    else:

        st.warning(
            "Packaging module not available."
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



    if sales_menu == "Dashboard":


        if sales_dashboard:

            sales_dashboard()

        else:

            st.warning(
                "Sales dashboard unavailable."
            )




    elif sales_menu == "Customers":


        if customers_page:

            customers_page()

        else:

            st.warning(
                "Customers module unavailable."
            )




    elif sales_menu == "Quotations":


        if quotations_page:

            quotations_page()

        else:

            st.warning(
                "Quotation module unavailable."
            )




    elif sales_menu == "Sales Orders":


        if sales_orders_page:

            sales_orders_page()

        else:

            st.warning(
                "Sales Orders module unavailable."
            )




    elif sales_menu == "Deliveries":


        if delivery_page:

            delivery_page()

        else:

            st.warning(
                "Delivery module unavailable."
            )




    elif sales_menu == "Invoices":


        if invoices_page:

            invoices_page()

        else:

            st.warning(
                "Invoices module unavailable."
            )




    elif sales_menu == "Payments":


        if payments_page:

            payments_page()

        else:

            st.warning(
                "Payments module unavailable."
            )




    else:


        st.info(

            f"{sales_menu} module will be developed next."

        )





elif menu == "💰 Finance":


    if finance_dashboard:

        finance_dashboard()

    else:

        st.warning(
            "Finance module unavailable."
        )




elif menu == "📊 Reports":


    if reports_dashboard:

        reports_dashboard()

    else:

        st.warning(
            "Reports module unavailable."
        )




else:


    st.info(
        "Select a module from the navigation menu."
    )




# =====================================
# FOOTER
# =====================================

st.divider()


st.caption(

"© Nile Harvest Foods Ltd. | Esan ERP Enterprise Platform"

)