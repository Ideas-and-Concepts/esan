import streamlit as st


def warehouse_dashboard():

    st.header(
        "📦 Warehouse Overview"
    )


    c1,c2,c3,c4 = st.columns(4)


    c1.metric(
        "Raw Materials",
        "1,170 Tonnes"
    )


    c2.metric(
        "Finished Goods",
        "685 Tonnes"
    )


    c3.metric(
        "Available Space",
        "72%"
    )


    c4.metric(
        "Low Stock Items",
        "5"
    )


    st.divider()


    st.success(
        "Main warehouse operating normally"
    )

    st.warning(
        "Packaging bags need replenishment"
    )