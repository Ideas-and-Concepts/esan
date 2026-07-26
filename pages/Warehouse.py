import streamlit as st


st.title("📦 Warehouse Management")


tab1, tab2, tab3 = st.tabs(
    [
        "Inventory",
        "Stock Movement",
        "Reports"
    ]
)


with tab1:

    st.subheader(
        "Current Inventory"
    )


    inventory = {
        "Product": [
            "Maize",
            "Cassava",
            "Maize Flour"
        ],

        "Quantity": [
            0,
            0,
            0
        ],

        "Unit": [
            "Tonnes",
            "Tonnes",
            "Bags"
        ]
    }


    st.table(
        inventory
    )


with tab2:

    st.subheader(
        "Record Stock Movement"
    )


    product = st.selectbox(
        "Product",
        [
            "Maize",
            "Cassava",
            "Maize Flour",
            "Cassava Flour"
        ]
    )


    movement = st.selectbox(
        "Movement Type",
        [
            "Receiving",
            "Production Consumption",
            "Production Output",
            "Dispatch"
        ]
    )


    quantity = st.number_input(
        "Quantity",
        min_value=0.0
    )


    if st.button("Save Movement"):

        st.success(
            "Stock movement recorded"
        )


with tab3:

    st.subheader(
        "Inventory Reports"
    )

    st.info(
        "Inventory analytics will be added here."
    )