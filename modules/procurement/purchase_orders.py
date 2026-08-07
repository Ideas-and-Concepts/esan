"""
Esan ERP Procurement - Purchase Orders

Nile Harvest Foods Ltd.

Functions:
- Create purchase orders
- View purchase orders
- Update purchase order status
- Receive materials
"""

import streamlit as st
import pandas as pd

from services.procurement_service import (
    get_all_suppliers,
    create_purchase_order,
    get_all_purchase_orders,
    update_purchase_order_status,
    receive_purchase_order
)



def purchase_orders_page():

    st.title("📄 Purchase Orders")


    tab1, tab2, tab3 = st.tabs(
        [
            "➕ Create PO",
            "📋 Purchase Orders",
            "📦 Receive Materials"
        ]
    )


    with tab1:
        create_po()


    with tab2:
        view_purchase_orders()


    with tab3:
        receive_materials()




# =====================================
# CREATE PURCHASE ORDER
# =====================================

def create_po():

    st.subheader(
        "Create Purchase Order"
    )


    suppliers = get_all_suppliers()


    if not suppliers:

        st.warning(
            "Please add suppliers first."
        )

        return



    supplier_map = {

        s.name: s.id

        for s in suppliers

    }



    supplier_name = st.selectbox(

        "Supplier",

        list(supplier_map.keys())

    )


    if "po_items" not in st.session_state:

        st.session_state.po_items = []



    with st.form(
        "po_item_form"
    ):


        col1, col2, col3 = st.columns(3)


        product = col1.text_input(
            "Material/Product"
        )


        quantity = col2.number_input(
            "Quantity",
            min_value=0.0
        )


        price = col3.number_input(
            "Unit Price",
            min_value=0.0
        )


        add = st.form_submit_button(
            "Add Item"
        )



        if add:

            if product and quantity > 0:

                st.session_state.po_items.append(

                    {

                        "product_name": product,

                        "quantity": quantity,

                        "unit_price": price

                    }

                )



    if st.session_state.po_items:


        st.dataframe(

            pd.DataFrame(
                st.session_state.po_items
            ),

            use_container_width=True

        )



    if st.button(
        "Create Purchase Order"
    ):


        if not st.session_state.po_items:

            st.error(
                "Add at least one item."
            )

            return



        try:


            po = create_purchase_order(

                supplier_map[supplier_name],

                st.session_state.po_items

            )


            st.success(

                f"Purchase Order {po.po_number} created"

            )


            st.session_state.po_items = []

            st.rerun()



        except Exception as e:

            st.error(
                str(e)
            )




# =====================================
# VIEW PURCHASE ORDERS
# =====================================

def view_purchase_orders():

    orders = get_all_purchase_orders()


    if not orders:

        st.info(
            "No purchase orders found."
        )

        return



    data = []


    for po in orders:

        data.append(

            {

                "PO Number":
                    po.po_number,

                "Supplier ID":
                    po.supplier_id,

                "Status":
                    po.status,

                "Amount":
                    po.total_amount,

                "Date":
                    po.created_at.strftime(
                        "%Y-%m-%d"
                    )

            }

        )


    st.dataframe(

        pd.DataFrame(data),

        use_container_width=True

    )




# =====================================
# RECEIVE MATERIALS
# =====================================

def receive_materials():

    orders = get_all_purchase_orders()


    if not orders:

        st.info(
            "No purchase orders."
        )

        return



    po_map = {

        po.po_number: po.id

        for po in orders

    }


    selected = st.selectbox(

        "Purchase Order",

        list(po_map.keys())

    )


    if st.button(
        "Receive Goods"
    ):


        try:

            receive_purchase_order(

                po_map[selected]

            )


            st.success(
                "Materials received into warehouse."
            )


            st.rerun()



        except Exception as e:

            st.error(
                str(e)
            )