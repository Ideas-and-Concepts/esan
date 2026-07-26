import streamlit as st


st.title("🚚 Sales & Distribution Management")


tab1, tab2, tab3 = st.tabs(
    [
        "Customers",
        "Sales Orders",
        "Shipments"
    ]
)


with tab1:

    st.subheader(
        "Customer Registration"
    )

    name = st.text_input(
        "Customer Name"
    )

    country = st.selectbox(
        "Country",
        [
            "Uganda",
            "South Sudan"
        ]
    )

    customer_type = st.selectbox(
        "Customer Type",
        [
            "Retail",
            "Wholesale",
            "Distributor",
            "Export"
        ]
    )

    if st.button("Save Customer"):
        st.success(
            "Customer registered"
        )


with tab2:

    st.subheader(
        "Create Sales Order"
    )

    st.info(
        "Sales order processing will connect to finished goods inventory."
    )


with tab3:

    st.subheader(
        "Shipment Tracking"
    )

    st.info(
        "Transport and export tracking module."
    )