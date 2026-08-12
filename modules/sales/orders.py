"""
Esan ERP - Sales Orders Module

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Version 1.4.0 Alpha

Functions:
- Create Sales Orders
- Select customers
- Create orders from quotations
- Add multiple order items
- Calculate order totals
- View Sales Orders
- Search Sales Orders
- Filter by status
- Edit Sales Orders
- Update Sales Order status
- Delete Sales Orders
"""

import streamlit as st
import pandas as pd

from datetime import datetime

from services.sales_service import (
    get_all_customers,
    get_all_quotations,
    get_quotation,
    get_all_sales_orders,
    get_sales_order,
    get_sales_products,
    create_sales_order,
    create_sales_order_from_quotation,
    update_sales_order_status,
    delete_sales_order,
    generate_sales_order_number,
    SALES_ORDER_STATUSES,
)


# ============================================================
# SESSION STATE
# ============================================================

if "editing_sales_order" not in st.session_state:
    st.session_state.editing_sales_order = None

if "delete_sales_order_id" not in st.session_state:
    st.session_state.delete_sales_order_id = None


# ============================================================
# HELPERS
# ============================================================

def format_currency(value):
    """Format an amount as UGX."""

    try:
        return f"UGX {float(value or 0):,.2f}"
    except (TypeError, ValueError):
        return "UGX 0.00"


def get_customer_label(customer):
    """Create a readable customer selector label."""

    if not customer:
        return "Unknown Customer"

    phone = getattr(customer, "phone", None)

    return (
        f"{customer.name} | "
        f"{phone or 'No phone'}"
    )


def get_order_number(order):
    """Support order_number and so_number schemas."""

    order_number = getattr(
        order,
        "order_number",
        None,
    )

    if order_number:
        return order_number

    order_number = getattr(
        order,
        "so_number",
        None,
    )

    if order_number:
        return order_number

    return f"SO-{order.id:05d}"


def get_item_total(quantity, unit_price):
    """Calculate an order item total."""

    return float(quantity or 0) * float(
        unit_price or 0
    )


# ============================================================
# CREATE SALES ORDER
# ============================================================

def create_sales_order_form():

    st.subheader("➕ Create Sales Order")

    customers = get_all_customers(
        active_only=True
    )

    if not customers:

        st.warning(
            "No active customers are available. "
            "Please create a customer first."
        )

        return

    customer_options = {
        get_customer_label(customer):
            customer.id
        for customer in customers
    }

    selected_customer = st.selectbox(
        "Customer",
        options=list(
            customer_options.keys()
        ),
    )

    customer_id = customer_options[
        selected_customer
    ]

    st.markdown(
        "### Order Information"
    )

    col1, col2 = st.columns(2)

    with col1:

        status = st.selectbox(
            "Sales Order Status",
            SALES_ORDER_STATUSES,
            index=0,
        )

    with col2:

        order_date = st.date_input(
            "Order Date",
            value=datetime.today().date(),
        )

    notes = st.text_area(
        "Order Notes",
        placeholder=(
            "Optional customer instructions, "
            "delivery notes or internal remarks."
        ),
    )

    st.markdown(
        "### Sales Order Items"
    )

    products = get_sales_products(
        active_only=True
    )

    product_names = [
        product.name
        for product in products
        if getattr(product, "name", None)
    ]

    item_count = st.number_input(
        "Number of Items",
        min_value=1,
        max_value=50,
        value=1,
        step=1,
    )

    items = []

    total_amount = 0.0

    for index in range(
        int(item_count)
    ):

        st.markdown(
            f"#### Item {index + 1}"
        )

        col1, col2, col3 = st.columns(
            [3, 1, 1]
        )

        with col1:

            if product_names:

                product_options = [
                    "Custom Product"
                ] + product_names

                selected_product = st.selectbox(
                    "Product",
                    options=product_options,
                    key=(
                        f"sales_order_product_"
                        f"{index}"
                    ),
                )

                if selected_product == "Custom Product":

                    product_name = st.text_input(
                        "Product Name",
                        key=(
                            f"sales_order_custom_"
                            f"{index}"
                        ),
                        placeholder="Enter product name",
                    )

                else:

                    product_name = selected_product

            else:

                product_name = st.text_input(
                    "Product / Item",
                    key=(
                        f"sales_order_product_"
                        f"{index}"
                    ),
                    placeholder="e.g. Maize Flour 25Kg",
                )

        with col2:

            quantity = st.number_input(
                "Quantity",
                min_value=0.0,
                step=1.0,
                key=(
                    f"sales_order_quantity_"
                    f"{index}"
                ),
            )

        with col3:

            unit_price = st.number_input(
                "Unit Price",
                min_value=0.0,
                step=100.0,
                key=(
                    f"sales_order_price_"
                    f"{index}"
                ),
            )

        item_total = get_item_total(
            quantity,
            unit_price,
        )

        st.write(
            f"Item Total: **"
            f"{format_currency(item_total)}"
            f"**"
        )

        if product_name.strip():

            items.append(
                {
                    "product_name":
                        product_name.strip(),

                    "quantity":
                        quantity,

                    "unit_price":
                        unit_price,
                }
            )

        total_amount += item_total

    st.divider()

    col1, col2 = st.columns(
        [2, 1]
    )

    with col1:

        st.caption(
            f"Order date: "
            f"{order_date.strftime('%Y-%m-%d')}"
        )

    with col2:

        st.metric(
            "Order Total",
            format_currency(
                total_amount
            ),
        )

    if st.button(
        "💾 Create Sales Order",
        type="primary",
        use_container_width=True,
    ):

        if not items:

            st.error(
                "Please enter at least one "
                "sales order item."
            )

            return

        for item in items:

            if item["quantity"] <= 0:

                st.error(
                    f"Quantity for "
                    f"{item['product_name']} "
                    "must be greater than zero."
                )

                return

            if item["unit_price"] < 0:

                st.error(
                    f"Unit price for "
                    f"{item['product_name']} "
                    "cannot be negative."
                )

                return

        try:

            order = create_sales_order(
                customer_id=customer_id,
                items=items,
                status=status,
                notes=notes.strip() or None,
            )

            st.success(
                f"Sales Order "
                f"{get_order_number(order)} "
                "created successfully."
            )

            st.rerun()

        except Exception as e:

            st.error(
                f"Unable to create Sales Order: {e}"
            )


