"""
Esan ERP - Sales & Distribution Deliveries Module

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Version 1.4.0 Alpha

Functions:
- Create Delivery Notes
- Select Sales Orders
- Select customers
- Add delivery items
- Calculate delivered quantities
- View deliveries
- Search deliveries
- Filter delivery status
- Update delivery status
- View delivery details
"""

import streamlit as st
import pandas as pd

from datetime import datetime

from services.sales_service import (
    get_all_sales_orders,
    get_sales_order,
)

# Delivery service is imported separately so that all
# database operations remain outside the Streamlit module.
from services.delivery_service import (
    get_all_deliveries,
    get_delivery,
    create_delivery,
    update_delivery_status,
    DELIVERY_STATUSES,
)


# ============================================================
# SESSION STATE
# ============================================================

if "selected_delivery_id" not in st.session_state:
    st.session_state.selected_delivery_id = None


# ============================================================
# HELPERS
# ============================================================

def format_currency(value):
    """Format amount as UGX."""

    try:
        return f"UGX {float(value or 0):,.2f}"
    except (TypeError, ValueError):
        return "UGX 0.00"


def order_number(order):
    """Return the Sales Order number safely."""

    value = getattr(
        order,
        "order_number",
        None,
    )

    if value:
        return value

    value = getattr(
        order,
        "so_number",
        None,
    )

    if value:
        return value

    return f"SO-{order.id:05d}"


def delivery_number(delivery):
    """Return delivery note number safely."""

    value = getattr(
        delivery,
        "delivery_number",
        None,
    )

    if value:
        return value

    value = getattr(
        delivery,
        "dn_number",
        None,
    )

    if value:
        return value

    return f"DN-{delivery.id:05d}"


def get_customer_name(order):
    """Get customer name from Sales Order."""

    customer = getattr(
        order,
        "customer",
        None,
    )

    if customer:
        return customer.name

    return "Unknown Customer"


# ============================================================
# CREATE DELIVERY NOTE
# ============================================================

def create_delivery_form():

    st.subheader(
        "🚚 Create Delivery Note"
    )

    orders = get_all_sales_orders()

    if not orders:

        st.warning(
            "No Sales Orders are available. "
            "Create a Sales Order before creating "
            "a Delivery Note."
        )

        return

    # --------------------------------------------------------
    # Only active fulfilment orders
    # --------------------------------------------------------

    eligible_orders = [
        order
        for order in orders
        if order.status not in [
            "Draft",
            "Cancelled",
        ]
    ]

    if not eligible_orders:

        st.info(
            "There are currently no Sales Orders "
            "available for delivery."
        )

        return

    order_options = {}

    for order in eligible_orders:

        order_options[
            (
                f"{order_number(order)}"
                f" | "
                f"{get_customer_name(order)}"
                f" | "
                f"{format_currency(order.total_amount)}"
            )
        ] = order.id

    selected_order = st.selectbox(
        "Sales Order",
        options=list(
            order_options.keys()
        ),
    )

    selected_order_id = order_options[
        selected_order
    ]

    order = get_sales_order(
        selected_order_id
    )

    if not order:

        st.error(
            "Sales Order could not be loaded."
        )

        return

    # --------------------------------------------------------
    # Order summary
    # --------------------------------------------------------

    st.markdown(
        "### Sales Order Information"
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Sales Order",
            order_number(order),
        )

    with col2:

        st.metric(
            "Customer",
            get_customer_name(order),
        )

    with col3:

        st.metric(
            "Order Status",
            order.status,
        )

    with col4:

        st.metric(
            "Order Total",
            format_currency(
                order.total_amount
            ),
        )

    st.divider()

    # --------------------------------------------------------
    # Delivery information
    # --------------------------------------------------------

    st.markdown(
        "### Delivery Information"
    )

    col1, col2 = st.columns(2)

    with col1:

        delivery_date = st.date_input(
            "Delivery Date",
            value=datetime.today().date(),
        )

    with col2:

        status = st.selectbox(
            "Delivery Status",
            DELIVERY_STATUSES,
        )

    vehicle_number = st.text_input(
        "Vehicle / Registration Number",
        placeholder="e.g. UAX 123A",
    )

    driver_name = st.text_input(
        "Driver Name",
        placeholder="Enter driver name",
    )

    delivery_address = st.text_area(
        "Delivery Address",
        placeholder=(
            "Enter delivery destination."
        ),
    )

    notes = st.text_area(
        "Delivery Notes",
        placeholder=(
            "Optional delivery instructions."
        ),
    )

    # --------------------------------------------------------
    # Delivery items
    # --------------------------------------------------------

    st.markdown(
        "### Delivery Items"
    )

    order_items = getattr(
        order,
        "items",
        []
    )

    if not order_items:

        st.warning(
            "This Sales Order contains no items."
        )

        return

    delivery_items = []

    total_delivery_value = 0.0

    for index, item in enumerate(
        order_items
    ):

        st.markdown(
            f"#### {item.product_name}"
        )

        col1, col2, col3 = st.columns(
            [2, 2, 2]
        )

        ordered_quantity = float(
            item.quantity or 0
        )

        unit_price = float(
            item.unit_price or 0
        )

        with col1:

            st.write(
                f"Ordered: **"
                f"{ordered_quantity:,.2f}"
                f"**"
            )

        with col2:

            delivered_quantity = st.number_input(
                "Delivery Quantity",
                min_value=0.0,
                max_value=ordered_quantity,
                value=ordered_quantity,
                step=1.0,
                key=(
                    f"delivery_quantity_"
                    f"{index}"
                ),
            )

        with col3:

            item_value = (
                delivered_quantity
                * unit_price
            )

            st.write(
                f"Value: **"
                f"{format_currency(item_value)}"
                f"**"
            )

        if delivered_quantity > 0:

            delivery_items.append(
                {
                    "sales_order_item_id":
                        item.id,

                    "product_name":
                        item.product_name,

                    "quantity":
                        delivered_quantity,

                    "unit_price":
                        unit_price,

                    "total":
                        item_value,
                }
            )

            total_delivery_value += (
                item_value
            )

    st.divider()

    st.metric(
        "Delivery Value",
        format_currency(
            total_delivery_value
        ),
    )

    # --------------------------------------------------------
    # Create
    # --------------------------------------------------------

    if st.button(
        "🚚 Create Delivery Note",
        type="primary",
        use_container_width=True,
    ):

        if not delivery_items:

            st.error(
                "Enter at least one delivery quantity."
            )

            return

        if not delivery_address.strip():

            st.warning(
                "Please enter the delivery address."
            )

            return

        try:

            delivery = create_delivery(
                sales_order_id=selected_order_id,
                delivery_date=delivery_date,
                items=delivery_items,
                status=status,
                vehicle_number=(
                    vehicle_number.strip()
                    or None
                ),
                driver_name=(
                    driver_name.strip()
                    or None
                ),
                delivery_address=(
                    delivery_address.strip()
                ),
                notes=(
                    notes.strip()
                    or None
                ),
            )

            st.success(
                f"Delivery Note "
                f"{delivery_number(delivery)} "
                "created successfully."
            )

            st.rerun()

        except Exception as e:

            st.error(
                f"Unable to create Delivery Note: {e}"
            )


