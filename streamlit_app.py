"""
Esan ERP Controller
Nile Harvest Foods Ltd.
Version 1.2.0 Alpha
"""

import streamlit as st


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
    SessionLocal
)


from models import User


from auth import verify_password


from services.user_service import create_admin


from components.navigation import esan_navigation


from components.themes import esan_theme



# =====================================
# SEED DATA
# =====================================

try:

    from seed.seed_data import load_seed_data

except Exception:

    load_seed_data = None



# =====================================
# DASHBOARD MODULES
# =====================================

from modules.dashboard.home import dashboard_home



# =====================================
# PROCUREMENT
# =====================================

try:

    from modules.procurement.dashboard import procurement_dashboard

except Exception:

    procurement_dashboard = None



# =====================================
# WAREHOUSE
# =====================================

try:

    from modules.warehouse.dashboard import warehouse_dashboard

except Exception:

    warehouse_dashboard = None



# =====================================
# MILLING
# =====================================

try:

    from modules.milling.dashboard import milling_dashboard

except Exception:

    milling_dashboard = None



# =====================================
# PACKAGING
# =====================================

try:

    from modules.packaging.dashboard import packaging_dashboard

except Exception:

    packaging_dashboard = None



# =====================================
# SALES
# =====================================

from modules.sales.dashboard import sales_dashboard

from modules.sales.customers import customers_page

from modules.sales.orders import sales_orders_page



# =====================================
# FINANCE
# =====================================

try:

    from modules.finance.dashboard import finance_dashboard

except Exception:

    finance_dashboard = None



# =====================================
# REPORTS
# =====================================

try:

    from modules.reports.dashboard import reports_dashboard

except Exception:

    reports_dashboard = None




# =====================================
# PAGE SETTINGS
# =====================================

st.set_page_config(

    page_title="Esan ERP",

    page_icon="🌾",

    layout="wide"

)



# =====================================
# DATABASE STARTUP
# =====================================

try:

    Base.metadata.create_all(
        bind=engine
    )


    db = SessionLocal()

    create_admin(db)

    db.close()



    if load_seed_data:

        load_seed_data()



except Exception as e:

    st.error(
        "Database startup failed"
    )

    st.exception(e)




# =====================================
# SESSION
# =====================================

if "logged_in" not in st.session_state:

    st.session_state.logged_in = False


if "username" not in st.session_state:

    st.session_state.username = None


if "role" not in st.session_state:

    st.session_state.role = None




# =====================================
# LOGIN
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


        if user and verify_password(
            password,
            user.password_hash
        ):


            st.session_state.logged_in=True

            st.session_state.username=user.username

            st.session_state.role=user.role


            return True


        return False


    finally:

        db.close()




# =====================================
# LOGIN SCREEN
# =====================================

if not st.session_state.logged_in:


    st.title(
        "🌾 Esan ERP"
    )


    st.subheader(
        COMPANY_NAME
    )


    username=st.text_input(
        "Username"
    )


    password=st.text_input(
        "Password",
        type="password"
    )


    if st.button(
        "Login"
    ):


        if login(username,password):

            st.success(
                "Welcome to Esan ERP"
            )

            st.rerun()

        else:

            st.error(
                "Invalid login"
            )


    st.info(
        "Default admin: admin / admin123"
    )


    st.stop()




# =====================================
# MAIN APP
# =====================================

st.title(
    "🌾 Esan ERP"
)


st.caption(
    f"{COMPANY_NAME} | Version {VERSION}"
)



theme = st.sidebar.selectbox(

    "Theme",

    [
        "Light",
        "Dark"
    ]

)


esan_theme(theme)



st.sidebar.success(

    f"User: {st.session_state.username}"

)



if st.sidebar.button(
    "Logout"
):

    st.session_state.logged_in=False

    st.rerun()




# =====================================
# NAVIGATION
# =====================================

menu = esan_navigation()




# =====================================
# ROUTER
# =====================================


if menu == "🏠 Dashboard":

    dashboard_home()



elif menu == "🌾 Procurement":


    if procurement_dashboard:

        procurement_dashboard()

    else:

        st.warning(
            "Procurement module not installed."
        )



elif menu == "📦 Warehouse":


    if warehouse_dashboard:

        warehouse_dashboard()

    else:

        st.warning(
            "Warehouse module not installed."
        )



elif menu == "🏭 Milling":


    if milling_dashboard:

        milling_dashboard()

    else:

        st.warning(
            "Milling module not installed."
        )



elif menu == "📦 Packaging":


    if packaging_dashboard:

        packaging_dashboard()

    else:

        st.warning(
            "Packaging module not installed."
        )



elif menu == "🚚 Sales & Distribution":


    st.header(
        "🚚 Sales & Distribution"
    )


    sales_menu = st.radio(

        "Sales Menu",

        [

            "Dashboard",

            "Customers",

            "Sales Orders"

        ]

    )


    if sales_menu=="Dashboard":

        sales_dashboard()


    elif sales_menu=="Customers":

        customers_page()


    elif sales_menu=="Sales Orders":

        sales_orders_page()




elif menu == "💰 Finance":


    if finance_dashboard:

        finance_dashboard()

    else:

        st.warning(
            "Finance module not installed."
        )




elif menu == "📊 Reports":


    if reports_dashboard:

        reports_dashboard()

    else:

        st.warning(
            "Reports module not installed."
        )




# =====================================
# FOOTER
# =====================================

st.divider()

st.caption(
"© Nile Harvest Foods Ltd. | Esan ERP Enterprise Platform"
)