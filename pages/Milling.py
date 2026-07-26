import streamlit as st


st.title("🏭 Milling Production Management")


tab1, tab2, tab3 = st.tabs(
    [
        "Production Batch",
        "Machine Status",
        "Reports"
    ]
)


with tab1:

    st.subheader(
        "Create Production Batch"
    )


    raw_material = st.selectbox(
        "Raw Material",
        [
            "Maize",
            "Cassava"
        ]
    )


    quantity = st.number_input(
        "Input Quantity (Tonnes)",
        min_value=0.0
    )


    line = st.selectbox(
        "Production Line",
        [
            "Mill Line 1",
            "Mill Line 2"
        ]
    )


    if st.button("Create Batch"):

        st.success(
            "Production batch created successfully"
        )


with tab2:

    st.subheader(
        "Machine Status"
    )


    st.table(
        {
            "Machine": [
                "Hammer Mill",
                "Packing Line"
            ],

            "Status": [
                "Available",
                "Available"
            ]
        }
    )


with tab3:

    st.subheader(
        "Production Reports"
    )

    st.info(
        "Production analytics will be connected to live data."
    )