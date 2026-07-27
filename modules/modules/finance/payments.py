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
    """Main payments page."""
    st.title("💰 Payment Management")
    
    tab1, tab2, tab3 = st.tabs(["Record Payment", "View Payments", "Payment Summary"])
    
    with tab1:
        record_payment()
    
    with tab2:
        view_payments()
    
    with tab3:
        payment_summary()

def record_payment():
    """Record a new payment."""
    st.subheader("Record New Payment")
    
    db = get_db()
    
    try:
        # Get unpaid invoices
        invoices = db.query(Invoice).filter(
            Invoice.status.in_(["Unpaid", "Partial"])
        ).all()
        
        if not invoices:
            st.warning("No unpaid invoices available.")
            return
        
        invoice_options = {}
        for inv in invoices:
            customer = db.query(Customer).filter(Customer.id == inv.customer_id).first()
            payments = db.query(Payment).filter(Payment.invoice_id == inv.id).all()
            paid_amount = sum(p.amount for p in payments)
            balance = inv.amount - paid_amount
            
            label = f"{inv.invoice_number} - {customer.name if customer else 'N/A'} (Balance: ${balance:,.2f})"
            invoice_options[label] = inv.id
        
        with st.form("payment_form"):
            selected_invoice = st.selectbox("Invoice", list(invoice_options.keys()))
            
            col1, col2 = st.columns(2)
            with col1:
                amount = st.number_input("Payment Amount", min_value=0.0, step=0.01)
            with col2:
                payment_method = st.selectbox(
                    "Payment Method",
                    ["Cash", "Bank Transfer", "Mobile Money", "Cheque", "Credit Card", "Other"]
                )
            
            reference = st.text_input("Reference Number (Optional)")
            payment_date = st.date_input("Payment Date", datetime.now().date())
            
            if st.form_submit_button("Record Payment"):
                if amount <= 0:
                    st.error("Please enter a valid amount.")
                    return
                
                try:
                    new_payment = Payment(
                        invoice_id=invoice_options[selected_invoice],
                        amount=amount,
                        payment_method=payment_method,
                        reference=reference,
                        status="Completed",
                        created_at=datetime.utcnow()
                    )
                    db.add(new_payment)
                    
                    # Update invoice status
                    invoice = db.query(Invoice).filter(
                        Invoice.id == invoice_options[selected_invoice]
                    ).first()
                    
                    if invoice:
                        total_paid = sum(p.amount for p in db.query(Payment).filter(
                            Payment.invoice_id == invoice.id
                        ).all()) + amount
                        
                        if total_paid >= invoice.amount:
                            invoice.status = "Paid"
                        elif total_paid > 0:
                            invoice.status = "Partial"
                    
                    db.commit()
                    st.success(f"Payment of ${amount:,.2f} recorded successfully!")
                    st.rerun()
                    
                except Exception as e:
                    db.rollback()
                    st.error(f"Error recording payment: {str(e)}")
    
    finally:
        db.close()

def view_payments():
    """View all payments."""
    st.subheader("Payment History")
    
    db = get_db()
    
    try:
        payments = db.query(Payment).order_by(Payment.created_at.desc()).all()
        
        if payments:
            data = []
            for payment in payments:
                invoice = db.query(Invoice).filter(Invoice.id == payment.invoice_id).first()
                customer = None
                if invoice:
                    customer = db.query(Customer).filter(Customer.id == invoice.customer_id).first()
                
                data.append({
                    'Date': payment.created_at.strftime('%Y-%m-%d'),
                    'Invoice': invoice.invoice_number if invoice else 'N/A',
                    'Customer': customer.name if customer else 'N/A',
                    'Amount': f"${payment.amount:,.2f}",
                    'Method': payment.payment_method,
                    'Reference': payment.reference or 'N/A',
                    'Status': payment.status
                })
            
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)
            
            # Filter options
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                method_filter = st.multiselect(
                    "Filter by Payment Method",
                    ["Cash", "Bank Transfer", "Mobile Money", "Cheque", "Credit Card", "Other"],
                    default=[]
                )
        else:
            st.info("No payments recorded yet.")
    
    finally:
        db.close()

def payment_summary():
    """Payment summary and statistics."""
    st.subheader("Payment Summary")
    
    db = get_db()
    
    try:
        payments = db.query(Payment).all()
        
        if payments:
            total_collected = sum(p.amount for p in payments)
            
            # Payment by method
            method_totals = {}
            for payment in payments:
                method_totals[payment.payment_method] = method_totals.get(payment.payment_method, 0) + payment.amount
            
            # Payment by month
            monthly_totals = {}
            for payment in payments:
                month = payment.created_at.strftime('%Y-%m') if payment.created_at else 'Unknown'
                monthly_totals[month] = monthly_totals.get(month, 0) + payment.amount
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Collected", f"${total_collected:,.2f}")
            with col2:
                st.metric("Total Payments", len(payments))
            with col3:
                avg_payment = total_collected / len(payments) if payments else 0
                st.metric("Average Payment", f"${avg_payment:,.2f}")
            
            st.markdown("---")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Payments by Method")
                method_df = pd.DataFrame(list(method_totals.items()), columns=['Method', 'Amount'])
                st.bar_chart(method_df.set_index('Method'))
            
            with col2:
                st.subheader("Payments by Month")
                monthly_df = pd.DataFrame(list(monthly_totals.items()), columns=['Month', 'Amount'])
                st.bar_chart(monthly_df.set_index('Month'))
            
            # Invoice status summary
            st.markdown("---")
            st.subheader("Invoice Status Overview")
            
            invoices = db.query(Invoice).all()
            status_counts = {}
            for inv in invoices:
                status_counts[inv.status] = status_counts.get(inv.status, 0) + 1
            
            status_df = pd.DataFrame(list(status_counts.items()), columns=['Status', 'Count'])
            st.dataframe(status_df, use_container_width=True)
        else:
            st.info("No payment data available.")
    
    finally:
        db.close()