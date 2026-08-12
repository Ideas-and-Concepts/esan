"""
Esan ERP - Sales Quotations Module

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Version 1.4.0 Alpha

Functions:
- Create quotations
- Select customers
- Add multiple quotation items
- Calculate quotation totals
- View quotations
- Search quotations
- Filter quotations by status
- Edit quotations
- Update quotation status
- Delete quotations
"""

import streamlit as st
import pandas as pd

from datetime import datetime, timedelta

from database import SessionLocal
from models import (
    Customer,
    Product,
    Quotation,
    QuotationItem,
)


# ==================================================
# CONSTANTS
# ==================================================

QUOTATION_STATUSES = [
    "Draft",
    "Sent",
    "Accepted",
    "Rejected",
    "Expired",
    "Cancelled",
]


# ==================================================
# HELPER FUNCTIONS
# ==================================================

def generate_quotation_number(db):
    """
    Generate the next quotation number.
    """

    last_quotation = (
        db.query(Quotation)
        .order_by(Quotation.id.desc())
        .first()
    )

    if not last_quotation:
        return "QT-00001"

    try:
        last_number = int(
            last_quotation.quotation_number
            .replace("QT-", "")
        )

        return f"QT-{last_number + 1:05d}"

    except (ValueError, AttributeError):

        return f"QT-{last_quotation.id + 1:05d}"


def get_customers():
    """
    Retrieve active customers.
    """

    db = SessionLocal()

    try:

        return (
            db.query(Customer)
            .filter(Customer.active.is_(True))
            .order_by(Customer.name.asc())
            .all()
        )

    finally:

        db.close()


def get_products():
    """
    Retrieve active products.

    If the Product model does not contain an active field,
    fall back to retrieving all products.
    """

    db = SessionLocal()

    try:

        try:

            return (
                db.query(Product)
                .filter(Product.active.is_(True))
                .order_by(Product.name.asc())
                .all()
            )

        except Exception:

            db.rollback()

            return (
                db.query(Product)
                .order_by(Product.name.asc())
                .all()
            )

    finally:

        db.close()


def get_quotations():
    """
    Retrieve quotations with their related customers and items.
    """

    db = SessionLocal()

    try:

        quotations = (
            db.query(Quotation)
            .order_by(Quotation.id.desc())
            .all()
        )

        # Access relationships while the session is open.
        for quotation in quotations:

            _ = quotation.customer
            _ = quotation.items

            for item in quotation.items:
                _ = item.product_name

        return quotations

    finally:

        db.close()


def get_quotation(quotation_id):
    """
    Retrieve a single quotation.
    """

    db = SessionLocal()

    try:

        quotation = (
            db.query(Quotation)
            .filter(
                Quotation.id == quotation_id
            )
            .first()
        )

        if quotation:

            _ = quotation.customer
            _ = quotation.items

            for item in quotation.items:
                _ = item.product_name

        return quotation

    finally:

        db.close()


# ==================================================
# CREATE QUOTATION
# ==================================================

def create_quotation(
    customer_id,
    items,
    status="Draft",
    valid_until=None,
    notes=None,
):
    """
    Create a quotation and its quotation items.
    """

    db = SessionLocal()

    try:

        if not items:

            raise ValueError(
                "A quotation must contain at least one item."
            )

        quotation_number = generate_quotation_number(db)

        total_amount = 0.0

        quotation = Quotation(
            quotation_number=quotation_number,
            customer_id=customer_id,
            status=status,
            valid_until=valid_until,
            notes=notes,
            total_amount=0.0,
        )

        db.add(quotation)
        db.flush()

        for item_data in items:

            product_name = str(
                item_data.get(
                    "product_name",
                    "",
                )
            ).strip()

            quantity = float(
                item_data.get(
                    "quantity",
                    0,
                )
            )

            unit_price = float(
                item_data.get(
                    "unit_price",
                    0,
                )
            )

            if not product_name:

                raise ValueError(
                    "Product name cannot be empty."
                )

            if quantity <= 0:

                raise ValueError(
                    f"Quantity for "
                    f"{product_name} must be greater than zero."
                )

            if unit_price < 0:

                raise ValueError(
                    f"Unit price for "
                    f"{product_name} cannot be negative."
                )

            item_total = quantity * unit_price

            quotation_item = QuotationItem(
                quotation_id=quotation.id,
                product_name=product_name,
                quantity=quantity,
                unit_price=unit_price,
                total=item_total,
            )

            db.add(quotation_item)

            total_amount += item_total

        quotation.total_amount = total_amount

        db.commit()

        db.refresh(quotation)

        return quotation

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()


