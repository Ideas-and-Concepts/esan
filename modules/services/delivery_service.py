"""
Esan ERP Delivery Service
Nile Harvest Foods Ltd.

Handles:
- Delivery creation
- Delivery tracking
- Delivery status updates
"""

from datetime import datetime

from database import SessionLocal

from models import (
    Delivery,
    SalesOrder
)



# =====================================
# GET ALL DELIVERIES
# =====================================

def get_all_deliveries():

    db = SessionLocal()

    try:

        return (
            db.query(Delivery)
            .order_by(
                Delivery.created_at.desc()
            )
            .all()
        )

    finally:

        db.close()



# =====================================
# CREATE DELIVERY
# =====================================

def create_delivery(
        order_id,
        destination,
        driver=None,
        vehicle=None
):

    db = SessionLocal()

    try:

        order = (
            db.query(SalesOrder)
            .filter(
                SalesOrder.id == order_id
            )
            .first()
        )


        if not order:

            raise Exception(
                "Sales order not found"
            )



        delivery_number = (
            "DN-"
            +
            datetime.now()
            .strftime("%Y%m%d%H%M%S")
        )



        delivery = Delivery(

            delivery_number=delivery_number,

            order_id=order_id,

            destination=destination,

            driver=driver,

            vehicle=vehicle,

            status="Pending"

        )


        db.add(delivery)



        # Update order status

        order.status = "Dispatched"



        db.commit()


        db.refresh(delivery)


        return delivery



    except Exception:

        db.rollback()

        raise


    finally:

        db.close()



# =====================================
# UPDATE DELIVERY STATUS
# =====================================

def update_delivery_status(
        delivery_id,
        status
):

    db = SessionLocal()

    try:

        delivery = (
            db.query(Delivery)
            .filter(
                Delivery.id == delivery_id
            )
            .first()
        )


        if not delivery:

            return None



        delivery.status = status



        if status == "Delivered":

            delivery.delivered_date = datetime.utcnow()


            order = (
                db.query(SalesOrder)
                .filter(
                    SalesOrder.id ==
                    delivery.order_id
                )
                .first()
            )


            if order:

                order.status = "Delivered"



        db.commit()

        db.refresh(delivery)


        return delivery



    finally:

        db.close()



# =====================================
# GET DELIVERY BY ORDER
# =====================================

def get_delivery_by_order(
        order_id
):

    db = SessionLocal()

    try:

        return (
            db.query(Delivery)
            .filter(
                Delivery.order_id == order_id
            )
            .first()
        )

    finally:

        db.close()



# =====================================
# DELIVERY SUMMARY
# =====================================

def delivery_summary():

    db = SessionLocal()

    try:

        deliveries = (
            db.query(Delivery)
            .all()
        )


        return {

            "total":
                len(deliveries),

            "pending":
                len(
                    [
                        d for d in deliveries
                        if d.status == "Pending"
                    ]
                ),

            "delivered":
                len(
                    [
                        d for d in deliveries
                        if d.status == "Delivered"
                    ]
                )

        }


    finally:

        db.close()
