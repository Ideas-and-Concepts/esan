"""
Esan ERP Controller
Nile Harvest Foods Ltd.
Version 1.1.0 Alpha
"""

import streamlit as st


from config import (
    APP_NAME,
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


# Dashboard
from modules.dashboard.home import dashboard_home


# Sales
from modules.sales.dashboard import sales_dashboard
from modules.sales.customers import customers_page



# =====================================
# PAGE CONFIGURATION
# =====================================

st.set_page_config(

    page_title="Esan ERP",

    page_icon="🌾",

    layout="wide"

)



# =====================================
# REMOVE STREAMLIT BRANDING
# =====================================

st.markdown(

"""
<style>

#MainMenu {

visibility:hidden;

}


footer {

visibility:hidden;

}


header {

visibility:hidden;

}


</style>

""",

unsafe_allow_html=True

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


except Exception as e:

    st.error(
        "Database startup failed"
    )

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
# LOGIN
# =====================================


def login(username, password):


    db = SessionLocal()


    user = (

        db.query(User)

        .filter(
            User.username == username
        )

        .first()

    )


    db.close()


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




# =====================================
# LOGIN SCREEN
# =====================================


if not st.session_state.logged_in:


    st.markdown(

    """
    <h1 style="text-align:center;">
    🌾 Esan ERP
    </h1>

    <h3 style="text-align:center;">
    Nile Harvest Foods Ltd.
    </h3>

    <p style="text-align:center;">
    Enterprise Milling & Packaging Management System
    </p>

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
                "Welcome to Esan ERP"
            )

            st.rerun()


        else:


            st.error(
                "Invalid login details"
            )


    st.info(
        "Default admin: admin / admin123"
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

    "Theme",

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
# MAIN NAVIGATION
# =====================================


menu = esan_navigation()



# =====================================
# MODULE ROUTER
# =====================================


if menu == "🏠 Dashboard":


    dashboard_home()



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

        sales_dashboard()



    elif sales_menu == "Customers":

        customers_page()



    else:

        st.info(

        f"{sales_menu} module is coming next."

        )



else:


    st.header(
        menu
    )


    st.info(
        "Module development in progress."
    )



# =====================================
# FOOTER
# =====================================


st.divider()


st.caption(

"© Nile Harvest Foods Ltd. | Esan ERP Enterprise Platform"

)