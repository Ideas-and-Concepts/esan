"""
Quotations Module – uses sales_service
"""

import streamlit as st
import pandas as pd
from services.sales_service import (
    get_all_customers,
    create_quotation,
    get_all_quotations
)

def quotations_page():
    st.title("📄 Sales Quotations")
    tab1, tab2 = st.tabs(["Create Quotation", "View Quotations"])
    with tab1:
        create_quotation_view()
    with tab2:
        view_quotations()

def create_quotation_view():
    customers = get_all_customers()
    if not customers:
        st.warning("No customers.")
        return
    cust_options = {c.name: c.id for c in customers}
    selected = st.selectbox("Customer", list(cust_options.keys()))

    st.markdown("### Quotation Items")
    if 'quotation_items' not in st.session_state:
        st.session_state.quotation_items = []
    with st.form("add_quote_item", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        product = col1.text_input("Product")
        qty = col2.number_input("Quantity", min_value=0.0)
        price = col3.number_input("Unit Price", min_value=0.0)
        if st.form_submit_button("Add"):
            if product and qty>0 and price>0:
                st.session_state.quotation_items.append({'product_name': product, 'quantity': qty, 'unit_price': price})

    if st.session_state.quotation_items:
        df = pd.DataFrame(st.session_state.quotation_items)
        st.dataframe(df, use_container_width=True)
        total = sum(it['quantity']*it['unit_price'] for it in st.session_state.quotation_items)
        st.markdown(f"**Total:** ${total:,.2f}")
        if st.button("Clear"):
            st.session_state.quotation_items = []
            st.rerun()

    if st.button("Create Quotation", type="primary"):
        if not st.session_state.quotation_items:
            st.error("No items.")
            return
        try:
            q = create_quotation(cust_options[selected], st.session_state.quotation_items)
            st.success(f"Quotation {q.quotation_number} created!")
            st.session_state.quotation_items = []
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

def view_quotations():
    quotes = get_all_quotations()
    if quotes:
        data = [{
            'Number': q.quotation_number,
            'Customer ID': q.customer_id,
            'Status': q.status,
            'Total': f"${q.total_amount:,.2f}",
            'Date': q.created_at.strftime('%Y-%m-%d')
        } for q in quotes]
        st.dataframe(pd.DataFrame(data), use_container_width=True)
    else:
        st.info("No quotations.")