# ==================================================
# UPDATE QUOTATION
# ==================================================

def update_quotation(
    quotation_id,
    customer_id,
    items,
    status,
    valid_until=None,
    notes=None,
):
    """
    Update an existing quotation.
    """

    db = SessionLocal()

    try:

        quotation = (
            db.query(Quotation)
            .filter(
                Quotation.id == quotation_id
            )
            .first()
        )

        if not quotation:

            return None

        if not items:

            raise ValueError(
                "A quotation must contain at least one item."
            )

        quotation.customer_id = customer_id
        quotation.status = status
        quotation.valid_until = valid_until
        quotation.notes = notes

        # Remove existing items.
        quotation.items.clear()

        total_amount = 0.0

        for item_data in items:

            product_name = str(
                item_data.get(
                    "product_name",
                    "",
                )
            ).strip()

            quantity = float(
                item_data.get(
                    "quantity",
                    0,
                )
            )

            unit_price = float(
                item_data.get(
                    "unit_price",
                    0,
                )
            )

            if not product_name:

                raise ValueError(
                    "Product name cannot be empty."
                )

            if quantity <= 0:

                raise ValueError(
                    f"Quantity for "
                    f"{product_name} must be greater than zero."
                )

            if unit_price < 0:

                raise ValueError(
                    f"Unit price for "
                    f"{product_name} cannot be negative."
                )

            item_total = quantity * unit_price

            quotation_item = QuotationItem(
                product_name=product_name,
                quantity=quantity,
                unit_price=unit_price,
                total=item_total,
            )

            quotation.items.append(
                quotation_item
            )

            total_amount += item_total

        quotation.total_amount = total_amount

        db.commit()

        db.refresh(quotation)

        return quotation

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()


# ==================================================
# UPDATE STATUS
# ==================================================

def update_quotation_status(
    quotation_id,
    new_status,
):
    """
    Update quotation status.
    """

    if new_status not in QUOTATION_STATUSES:

        raise ValueError(
            f"Invalid quotation status: {new_status}"
        )

    db = SessionLocal()

    try:

        quotation = (
            db.query(Quotation)
            .filter(
                Quotation.id == quotation_id
            )
            .first()
        )

        if not quotation:

            return None

        quotation.status = new_status

        db.commit()

        db.refresh(quotation)

        return quotation

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()


# ==================================================
# DELETE QUOTATION
# ==================================================

def delete_quotation(quotation_id):
    """
    Delete a quotation and its quotation items.
    """

    db = SessionLocal()

    try:

        quotation = (
            db.query(Quotation)
            .filter(
                Quotation.id == quotation_id
            )
            .first()
        )

        if not quotation:

            return False

        db.delete(quotation)

        db.commit()

        return True

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()


# ==================================================
# CREATE QUOTATION FORM
# ==================================================

