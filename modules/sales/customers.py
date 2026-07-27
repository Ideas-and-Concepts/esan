"""
Esan ERP
Sales & Distribution - Customer Management

Nile Harvest Foods Ltd.
"""


import streamlit as st

from sqlalchemy import or_

from database import SessionLocal

from models import Customer



# =====================================
# CUSTOMER DASHBOARD
# =====================================

def customer_summary(db):

    total = db.query(
        Customer
    ).count()


    uganda = db.query(
        Customer
    ).filter(
        Customer.country == "Uganda"
    ).count()


    south_sudan = db.query(
        Customer
    ).filter(
        Customer.country == "South Sudan"
    ).count()


    return total, uganda, south_sudan




# =====================================
# ADD CUSTOMER
# =====================================

def add_customer_form():


    st.subheader(
        "➕ Register New Customer"
    )


    with st.form(
        "customer_form"
    ):


        name = st.text_input(
            "Customer Name"
        )


        phone = st.text_input(
            "Phone Number"
        )


        country = st.selectbox(

            "Country",

            [
                "Uganda",
                "South Sudan"
            ]

        )


        location = st.text_input(
            "Location"
        )


        customer_type = st.selectbox(

            "Customer Type",

            [

                "Distributor",

                "Wholesale",

                "Retail",

                "Export Customer"

            ]

        )


        submitted = st.form_submit_button(

            "Save Customer"

        )



        if submitted:


            if not name:


                st.error(
                    "Customer name is required"
                )


                return



            db = SessionLocal()


            customer = Customer(

                name=name,

                phone=phone,

                country=country,

                location=location,

                customer_type=customer_type

            )


            db.add(customer)

            db.commit()

            db.close()



            st.success(
                "Customer registered successfully"
            )


            st.rerun()




# =====================================
# CUSTOMER DATABASE
# =====================================

def customer_database():


    st.subheader(
        "📋 Customer Database"
    )


    db = SessionLocal()



    search = st.text_input(

        "🔍 Search Customer"

    )



    query = db.query(Customer)



    if search:


        query = query.filter(

            or_(

                Customer.name.contains(search),

                Customer.location.contains(search),

                Customer.country.contains(search)

            )

        )



    customers = query.all()



    if customers:


        for customer in customers:


            with st.expander(

                f"{customer.name} | {customer.country}"

            ):


                st.write(
                    f"📍 Location: {customer.location}"
                )


                st.write(
                    f"☎ Phone: {customer.phone}"
                )


                st.write(
                    f"Category: {customer.customer_type}"
                )



                if st.button(

                    "Delete Customer",

                    key=f"delete_{customer.id}"

                ):


                    db.delete(customer)

                    db.commit()


                    st.success(
                        "Customer deleted"
                    )


                    st.rerun()



    else:


        st.info(
            "No customers found"
        )



    db.close()




# =====================================
# MAIN CUSTOMER PAGE
# =====================================

def customers_page():


    st.header(
        "👥 Customer Management"
    )



    db = SessionLocal()



    total, uganda, south_sudan = customer_summary(db)



    db.close()



    c1,c2,c3 = st.columns(3)



    c1.metric(

        "Total Customers",

        total

    )


    c2.metric(

        "Uganda Customers",

        uganda

    )


    c3.metric(

        "South Sudan Customers",

        south_sudan

    )



    st.divider()



    tab1, tab2 = st.tabs(

        [

            "➕ Add Customer",

            "📋 Customer Database"

        ]

    )



    with tab1:

        add_customer_form()



    with tab2:

        customer_database()