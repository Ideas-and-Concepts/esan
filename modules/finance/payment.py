"""
Payments Module
Nile Harvest Foods Ltd.
Esan ERP - Payment Management
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from database import SessionLocal
from models import Payment, Invoice, Customer

def get_db():
    return SessionLocal()

def payments_page():
    st.title("💰 Payment Management")
    tab1, tab2, tab3 = st.tabs(["Record Payment", "View Payments", "Payment Summary"])
    with tab1:
        record_payment()
    with tab2:
        view_payments()
    with tab3:
        payment_summary()

def record_payment():
    st.subheader("Record New Payment")
    db = get_db()
    try:
        invoices = db.query(Invoice).filter(Invoice.status.in_(["Unpaid", "Partial"])).all()
        if not invoices:
            st.warning("No unpaid invoices available.")
            return
        inv_options = {}
        for inv in invoices:
            customer = db.query(Customer).filter(Customer.id == inv.customer_id).first()
            payments = db.query(Payment).filter(Payment.invoice_id == inv.id).all()
            paid = sum(p.amount for p in payments)
            balance = inv.amount - paid
            label = f"{inv.invoice_number} - {customer.name if customer else 'N/A'} (Balance: ${balance:,.2f})"
            inv_options[label] = inv.id

        with st.form("payment_form"):
            selected = st.selectbox("Invoice", list(inv_options.keys()))
            amount = st.number_input("Payment Amount", min_value=0.0, step=0.01)
            method = st.selectbox("Payment Method", ["Cash", "Bank Transfer", "Mobile Money", "Cheque", "Credit Card", "Other"])
            reference = st.text_input("Reference (Optional)")
            st.date_input("Payment Date", datetime.now().date())
            if st.form_submit_button("Record Payment"):
                if amount <= 0:
                    st.error("Please enter a valid amount.")
                    return
                new_payment = Payment(
                    invoice_id=inv_options[selected],
                    amount=amount,
                    payment_method=method,
                    reference=reference,
                    status="Completed",
                    created_at=datetime.utcnow()
                )
                db.add(new_payment)
                inv = db.query(Invoice).filter(Invoice.id == inv_options[selected]).first()
                if inv:
                    total_paid = sum(p.amount for p in db.query(Payment).filter(Payment.invoice_id == inv.id).all()) + amount
                    if total_paid >= inv.amount:
                        inv.status = "Paid"
                    elif total_paid > 0:
                        inv.status = "Partial"
                db.commit()
                st.success(f"Payment of ${amount:,.2f} recorded successfully!")
                st.rerun()
    finally:
        db.close()

def view_payments():
    st.subheader("Payment History")
    db = get_db()
    try:
        payments = db.query(Payment).order_by(Payment.created_at.desc()).all()
        if payments:
            data = []
            for p in payments:
                inv = db.query(Invoice).filter(Invoice.id == p.invoice_id).first()
                customer = db.query(Customer).filter(Customer.id == inv.customer_id).first() if inv else None
                data.append({
                    'Date': p.created_at.strftime('%Y-%m-%d'),
                    'Invoice': inv.invoice_number if inv else 'N/A',
                    'Customer': customer.name if customer else 'N/A',
                    'Amount': f"${p.amount:,.2f}",
                    'Method': p.payment_method,
                    'Reference': p.reference or 'N/A',
                    'Status': p.status
                })
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No payments recorded yet.")
    finally:
        db.close()

def payment_summary():
    st.subheader("Payment Summary")
    db = get_db()
    try:
        payments = db.query(Payment).all()
        if payments:
            total = sum(p.amount for p in payments)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Collected", f"${total:,.2f}")
            with col2:
                st.metric("Total Payments", len(payments))
            with col3:
                st.metric("Average", f"${total/len(payments):,.2f}")

            st.subheader("Payments by Method")
            method_totals = {}
            for p in payments:
                method_totals[p.payment_method] = method_totals.get(p.payment_method, 0) + p.amount
            method_df = pd.DataFrame(list(method_totals.items()), columns=['Method', 'Amount'])
            st.bar_chart(method_df.set_index('Method'))
        else:
            st.info("No payment data available.")
    finally:
        db.close()