def create_quotation_form():

    st.subheader("➕ Create New Quotation")

    customers = get_customers()

    if not customers:

        st.warning(
            "No active customers are available. "
            "Please create a customer first."
        )

        return

    customer_options = {
        (
            f"{customer.name}"
            f" | "
            f"{customer.phone or 'No phone'}"
        ): customer.id
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
        "### Quotation Details"
    )

    col1, col2 = st.columns(2)

    with col1:

        status = st.selectbox(
            "Quotation Status",
            QUOTATION_STATUSES,
            index=0,
        )

    with col2:

        valid_until_date = st.date_input(
            "Valid Until",
            value=(
                datetime.today().date()
                + timedelta(days=30)
            ),
        )

    notes = st.text_area(
        "Notes",
        placeholder=(
            "Optional quotation notes, "
            "terms or special instructions."
        ),
    )

    st.markdown(
        "### Quotation Items"
    )

    item_count = st.number_input(
        "Number of Items",
        min_value=1,
        max_value=30,
        value=1,
        step=1,
    )

    items = []

    total_amount = 0.0

    products = get_products()

    product_names = [
        product.name
        for product in products
        if getattr(product, "name", None)
    ]

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

                product_choice = st.selectbox(
                    "Product",
                    options=[
                        "Custom Product"
                    ] + product_names,
                    key=f"quotation_product_{index}",
                )

                if product_choice == "Custom Product":

                    product_name = st.text_input(
                        "Product Name",
                        key=(
                            f"quotation_custom_product_"
                            f"{index}"
                        ),
                    )

                else:

                    product_name = product_choice

            else:

                product_name = st.text_input(
                    "Product / Item",
                    key=f"quotation_product_{index}",
                    placeholder="e.g. Maize Flour 25Kg",
                )

        with col2:

            quantity = st.number_input(
                "Quantity",
                min_value=0.0,
                step=1.0,
                key=f"quotation_quantity_{index}",
            )

        with col3:

            unit_price = st.number_input(
                "Unit Price",
                min_value=0.0,
                step=100.0,
                key=f"quotation_price_{index}",
            )

        item_total = (
            quantity * unit_price
        )

        st.write(
            f"Item Total: "
            f"**UGX {item_total:,.2f}**"
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
            "Quotation totals are calculated "
            "automatically from the items above."
        )

    with col2:

        st.metric(
            "Quotation Total",
            f"UGX {total_amount:,.2f}",
        )

    if st.button(
        "💾 Create Quotation",
        type="primary",
        use_container_width=True,
    ):

        if not items:

            st.error(
                "Please enter at least one quotation item."
            )

            return

        if valid_until_date < datetime.today().date():

            st.error(
                "Valid Until date cannot be in the past."
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

            valid_until = datetime.combine(
                valid_until_date,
                datetime.min.time(),
            )

            quotation = create_quotation(
                customer_id=customer_id,
                items=items,
                status=status,
                valid_until=valid_until,
                notes=notes.strip() or None,
            )

            st.success(
                f"Quotation "
                f"{quotation.quotation_number} "
                "created successfully."
            )

            st.rerun()

        except Exception as e:

            st.error(
                f"Unable to create quotation: {e}"
            )


# ==================================================
# EDIT QUOTATION
# ==================================================

def edit_quotation_form(
    quotation_id,
):

    quotation = get_quotation(
        quotation_id
    )

    if not quotation:

        st.error(
            "Quotation could not be found."
        )

        return

    customers = get_customers()

    if not customers:

        st.warning(
            "No customers are available."
        )

        return

    customer_options = {
        (
            f"{customer.name}"
            f" | "
            f"{customer.phone or 'No phone'}"
        ): customer.id
        for customer in customers
    }

    current_customer_label = next(
        (
            label
            for label, customer_id
            in customer_options.items()
            if customer_id == quotation.customer_id
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
            current_customer_label
        ),
        key="edit_quotation_customer",
    )

    customer_id = customer_options[
        selected_customer
    ]

    status = st.selectbox(
        "Status",
        QUOTATION_STATUSES,
        index=(
            QUOTATION_STATUSES.index(
                quotation.status
            )
            if quotation.status
            in QUOTATION_STATUSES
            else 0
        ),
        key="edit_quotation_status",
    )

    current_date = (
        quotation.valid_until.date()
        if quotation.valid_until
        else (
            datetime.today().date()
            + timedelta(days=30)
        )
    )

    valid_until_date = st.date_input(
        "Valid Until",
        value=current_date,
        key="edit_quotation_valid_until",
    )

    notes = st.text_area(
        "Notes",
        value=quotation.notes or "",
        key="edit_quotation_notes",
    )

    st.markdown(
        "### Quotation Items"
    )

    existing_items = quotation.items

    item_count = st.number_input(
        "Number of Items",
        min_value=1,
        max_value=30,
        value=max(
            1,
            len(existing_items),
        ),
        step=1,
        key="edit_quotation_item_count",
    )

    items = []

    total_amount = 0.0

    products = get_products()

    product_names = [
        product.name
        for product in products
        if getattr(product, "name", None)
    ]

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
            existing_item.quantity
            if existing_item
            else 0.0
        )

        default_price = (
            existing_item.unit_price
            if existing_item
            else 0.0
        )

        col1, col2, col3 = st.columns(
            [3, 1, 1]
        )

        with col1:

            if product_names:

                options = [
                    "Custom Product"
                ] + product_names

                if default_product in product_names:

                    default_index = options.index(
                        default_product
                    )

                    product_choice = st.selectbox(
                        "Product",
                        options=options,
                        index=default_index,
                        key=(
                            f"edit_product_"
                            f"{index}"
                        ),
                    )

                    product_name = product_choice

                else:

                    product_choice = st.selectbox(
                        "Product",
                        options=options,
                        index=0,
                        key=(
                            f"edit_product_"
                            f"{index}"
                        ),
                    )

                    if product_choice == "Custom Product":

                        product_name = st.text_input(
                            "Product Name",
                            value=default_product,
                            key=(
                                f"edit_custom_product_"
                                f"{index}"
                            ),
                        )

                    else:

                        product_name = product_choice

            else:

                product_name = st.text_input(
                    "Product / Item",
                    value=default_product,
                    key=(
                        f"edit_product_"
                        f"{index}"
                    ),
                )

        with col2:

            quantity = st.number_input(
                "Quantity",
                min_value=0.0,
                value=float(
                    default_quantity
                ),
                step=1.0,
                key=(
                    f"edit_quantity_"
                    f"{index}"
                ),
            )

        with col3:

            unit_price = st.number_input(
                "Unit Price",
                min_value=0.0,
                value=float(
                    default_price
                ),
                step=100.0,
                key=(
                    f"edit_price_"
                    f"{index}"
                ),
            )

        item_total = (
            quantity * unit_price
        )

        st.write(
            f"Item Total: "
            f"**UGX {item_total:,.2f}**"
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
        "Updated Total",
        f"UGX {total_amount:,.2f}",
    )

    col1, col2 = st.columns(2)

    with col1:

        save_changes = st.button(
            "💾 Save Changes",
            type="primary",
            use_container_width=True,
        )

    with col2:

        cancel = st.button(
            "Cancel",
            use_container_width=True,
        )

    if cancel:

        st.session_state.editing_quotation = None
        st.rerun()

    if save_changes:

        if not items:

            st.error(
                "Please enter at least one item."
            )

            return

        if valid_until_date < datetime.today().date():

            st.error(
                "Valid Until date cannot be in the past."
            )

            return

        try:

            valid_until = datetime.combine(
                valid_until_date,
                datetime.min.time(),
            )

            updated = update_quotation(
                quotation_id=quotation_id,
                customer_id=customer_id,
                items=items,
                status=status,
                valid_until=valid_until,
                notes=notes.strip() or None,
            )

            if updated:

                st.success(
                    f"{updated.quotation_number} "
                    "updated successfully."
                )

                st.session_state.editing_quotation = None

                st.rerun()

            else:

                st.error(
                    "Quotation not found."
                )

        except Exception as e:

            st.error(
                f"Unable to update quotation: {e}"
            )


