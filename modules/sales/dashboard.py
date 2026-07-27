import streamlit as st


def sales_dashboard():


    st.header(
        "🚚 Sales & Distribution"
    )


    col1, col2, col3, col4 = st.columns(4)


    with col1:

        st.metric(
            "Today's Sales",
            "UGX 45.2M",
            "+8%"
        )


    with col2:

        st.metric(
            "Pending Orders",
            "24",
            "+5"
        )


    with col3:

        st.metric(
            "Deliveries Today",
            "8"
        )


    with col4:

        st.metric(
            "Outstanding Payments",
            "UGX 12.5M"
        )


    st.divider()


    st.subheader(
        "Order Pipeline"
    )


    st.info(
        "Quotation → Sales Order → Dispatch → Delivery → Payment"
    )


    st.divider()


    st.subheader(
        "🚛 Delivery Status"
    )


    deliveries = [

        ("UGX-204",
         "Juba",
         "In Transit"),

        ("UGX-205",
         "Kampala",
         "Delivered"),

        ("UGX-206",
         "Gulu",
         "Loading")

    ]


    for truck, destination, status in deliveries:

        st.write(
            f"🚚 {truck} | {destination} | {status}"
        )