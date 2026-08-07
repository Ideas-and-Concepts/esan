"""
Esan ERP Invoice Service
Nile Harvest Foods Ltd.

Handles:
- Invoice creation
- Invoice listing
- Invoice status updates
"""

from datetime import datetime

from database import SessionLocal

from models import (
    Invoice,
    SalesOrder,
    Customer
)



# =====================================
# GET ALL INVOICES
# =====================================

def get_all_invoices():

    db = SessionLocal()

    try:

        return (
            db.query(Invoice)
            .order_by(
                Invoice.created_at.desc()
            )
            .all()
        )

    finally:

        db.close()



# =====================================
# CREATE INVOICE
# =====================================

def create_invoice(order_id):

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



        invoice_number = (
            "INV-"
            +
            datetime.now()
            .strftime("%Y%m%d%H%M%S")
        )



        invoice = Invoice(

            invoice_number=invoice_number,

            customer_id=order.customer_id,

            order_id=order.id,

            amount=order.total_amount,

            status="Unpaid"

        )


        db.add(invoice)


        db.commit()

        db.refresh(invoice)


        return invoice



    except Exception:

        db.rollback()

        raise


    finally:

        db.close()



# =====================================
# UPDATE INVOICE STATUS
# =====================================

def update_invoice_status(
        invoice_id,
        status
):

    db = SessionLocal()

    try:

        invoice = (
            db.query(Invoice)
            .filter(
                Invoice.id == invoice_id
            )
            .first()
        )


        if not invoice:

            return None



        invoice.status = status


        db.commit()

        db.refresh(invoice)


        return invoice



    finally:

        db.close()



# =====================================
# GET CUSTOMER INVOICES
# =====================================

def get_customer_invoices(
        customer_id
):

    db = SessionLocal()

    try:

        return (
            db.query(Invoice)
            .filter(
                Invoice.customer_id == customer_id
            )
            .all()
        )


    finally:

        db.close()



# =====================================
# INVOICE SUMMARY
# =====================================

def invoice_summary():

    db = SessionLocal()

    try:

        invoices = (
            db.query(Invoice)
            .all()
        )


        return {

            "total":
                len(invoices),

            "paid":
                len(
                    [
                        i for i in invoices
                        if i.status == "Paid"
                    ]
                ),

            "unpaid":
                len(
                    [
                        i for i in invoices
                        if i.status == "Unpaid"
                    ]
                ),

            "amount":
                sum(
                    i.amount or 0
                    for i in invoices
                )

        }


    finally:

        db.close()
