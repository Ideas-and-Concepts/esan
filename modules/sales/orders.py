"""
Esan ERP
Sales Orders Module

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System
"""

import streamlit as st

from database import SessionLocal
from models import Customer, Product

from services.sales_service import (
    get_all_sales_orders,
    get_sales_order,
    get_sales_order_items,
    create_sales_order,
    update_sales_order,
    add_sales_order_item,
    update_sales_order_item,
    delete_sales_order_item,
    calculate_sales_order_total,
    check_order_stock,
    confirm_sales_order,
    reserve_stock,
    release_stock,
    cancel_sales_order,
)


# ==========================================================
# HELPERS
# ==========================================================

def _get(obj, field, default=None):
    """Safely retrieve a model attribute."""
    return getattr(obj, field, default)


def _money(value):
    try:
        return f"UGX {float(value):,.0f}"
    except (TypeError, ValueError):
        return "UGX 0"


def _quantity(value):
    try:
        return f"{float(value):,.2f}"
    except (TypeError, ValueError):
        return "0.00"


def _status(order):
    return _get(order, "status", "Draft") or "Draft"


def _status_icon(status):
    status = str(status).lower()

    if status == "draft":
        return "🟡"

    if status == "confirmed":
        return "🟢"

    if status in ("cancelled", "canceled"):
        return "🔴"

    if status in ("completed", "delivered"):
        return "🔵"

    return "⚪"


# ==========================================================
# PAGE HEADER
# ==========================================================

def sales_orders_page():

    st.title("🧾 Sales Orders")

    st.caption(
        "Create, manage, confirm and reserve stock "
        "for customer Sales Orders."
    )

    # ------------------------------------------------------
    # Database session
    # ------------------------------------------------------

    db = SessionLocal()

    try:

        # ==================================================
        # TABS
        # ==================================================

        tab_create, tab_orders, tab_manage = st.tabs(
            [
                "➕ Create Order",
                "📋 Sales Orders",
                "⚙️ Manage Order",
            ]
        )

        # ==================================================
        # CREATE ORDER
        # ==================================================

        with tab_create:

            st.subheader("Create Sales Order")

            customers = (
                db.query(Customer)
                .order_by(Customer.name)
                .all()
            )

            if not customers:

                st.warning(
                    "No customers are available. "
                    "Create a customer first."
                )

            else:

                customer_options = {
                    f"{customer.name} "
                    f"(ID: {customer.id})":
                    customer.id
                    for customer in customers
                }

                selected_customer = st.selectbox(
                    "Customer",
                    list(customer_options.keys()),
                    key="sales_order_customer",
                )

                customer_id = customer_options[
                    selected_customer
                ]

                order_date = st.date_input(
                    "Order Date",
                    key="sales_order_date",
                )

                notes = st.text_area(
                    "Notes",
                    placeholder=(
                        "Optional order notes..."
                    ),
                    key="sales_order_notes",
                )

                if st.button(
                    "Create Draft Sales Order",
                    type="primary",
                    use_container_width=True,
                ):

                    try:

                        order = create_sales_order(
                            db=db,
                            customer_id=customer_id,
                            order_date=order_date,
                            notes=notes,
                        )

                        st.session_state[
                            "selected_sales_order_id"
                        ] = order.id

                        st.success(
                            f"Sales Order #{order.id} "
                            "created successfully."
                        )

                        st.rerun()

                    except Exception as e:

                        st.error(
                            f"Could not create Sales Order: {e}"
                        )

        # ==================================================
        # SALES ORDER LIST
        # ==================================================

        with tab_orders:

            st.subheader("Sales Orders")

            orders = get_all_sales_orders(db)

            if not orders:

                st.info(
                    "No Sales Orders have been created yet."
                )

            else:

                # --------------------------------------------------
                # Filters
                # --------------------------------------------------

                statuses = sorted(
                    {
                        _status(order)
                        for order in orders
                    }
                )

                filter_options = [
                    "All"
                ] + statuses

                selected_status = st.selectbox(
                    "Filter by Status",
                    filter_options,
                    key="sales_order_status_filter",
                )

                search = st.text_input(
                    "Search Sales Orders",
                    placeholder=(
                        "Search by order number or customer..."
                    ),
                    key="sales_order_search",
                ).strip().lower()

                filtered_orders = []

                for order in orders:

                    status = _status(order)

                    customer = (
                        db.query(Customer)
                        .filter(
                            Customer.id
                            == order.customer_id
                        )
                        .first()
                    )

                    customer_name = _get(
                        customer,
                        "name",
                        "Unknown",
                    )

                    if (
                        selected_status != "All"
                        and status != selected_status
                    ):
                        continue

                    searchable = (
                        f"{order.id} "
                        f"{customer_name}"
                    ).lower()

                    if (
                        search
                        and search not in searchable
                    ):
                        continue

                    filtered_orders.append(
                        (
                            order,
                            customer_name,
                        )
                    )

                # --------------------------------------------------
                # Display
                # --------------------------------------------------

                for order, customer_name in filtered_orders:

                    status = _status(order)

                    total = calculate_sales_order_total(
                        db,
                        order.id,
                    )

                    reserved = (
                        bool(
                            _get(
                                order,
                                "stock_reserved",
                                False,
                            )
                        )
                        or bool(
                            _get(
                                order,
                                "reserved",
                                False,
                            )
                        )
                    )

                    with st.container(
                        border=True
                    ):

                        col1, col2, col3, col4, col5 = st.columns(
                            [
                                1.2,
                                2,
                                1.4,
                                1.6,
                                1.4,
                            ]
                        )

                        with col1:

                            st.markdown(
                                f"### SO-{order.id:05d}"
                            )

                        with col2:

                            st.write(
                                f"**{customer_name}**"
                            )

                        with col3:

                            st.write(
                                f"{_status_icon(status)} "
                                f"{status}"
                            )

                        with col4:

                            st.write(
                                _money(total)
                            )

                        with col5:

                            if reserved:

                                st.success(
                                    "Reserved"
                                )

                            else:

                                st.caption(
                                    "Not Reserved"
                                )

                        if st.button(
                            "Open",
                            key=f"open_order_{order.id}",
                            use_container_width=True,
                        ):

                            st.session_state[
                                "selected_sales_order_id"
                            ] = order.id

                            st.rerun()

        # ==================================================
        # MANAGE ORDER
        # ==================================================

        with tab_manage:

            selected_order_id = st.session_state.get(
                "selected_sales_order_id"
            )

            if not selected_order_id:

                st.info(
                    "Select a Sales Order from the "
                    "'Sales Orders' tab to manage it."
                )

            else:

                order = get_sales_order(
                    db,
                    selected_order_id,
                )

                if not order:

                    st.error(
                        "The selected Sales Order "
                        "could not be found."
                    )

                else:

                    render_sales_order_manager(
                        db,
                        order,
                    )

    finally:

        db.close()