# ==================================================
# VIEW QUOTATIONS
# ==================================================

def view_quotations():

    st.subheader("📋 Quotations")

    quotations = get_quotations()

    if not quotations:

        st.info(
            "No quotations have been created yet."
        )

        return

    # --------------------------------------------------
    # SEARCH
    # --------------------------------------------------

    search = st.text_input(
        "🔎 Search Quotations",
        placeholder=(
            "Search by quotation number "
            "or customer..."
        ),
    )

    # --------------------------------------------------
    # STATUS FILTER
    # --------------------------------------------------

    status_filter = st.selectbox(
        "Filter by Status",
        ["All"] + QUOTATION_STATUSES,
    )

    filtered = quotations

    if search:

        search_lower = search.lower()

        filtered = [
            quotation
            for quotation in filtered
            if (
                search_lower
                in quotation.quotation_number.lower()
            )
            or (
                quotation.customer
                and search_lower
                in quotation.customer.name.lower()
            )
        ]

    if status_filter != "All":

        filtered = [
            quotation
            for quotation in filtered
            if quotation.status
            == status_filter
        ]

    # --------------------------------------------------
    # SUMMARY
    # --------------------------------------------------

    total_value = sum(
        quotation.total_amount or 0
        for quotation in filtered
    )

    accepted_value = sum(
        quotation.total_amount or 0
        for quotation in filtered
        if quotation.status == "Accepted"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Quotations",
            len(filtered),
        )

    with col2:

        st.metric(
            "Total Value",
            f"UGX {total_value:,.0f}",
        )

    with col3:

        st.metric(
            "Accepted Value",
            f"UGX {accepted_value:,.0f}",
        )

    st.divider()

    # --------------------------------------------------
    # TABLE
    # --------------------------------------------------

    data = []

    for quotation in filtered:

        customer_name = (
            quotation.customer.name
            if quotation.customer
            else "Unknown Customer"
        )

        data.append(
            {
                "ID":
                    quotation.id,

                "Quotation":
                    quotation.quotation_number,

                "Customer":
                    customer_name,

                "Status":
                    quotation.status,

                "Total":
                    f"UGX "
                    f"{quotation.total_amount or 0:,.2f}",

                "Valid Until":
                    (
                        quotation.valid_until.strftime(
                            "%Y-%m-%d"
                        )
                        if quotation.valid_until
                        else ""
                    ),

                "Created":
                    (
                        quotation.created_at.strftime(
                            "%Y-%m-%d"
                        )
                        if quotation.created_at
                        else ""
                    ),
            }
        )

    df = pd.DataFrame(data)

    st.dataframe(
        df.drop(
            columns=["ID"]
        ),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    # --------------------------------------------------
    # SELECT QUOTATION
    # --------------------------------------------------

    quotation_options = {
        (
            f"{quotation.quotation_number}"
            f" | "
            f"{quotation.customer.name if quotation.customer else 'Unknown Customer'}"
        ):
            quotation.id
        for quotation in filtered
    }

    if not quotation_options:

        st.info(
            "No quotations match the selected filters."
        )

        return

    selected_label = st.selectbox(
        "Select Quotation",
        options=list(
            quotation_options.keys()
        ),
    )

    selected_id = quotation_options[
        selected_label
    ]

    selected_quotation = get_quotation(
        selected_id
    )

    if not selected_quotation:

        st.error(
            "Selected quotation could not be found."
        )

        return

    # --------------------------------------------------
    # QUOTATION DETAILS
    # --------------------------------------------------

    with st.expander(
        "📄 View Quotation Details",
        expanded=True,
    ):

        customer_name = (
            selected_quotation.customer.name
            if selected_quotation.customer
            else "Unknown Customer"
        )

        st.markdown(
            f"### "
            f"{selected_quotation.quotation_number}"
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
                f"{selected_quotation.status}"
            )

        with col3:

            st.write(
                f"**Total:** "
                f"UGX "
                f"{selected_quotation.total_amount or 0:,.2f}"
            )

        if selected_quotation.notes:

            st.write(
                f"**Notes:** "
                f"{selected_quotation.notes}"
            )

        st.markdown(
            "#### Items"
        )

        item_data = []

        for item in selected_quotation.items:

            item_data.append(
                {
                    "Product":
                        item.product_name,

                    "Quantity":
                        item.quantity,

                    "Unit Price":
                        f"UGX "
                        f"{item.unit_price:,.2f}",

                    "Total":
                        f"UGX "
                        f"{item.total:,.2f}",
                }
            )

        if item_data:

            st.dataframe(
                pd.DataFrame(item_data),
                use_container_width=True,
                hide_index=True,
            )

    # --------------------------------------------------
    # ACTIONS
    # --------------------------------------------------

    st.subheader(
        "⚙️ Quotation Management"
    )

    action_col1, action_col2, action_col3 = st.columns(
        3
    )

    with action_col1:

        if st.button(
            "✏️ Edit Quotation",
            use_container_width=True,
        ):

            st.session_state.editing_quotation = (
                selected_id
            )

            st.rerun()

    with action_col2:

        new_status = st.selectbox(
            "Change Status",
            QUOTATION_STATUSES,
            index=(
                QUOTATION_STATUSES.index(
                    selected_quotation.status
                )
                if selected_quotation.status
                in QUOTATION_STATUSES
                else 0
            ),
            key="quotation_status_change",
        )

        if st.button(
            "🔄 Update Status",
            use_container_width=True,
        ):

            try:

                updated = update_quotation_status(
                    selected_id,
                    new_status,
                )

                if updated:

                    st.success(
                        f"{updated.quotation_number} "
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
            "🗑️ Delete Quotation",
            use_container_width=True,
        ):

            st.session_state.delete_quotation_id = (
                selected_id
            )

            st.rerun()

    # --------------------------------------------------
    # DELETE CONFIRMATION
    # --------------------------------------------------

    if (
        st.session_state.get(
            "delete_quotation_id"
        )
        == selected_id
    ):

        st.warning(
            "Deleting this quotation will also "
            "delete all quotation items."
        )

        confirm_col1, confirm_col2 = st.columns(2)

        with confirm_col1:

            if st.button(
                "Yes, Delete",
                type="primary",
                use_container_width=True,
            ):

                try:

                    deleted = delete_quotation(
                        selected_id
                    )

                    if deleted:

                        st.session_state.delete_quotation_id = None

                        st.success(
                            "Quotation deleted successfully."
                        )

                        st.rerun()

                    else:

                        st.error(
                            "Quotation could not be found."
                        )

                except Exception as e:

                    st.error(
                        f"Unable to delete quotation: {e}"
                    )

        with confirm_col2:

            if st.button(
                "Cancel Delete",
                use_container_width=True,
            ):

                st.session_state.delete_quotation_id = None

                st.rerun()


# ==================================================
# MAIN QUOTATIONS PAGE
# ==================================================

def quotations_page():

    st.title(
        "💼 Sales Quotations"
    )

    st.caption(
        "Create, manage and track customer quotations."
    )

    tab1, tab2 = st.tabs(
        [
            "➕ Create Quotation",
            "📋 Quotations",
        ]
    )

    with tab1:

        create_quotation_form()

    with tab2:

        if st.session_state.get(
            "editing_quotation"
        ):

            quotation_id = (
                st.session_state.editing_quotation
            )

            st.subheader(
                "✏️ Edit Quotation"
            )

            edit_quotation_form(
                quotation_id
            )

        else:

            view_quotations()


# ==================================================
# STANDALONE EXECUTION
# ==================================================

if __name__ == "__main__":

    quotations_page()