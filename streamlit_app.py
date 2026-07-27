"""
Esan ERP Controller
Nile Harvest Foods Ltd.
Version 1.1.0 Alpha
"""

import streamlit as st


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

from seed.seed_data import load_seed_data


from modules.dashboard.home import dashboard_home

from modules.sales.dashboard import sales_dashboard
from modules.sales.customers import customers_page
from modules.sales.orders import sales_orders_page


# =====================================
# MODULE IMPORTS
# =====================================

from modules.dashboard.home import dashboard_home


from modules.sales.dashboard import sales_dashboard

from modules.sales.customers import customers_page

from modules.sales.orders import sales_orders_page

from seed.seed_data import load_seed_data


# =====================================
# PAGE CONFIGURATION
# =====================================

st.set_page_config(

    page_title="Esan ERP",

    page_icon="🌾",

    layout="wide"

)



# =====================================
# HIDE STREAMLIT DEFAULT UI
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
# DATABASE INITIALIZATION
# =====================================

try:

    Base.metadata.create_all(
        bind=engine
    )


    db = SessionLocal()

    create_admin(db)

    db.close()


    # Load demo/company seed data
    load_seed_data()


except Exception as e:

    st.error(
        "Database initialization failed"
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
# LOGIN FUNCTION
# =====================================

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
# LOGIN PAGE
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
# MAIN APPLICATION HEADER
# =====================================

st.title(
    "🌾 Esan ERP"
)


st.caption(

f"{COMPANY_NAME} | Version {VERSION}"

)



# =====================================
# THEME CONTROL
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
# USER INFORMATION
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

            "Sales Orders",

            "Quotations",

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



    elif sales_menu == "Sales Orders":


        sales_orders_page()



    else:


        st.info(

            f"{sales_menu} module will be developed next."

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