# ==========================================================
# ORDER MANAGER
# ==========================================================

def render_sales_order_manager(
    db,
    order,
):

    customer = (
        db.query(Customer)
        .filter(
            Customer.id
            == order.customer_id
        )
        .first()
    )

    customer_name = _get(
        customer,
        "name",
        "Unknown",
    )

    status = _status(order)

    # ======================================================
    # HEADER
    # ======================================================

    st.subheader(
        f"SO-{order.id:05d}"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Customer",
            customer_name,
        )

    with col2:

        st.metric(
            "Status",
            status,
        )

    with col3:

        total = calculate_sales_order_total(
            db,
            order.id,
        )

        st.metric(
            "Order Total",
            _money(total),
        )

    # ======================================================
    # STOCK STATUS
    # ======================================================

    reserved = (
        bool(
            _get(
                order,
                "stock_reserved",
                False,
            )
        )
        or bool(
            _get(
                order,
                "reserved",
                False,
            )
        )
    )

    if reserved:

        st.success(
            "🟢 Stock is reserved for this order."
        )

    else:

        st.info(
            "⚪ Stock has not been reserved."
        )

    st.divider()

    # ======================================================
    # EDIT ORDER
    # ======================================================

    if status.lower() == "draft":

        st.markdown(
            "### ✏️ Edit Order"
        )

        customers = (
            db.query(Customer)
            .order_by(Customer.name)
            .all()
        )

        customer_map = {
            customer.name:
                customer.id
            for customer in customers
        }

        customer_names = list(
            customer_map.keys()
        )

        current_customer_name = (
            customer_name
        )

        if current_customer_name not in customer_names:
            customer_names.append(
                current_customer_name
            )

        selected_customer_name = st.selectbox(
            "Customer",
            customer_names,
            index=customer_names.index(
                current_customer_name
            ),
            key=f"edit_customer_{order.id}",
        )

        new_customer_id = customer_map.get(
            selected_customer_name,
            order.customer_id,
        )

        current_notes = _get(
            order,
            "notes",
            "",
        )

        new_notes = st.text_area(
            "Notes",
            value=current_notes or "",
            key=f"edit_notes_{order.id}",
        )

        if st.button(
            "Save Order Changes",
            key=f"save_order_{order.id}",
            type="primary",
        ):

            try:

                update_sales_order(
                    db=db,
                    order_id=order.id,
                    customer_id=new_customer_id,
                    notes=new_notes,
                )

                st.success(
                    "Sales Order updated successfully."
                )

                st.rerun()

            except Exception as e:

                st.error(
                    f"Could not update order: {e}"
                )

    # ======================================================
    # ORDER ITEMS
    # ======================================================

    st.markdown(
        "### 📦 Order Items"
    )

    items = get_sales_order_items(
        db,
        order.id,
    )

    if items:

        for item in items:

            product = (
                db.query(Product)
                .filter(
                    Product.id
                    == item.product_id
                )
                .first()
            )

            product_name = _get(
                product,
                "name",
                f"Product #{item.product_id}",
            )

            quantity = float(
                _get(
                    item,
                    "quantity",
                    0,
                )
                or 0
            )

            unit_price = float(
                _get(
                    item,
                    "unit_price",
                    _get(
                        item,
                        "price",
                        0,
                    ),
                )
                or 0
            )

            item_total = quantity * unit_price

            with st.container(
                border=True
            ):

                col1, col2, col3, col4 = st.columns(
                    [3, 1.2, 1.5, 1]
                )

                with col1:

                    st.write(
                        f"**{product_name}**"
                    )

                with col2:

                    st.write(
                        _quantity(quantity)
                    )

                with col3:

                    st.write(
                        _money(unit_price)
                    )

                with col4:

                    st.write(
                        _money(item_total)
                    )

                # --------------------------------------------------
                # Draft item controls
                # --------------------------------------------------

                if status.lower() == "draft":

                    edit_col, delete_col = st.columns(2)

                    with edit_col:

                        with st.expander(
                            "Edit"
                        ):

                            new_quantity = st.number_input(
                                "Quantity",
                                min_value=0.01,
                                value=max(
                                    quantity,
                                    0.01,
                                ),
                                key=f"qty_{item.id}",
                            )

                            new_price = st.number_input(
                                "Unit Price",
                                min_value=0.0,
                                value=max(
                                    unit_price,
                                    0.0,
                                ),
                                key=f"price_{item.id}",
                            )

                            if st.button(
                                "Save",
                                key=f"save_item_{item.id}",
                            ):

                                try:

                                    update_sales_order_item(
                                        db=db,
                                        item_id=item.id,
                                        quantity=new_quantity,
                                        unit_price=new_price,
                                    )

                                    st.success(
                                        "Item updated."
                                    )

                                    st.rerun()

                                except Exception as e:

                                    st.error(
                                        f"Could not update item: {e}"
                                    )

                    with delete_col:

                        if st.button(
                            "Delete",
                            key=f"delete_item_{item.id}",
                        ):

                            try:

                                delete_sales_order_item(
                                    db=db,
                                    item_id=item.id,
                                )

                                st.success(
                                    "Item deleted."
                                )

                                st.rerun()

                            except Exception as e:

                                st.error(
                                    f"Could not delete item: {e}"
                                )

    else:

        st.info(
            "No items have been added to this order."
        )

    # ======================================================
    # ADD ITEM
    # ======================================================

    if status.lower() == "draft":

        st.markdown(
            "### ➕ Add Product"
        )

        products = (
            db.query(Product)
            .order_by(Product.name)
            .all()
        )

        if not products:

            st.warning(
                "No products are available."
            )

        else:

            product_map = {
                f"{product.name} "
                f"(ID: {product.id})":
                product
                for product in products
            }

            selected_product_label = st.selectbox(
                "Product",
                list(product_map.keys()),
                key=f"add_product_{order.id}",
            )

            selected_product = product_map[
                selected_product_label
            ]

            default_price = float(
                _get(
                    selected_product,
                    "selling_price",
                    0,
                )
                or 0
            )

            col1, col2 = st.columns(2)

            with col1:

                quantity = st.number_input(
                    "Quantity",
                    min_value=0.01,
                    value=1.0,
                    step=1.0,
                    key=f"add_qty_{order.id}",
                )

            with col2:

                unit_price = st.number_input(
                    "Unit Price",
                    min_value=0.0,
                    value=default_price,
                    step=100.0,
                    key=f"add_price_{order.id}",
                )

            if st.button(
                "Add Product to Order",
                key=f"add_item_button_{order.id}",
                type="primary",
                use_container_width=True,
            ):

                try:

                    add_sales_order_item(
                        db=db,
                        order_id=order.id,
                        product_id=selected_product.id,
                        quantity=quantity,
                        unit_price=unit_price,
                    )

                    st.success(
                        "Product added to Sales Order."
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        f"Could not add product: {e}"
                    )

    # ======================================================
    # STOCK CHECK
    # ======================================================

    st.divider()

    st.markdown(
        "### 📊 Stock Availability"
    )

    if items:

        try:

            stock_result = check_order_stock(
                db,
                order.id,
            )

            if stock_result["available"]:

                st.success(
                    "🟢 All required stock is available."
                )

            else:

                st.warning(
                    "🟠 Some items do not have "
                    "sufficient available stock."
                )

            for stock_item in stock_result["items"]:

                col1, col2, col3, col4 = st.columns(
                    [3, 1.2, 1.2, 1]
                )

                with col1:

                    st.write(
                        stock_item["product"]
                    )

                with col2:

                    st.write(
                        f"Required: "
                        f"{_quantity(stock_item['requested'])}"
                    )

                with col3:

                    st.write(
                        f"Available: "
                        f"{_quantity(stock_item['available'])}"
                    )

                with col4:

                    if stock_item["sufficient"]:

                        st.success("OK")

                    else:

                        st.error("Short")

        except Exception as e:

            st.error(
                f"Could not check stock: {e}"
            )

    # ======================================================
    # ORDER ACTIONS
    # ======================================================

    st.divider()

    st.markdown(
        "### ⚙️ Order Actions"
    )

    action_col1, action_col2, action_col3 = st.columns(3)

    # ------------------------------------------------------
    # CONFIRM
    # ------------------------------------------------------

    with action_col1:

        if status.lower() == "draft":

            if st.button(
                "✅ Confirm Order",
                key=f"confirm_{order.id}",
                use_container_width=True,
            ):

                try:

                    confirm_sales_order(
                        db=db,
                        order_id=order.id,
                        reserve=True,
                    )

                    st.success(
                        "Sales Order confirmed and "
                        "stock reserved."
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        f"Could not confirm order: {e}"
                    )

    # ------------------------------------------------------
    # RESERVE
    # ------------------------------------------------------

    with action_col2:

        if (
            status.lower()
            == "confirmed"
            and not reserved
        ):

            if st.button(
                "📦 Reserve Stock",
                key=f"reserve_{order.id}",
                use_container_width=True,
            ):

                try:

                    reserve_stock(
                        db=db,
                        order_id=order.id,
                    )

                    st.success(
                        "Stock reserved successfully."
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        f"Could not reserve stock: {e}"
                    )

        elif reserved:

            st.success(
                "📦 Stock Reserved"
            )

    # ------------------------------------------------------
    # RELEASE
    # ------------------------------------------------------

    with action_col3:

        if reserved:

            if st.button(
                "↩️ Release Stock",
                key=f"release_{order.id}",
                use_container_width=True,
            ):

                try:

                    release_stock(
                        db=db,
                        order_id=order.id,
                    )

                    st.success(
                        "Stock reservation released."
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        f"Could not release stock: {e}"
                    )

    # ======================================================
    # CANCEL
    # ======================================================

    if status.lower() not in (
        "cancelled",
        "canceled",
        "completed",
        "delivered",
        "closed",
    ):

        st.divider()

        st.markdown(
            "### ⚠️ Cancel Order"
        )

        st.warning(
            "Cancelling this Sales Order will release "
            "any stock reservation associated with it."
        )

        confirm_cancel = st.checkbox(
            "I understand that this order will be cancelled.",
            key=f"cancel_confirm_{order.id}",
        )

        if confirm_cancel:

            if st.button(
                "❌ Cancel Sales Order",
                key=f"cancel_order_{order.id}",
                use_container_width=True,
            ):

                try:

                    cancel_sales_order(
                        db=db,
                        order_id=order.id,
                    )

                    st.success(
                        "Sales Order cancelled successfully."
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        f"Could not cancel order: {e}"
                    )

    # ======================================================
    # ORDER SUMMARY
    # ======================================================

    st.divider()

    final_total = calculate_sales_order_total(
        db,
        order.id,
    )

    st.markdown(
        f"""
        ### 💰 Order Total

        ## {_money(final_total)}
        """
    )


# ==========================================================
# STREAMLIT ENTRY POINT
# ==========================================================

def sales_orders():
    """
    Compatibility alias for routers that use
    sales_orders instead of sales_orders_page.
    """
    sales_orders_page()