"""
Esan ERP Delivery Service
Nile Harvest Foods Ltd.

Handles:
- Delivery creation
- Delivery status updates
- Delivery retrieval
"""

from datetime import datetime
from database import SessionLocal
from models import Delivery


def generate_delivery_number():
    """
    Generate unique delivery number
    """

    db = SessionLocal()

    try:

        count = (
            db.query(Delivery)
            .count()
        )

        return f"DEL-{datetime.now().year}-{count + 1:05d}"

    finally:

        db.close()



def create_delivery(
    order_id,
    destination,
    driver=None,
    vehicle=None
):
    """
    Create delivery record from sales order
    """

    db = SessionLocal()

    try:

        delivery = Delivery(

            delivery_number=
            generate_delivery_number(),

            order_id=order_id,

            destination=destination,

            driver=driver,

            vehicle=vehicle,

            status="Pending",

            created_at=datetime.utcnow()

        )


        db.add(delivery)

        db.commit()

        db.refresh(delivery)


        return delivery


    except Exception:

        db.rollback()

        raise


    finally:

        db.close()



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



def get_delivery(delivery_id):

    db = SessionLocal()

    try:

        return (
            db.query(Delivery)
            .filter(
                Delivery.id == delivery_id
            )
            .first()
        )

    finally:

        db.close()



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

            delivery.delivered_date = (
                datetime.utcnow()
            )


        db.commit()

        db.refresh(delivery)


        return delivery


    except Exception:

        db.rollback()

        raise


    finally:

        db.close()
