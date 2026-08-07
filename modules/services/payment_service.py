"""
Esan ERP Payment Service
Nile Harvest Foods Ltd.

Handles:
- Customer payments
- Payment records
- Invoice settlement
"""

from datetime import datetime

from database import SessionLocal

from models import (
    Payment,
    Invoice,
    FinanceTransaction
)



# =====================================
# GET ALL PAYMENTS
# =====================================

def get_all_payments():

    db = SessionLocal()

    try:

        return (
            db.query(Payment)
            .order_by(
                Payment.created_at.desc()
            )
            .all()
        )

    finally:

        db.close()



# =====================================
# CREATE PAYMENT
# =====================================

def create_payment(
        invoice_id,
        amount,
        payment_method,
        reference=None
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

            raise Exception(
                "Invoice not found"
            )



        payment = Payment(

            invoice_id=invoice_id,

            amount=amount,

            payment_method=payment_method,

            reference=reference,

            status="Completed"

        )


        db.add(payment)



        # Update invoice

        if amount >= invoice.amount:

            invoice.status = "Paid"

        else:

            invoice.status = "Partially Paid"



        # Create finance record

        transaction = FinanceTransaction(

            transaction_type="Income",

            category="Customer Payment",

            description=
            f"Payment for invoice {invoice.invoice_number}",

            amount=amount,

            reference=reference,

            created_at=datetime.utcnow()

        )


        db.add(transaction)


        db.commit()


        db.refresh(payment)


        return payment



    except Exception:

        db.rollback()

        raise


    finally:

        db.close()



# =====================================
# UPDATE PAYMENT STATUS
# =====================================

def update_payment_status(
        payment_id,
        status
):

    db = SessionLocal()

    try:

        payment = (
            db.query(Payment)
            .filter(
                Payment.id == payment_id
            )
            .first()
        )


        if not payment:

            return None


        payment.status = status


        db.commit()


        db.refresh(payment)


        return payment



    finally:

        db.close()



# =====================================
# GET PAYMENTS BY INVOICE
# =====================================

def get_invoice_payments(
        invoice_id
):

    db = SessionLocal()

    try:

        return (
            db.query(Payment)
            .filter(
                Payment.invoice_id == invoice_id
            )
            .all()
        )


    finally:

        db.close()



# =====================================
# PAYMENT SUMMARY
# =====================================

def payment_summary():

    db = SessionLocal()

    try:

        payments = (
            db.query(Payment)
            .all()
        )


        return {

            "total_payments":
                len(payments),

            "total_received":
                sum(
                    p.amount or 0
                    for p in payments
                )

        }


    finally:

        db.close()