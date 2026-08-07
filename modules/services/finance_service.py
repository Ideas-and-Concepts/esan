"""
Esan ERP Finance Service
Nile Harvest Foods Ltd.

Handles:
- Income tracking
- Expense tracking
- Finance transactions
- Dashboard summaries
"""

from datetime import datetime

from database import SessionLocal

from models import FinanceTransaction



# =====================================
# GET ALL TRANSACTIONS
# =====================================

def get_all_transactions():

    db = SessionLocal()

    try:

        return (
            db.query(FinanceTransaction)
            .order_by(
                FinanceTransaction.created_at.desc()
            )
            .all()
        )

    finally:

        db.close()



# =====================================
# CREATE TRANSACTION
# =====================================

def create_transaction(
        transaction_type,
        category,
        description,
        amount,
        reference=None
):

    db = SessionLocal()

    try:

        transaction = FinanceTransaction(

            transaction_type=transaction_type,

            category=category,

            description=description,

            amount=amount,

            reference=reference,

            created_at=datetime.utcnow()

        )


        db.add(transaction)

        db.commit()

        db.refresh(transaction)


        return transaction


    except Exception:

        db.rollback()

        raise


    finally:

        db.close()



# =====================================
# GET INCOME
# =====================================

def get_total_income():

    db = SessionLocal()

    try:

        transactions = (
            db.query(FinanceTransaction)
            .filter(
                FinanceTransaction.transaction_type
                ==
                "Income"
            )
            .all()
        )


        return sum(
            t.amount or 0
            for t in transactions
        )


    finally:

        db.close()



# =====================================
# GET EXPENSES
# =====================================

def get_total_expenses():

    db = SessionLocal()

    try:

        transactions = (
            db.query(FinanceTransaction)
            .filter(
                FinanceTransaction.transaction_type
                ==
                "Expense"
            )
            .all()
        )


        return sum(
            t.amount or 0
            for t in transactions
        )


    finally:

        db.close()



# =====================================
# PROFIT SUMMARY
# =====================================

def finance_summary():

    income = get_total_income()

    expenses = get_total_expenses()


    return {

        "income": income,

        "expenses": expenses,

        "profit":
            income - expenses

    }



# =====================================
# DASHBOARD KPIs
# =====================================

def finance_kpis():

    db = SessionLocal()

    try:

        transactions = (
            db.query(FinanceTransaction)
            .all()
        )


        return {

            "transactions":
                len(transactions),

            "income":
                sum(
                    t.amount or 0
                    for t in transactions
                    if t.transaction_type
                    ==
                    "Income"
                ),

            "expenses":
                sum(
                    t.amount or 0
                    for t in transactions
                    if t.transaction_type
                    ==
                    "Expense"
                )

        }


    finally:

        db.close()