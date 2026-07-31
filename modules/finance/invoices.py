"""
Invoices Module – uses invoice_service and payment_service
"""

import streamlit as st
import pandas as pd
from services.invoice_service import (
    get_all_invoices, create_invoice, get_invoice_balance
)
from services.sales_service import get_all_sales_orders
from services.payment_service import get_payments_by_invoice

def invoices_page():
    st.title("🧾 Invoices")
    tab1, tab2 = st.tabs(["Create Invoice", "View Invoices"])
    with tab1:
        create_view()
    with tab2:
        view_invoices()

def create_view():
    st.subheader("Generate Invoice from Delivered Orders")
    orders = get_all_sales_orders()
    delivered = [o for o in orders if o.status == "Delivered"]
    if not delivered:
        st.warning("No delivered orders available.")
        return
    order_nums = [o.order_number for o in delivered]
    selected = st.selectbox("Order", order_nums)
    if st.button("Create Invoice"):
        order_id = next(o.id for o in delivered if o.order_number == selected)
        inv = create_invoice(order_id)
        st.success(f"Invoice {inv.invoice_number} created!")
        st.rerun()

def view_invoices():
    invoices = get_all_invoices()
    if invoices:
        data = []
        for inv in invoices:
            balance = get_invoice_balance(inv.id)
            data.append({
                "Invoice #": inv.invoice_number,
                "Customer ID": inv.customer_id,
                "Amount": f"${inv.amount:,.2f}",
                "Balance": f"${balance:,.2f}",
                "Status": inv.status
            })
        st.dataframe(pd.DataFrame(data), use_container_width=True)
    else:
        st.info("No invoices.")
