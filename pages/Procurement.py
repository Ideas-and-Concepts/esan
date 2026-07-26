import streamlit as st


st.title("🌾 Procurement Management")


tab1, tab2, tab3 = st.tabs(
    [
        "Suppliers",
        "Purchase Orders",
        "Deliveries"
    ]
)


with tab1:

    st.subheader(
        "Register Supplier"
    )

    name = st.text_input(
        "Supplier Name"
    )

    phone = st.text_input(
        "Phone Number"
    )

    location = st.text_input(
        "Location"
    )

    product = st.selectbox(
        "Product",
        [
            "Maize",
            "Cassava",
            "Sorghum",
            "Other"
        ]
    )


    if st.button("Save Supplier"):

        st.success(
            "Supplier registered successfully"
        )


with tab2:

    st.subheader(
        "Create Purchase Order"
    )

    st.info(
        "Purchase order management will connect to the supplier database."
    )


with tab3:

    st.subheader(
        "Receive Delivery"
    )

    st.info(
        "Delivery and quality inspection module."
    )