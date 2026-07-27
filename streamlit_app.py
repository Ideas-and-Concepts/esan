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

from modules.sales.quotations import quotations_page

# =====================================
# SEED DATA
# =====================================

try:

    from seed.seed_data import load_seed_data

except Exception:

    load_seed_data = None



# =====================================
# MODULE IMPORTS
# =====================================


from modules.dashboard.home import dashboard_home



# Sales

from modules.sales.dashboard import sales_dashboard

from modules.sales.customers import customers_page

from modules.sales.orders import sales_orders_page




# Optional modules

try:
    from modules.procurement.dashboard import procurement_dashboard
except Exception:
    procurement_dashboard = None



try:
    from modules.warehouse.dashboard import warehouse_dashboard
except Exception:
    warehouse_dashboard = None



try:
    from modules.milling.dashboard import milling_dashboard
except Exception:
    milling_dashboard = None



try:
    from modules.packaging.dashboard import packaging_dashboard
except Exception:
    packaging_dashboard = None



try:
    from modules.finance.dashboard import finance_dashboard
except Exception:
    finance_dashboard = None



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
# HIDE STREAMLIT UI
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


        if login(username,password):

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
# HEADER
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
# ERP ROUTER
# =====================================


if menu == "Overview":

elif menu == "🌾 Procurement":

    procurement_dashboard()


    if procurement_dashboard:

        procurement_dashboard()

    else:

        st.warning(
            "Procurement module not available yet."
        )



elif menu == "📦 Warehouse":


    if warehouse_dashboard:

        warehouse_dashboard()

    else:

        st.warning(
            "Warehouse module not available yet."
        )



elif menu == "🏭 Milling":


    if milling_dashboard:

        milling_dashboard()

    else:

        st.warning(
            "Milling module not available yet."
        )



elif menu == "📦 Packaging":


    if packaging_dashboard:

        packaging_dashboard()

    else:

        st.warning(
            "Packaging module not available yet."
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



elif menu == "💰 Finance":


    if finance_dashboard:

        finance_dashboard()

    else:

        st.warning(
            "Finance module not available yet."
        )



elif menu == "📊 Reports":


    if reports_dashboard:

        reports_dashboard()

    else:

        st.warning(
            "Reports module not available yet."
        )



else:

    st.info(
        "Select a module from the navigation menu."
    )

elif sales_menu == "Quotations":

    quotations_page()



# =====================================
# FOOTER
# =====================================

st.divider()


st.caption(

"© Nile Harvest Foods Ltd. | Esan ERP Enterprise Platform"

)