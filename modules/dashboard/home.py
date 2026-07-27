import streamlit as st


def dashboard_home():

    st.header(
        "📊 Executive Dashboard"
    )


    col1, col2, col3, col4 = st.columns(4)


    with col1:

        st.metric(
            "🌾 Production",
            "128 Tonnes",
            "+12%"
        )


    with col2:

        st.metric(
            "📦 Inventory",
            "685 Tonnes",
            "+5%"
        )


    with col3:

        st.metric(
            "🚚 Orders",
            "24",
            "+3"
        )


    with col4:

        st.metric(
            "💰 Sales",
            "UGX 45.2M",
            "+8%"
        )


    st.divider()


    st.subheader(
        "🏭 Factory Status"
    )


    st.success(
        "🟢 Milling Line 1 Running"
    )


    st.success(
        "🟢 Warehouse Operational"
    )


    st.warning(
        "🟡 Packaging Line Maintenance Scheduled"
    )