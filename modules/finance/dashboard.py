import streamlit as st


def finance_dashboard():

    st.header(
        "💰 Finance Overview"
    )


    a,b,c,c2 = st.columns(4)


    a.metric(
        "Revenue",
        "UGX 142M"
    )


    b.metric(
        "Receivables",
        "UGX 85M"
    )


    c.metric(
        "Expenses",
        "UGX 48M"
    )


    c2.metric(
        "Profit",
        "UGX 94M"
    )