# ============================================================
# CREATE ORDER FROM QUOTATION
# ============================================================

def create_from_quotation_form():

    st.subheader(
        "📄 Create Sales Order from Quotation"
    )

    quotations = get_all_quotations(
        status="Accepted"
    )

    if not quotations:

        st.info(
            "There are no accepted quotations "
            "available for conversion."
        )

        return

    quotation_options = {}

    for quotation in quotations:

        customer_name = (
            quotation.customer.name
            if quotation.customer
            else "Unknown Customer"
        )

        quotation_options[
            (
                f"{quotation.quotation_number}"
                f" | "
                f"{customer_name}"
                f" | "
                f"{format_currency(quotation.total_amount)}"
            )
        ] = quotation.id

    selected = st.selectbox(
        "Accepted Quotation",
        options=list(
            quotation_options.keys()
        ),
    )

    quotation_id = quotation_options[
        selected
    ]

    quotation = get_quotation(
        quotation_id
    )

    if not quotation:

        st.error(
            "Quotation could not be found."
        )

        return

    st.markdown(
        "### Quotation Preview"
    )

    customer_name = (
        quotation.customer.name
        if quotation.customer
        else "Unknown Customer"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.write(
            f"**Quotation:** "
            f"{quotation.quotation_number}"
        )

    with col2:

        st.write(
            f"**Customer:** "
            f"{customer_name}"
        )

    with col3:

        st.write(
            f"**Total:** "
            f"{format_currency(quotation.total_amount)}"
        )

    if quotation.items:

        item_data = []

        for item in quotation.items:

            item_data.append(
                {
                    "Product":
                        item.product_name,

                    "Quantity":
                        item.quantity,

                    "Unit Price":
                        format_currency(
                            item.unit_price
                        ),

                    "Total":
                        format_currency(
                            item.total
                        ),
                }
            )

        st.dataframe(
            pd.DataFrame(item_data),
            use_container_width=True,
            hide_index=True,
        )

    order_status = st.selectbox(
        "Initial Sales Order Status",
        SALES_ORDER_STATUSES,
        index=0,
        key="quotation_order_status",
    )

    if st.button(
        "Convert to Sales Order",
        type="primary",
        use_container_width=True,
    ):

        try:

            order = (
                create_sales_order_from_quotation(
                    quotation_id=quotation_id,
                    status=order_status,
                )
            )

            st.success(
                f"Quotation "
                f"{quotation.quotation_number} "
                f"converted to Sales Order "
                f"{get_order_number(order)}."
            )

            st.rerun()

        except Exception as e:

            st.error(
                f"Unable to convert quotation: {e}"
            )


# ============================================================
# VIEW SALES ORDER
# ============================================================

def view_sales_order_details(
    order_id
):

    order = get_sales_order(
        order_id
    )

    if not order:

        st.error(
            "Sales Order could not be found."
        )

        return

    order_number = get_order_number(
        order
    )

    customer_name = (
        order.customer.name
        if getattr(order, "customer", None)
        else "Unknown Customer"
    )

    st.markdown(
        f"### 📄 {order_number}"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.write(
            f"**Customer:** "
            f"{customer_name}"
        )

    with col2:

        st.write(
            f"**Status:** "
            f"{order.status}"
        )

    with col3:

        st.write(
            f"**Total:** "
            f"{format_currency(order.total_amount)}"
        )

    order_date = getattr(
        order,
        "order_date",
        None,
    )

    if order_date:

        if hasattr(
            order_date,
            "strftime",
        ):

            st.caption(
                f"Order Date: "
                f"{order_date.strftime('%Y-%m-%d')}"
            )

    notes = getattr(
        order,
        "notes",
        None,
    )

    if notes:

        st.write(
            f"**Notes:** {notes}"
        )

    st.markdown(
        "#### Order Items"
    )

    items = getattr(
        order,
        "items",
        []
    )

    if not items:

        st.info(
            "This order has no items."
        )

        return

    item_data = []

    for item in items:

        item_data.append(
            {
                "Product":
                    item.product_name,

                "Quantity":
                    item.quantity,

                "Unit Price":
                    format_currency(
                        item.unit_price
                    ),

                "Total":
                    format_currency(
                        item.total
                    ),
            }
        )

    st.dataframe(
        pd.DataFrame(item_data),
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# EDIT SALES ORDER
# ============================================================

def edit_sales_order_form(
    order_id
):

    order = get_sales_order(
        order_id
    )

    if not order:

        st.error(
            "Sales Order could not be found."
        )

        return

    customers = get_all_customers(
        active_only=True
    )

    if not customers:

        st.warning(
            "No active customers are available."
        )

        return

    customer_options = {
        get_customer_label(customer):
            customer.id
        for customer in customers
    }

    current_customer = next(
        (
            label
            for label, customer_id
            in customer_options.items()
            if customer_id
            == order.customer_id
        ),
        list(
            customer_options.keys()
        )[0],
    )

    selected_customer = st.selectbox(
        "Customer",
        options=list(
            customer_options.keys()
        ),
        index=list(
            customer_options.keys()
        ).index(
            current_customer
        ),
        key="edit_sales_order_customer",
    )

    customer_id = customer_options[
        selected_customer
    ]

    status = st.selectbox(
        "Status",
        SALES_ORDER_STATUSES,
        index=(
            SALES_ORDER_STATUSES.index(
                order.status
            )
            if order.status
            in SALES_ORDER_STATUSES
            else 0
        ),
        key="edit_sales_order_status",
    )

    notes = st.text_area(
        "Notes",
        value=getattr(
            order,
            "notes",
            ""
        ) or "",
        key="edit_sales_order_notes",
    )

    st.markdown(
        "### Order Items"
    )

    existing_items = getattr(
        order,
        "items",
        []
    )

    item_count = st.number_input(
        "Number of Items",
        min_value=1,
        max_value=50,
        value=max(
            1,
            len(existing_items),
        ),
        step=1,
        key="edit_sales_order_item_count",
    )

    products = get_sales_products(
        active_only=True
    )

    product_names = [
        product.name
        for product in products
        if getattr(product, "name", None)
    ]

    items = []

    total_amount = 0.0

    for index in range(
        int(item_count)
    ):

        existing_item = (
            existing_items[index]
            if index < len(existing_items)
            else None
        )

        default_product = (
            existing_item.product_name
            if existing_item
            else ""
        )

        default_quantity = (
            float(
                existing_item.quantity
            )
            if existing_item
            else 0.0
        )

        default_price = (
            float(
                existing_item.unit_price
            )
            if existing_item
            else 0.0
        )

        col1, col2, col3 = st.columns(
            [3, 1, 1]
        )

        with col1:

            if product_names:

                product_options = [
                    "Custom Product"
                ] + product_names

                if (
                    default_product
                    in product_names
                ):

                    default_index = (
                        product_options.index(
                            default_product
                        )
                    )

                    selected_product = st.selectbox(
                        "Product",
                        options=product_options,
                        index=default_index,
                        key=(
                            f"edit_order_product_"
                            f"{index}"
                        ),
                    )

                    product_name = (
                        selected_product
                    )

                else:

                    selected_product = st.selectbox(
                        "Product",
                        options=product_options,
                        index=0,
                        key=(
                            f"edit_order_product_"
                            f"{index}"
                        ),
                    )

                    if (
                        selected_product
                        == "Custom Product"
                    ):

                        product_name = st.text_input(
                            "Product Name",
                            value=default_product,
                            key=(
                                f"edit_order_custom_"
                                f"{index}"
                            ),
                        )

                    else:

                        product_name = (
                            selected_product
                        )

            else:

                product_name = st.text_input(
                    "Product / Item",
                    value=default_product,
                    key=(
                        f"edit_order_product_"
                        f"{index}"
                    ),
                )

        with col2:

            quantity = st.number_input(
                "Quantity",
                min_value=0.0,
                value=default_quantity,
                step=1.0,
                key=(
                    f"edit_order_quantity_"
                    f"{index}"
                ),
            )

        with col3:

            unit_price = st.number_input(
                "Unit Price",
                min_value=0.0,
                value=default_price,
                step=100.0,
                key=(
                    f"edit_order_price_"
                    f"{index}"
                ),
            )

        item_total = get_item_total(
            quantity,
            unit_price,
        )

        st.write(
            f"Item Total: **"
            f"{format_currency(item_total)}"
            f"**"
        )

        if product_name.strip():

            items.append(
                {
                    "product_name":
                        product_name.strip(),

                    "quantity":
                        quantity,

                    "unit_price":
                        unit_price,
                }
            )

        total_amount += item_total

    st.metric(
        "Updated Order Total",
        format_currency(
            total_amount
        ),
    )

    st.info(
        "Sales Order editing is currently "
        "limited to the fields supported by "
        "the Sales service."
    )

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "💾 Save Changes",
            type="primary",
            use_container_width=True,
        ):

            if not items:

                st.error(
                    "Please enter at least one item."
                )

                return

            try:

                from services.sales_service import (
                    update_sales_order,
                )

                updated = update_sales_order(
                    order_id=order_id,
                    customer_id=customer_id,
                    items=items,
                    status=status,
                    notes=notes.strip() or None,
                )

                if updated:

                    st.success(
                        f"{get_order_number(updated)} "
                        "updated successfully."
                    )

                    st.session_state.editing_sales_order = (
                        None
                    )

                    st.rerun()

                else:

                    st.error(
                        "Sales Order not found."
                    )

            except ImportError:

                st.error(
                    "The Sales service does not yet "
                    "provide update_sales_order()."
                )

            except Exception as e:

                st.error(
                    f"Unable to update Sales Order: {e}"
                )

    with col2:

        if st.button(
            "Cancel",
            use_container_width=True,
        ):

            st.session_state.editing_sales_order = (
                None
            )

            st.rerun()


# ============================================================
# VIEW SALES ORDERS
# ============================================================

def view_sales_orders():

    st.subheader(
        "📋 Sales Orders"
    )

    orders = get_all_sales_orders()

    if not orders:

        st.info(
            "No Sales Orders have been created yet."
        )

        return

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    search = st.text_input(
        "🔎 Search Sales Orders",
        placeholder=(
            "Search by order number..."
        ),
    )

    # --------------------------------------------------------
    # STATUS FILTER
    # --------------------------------------------------------

    status_filter = st.selectbox(
        "Filter by Status",
        ["All"] + SALES_ORDER_STATUSES,
    )

    filtered_orders = orders

    if search:

        search_lower = search.lower()

        filtered_orders = [
            order
            for order in filtered_orders
            if search_lower
            in get_order_number(
                order
            ).lower()
        ]

    if status_filter != "All":

        filtered_orders = [
            order
            for order in filtered_orders
            if order.status
            == status_filter
        ]

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    total_value = sum(
        float(
            order.total_amount or 0
        )
        for order in filtered_orders
    )

    approved_value = sum(
        float(
            order.total_amount or 0
        )
        for order in filtered_orders
        if order.status == "Approved"
    )

    delivered_value = sum(
        float(
            order.total_amount or 0
        )
        for order in filtered_orders
        if order.status == "Delivered"
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Orders",
            len(filtered_orders),
        )

    with col2:

        st.metric(
            "Total Value",
            format_currency(
                total_value
            ),
        )

    with col3:

        st.metric(
            "Approved",
            format_currency(
                approved_value
            ),
        )

    with col4:

        st.metric(
            "Delivered",
            format_currency(
                delivered_value
            ),
        )

    st.divider()

    # --------------------------------------------------------
    # TABLE
    # --------------------------------------------------------

    data = []

    for order in filtered_orders:

        customer_name = (
            order.customer.name
            if getattr(
                order,
                "customer",
                None,
            )
            else "Unknown Customer"
        )

        created_at = getattr(
            order,
            "created_at",
            None,
        )

        data.append(
            {
                "Order":
                    get_order_number(order),

                "Customer":
                    customer_name,

                "Status":
                    order.status,

                "Total":
                    format_currency(
                        order.total_amount
                    ),

                "Created":
                    (
                        created_at.strftime(
                            "%Y-%m-%d"
                        )
                        if created_at
                        else ""
                    ),
            }
        )

    st.dataframe(
        pd.DataFrame(data),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    # --------------------------------------------------------
    # SELECT ORDER
    # --------------------------------------------------------

    order_options = {
        (
            f"{get_order_number(order)}"
            f" | "
            f"{order.customer.name if getattr(order, 'customer', None) else 'Unknown Customer'}"
        ):
            order.id
        for order in filtered_orders
    }

    if not order_options:

        st.info(
            "No Sales Orders match the selected filters."
        )

        return

    selected_order_label = st.selectbox(
        "Select Sales Order",
        options=list(
            order_options.keys()
        ),
    )

    selected_order_id = order_options[
        selected_order_label
    ]

    # --------------------------------------------------------
    # DETAILS
    # --------------------------------------------------------

    view_sales_order_details(
        selected_order_id
    )

    st.divider()

    # --------------------------------------------------------
    # MANAGEMENT
    # --------------------------------------------------------

    st.subheader(
        "⚙️ Sales Order Management"
    )

    action_col1, action_col2, action_col3 = st.columns(
        3
    )

    with action_col1:

        if st.button(
            "✏️ Edit Order",
            use_container_width=True,
        ):

            st.session_state.editing_sales_order = (
                selected_order_id
            )

            st.rerun()

    with action_col2:

        selected_order = get_sales_order(
            selected_order_id
        )

        current_status = (
            selected_order.status
            if selected_order
            else "Draft"
        )

        new_status = st.selectbox(
            "New Status",
            SALES_ORDER_STATUSES,
            index=(
                SALES_ORDER_STATUSES.index(
                    current_status
                )
                if current_status
                in SALES_ORDER_STATUSES
                else 0
            ),
            key="sales_order_new_status",
        )

        if st.button(
            "🔄 Update Status",
            use_container_width=True,
        ):

            try:

                updated = (
                    update_sales_order_status(
                        selected_order_id,
                        new_status,
                    )
                )

                if updated:

                    st.success(
                        f"{get_order_number(updated)} "
                        f"status changed to "
                        f"{updated.status}."
                    )

                    st.rerun()

            except Exception as e:

                st.error(
                    f"Unable to update status: {e}"
                )

    with action_col3:

        if st.button(
            "🗑️ Delete Order",
            use_container_width=True,
        ):

            st.session_state.delete_sales_order_id = (
                selected_order_id
            )

            st.rerun()

    # --------------------------------------------------------
    # DELETE CONFIRMATION
    # --------------------------------------------------------

    if (
        st.session_state.get(
            "delete_sales_order_id"
        )
        == selected_order_id
    ):

        st.warning(
            "Deleting this Sales Order will "
            "also remove its order items."
        )

        confirm_col1, confirm_col2 = st.columns(
            2
        )

        with confirm_col1:

            if st.button(
                "Yes, Delete Order",
                type="primary",
                use_container_width=True,
            ):

                try:

                    deleted = delete_sales_order(
                        selected_order_id
                    )

                    if deleted:

                        st.session_state.delete_sales_order_id = (
                            None
                        )

                        st.success(
                            "Sales Order deleted successfully."
                        )

                        st.rerun()

                    else:

                        st.error(
                            "Sales Order could not be found."
                        )

                except Exception as e:

                    st.error(
                        f"Unable to delete Sales Order: {e}"
                    )

        with confirm_col2:

            if st.button(
                "Cancel Delete",
                use_container_width=True,
            ):

                st.session_state.delete_sales_order_id = (
                    None
                )

                st.rerun()


# ============================================================
# MAIN SALES ORDERS PAGE
# ============================================================

def sales_orders_page():

    st.title(
        "🧾 Sales Order Management"
    )

    st.caption(
        "Manage customer orders from quotation "
        "conversion through fulfilment."
    )

    tab1, tab2, tab3 = st.tabs(
        [
            "➕ New Sales Order",
            "📄 From Quotation",
            "📋 Sales Orders",
        ]
    )

    with tab1:

        create_sales_order_form()

    with tab2:

        create_from_quotation_form()

    with tab3:

        if st.session_state.get(
            "editing_sales_order"
        ):

            st.subheader(
                "✏️ Edit Sales Order"
            )

            edit_sales_order_form(
                st.session_state.editing_sales_order
            )

        else:

            view_sales_orders()


# ============================================================
# STANDALONE EXECUTION
# ============================================================

if __name__ == "__main__":

    sales_orders_page()