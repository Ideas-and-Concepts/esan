"""
Esan ERP
Sales & Distribution - Quotations

Quotation management interface.

Nile Harvest Foods Ltd.
"""

import streamlit as st

from database import SessionLocal

from models import Customer, Product

from services.quotation_service import (
    get_all_quotations,
    get_quotation,
    get_quotation_items,
    create_quotation,
    update_quotation,
    add_quotation_item,
    update_quotation_item,
    delete_quotation_item,
    cancel_quotation,
    calculate_quotation_total,
    convert_quotation_to_sales_order,
)


# ==========================================================
# HELPERS
# ==========================================================

def _money(value):
    """Format currency."""
    try:
        return f"UGX {float(value):,.0f}"
    except (TypeError, ValueError):
        return "UGX 0"


def _status_badge(status):
    """Return a readable status."""
    status = status or "Draft"

    if status.lower() == "draft":
        return "🟡 Draft"

    if status.lower() == "converted":
        return "🟢 Converted"

    if status.lower() == "cancelled":
        return "🔴 Cancelled"

    if status.lower() == "approved":
        return "🔵 Approved"

    return status


# ==========================================================
# PAGE
# ==========================================================

def quotations_page():

    st.subheader("📄 Quotations")

    st.caption(
        "Create, manage and convert customer quotations."
    )

    db = SessionLocal()

    try:

        # ==================================================
        # TABS
        # ==================================================

        (
            create_tab,
            view_tab,
            edit_tab,
            convert_tab,
            cancel_tab,
        ) = st.tabs(
            [
                "➕ Create",
                "📋 View",
                "✏️ Edit",
                "🔄 Convert",
                "🚫 Cancel",
            ]
        )

        # ==================================================
        # CREATE
        # ==================================================

        with create_tab:

            st.markdown(
                "### Create Quotation"
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
                    f"{customer.id} - {customer.name}":
                    customer.id
                    for customer in customers
                }

                with st.form(
                    "create_quotation_form"
                ):

                    selected_customer = st.selectbox(
                        "Customer *",
                        list(
                            customer_options.keys()
                        ),
                    )

                    valid_until = st.date_input(
                        "Valid Until"
                    )

                    notes = st.text_area(
                        "Notes"
                    )

                    submitted = st.form_submit_button(
                        "Create Quotation",
                        use_container_width=True,
                        type="primary",
                    )

                    if submitted:

                        try:

                            quotation = create_quotation(
                                db=db,
                                customer_id=customer_options[
                                    selected_customer
                                ],
                                valid_until=valid_until,
                                notes=notes,
                            )

                            st.success(
                                f"Quotation #{quotation.id} "
                                "created successfully."
                            )

                            st.session_state[
                                "quotation_to_edit"
                            ] = quotation.id

                            st.rerun()

                        except Exception as e:

                            db.rollback()

                            st.error(
                                f"Unable to create quotation: {e}"
                            )

        # ==================================================
        # VIEW
        # ==================================================

        with view_tab:

            st.markdown(
                "### Quotation Register"
            )

            quotations = get_all_quotations(db)

            if not quotations:

                st.info(
                    "No quotations have been created."
                )

            else:

                rows = []

                for quotation in quotations:

                    customer = (
                        db.query(Customer)
                        .filter(
                            Customer.id
                            == quotation.customer_id
                        )
                        .first()
                    )

                    total = calculate_quotation_total(
                        db,
                        quotation.id,
                    )

                    rows.append(
                        {
                            "Quotation": f"Q-{quotation.id:05d}",
                            "Customer": (
                                customer.name
                                if customer
                                else "Unknown"
                            ),
                            "Status": _status_badge(
                                getattr(
                                    quotation,
                                    "status",
                                    "Draft",
                                )
                            ),
                            "Total": _money(total),
                        }
                    )

                st.dataframe(
                    rows,
                    use_container_width=True,
                    hide_index=True,
                )

                st.divider()

                quotation_options = {
                    f"Q-{q.id:05d}":
                    q.id
                    for q in quotations
                }

                selected = st.selectbox(
                    "View quotation",
                    list(
                        quotation_options.keys()
                    ),
                    key="view_quotation",
                )

                quotation = get_quotation(
                    db,
                    quotation_options[selected],
                )

                if quotation:

                    customer = (
                        db.query(Customer)
                        .filter(
                            Customer.id
                            == quotation.customer_id
                        )
                        .first()
                    )

                    st.markdown(
                        f"### {selected}"
                    )

                    col1, col2, col3 = st.columns(3)

                    col1.metric(
                        "Customer",
                        customer.name
                        if customer
                        else "Unknown",
                    )

                    col2.metric(
                        "Status",
                        getattr(
                            quotation,
                            "status",
                            "Draft",
                        ),
                    )

                    col3.metric(
                        "Total",
                        _money(
                            calculate_quotation_total(
                                db,
                                quotation.id,
                            )
                        ),
                    )

                    items = get_quotation_items(
                        db,
                        quotation.id,
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

                            quantity = float(
                                item.quantity or 0
                            )

                            price = float(
                                item.unit_price or 0
                            )

                            item_rows.append(
                                {
                                    "Product":
                                        product.name
                                        if product
                                        else "Unknown",
                                    "Quantity":
                                        quantity,
                                    "Unit Price":
                                        _money(price),
                                    "Total":
                                        _money(
                                            quantity
                                            * price
                                        ),
                                }
                            )

                        st.dataframe(
                            item_rows,
                            use_container_width=True,
                            hide_index=True,
                        )

                    else:

                        st.info(
                            "This quotation has no items."
                        )

        # ==================================================
        # EDIT
        # ==================================================

        with edit_tab:

            st.markdown(
                "### Edit Quotation"
            )

            quotations = get_all_quotations(db)

            editable = [
                q
                for q in quotations
                if (
                    getattr(
                        q,
                        "status",
                        "Draft",
                    )
                    or "Draft"
                ).lower()
                == "draft"
            ]

            if not editable:

                st.info(
                    "There are no Draft quotations to edit."
                )

            else:

                quotation_options = {
                    f"Q-{q.id:05d}":
                    q.id
                    for q in editable
                }

                selected = st.selectbox(
                    "Select quotation",
                    list(
                        quotation_options.keys()
                    ),
                    key="edit_quotation",
                )

                quotation_id = quotation_options[
                    selected
                ]

                quotation = get_quotation(
                    db,
                    quotation_id,
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
                        == quotation.customer_id
                    ),
                    list(
                        customer_options.keys()
                    )[0],
                )

                with st.form(
                    "edit_quotation_form"
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

                    valid_until = st.date_input(
                        "Valid Until",
                        value=getattr(
                            quotation,
                            "valid_until",
                            None,
                        ),
                    )

                    notes = st.text_area(
                        "Notes",
                        value=getattr(
                            quotation,
                            "notes",
                            "",
                        )
                        or "",
                    )

                    submitted = st.form_submit_button(
                        "Save Quotation",
                        use_container_width=True,
                        type="primary",
                    )

                    if submitted:

                        try:

                            update_quotation(
                                db=db,
                                quotation_id=quotation_id,
                                customer_id=customer_options[
                                    customer_label
                                ],
                                valid_until=valid_until,
                                notes=notes,
                            )

                            st.success(
                                "Quotation updated successfully."
                            )

                            st.rerun()

                        except Exception as e:

                            db.rollback()

                            st.error(
                                f"Unable to update quotation: {e}"
                            )

                # ------------------------------------------
                # ITEMS
                # ------------------------------------------

                st.divider()

                st.markdown(
                    "#### Quotation Items"
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
                        "add_quotation_item"
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

                        default_price = float(
                            getattr(
                                next(
                                    p
                                    for p in products
                                    if p.id
                                    == product_options[
                                        product_label
                                    ]
                                ),
                                "selling_price",
                                0,
                            )
                            or 0
                        )

                        unit_price = st.number_input(
                            "Unit Price",
                            min_value=0.0,
                            value=default_price,
                            step=100.0,
                        )

                        add_item = st.form_submit_button(
                            "Add Item",
                            use_container_width=True,
                        )

                        if add_item:

                            try:

                                add_quotation_item(
                                    db=db,
                                    quotation_id=quotation_id,
                                    product_id=product_options[
                                        product_label
                                    ],
                                    quantity=quantity,
                                    unit_price=unit_price,
                                )

                                st.success(
                                    "Item added."
                                )

                                st.rerun()

                            except Exception as e:

                                db.rollback()

                                st.error(
                                    f"Unable to add item: {e}"
                                )

                items = get_quotation_items(
                    db,
                    quotation_id,
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
                        f"**{product.name if product else 'Unknown'}** "
                        f"| Qty: {item.quantity} "
                        f"| Price: {_money(item.unit_price)}"
                    )

                    c1, c2, c3 = st.columns(
                        [2, 2, 1]
                    )

                    with c1:

                        new_quantity = st.number_input(
                            "Quantity",
                            min_value=0.01,
                            value=float(
                                item.quantity
                            ),
                            key=f"qty_{item.id}",
                        )

                    with c2:

                        new_price = st.number_input(
                            "Unit Price",
                            min_value=0.0,
                            value=float(
                                item.unit_price
                            ),
                            key=f"price_{item.id}",
                        )

                    with c3:

                        if st.button(
                            "Save",
                            key=f"save_item_{item.id}",
                        ):

                            try:

                                update_quotation_item(
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

                                db.rollback()

                                st.error(
                                    str(e)
                                )

                        if st.button(
                            "Delete",
                            key=f"delete_item_{item.id}",
                        ):

                            try:

                                delete_quotation_item(
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
        # CONVERT
        # ==================================================

        with convert_tab:

            st.markdown(
                "### Convert Quotation to Sales Order"
            )

            quotations = get_all_quotations(db)

            convertible = [
                q
                for q in quotations
                if (
                    getattr(
                        q,
                        "status",
                        "Draft",
                    )
                    or "Draft"
                ).lower()
                not in {
                    "converted",
                    "cancelled",
                }
            ]

            if not convertible:

                st.info(
                    "There are no quotations available "
                    "for conversion."
                )

            else:

                options = {
                    f"Q-{q.id:05d}":
                    q.id
                    for q in convertible
                }

                selected = st.selectbox(
                    "Select quotation",
                    list(options.keys()),
                    key="convert_quotation",
                )

                quotation_id = options[
                    selected
                ]

                quotation = get_quotation(
                    db,
                    quotation_id,
                )

                items = get_quotation_items(
                    db,
                    quotation_id,
                )

                total = calculate_quotation_total(
                    db,
                    quotation_id,
                )

                st.metric(
                    "Quotation Total",
                    _money(total),
                )

                st.write(
                    f"Items: **{len(items)}**"
                )

                if not items:

                    st.warning(
                        "Add at least one item before conversion."
                    )

                else:

                    confirm = st.checkbox(
                        "I confirm that this quotation should become a Sales Order.",
                        key="confirm_conversion",
                    )

                    if st.button(
                        "🔄 Convert to Sales Order",
                        disabled=not confirm,
                        use_container_width=True,
                        type="primary",
                    ):

                        try:

                            order = convert_quotation_to_sales_order(
                                db,
                                quotation_id,
                            )

                            st.success(
                                f"Quotation converted successfully "
                                f"to Sales Order #{order.id}."
                            )

                            st.rerun()

                        except Exception as e:

                            db.rollback()

                            st.error(
                                f"Conversion failed: {e}"
                            )

        # ==================================================
        # CANCEL
        # ==================================================

        with cancel_tab:

            st.markdown(
                "### Cancel Quotation"
            )

            quotations = get_all_quotations(db)

            cancellable = [
                q
                for q in quotations
                if (
                    getattr(
                        q,
                        "status",
                        "Draft",
                    )
                    or "Draft"
                ).lower()
                not in {
                    "cancelled",
                    "converted",
                }
            ]

            if not cancellable:

                st.info(
                    "There are no quotations available for cancellation."
                )

            else:

                options = {
                    f"Q-{q.id:05d}":
                    q.id
                    for q in cancellable
                }

                selected = st.selectbox(
                    "Select quotation",
                    list(options.keys()),
                    key="cancel_quotation",
                )

                quotation_id = options[
                    selected
                ]

                st.warning(
                    "Cancelled quotations cannot be converted "
                    "into Sales Orders."
                )

                confirm = st.checkbox(
                    "I confirm that I want to cancel this quotation.",
                    key="confirm_cancel_quotation",
                )

                if st.button(
                    "🚫 Cancel Quotation",
                    disabled=not confirm,
                    use_container_width=True,
                ):

                    try:

                        cancel_quotation(
                            db,
                            quotation_id,
                        )

                        st.success(
                            "Quotation cancelled successfully."
                        )

                        st.rerun()

                    except Exception as e:

                        db.rollback()

                        st.error(
                            f"Unable to cancel quotation: {e}"
                        )

    finally:

        db.close()