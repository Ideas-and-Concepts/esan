import streamlit as st


def procurement_dashboard():

    st.header(
        "🌾 Procurement Overview"
    )


    c1, c2, c3, c4 = st.columns(4)


    c1.metric(
        "Active Suppliers",
        "25"
    )

    c2.metric(
        "Maize Purchased",
        "850 Tonnes"
    )

    c3.metric(
        "Cassava Purchased",
        "320 Tonnes"
    )

    c4.metric(
        "Pending Purchases",
        "12"
    )


    st.divider()

    st.subheader(
        "Recent Procurement Activity"
    )


    st.info(
        "Maize delivery from Northern Uganda scheduled"
    )

    st.info(
        "Cassava supplier contract under review"
    )