"""
Milling Batch Management
"""

import streamlit as st
import pandas as pd

from database import SessionLocal
from models import MillingBatch



def milling_batches_page():

    st.subheader("🌽 Milling Batches")


    tab1, tab2 = st.tabs(
        [
            "Create Batch",
            "View Batches"
        ]
    )


    with tab1:

        create_batch()


    with tab2:

        view_batches()




def create_batch():

    with st.form("milling_batch"):


        batch_number = st.text_input(
            "Batch Number"
        )


        raw_material = st.selectbox(
            "Raw Material",
            [
                "Maize",
                "Cassava"
            ]
        )


        input_qty = st.number_input(
            "Input Quantity (Kg)",
            min_value=0.0
        )


        output_qty = st.number_input(
            "Output Quantity (Kg)",
            min_value=0.0
        )


        submit = st.form_submit_button(
            "Create Batch"
        )


        if submit:


            db = SessionLocal()


            batch = MillingBatch(

                batch_number=batch_number,

                raw_material=raw_material,

                input_quantity=input_qty,

                output_quantity=output_qty,

                wastage=input_qty-output_qty,

                status="Completed"

            )


            db.add(batch)

            db.commit()

            db.close()


            st.success(
                "Milling batch created"
            )

            st.rerun()




def view_batches():

    db = SessionLocal()


    batches = (
        db.query(MillingBatch)
        .all()
    )


    db.close()


    if batches:


        data=[]


        for b in batches:

            data.append({

                "Batch":
                    b.batch_number,

                "Material":
                    b.raw_material,

                "Input":
                    b.input_quantity,

                "Output":
                    b.output_quantity,

                "Wastage":
                    b.wastage,

                "Status":
                    b.status

            })


        st.dataframe(
            pd.DataFrame(data),
            use_container_width=True
        )

    else:

        st.info(
            "No milling batches."
        )