"""
Esan ERP
Sales & Distribution - Deliveries

Delivery Note management interface.

Nile Harvest Foods Ltd.
"""

import streamlit as st

from database import SessionLocal

from models import (
    Customer,
    Product,
    SalesOrder,
)

from services.delivery_service import (
    get_all_deliveries,
    get_delivery,
    get_delivery_items,
    create_delivery,
    update_delivery,
    add_delivery_item,
    update_delivery_item,
    delete_delivery_item,
    check_delivery_stock,
    post_delivery,
    cancel_delivery,
    reverse_delivery,
)


# ==========================================================
# HELPERS
# ==========================================================

def _status_badge(status):

    status = status or "Draft"

    mapping = {
        "Draft": "🟡 Draft",
        "Posted": "🟢 Posted",
        "Cancelled": "🔴 Cancelled",
        "Reversed": "🟠 Reversed",
    }

    return mapping.get(
        status,
        status,
    )


# ==========================================================
# PAGE
# ==========================================================

def deliveries_page():

    st.subheader("🚚 Deliveries")

    st.caption(
        "Create, edit, post and reverse customer deliveries."
    )

    db = SessionLocal()

    try:

        (
            create_tab,
            view_tab,
            edit_tab,
            post_tab,
            cancel_tab,
        ) = st.tabs(
            [
                "➕ Create",
                "📋 View",
                "✏️ Edit",
                "📦 Post",
                "↩️ Cancel / Reverse",
            ]
        )

        # ==================================================
        # CREATE
        # ==================================================

        with create_tab:

            st.markdown(
                "### Create Delivery"
            )

            customers = (
                db.query(Customer)
                .order_by(Customer.name)
                .all()
            )

            if not customers:

                st.warning(
                    "Create a customer first."
                )

            else:

                customer_options = {
                    f"{c.id} - {c.name}":
                    c.id
                    for c in customers
                }

                orders = (
                    db.query(SalesOrder)
                    .order_by(
                        SalesOrder.id.desc()
                    )
                    .all()
                )

                order_options = {
                    "No Sales Order":
                    None
                }

                for order in orders:

                    order_options[
                        f"SO-{order.id:05d}"
                    ] = order.id

                with st.form(
                    "create_delivery_form"
                ):

                    customer_label = st.selectbox(
                        "Customer *",
                        list(
                            customer_options.keys()
                        ),
                    )

                    order_label = st.selectbox(
                        "Sales Order",
                        list(
                            order_options.keys()
                        ),
                    )

                    delivery_date = st.date_input(
                        "Delivery Date"
                    )

                    notes = st.text_area(
                        "Notes"
                    )

                    submitted = st.form_submit_button(
                        "Create Delivery",
                        use_container_width=True,
                        type="primary",
                    )

                    if submitted:

                        try:

                            delivery = create_delivery(
                                db=db,
                                customer_id=
                                    customer_options[
                                        customer_label
                                    ],
                                sales_order_id=
                                    order_options[
                                        order_label
                                    ],
                                delivery_date=
                                    delivery_date,
                                notes=notes,
                            )

                            st.success(
                                f"Delivery #{delivery.id} "
                                "created successfully."
                            )

                            st.rerun()

                        except Exception as e:

                            db.rollback()

                            st.error(
                                f"Unable to create delivery: {e}"
                            )

        # ==================================================
        # VIEW
        # ==================================================

        with view_tab:

            st.markdown(
                "### Delivery Register"
            )

            deliveries = get_all_deliveries(
                db
            )

            if not deliveries:

                st.info(
                    "No deliveries have been created."
                )

            else:

                rows = []

                for delivery in deliveries:

                    customer = (
                        db.query(Customer)
                        .filter(
                            Customer.id
                            == delivery.customer_id
                        )
                        .first()
                    )

                    items = get_delivery_items(
                        db,
                        delivery.id,
                    )

                    total_quantity = sum(
                        float(
                            item.quantity or 0
                        )
                        for item in items
                    )

                    rows.append(
                        {
                            "Delivery":
                                f"DN-{delivery.id:05d}",
                            "Customer":
                                customer.name
                                if customer
                                else "Unknown",
                            "Sales Order":
                                (
                                    f"SO-{delivery.sales_order_id:05d}"
                                    if getattr(
                                        delivery,
                                        "sales_order_id",
                                        None,
                                    )
                                    else "-"
                                ),
                            "Items":
                                len(items),
                            "Quantity":
                                total_quantity,
                            "Status":
                                _status_badge(
                                    getattr(
                                        delivery,
                                        "status",
                                        "Draft",
                                    )
                                ),
                        }
                    )

                st.dataframe(
                    rows,
                    use_container_width=True,
                    hide_index=True,
                )

                st.divider()

                options = {
                    f"DN-{d.id:05d}":
                    d.id
                    for d in deliveries
                }

                selected = st.selectbox(
                    "View delivery",
                    list(
                        options.keys()
                    ),
                    key="view_delivery",
                )

                delivery = get_delivery(
                    db,
                    options[selected],
                )

                if delivery:

                    customer = (
                        db.query(Customer)
                        .filter(
                            Customer.id
                            == delivery.customer_id
                        )
                        .first()
                    )

                    c1, c2, c3 = st.columns(3)

                    c1.metric(
                        "Customer",
                        customer.name
                        if customer
                        else "Unknown",
                    )

                    c2.metric(
                        "Status",
                        getattr(
                            delivery,
                            "status",
                            "Draft",
                        ),
                    )

                    items = get_delivery_items(
                        db,
                        delivery.id,
                    )

                    c3.metric(
                        "Total Quantity",
                        sum(
                            float(
                                item.quantity or 0
                            )
                            for item in items
                        ),
                    )

                    if items:

                        item_rows = []

                        for item in items:

                            product = (
                                db.query(Product)
                                .filter(
                                    Product.id
                                    == item.product_id
                                )
                                .first()
                            )

                            item_rows.append(
                                {
                                    "Product":
                                        product.name
                                        if product
                                        else "Unknown",
                                    "Quantity":
                                        item.quantity,
                                }
                            )

                        st.dataframe(
                            item_rows,
                            use_container_width=True,
                            hide_index=True,
                        )

        # ==================================================
        # EDIT
        # ==================================================

        with edit_tab:

            st.markdown(
                "### Edit Delivery"
            )

            deliveries = get_all_deliveries(
                db
            )

            editable = [
                d
                for d in deliveries
                if (
                    getattr(
                        d,
                        "status",
                        "Draft",
                    )
                    or "Draft"
                ).lower()
                == "draft"
            ]

            if not editable:

                st.info(
                    "No Draft deliveries are available."
                )

            else:

                options = {
                    f"DN-{d.id:05d}":
                    d.id
                    for d in editable
                }

                selected = st.selectbox(
                    "Select delivery",
                    list(options.keys()),
                    key="edit_delivery",
                )

                delivery_id = options[
                    selected
                ]

                delivery = get_delivery(
                    db,
                    delivery_id,
                )

                customers = (
                    db.query(Customer)
                    .order_by(Customer.name)
                    .all()
                )

                customer_options = {
                    f"{c.id} - {c.name}":
                    c.id
                    for c in customers
                }

                current_customer = next(
                    (
                        label
                        for label, cid
                        in customer_options.items()
                        if cid
                        == delivery.customer_id
                    ),
                    list(
                        customer_options.keys()
                    )[0],
                )

                with st.form(
                    "edit_delivery_form"
                ):

                    customer_label = st.selectbox(
                        "Customer",
                        list(
                            customer_options.keys()
                        ),
                        index=list(
                            customer_options.keys()
                        ).index(
                            current_customer
                        ),
                    )

                    delivery_date = st.date_input(
                        "Delivery Date",
                        value=getattr(
                            delivery,
                            "delivery_date",
                            None,
                        ),
                    )

                    notes = st.text_area(
                        "Notes",
                        value=getattr(
                            delivery,
                            "notes",
                            "",
                        )
                        or "",
                    )

                    save = st.form_submit_button(
                        "Save Delivery",
                        use_container_width=True,
                        type="primary",
                    )

                    if save:

                        try:

                            update_delivery(
                                db=db,
                                delivery_id=
                                    delivery_id,
                                customer_id=
                                    customer_options[
                                        customer_label
                                    ],
                                delivery_date=
                                    delivery_date,
                                notes=notes,
                            )

                            st.success(
                                "Delivery updated."
                            )

                            st.rerun()

                        except Exception as e:

                            db.rollback()

                            st.error(
                                str(e)
                            )

                # ------------------------------------------
                # ITEMS
                # ------------------------------------------

                st.divider()

                st.markdown(
                    "#### Delivery Items"
                )

                products = (
                    db.query(Product)
                    .order_by(Product.name)
                    .all()
                )

                if products:

                    product_options = {
                        f"{p.id} - {p.name}":
                        p.id
                        for p in products
                    }

                    with st.form(
                        "add_delivery_item_form"
                    ):

                        product_label = st.selectbox(
                            "Product",
                            list(
                                product_options.keys()
                            ),
                        )

                        quantity = st.number_input(
                            "Quantity",
                            min_value=0.01,
                            value=1.0,
                            step=1.0,
                        )

                        add = st.form_submit_button(
                            "Add Item",
                            use_container_width=True,
                        )

                        if add:

                            try:

                                add_delivery_item(
                                    db=db,
                                    delivery_id=
                                        delivery_id,
                                    product_id=
                                        product_options[
                                            product_label
                                        ],
                                    quantity=
                                        quantity,
                                )

                                st.success(
                                    "Item added."
                                )

                                st.rerun()

                            except Exception as e:

                                db.rollback()

                                st.error(
                                    str(e)
                                )

                items = get_delivery_items(
                    db,
                    delivery_id,
                )

                for item in items:

                    product = (
                        db.query(Product)
                        .filter(
                            Product.id
                            == item.product_id
                        )
                        .first()
                    )

                    st.write(
                        f"**{product.name if product else 'Unknown'}**"
                    )

                    c1, c2 = st.columns(
                        [3, 1]
                    )

                    with c1:

                        quantity = st.number_input(
                            "Quantity",
                            min_value=0.01,
                            value=float(
                                item.quantity
                            ),
                            key=f"delivery_qty_{item.id}",
                        )

                    with c2:

                        if st.button(
                            "Save",
                            key=f"save_delivery_{item.id}",
                        ):

                            try:

                                update_delivery_item(
                                    db,
                                    item.id,
                                    quantity,
                                )

                                st.success(
                                    "Item updated."
                                )

                                st.rerun()

                            except Exception as e:

                                db.rollback()

                                st.error(
                                    str(e)
                                )

                        if st.button(
                            "Delete",
                            key=f"delete_delivery_{item.id}",
                        ):

                            try:

                                delete_delivery_item(
                                    db,
                                    item.id,
                                )

                                st.success(
                                    "Item deleted."
                                )

                                st.rerun()

                            except Exception as e:

                                db.rollback()

                                st.error(
                                    str(e)
                                )

        # ==================================================
        # POST
        # ==================================================

        with post_tab:

            st.markdown(
                "### Post Delivery"
            )

            deliveries = get_all_deliveries(
                db
            )

            draft_deliveries = [
                d
                for d in deliveries
                if (
                    getattr(
                        d,
                        "status",
                        "Draft",
                    )
                    or "Draft"
                ).lower()
                == "draft"
            ]

            if not draft_deliveries:

                st.info(
                    "No Draft deliveries are ready for posting."
                )

            else:

                options = {
                    f"DN-{d.id:05d}":
                    d.id
                    for d in draft_deliveries
                }

                selected = st.selectbox(
                    "Select delivery",
                    list(options.keys()),
                    key="post_delivery",
                )

                delivery_id = options[
                    selected
                ]

                stock = check_delivery_stock(
                    db,
                    delivery_id,
                )

                if stock["items"]:

                    stock_rows = []

                    for item in stock["items"]:

                        stock_rows.append(
                            {
                                "Product":
                                    item["product"],
                                "Requested":
                                    item["requested"],
                                "Available":
                                    item[
                                        "available_stock"
                                    ],
                                "Status":
                                    (
                                        "✅ Available"
                                        if item[
                                            "available"
                                        ]
                                        else "❌ Short"
                                    ),
                            }
                        )

                    st.dataframe(
                        stock_rows,
                        use_container_width=True,
                        hide_index=True,
                    )

                if not stock["available"]:

                    st.error(
                        "Delivery cannot be posted because "
                        "there is insufficient stock."
                    )

                else:

                    confirm = st.checkbox(
                        "I confirm that the goods have been dispatched.",
                        key="confirm_post_delivery",
                    )

                    if st.button(
                        "📦 Post Delivery",
                        disabled=not confirm,
                        use_container_width=True,
                        type="primary",
                    ):

                        try:

                            post_delivery(
                                db,
                                delivery_id,
                            )

                            st.success(
                                "Delivery posted successfully. "
                                "Stock has been updated."
                            )

                            st.rerun()

                        except Exception as e:

                            db.rollback()

                            st.error(
                                f"Unable to post delivery: {e}"
                            )

        # ==================================================
        # CANCEL / REVERSE
        # ==================================================

        with cancel_tab:

            st.markdown(
                "### Cancel / Reverse Delivery"
            )

            deliveries = get_all_deliveries(
                db
            )

            draft_deliveries = [
                d
                for d in deliveries
                if (
                    getattr(
                        d,
                        "status",
                        "Draft",
                    )
                    or "Draft"
                ).lower()
                == "draft"
            ]

            posted_deliveries = [
                d
                for d in deliveries
                if (
                    getattr(
                        d,
                        "status",
                        "",
                    )
                    or ""
                ).lower()
                == "posted"
            ]

            # ------------------------------------------------
            # CANCEL DRAFT
            # ------------------------------------------------

            if draft_deliveries:

                st.markdown(
                    "#### Cancel Draft Delivery"
                )

                options = {
                    f"DN-{d.id:05d}":
                    d.id
                    for d in draft_deliveries
                }

                selected = st.selectbox(
                    "Draft delivery",
                    list(options.keys()),
                    key="cancel_delivery",
                )

                delivery_id = options[
                    selected
                ]

                confirm_cancel = st.checkbox(
                    "I confirm that I want to cancel this delivery.",
                    key="confirm_cancel_delivery",
                )

                if st.button(
                    "🚫 Cancel Delivery",
                    disabled=not confirm_cancel,
                    use_container_width=True,
                ):

                    try:

                        cancel_delivery(
                            db,
                            delivery_id,
                        )

                        st.success(
                            "Delivery cancelled."
                        )

                        st.rerun()

                    except Exception as e:

                        db.rollback()

                        st.error(
                            str(e)
                        )

            else:

                st.info(
                    "No Draft deliveries available for cancellation."
                )

            # ------------------------------------------------
            # REVERSE POSTED
            # ------------------------------------------------

            st.divider()

            st.markdown(
                "#### Reverse Posted Delivery"
            )

            if not posted_deliveries:

                st.info(
                    "No Posted deliveries are available for reversal."
                )

            else:

                options = {
                    f"DN-{d.id:05d}":
                    d.id
                    for d in posted_deliveries
                }

                selected = st.selectbox(
                    "Posted delivery",
                    list(options.keys()),
                    key="reverse_delivery",
                )

                delivery_id = options[
                    selected
                ]

                st.warning(
                    "Reversing a Posted delivery will "
                    "return its quantities to stock."
                )

                confirm_reverse = st.checkbox(
                    "I confirm that I want to reverse this delivery.",
                    key="confirm_reverse_delivery",
                )

                if st.button(
                    "↩️ Reverse Delivery",
                    disabled=not confirm_reverse,
                    use_container_width=True,
                ):

                    try:

                        reverse_delivery(
                            db,
                            delivery_id,
                        )

                        st.success(
                            "Delivery reversed. "
                            "Stock has been returned."
                        )

                        st.rerun()

                    except Exception as e:

                        db.rollback()

                        st.error(
                            str(e)
                        )

    finally:

        db.close()