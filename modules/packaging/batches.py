"""
Packaging Batch Management
"""

import streamlit as st
import pandas as pd

from database import SessionLocal
from models import PackagingBatch



def packaging_batches_page():

    st.subheader(
        "📦 Packaging Batches"
    )


    tab1, tab2 = st.tabs(
        [
            "Create Batch",
            "View Batches"
        ]
    )


    with tab1:

        create_packaging_batch()


    with tab2:

        view_packaging_batches()




def create_packaging_batch():

    with st.form(
        "packaging_batch_form"
    ):


        batch_number = st.text_input(
            "Batch Number"
        )


        product_name = st.text_input(
            "Product Name"
        )


        input_quantity = st.number_input(
            "Input Quantity (Kg)",
            min_value=0.0
        )


        packed_quantity = st.number_input(
            "Packed Quantity (Kg)",
            min_value=0.0
        )


        package_size = st.selectbox(
            "Package Size",
            [
                "1 Kg",
                "5 Kg",
                "10 Kg",
                "25 Kg",
                "50 Kg"
            ]
        )


        submit = st.form_submit_button(
            "Create Packaging Batch"
        )


        if submit:


            db = SessionLocal()


            batch = PackagingBatch(

                batch_number=batch_number,

                product_name=product_name,

                input_quantity=input_quantity,

                packed_quantity=packed_quantity,

                package_size=package_size,

                status="Completed"

            )


            db.add(batch)

            db.commit()

            db.close()


            st.success(
                "Packaging batch created"
            )

            st.rerun()




def view_packaging_batches():

    db = SessionLocal()


    batches = (
        db.query(PackagingBatch)
        .all()
    )


    db.close()


    if batches:


        data=[]


        for b in batches:

            data.append({

                "Batch":
                    b.batch_number,

                "Product":
                    b.product_name,

                "Input":
                    b.input_quantity,

                "Packed":
                    b.packed_quantity,

                "Size":
                    b.package_size,

                "Status":
                    b.status

            })


        st.dataframe(
            pd.DataFrame(data),
            use_container_width=True
        )


    else:

        st.info(
            "No packaging batches."
        )