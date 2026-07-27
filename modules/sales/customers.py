"""
Esan ERP
Customer Management Module
Nile Harvest Foods Ltd.
"""

import streamlit as st

from database import SessionLocal
from models import Customer


def customers_page():

    st.header("👥 Customer Management")

    db = SessionLocal()


    # =====================================
    # ADD CUSTOMER FORM
    # =====================================

    st.subheader("➕ Register New Customer")


    with st.form("customer_form"):

        customer_name = st.text_input(
            "Customer Name"
        )


        phone = st.text_input(
            "Phone Number"
        )


        email = st.text_input(
            "Email Address"
        )


        location = st.text_input(
            "Location / Address"
        )


        country = st.selectbox(

            "Country",

            [
                "Uganda",
                "South Sudan",
                "Kenya",
                "Tanzania",
                "Other"
            ]

        )


        customer_type = st.selectbox(

            "Customer Type",

            [
                "Retail",
                "Wholesale",
                "Distributor",
                "Export Customer"
            ]

        )


        credit_limit = st.number_input(

            "Credit Limit",

            min_value=0.0,

            step=100000.0

        )


        submitted = st.form_submit_button(
            "💾 Save Customer"
        )


        if submitted:


            if customer_name:


                new_customer = Customer(

                    name=customer_name,

                    phone=phone,

                    location=location,

                    country=country

                )


                db.add(new_customer)

                db.commit()


                st.success(
                    "Customer registered successfully."
                )


                st.rerun()


            else:

                st.warning(
                    "Customer name is required."
                )



    st.divider()



    # =====================================
    # CUSTOMER DATABASE
    # =====================================

    st.subheader(
        "📋 Customer Database"
    )


    search = st.text_input(
        "🔍 Search Customer"
    )


    customers = (

        db.query(Customer)

        .order_by(
            Customer.id.desc()
        )

        .all()

    )


    if search:

        customers = [

            customer for customer in customers

            if search.lower()

            in customer.name.lower()

        ]



    if customers:


        for customer in customers:


            with st.expander(

                f"👤 {customer.name}"

            ):


                st.write(

                    f"""
                    **Phone:** {customer.phone}

                    **Location:** {customer.location}

                    **Country:** {customer.country}

                    **Customer ID:** {customer.id}
                    """

                )


                col1, col2 = st.columns(2)


                with col1:

                    st.button(

                        "✏ Edit",

                        key=f"edit_{customer.id}"

                    )


                with col2:

                    if st.button(

                        "🗑 Delete",

                        key=f"delete_{customer.id}"

                    ):

                        db.delete(customer)

                        db.commit()


                        st.success(
                            "Customer deleted."
                        )

                        st.rerun()


    else:


        st.info(
            "No customers found."
        )


    db.close()