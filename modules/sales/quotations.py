"""
Esan ERP
Sales & Distribution - Quotations

Quotation management interface.

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System
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
    """Format currency as UGX."""
    try:
        return f"UGX {float(value):,.0f}"
    except (TypeError, ValueError):
        return "UGX 0"


def _status_badge(status):
    """Return a readable quotation status."""
    status = status or "Draft"

    normalized = str(status).lower()

    if normalized == "draft":
        return "🟡 Draft"

    if normalized == "converted":
        return "🟢 Converted"

    if normalized == "cancelled":
        return "🔴 Cancelled"

    if normalized == "approved":
        return "🔵 Approved"

    return str(status)


def _quotation_label(quotation):
    """
    Return the canonical quotation number.

    Falls back to the database ID if an older record
    does not have quotation_number.
    """

    quotation_number = getattr(
        quotation,
        "quotation_number",
        None,
    )

    if quotation_number:
        return str(quotation_number)

    quotation_id = getattr(
        quotation,
        "id",
        0,
    )

    return f"QT-{quotation_id:05d}"


def _quotation_status(quotation):
    """Return normalized quotation status."""
    return (
        getattr(
            quotation,
            "status",
            None,
        )
        or "Draft"
    ).strip()


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
                                f"Quotation "
                                f"{_quotation_label(quotation)} "
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

                    total = getattr(
                        quotation,
                        "total_amount",
                        0.0,
                    ) or 0.0

                    rows.append(
                        {
                            "Quotation":
                                _quotation_label(
                                    quotation
                                ),

                            "Customer":
                                (
                                    customer.name
                                    if customer
                                    else "Unknown"
                                ),

                            "Status":
                                _status_badge(
                                    getattr(
                                        quotation,
                                        "status",
                                        "Draft",
                                    )
                                ),

                            "Total":
                                _money(total),
                        }
                    )

                st.dataframe(
                    rows,
                    use_container_width=True,
                    hide_index=True,
                )

                st.divider()

                quotation_options = {
                    _quotation_label(q):
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
                        f"### {_quotation_label(quotation)}"
                    )

                    col1, col2, col3 = st.columns(3)

                    col1.metric(
                        "Customer",
                        (
                            customer.name
                            if customer
                            else "Unknown"
                        ),
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
                            getattr(
                                quotation,
                                "total_amount",
                                0,
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
                                        (
                                            item.product_name
                                            or (
                                                product.name
                                                if product
                                                else "Unknown"
                                            )
                                        ),

                                    "Quantity":
                                        quantity,

                                    "Unit Price":
                                        _money(price),

                                    "Total":
                                        _money(
                                            item.total
                                            or (
                                                quantity
                                                * price
                                            )
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
                if _quotation_status(q).lower()
                == "draft"
            ]

            if not editable:

                st.info(
                    "There are no Draft quotations to edit."
                )

            else:

                quotation_options = {
                    _quotation_label(q):
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

                if not customers:

                    st.warning(
                        "No customers are available."
                    )

                else:

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

                        existing_valid_until = getattr(
                            quotation,
                            "valid_until",
                            None,
                        )

                        valid_until = st.date_input(
                            "Valid Until",
                            value=(
                                existing_valid_until
                                or date.today()
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

                    # ======================================
                    # ITEMS
                    # ======================================

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

                            selected_product = next(
                                (
                                    p
                                    for p in products
                                    if p.id
                                    == product_options[
                                        product_label
                                    ]
                                ),
                                None,
                            )

                            default_price = float(
                                getattr(
                                    selected_product,
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

                    else:

                        st.info(
                            "Create a product before adding quotation items."
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
                            f"**{item.product_name or (product.name if product else 'Unknown')}** "
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
                                    item.quantity or 0
                                ),
                                key=f"qty_{item.id}",
                            )

                        with c2:

                            new_price = st.number_input(
                                "Unit Price",
                                min_value=0.0,
                                value=float(
                                    item.unit_price or 0
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
                if _quotation_status(q).lower()
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
                    _quotation_label(q):
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

                items = get_quotation_items(
                    db,
                    quotation_id,
                )

                quotation = get_quotation(
                    db,
                    quotation_id,
                )

                total = float(
                    getattr(
                        quotation,
                        "total_amount",
                        0,
                    )
                    or 0
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

                            order = (
                                convert_quotation_to_sales_order(
                                    db,
                                    quotation_id,
                                )
                            )

                            order_number = getattr(
                                order,
                                "order_number",
                                None,
                            )

                            if order_number:
                                order_reference = order_number
                            else:
                                order_reference = (
                                    f"SO-{order.id:05d}"
                                )

                            st.success(
                                "Quotation converted successfully "
                                f"to Sales Order {order_reference}."
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
                if _quotation_status(q).lower()
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
                    _quotation_label(q):
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