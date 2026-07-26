import streamlit as st


st.title("📦 Packaging Management")


tab1, tab2, tab3 = st.tabs(
    [
        "Packaging Batch",
        "Materials",
        "Reports"
    ]
)


with tab1:

    st.subheader(
        "Create Packaging Batch"
    )


    product = st.selectbox(
        "Product",
        [
            "Maize Flour Premium",
            "Cassava Flour"
        ]
    )


    quantity = st.number_input(
        "Input Flour (Tonnes)",
        min_value=0.0
    )


    size = st.selectbox(
        "Package Size",
        [
            "1 kg",
            "5 kg",
            "25 kg",
            "50 kg"
        ]
    )


    if st.button("Create Packaging Batch"):

        st.success(
            "Packaging batch created"
        )



with tab2:

    st.subheader(
        "Packaging Materials"
    )

    st.table(
        {
            "Material": [
                "25kg Bags",
                "Labels",
                "Pallets"
            ],

            "Stock": [
                0,
                0,
                0
            ]
        }
    )



with tab3:

    st.subheader(
        "Packaging Reports"
    )

    st.info(
        "Packaging analytics will be connected to production data."
    )