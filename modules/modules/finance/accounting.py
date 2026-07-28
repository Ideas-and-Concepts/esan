"""
Accounting Module
Esan ERP - Basic General Ledger
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from database import SessionLocal
from models import FinanceTransaction

def get_db():
    return SessionLocal()

def accounting_page():
    st.title("📒 Accounting (General Ledger)")
    tab1, tab2 = st.tabs(["Transactions", "Add Transaction"])
    with tab1:
        view_transactions()
    with tab2:
        add_transaction()

def view_transactions():
    db = get_db()
    try:
        trans = db.query(FinanceTransaction).order_by(FinanceTransaction.created_at.desc()).limit(100).all()
        if trans:
            data = [{
                'Date': t.created_at.strftime('%Y-%m-%d'),
                'Type': t.transaction_type,
                'Category': t.category,
                'Description': t.description,
                'Amount': f"${t.amount:,.2f}",
                'Reference': t.reference
            } for t in trans]
            st.dataframe(pd.DataFrame(data), use_container_width=True)
        else:
            st.info("No transactions recorded.")
    finally:
        db.close()

def add_transaction():
    st.subheader("New Journal Entry")
    with st.form("add_accounting_trans"):
        trans_type = st.selectbox("Type", ["Income", "Expense", "Transfer", "Asset Purchase", "Liability"])
        category = st.text_input("Category")
        description = st.text_area("Description")
        amount = st.number_input("Amount", min_value=0.0, step=0.01)
        reference = st.text_input("Reference")
        if st.form_submit_button("Save"):
            if amount > 0:
                db = get_db()
                try:
                    t = FinanceTransaction(
                        transaction_type=trans_type,
                        category=category,
                        description=description,
                        amount=amount,
                        reference=reference,
                        created_at=datetime.utcnow()
                    )
                    db.add(t)
                    db.commit()
                    st.success("Transaction recorded!")
                    st.rerun()
                except Exception as e:
                    db.rollback()
                    st.error(f"Error: {e}")
                finally:
                    db.close()