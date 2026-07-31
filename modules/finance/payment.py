"""
Payments Module – uses payment_service
"""

import streamlit as st
import pandas as pd
from services.payment_service import (
    record_payment, get_all_payments, get_payments_by_invoice
)
from services.invoice_service import get_all_invoices, get_invoice_balance

def payments_page():
    st.title("💰 Payments")
    tab1, tab2 = st.tabs(["Record Payment", "Payment History"])
    with tab1:
        record_view()
    with tab2:
        history_view()

def record_view():
    invoices = get_all_invoices()
    unpaid = [inv for inv in invoices if inv.status != "Paid"]
    if not unpaid:
        st.warning("No unpaid invoices.")
        return
    options = {f"{inv.invoice_number} (Bal: ${get_invoice_balance(inv.id):,.2f})": inv.id for inv in unpaid}
    selected = st.selectbox("Invoice", list(options.keys()))
    amount = st.number_input("Amount", min_value=0.0)
    method = st.selectbox("Method", ["Cash", "Bank Transfer", "Mobile Money", "Cheque"])
    reference = st.text_input("Reference")
    if st.button("Record Payment"):
        if amount > 0:
            record_payment(options[selected], amount, method, reference)
            st.success("Payment recorded")
            st.rerun()

def history_view():
    payments = get_all_payments()
    if payments:
        data = [{
            "Date": p.created_at.strftime('%Y-%m-%d'),
            "Invoice ID": p.invoice_id,
            "Amount": f"${p.amount:,.2f}",
            "Method": p.payment_method,
            "Reference": p.reference
        } for p in payments]
        st.dataframe(pd.DataFrame(data), use_container_width=True)
    else:
        st.info("No payments.")
