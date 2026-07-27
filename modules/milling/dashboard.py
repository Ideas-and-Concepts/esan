import streamlit as st


def milling_dashboard():

    st.header(
        "🏭 Milling Production"
    )


    a,b,c,d = st.columns(4)


    a.metric(
        "Daily Production",
        "128 Tonnes"
    )


    b.metric(
        "Efficiency",
        "92%"
    )


    c.metric(
        "Running Lines",
        "2"
    )


    d.metric(
        "Maintenance",
        "1 Pending"
    )


    st.divider()


    st.success(
        "Milling Line 1: Running"
    )

    st.success(
        "Milling Line 2: Running"
    )