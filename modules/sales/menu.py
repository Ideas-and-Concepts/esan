import streamlit as st


def sales_navigation():

    option = st.radio(

        "Sales Menu",

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


    return option