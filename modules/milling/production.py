"""
Milling Production Overview
"""

import streamlit as st

from database import SessionLocal
from models import MillingBatch



def production_page():

    st.subheader(
        "⚙️ Production Overview"
    )


    db = SessionLocal()


    total_batches = (
        db.query(MillingBatch)
        .count()
    )


    completed = (
        db.query(MillingBatch)
        .filter(
            MillingBatch.status=="Completed"
        )
        .count()
    )


    db.close()


    col1, col2 = st.columns(2)


    col1.metric(
        "Total Batches",
        total_batches
    )


    col2.metric(
        "Completed",
        completed
    )