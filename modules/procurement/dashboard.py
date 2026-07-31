"""
Procurement Dashboard – uses procurement_service
"""

import streamlit as st
import pandas as pd
from services.procurement_service import (
    get_all_suppliers, create_supplier,
    get_all_purchase_orders, create_purchase_order
)

def procurement_dashboard():
    st.title("🌾 Procurement")
    tab1, tab2, tab3 = st.tabs(["Suppliers", "Purchase Orders", "New PO"])
    with tab1:
        suppliers_view()
    with tab2:
        po_view()
    with tab3:
        new_po_view()

def suppliers_view():
    suppliers = get_all_suppliers()
    if suppliers:
        data = [{"Name": s.name, "Type": s.supplier_type, "Phone": s.phone, "Email": s.email} for s in suppliers]
        st.dataframe(pd.DataFrame(data), use_container_width=True)
    else:
        st.info("No suppliers.")
    with st.expander("Add Supplier"):
        with st.form("add_supplier"):
            name = st.text_input("Name *")
            stype = st.selectbox("Type", ["Agricultural Supplier", "Manufacturer", "Distributor"])
            phone = st.text_input("Phone")
            email = st.text_input("Email")
            address = st.text_input("Address")
            location = st.text_input("Location")
            country = st.text_input("Country")
            contact = st.text_input("Contact Person")
            if st.form_submit_button("Save"):
                if name:
                    create_supplier(name, phone, email, address, stype, location, country, contact)
                    st.success("Supplier added")
                    st.rerun()

def po_view():
    pos = get_all_purchase_orders()
    if pos:
        data = [{
            "PO #": p.po_number,
            "Supplier ID": p.supplier_id,
            "Status": p.status,
            "Total": f"${p.total_amount:,.2f}",
            "Date": p.created_at.strftime('%Y-%m-%d')
        } for p in pos]
        st.dataframe(pd.DataFrame(data), use_container_width=True)
    else:
        st.info("No POs.")

def new_po_view():
    suppliers = get_all_suppliers()
    if not suppliers:
        st.warning("No suppliers.")
        return
    supplier_names = {s.name: s.id for s in suppliers}
    selected = st.selectbox("Supplier", list(supplier_names.keys()))
    if 'po_items' not in st.session_state:
        st.session_state.po_items = []
    with st.form("add_po_item", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        product = col1.text_input("Product")
        qty = col2.number_input("Qty", min_value=0.0)
        price = col3.number_input("Price", min_value=0.0)
        if st.form_submit_button("Add Item"):
            if product and qty > 0 and price > 0:
                st.session_state.po_items.append({"product_name": product, "quantity": qty, "unit_price": price})
    if st.session_state.po_items:
        st.dataframe(pd.DataFrame(st.session_state.po_items), use_container_width=True)
        if st.button("Clear Items"):
            st.session_state.po_items = []
            st.rerun()
    if st.button("Create PO", type="primary"):
        if not st.session_state.po_items:
            st.error("No items.")
            return
        try:
            po = create_purchase_order(supplier_names[selected], st.session_state.po_items)
            st.success(f"PO {po.po_number} created!")
            st.session_state.po_items = []
            st.rerun()
        except Exception as e:
            st.error(str(e))
