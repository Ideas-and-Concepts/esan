import streamlit as st


def esan_navigation():

    st.sidebar.image(
        "assets/logo.png",
        width=120
    )

    st.sidebar.title(
        "🌾 Esan ERP"
    )


    menu = st.sidebar.selectbox(

        "Main Menu",

        [
            "🏠 Dashboard",
            "🌾 Procurement",
            "📦 Warehouse",
            "🏭 Milling",
            "📦 Packaging",
            "🚚 Sales & Distribution",
            "💰 Finance",
            "📊 Reports",
            "⚙ Settings"
        ]

    )

    return menu