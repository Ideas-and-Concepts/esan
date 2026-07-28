"""
Invoicing Module
Nile Harvest Foods Ltd.
Esan ERP - Invoice Management
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from database import SessionLocal
from models import Invoice, SalesOrder, Customer, Payment

def get_db():
    return SessionLocal()

def generate_invoice_number():
    db = get_db()
    count = db.query(Invoice).count()
    db.close()
    return f"INV-{datetime.now().strftime('%Y%m')}-{count + 1:04d}"

def invoices_page():
    st.title("🧾 Invoice Management")
    tab1, tab2, tab3 = st.tabs(["Create Invoice", "View Invoices", "Invoice Details"])
    with tab1:
        create_invoice()
    with tab2:
        view_invoices()
    with tab3:
        view_invoice_details()

def create_invoice():
    st.subheader("Generate New Invoice")
    db = get_db()
    try:
        orders = db.query(SalesOrder).filter(SalesOrder.status == "Delivered").all()
        if not orders:
            st.warning("No delivered orders available for invoicing.")
            return
        order_options = {f"{o.order_number}": o.id for o in orders}
        with st.form("invoice_form"):
            selected = st.selectbox("Sales Order", list(order_options.keys()))
            order = db.query(SalesOrder).filter(SalesOrder.id == order_options[selected]).first()
            if order:
                customer = db.query(Customer).filter(Customer.id == order.customer_id).first()
                st.info(f"Customer: {customer.name if customer else 'N/A'}")
                st.info(f"Order Total: ${order.total_amount:,.2f}")
            st.date_input("Invoice Date", datetime.now().date())
            st.date_input("Due Date", datetime.now().date())
            if st.form_submit_button("Generate Invoice"):
                invoice_number = generate_invoice_number()
                new_inv = Invoice(
                    invoice_number=invoice_number,
                    customer_id=order.customer_id,
                    order_id=order.id,
                    amount=order.total_amount,
                    status="Unpaid",
                    created_at=datetime.utcnow()
                )
                db.add(new_inv)
                db.commit()
                st.success(f"Invoice {invoice_number} generated!")
                st.rerun()
    finally:
        db.close()

def view_invoices():
    st.subheader("All Invoices")
    db = get_db()
    try:
        invoices = db.query(Invoice).order_by(Invoice.created_at.desc()).all()
        if invoices:
            data = []
            for inv in invoices:
                customer = db.query(Customer).filter(Customer.id == inv.customer_id).first()
                payments = db.query(Payment).filter(Payment.invoice_id == inv.id).all()
                paid = sum(p.amount for p in payments)
                balance = inv.amount - paid
                data.append({
                    'Invoice #': inv.invoice_number,
                    'Customer': customer.name if customer else 'N/A',
                    'Amount': f"${inv.amount:,.2f}",
                    'Paid': f"${paid:,.2f}",
                    'Balance': f"${balance:,.2f}",
                    'Status': inv.status,
                    'Date': inv.created_at.strftime('%Y-%m-%d') if inv.created_at else 'N/A'
                })
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)

            total_invoiced = sum(inv.amount for inv in invoices)
            total_paid = sum(
                sum(p.amount for p in db.query(Payment).filter(Payment.invoice_id == inv.id).all())
                for inv in invoices
            )
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Invoiced", f"${total_invoiced:,.2f}")
            with col2:
                st.metric("Total Paid", f"${total_paid:,.2f}")
            with col3:
                st.metric("Outstanding", f"${total_invoiced - total_paid:,.2f}")
        else:
            st.info("No invoices found.")
    finally:
        db.close()

def view_invoice_details():
    st.subheader("Invoice Details")
    db = get_db()
    try:
        invoices = db.query(Invoice).order_by(Invoice.created_at.desc()).all()
        if invoices:
            inv_options = {inv.invoice_number: inv.id for inv in invoices}
            selected = st.selectbox("Select Invoice", list(inv_options.keys()))
            if selected:
                inv = db.query(Invoice).filter(Invoice.id == inv_options[selected]).first()
                if inv:
                    customer = db.query(Customer).filter(Customer.id == inv.customer_id).first()
                    order = db.query(SalesOrder).filter(SalesOrder.id == inv.order_id).first()
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Invoice Number:** {inv.invoice_number}")
                        st.markdown(f"**Customer:** {customer.name if customer else 'N/A'}")
                        st.markdown(f"**Order:** {order.order_number if order else 'N/A'}")
                    with col2:
                        st.markdown(f"**Amount:** ${inv.amount:,.2f}")
                        st.markdown(f"**Status:** {inv.status}")
                        st.markdown(f"**Date:** {inv.created_at.strftime('%Y-%m-%d')}")
                    st.markdown("---")
                    st.subheader("Payment History")
                    payments = db.query(Payment).filter(Payment.invoice_id == inv.id).order_by(Payment.created_at.desc()).all()
                    if payments:
                        pay_data = []
                        total_paid = 0
                        for p in payments:
                            pay_data.append({
                                'Date': p.created_at.strftime('%Y-%m-%d'),
                                'Amount': f"${p.amount:,.2f}",
                                'Method': p.payment_method,
                                'Reference': p.reference or 'N/A',
                                'Status': p.status
                            })
                            total_paid += p.amount
                        st.dataframe(pd.DataFrame(pay_data), use_container_width=True)
                        st.markdown(f"**Total Paid:** ${total_paid:,.2f}")
                        st.markdown(f"**Balance Due:** ${inv.amount - total_paid:,.2f}")
                    else:
                        st.info("No payments recorded yet.")
        else:
            st.info("No invoices available.")
    finally:
        db.close()
