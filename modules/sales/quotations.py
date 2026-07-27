"""
Esan ERP
Sales & Distribution - Quotations

Nile Harvest Foods Ltd.
"""

import streamlit as st
from datetime import datetime

from database import SessionLocal
from models import Quotation, Customer



def quotation_form():

    st.subheader(
        "➕ Create New Quotation"
    )


    db = SessionLocal()


    customers = db.query(
        Customer
    ).all()


    customer_list = [
        c.name for c in customers
    ]


    if not customer_list:

        st.warning(
            "Please register customers first."
        )

        db.close()

        return



    with st.form(
        "quotation_form"
    ):


        customer = st.selectbox(

            "Customer",

            customer_list

        )


        product = st.selectbox(

            "Product",

            [

                "Maize Flour 5kg",

                "Maize Flour 25kg",

                "Cassava Flour 25kg",

                "Animal Feed"

            ]

        )


        quantity = st.number_input(

            "Quantity",

            min_value=1.0

        )


        unit_price = st.number_input(

            "Unit Price (UGX)",

            min_value=0.0

        )


        submit = st.form_submit_button(

            "Save Quotation"

        )



        if submit:


            total = quantity * unit_price


            quotation = Quotation(

                quotation_number=

                f"QT-{datetime.now().strftime('%Y%m%d%H%M%S')}",


                customer=customer,


                product=product,


                quantity=quantity,


                unit_price=unit_price,


                total_amount=total,


                status="Draft"

            )


            db.add(
                quotation
            )


            db.commit()


            st.success(
                "Quotation created successfully"
            )


            st.rerun()



    db.close()



def quotation_database():


    st.subheader(
        "📋 Quotation Database"
    )


    db = SessionLocal()


    quotations = db.query(
        Quotation
    ).order_by(
        Quotation.id.desc()
    ).all()



    for q in quotations:


        with st.expander(

            f"{q.quotation_number} - {q.customer}"

        ):


            st.write(
                f"Product: {q.product}"
            )


            st.write(
                f"Quantity: {q.quantity}"
            )


            st.write(
                f"Total: UGX {q.total_amount:,.0f}"
            )


            st.write(
                f"Status: {q.status}"
            )


    db.close()



def quotations_page():


    st.header(
        "📄 Sales Quotations"
    )


    tab1, tab2 = st.tabs(

        [

            "Create Quotation",

            "Quotation Database"

        ]

    )


    with tab1:

        quotation_form()



    with tab2:

        quotation_database()