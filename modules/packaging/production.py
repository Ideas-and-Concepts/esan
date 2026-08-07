"""
Packaging Production Dashboard
"""

import streamlit as st

from database import SessionLocal
from models import PackagingBatch



def packaging_production_page():

    st.subheader(
        "⚙️ Packaging Production"
    )


    db = SessionLocal()


    total = (
        db.query(PackagingBatch)
        .count()
    )


    completed = (
        db.query(PackagingBatch)
        .filter(
            PackagingBatch.status=="Completed"
        )
        .count()
    )


    db.close()



    col1, col2 = st.columns(2)


    col1.metric(
        "Total Packaging Batches",
        total
    )


    col2.metric(
        "Completed",
        completed
    )