# ============================================================
# DELIVERY DETAILS
# ============================================================

def view_delivery_details(
    delivery_id,
):

    delivery = get_delivery(
        delivery_id
    )

    if not delivery:

        st.error(
            "Delivery Note could not be found."
        )

        return

    st.subheader(
        f"📄 {delivery_number(delivery)}"
    )

    sales_order = getattr(
        delivery,
        "sales_order",
        None,
    )

    customer = (
        sales_order.customer
        if sales_order
        and getattr(
            sales_order,
            "customer",
            None,
        )
        else None
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.write(
            f"**Delivery:** "
            f"{delivery_number(delivery)}"
        )

    with col2:

        st.write(
            f"**Sales Order:** "
            f"{order_number(sales_order) if sales_order else 'N/A'}"
        )

    with col3:

        st.write(
            f"**Customer:** "
            f"{customer.name if customer else 'Unknown'}"
        )

    with col4:

        st.write(
            f"**Status:** "
            f"{delivery.status}"
        )

    st.divider()

    # --------------------------------------------------------
    # Logistics
    # --------------------------------------------------------

    st.markdown(
        "### 🚛 Logistics"
    )

    col1, col2 = st.columns(2)

    with col1:

        st.write(
            f"**Vehicle:** "
            f"{getattr(delivery, 'vehicle_number', None) or 'Not specified'}"
        )

        st.write(
            f"**Driver:** "
            f"{getattr(delivery, 'driver_name', None) or 'Not specified'}"
        )

    with col2:

        st.write(
            f"**Delivery Address:** "
            f"{getattr(delivery, 'delivery_address', None) or 'Not specified'}"
        )

        delivery_date = getattr(
            delivery,
            "delivery_date",
            None,
        )

        if delivery_date:

            if hasattr(
                delivery_date,
                "strftime",
            ):

                st.write(
                    f"**Delivery Date:** "
                    f"{delivery_date.strftime('%Y-%m-%d')}"
                )

    # --------------------------------------------------------
    # Items
    # --------------------------------------------------------

    st.markdown(
        "### 📦 Delivered Items"
    )

    items = getattr(
        delivery,
        "items",
        []
    )

    if not items:

        st.info(
            "No delivery items found."
        )

    else:

        data = []

        for item in items:

            data.append(
                {
                    "Product":
                        item.product_name,

                    "Quantity":
                        item.quantity,

                    "Unit Price":
                        format_currency(
                            item.unit_price
                        ),

                    "Value":
                        format_currency(
                            item.total
                        ),
                }
            )

        st.dataframe(
            pd.DataFrame(data),
            use_container_width=True,
            hide_index=True,
        )

    notes = getattr(
        delivery,
        "notes",
        None,
    )

    if notes:

        st.markdown(
            "### Notes"
        )

        st.write(notes)


# ============================================================
# VIEW DELIVERIES
# ============================================================

def view_deliveries():

    st.subheader(
        "📋 Delivery Notes"
    )

    deliveries = get_all_deliveries()

    if not deliveries:

        st.info(
            "No Delivery Notes have been created yet."
        )

        return

    # --------------------------------------------------------
    # Search
    # --------------------------------------------------------

    search = st.text_input(
        "🔎 Search Delivery Notes",
        placeholder=(
            "Search by delivery number..."
        ),
    )

    # --------------------------------------------------------
    # Status filter
    # --------------------------------------------------------

    status_filter = st.selectbox(
        "Filter by Status",
        ["All"] + DELIVERY_STATUSES,
    )

    filtered = deliveries

    if search:

        search_lower = search.lower()

        filtered = [
            delivery
            for delivery in filtered
            if search_lower
            in delivery_number(
                delivery
            ).lower()
        ]

    if status_filter != "All":

        filtered = [
            delivery
            for delivery in filtered
            if delivery.status
            == status_filter
        ]

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    total_deliveries = len(
        filtered
    )

    completed = len(
        [
            delivery
            for delivery in filtered
            if delivery.status
            == "Delivered"
        ]
    )

    pending = len(
        [
            delivery
            for delivery in filtered
            if delivery.status
            in [
                "Draft",
                "Pending",
                "Dispatched",
            ]
        ]
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Total Deliveries",
            total_deliveries,
        )

    with col2:

        st.metric(
            "Pending",
            pending,
        )

    with col3:

        st.metric(
            "Completed",
            completed,
        )

    st.divider()

    # --------------------------------------------------------
    # Table
    # --------------------------------------------------------

    data = []

    for delivery in filtered:

        sales_order = getattr(
            delivery,
            "sales_order",
            None,
        )

        customer = (
            sales_order.customer.name
            if sales_order
            and getattr(
                sales_order,
                "customer",
                None,
            )
            else "Unknown Customer"
        )

        delivery_date = getattr(
            delivery,
            "delivery_date",
            None,
        )

        data.append(
            {
                "Delivery Note":
                    delivery_number(
                        delivery
                    ),

                "Sales Order":
                    (
                        order_number(
                            sales_order
                        )
                        if sales_order
                        else "N/A"
                    ),

                "Customer":
                    customer,

                "Status":
                    delivery.status,

                "Delivery Date":
                    (
                        delivery_date.strftime(
                            "%Y-%m-%d"
                        )
                        if delivery_date
                        and hasattr(
                            delivery_date,
                            "strftime",
                        )
                        else ""
                    ),
            }
        )

    st.dataframe(
        pd.DataFrame(data),
        use_container_width=True,
        hide_index=True,
    )

    if not filtered:

        st.info(
            "No deliveries match the selected filters."
        )

        return

    # --------------------------------------------------------
    # Select delivery
    # --------------------------------------------------------

    delivery_options = {}

    for delivery in filtered:

        sales_order = getattr(
            delivery,
            "sales_order",
            None,
        )

        delivery_options[
            (
                f"{delivery_number(delivery)}"
                f" | "
                f"{order_number(sales_order) if sales_order else 'N/A'}"
            )
        ] = delivery.id

    selected_delivery = st.selectbox(
        "Select Delivery Note",
        options=list(
            delivery_options.keys()
        ),
    )

    selected_delivery_id = delivery_options[
        selected_delivery
    ]

    view_delivery_details(
        selected_delivery_id
    )

    st.divider()

    # --------------------------------------------------------
    # Status Management
    # --------------------------------------------------------

    st.subheader(
        "🔄 Delivery Status Management"
    )

    selected_delivery = get_delivery(
        selected_delivery_id
    )

    current_status = (
        selected_delivery.status
        if selected_delivery
        else DELIVERY_STATUSES[0]
    )

    col1, col2 = st.columns(2)

    with col1:

        new_status = st.selectbox(
            "New Status",
            DELIVERY_STATUSES,
            index=(
                DELIVERY_STATUSES.index(
                    current_status
                )
                if current_status
                in DELIVERY_STATUSES
                else 0
            ),
            key="delivery_status_selector",
        )

    with col2:

        st.write("")
        st.write("")

        if st.button(
            "🔄 Update Delivery Status",
            use_container_width=True,
        ):

            try:

                updated = update_delivery_status(
                    selected_delivery_id,
                    new_status,
                )

                if updated:

                    st.success(
                        f"{delivery_number(updated)} "
                        f"status updated to "
                        f"{updated.status}."
                    )

                    st.rerun()

                else:

                    st.error(
                        "Delivery Note not found."
                    )

            except Exception as e:

                st.error(
                    f"Unable to update delivery status: {e}"
                )


# ============================================================
# MAIN PAGE
# ============================================================

def deliveries_page():

    st.title(
        "🚚 Delivery Management"
    )

    st.caption(
        "Manage Delivery Notes and Sales Order fulfilment."
    )

    tab1, tab2 = st.tabs(
        [
            "➕ Create Delivery",
            "📋 Delivery Notes",
        ]
    )

    with tab1:

        create_delivery_form()

    with tab2:

        view_deliveries()


# ============================================================
# STANDALONE EXECUTION
# ============================================================

if __name__ == "__main__":

    deliveries_page()