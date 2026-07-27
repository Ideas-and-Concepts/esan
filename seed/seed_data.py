"""
Esan ERP Seed Data
Nile Harvest Foods Ltd.
"""

from database import SessionLocal

from models import (
    Customer,
    SalesOrder
)



def load_seed_data():

    db = SessionLocal()


    # =====================================
    # CHECK EXISTING DATA
    # =====================================

    existing_customer = (
        db.query(Customer)
        .first()
    )


    if existing_customer:

        db.close()

        return



    # =====================================
    # CUSTOMERS
    # =====================================

    customers = [

        Customer(
            name="Juba Traders Ltd",
            phone="+211900000001",
            location="Juba",
            country="South Sudan"
        ),


        Customer(
            name="Equatoria Wholesale Centre",
            phone="+211900000002",
            location="Juba",
            country="South Sudan"
        ),


        Customer(
            name="Nile Food Stores",
            phone="+256700000003",
            location="Kampala",
            country="Uganda"
        ),


        Customer(
            name="Gulu Agro Market",
            phone="+256700000004",
            location="Gulu",
            country="Uganda"
        ),


        Customer(
            name="Torit Food Suppliers",
            phone="+211900000005",
            location="Torit",
            country="South Sudan"
        )

    ]


    db.add_all(customers)

    db.commit()



    # =====================================
    # SALES ORDERS
    # =====================================


    customer_list = (

        db.query(Customer)
        .all()

    )


    orders = [

        SalesOrder(

            customer_id=customer_list[0].id,

            product="Maize Flour 25kg",

            quantity=2000,

            unit_price=35000,

            total_amount=70000000,

            status="Approved"

        ),



        SalesOrder(

            customer_id=customer_list[1].id,

            product="Maize Flour 10kg",

            quantity=3000,

            unit_price=15000,

            total_amount=45000000,

            status="Processing"

        ),



        SalesOrder(

            customer_id=customer_list[2].id,

            product="Cassava Flour 10kg",

            quantity=1500,

            unit_price=18000,

            total_amount=27000000,

            status="Completed"

        )

    ]


    db.add_all(orders)


    db.commit()


    db.close()