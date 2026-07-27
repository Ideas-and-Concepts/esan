import streamlit as st

from database import SessionLocal
from models import Customer


def customers_page():

    st.header(
        "👥 Customer Management"
    )


    db = SessionLocal()


    # -----------------------------
    # Add Customer
    # -----------------------------

    with st.expander(
        "➕ Add New Customer"
    ):

        name = st.text_input(
            "Customer Name"
        )


        phone = st.text_input(
            "Phone Number"
        )


        location = st.text_input(
            "Location"
        )


        country = st.selectbox(
            "Country",
            [
                "Uganda",
                "South Sudan"
            ]
        )


        if st.button(
            "Save Customer"
        ):


            customer = Customer(

                name=name,

                phone=phone,

                location=location,

                country=country

            )


            db.add(customer)

            db.commit()


            st.success(
                "Customer saved successfully"
            )



    st.divider()


    # -----------------------------
    # Customer List
    # -----------------------------

    st.subheader(
        "📋 Customer List"
    )


    customers = (
        db.query(Customer)
        .order_by(
            Customer.id.desc()
        )
        .all()
    )


    if customers:


        for customer in customers:


            with st.container():

                st.write(
                    f"""
                    👤 **{customer.name}**

                    📞 {customer.phone}

                    📍 {customer.location}

                    🌍 {customer.country}
                    """
                )

                st.divider()


    else:

        st.info(
            "No customers registered yet."
        )


    db.close()