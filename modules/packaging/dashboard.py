import streamlit as st


def packaging_dashboard():

    st.header(
        "📦 Packaging Operations"
    )


    c1,c2,c3 = st.columns(3)


    c1.metric(
        "Bags Packed Today",
        "5,120"
    )


    c2.metric(
        "Packaging Stock",
        "85%"
    )


    c3.metric(
        "Rejected Units",
        "12"
    )