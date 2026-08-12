"""
Esan ERP - Sales Invoices Module

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Version 1.4.0 Alpha

Features:
- Create invoices
- View invoices
- Edit draft invoices
- Post invoices
- Void invoices
- Invoice item management
- Customer management integration
- Sales Order integration
- Finance journal visibility
"""

from datetime import date, timedelta

import streamlit as st

from database import SessionLocal

from models import (
    Customer,
    Product,
    SalesOrder,
    Invoice,
)

from services.invoice_service import (
    create_invoice,
    update_invoice,
    get_invoice,
    list_invoices,
    post_invoice,
    void_invoice,
    get_invoice_journal,
)


# ============================================================
# PAGE CONFIGURATION
# ============================================================

PAGE_TITLE = "Invoices"


# ============================================================
# HELPERS
# ============================================================

def money(value):
    """Format monetary values."""

    try:
        return f"UGX {float(value or 0):,.2f}"
    except Exception:
        return "UGX 0.00"


def safe_date(value):
    """Return a valid date."""

    return value if value else date.today()


def get_customers(db):
    return (
        db.query(Customer)
        .filter(Customer.active.is_(True))
        .order_by(Customer.name)
        .all()
    )


def get_products(db):
    return (
        db.query(Product)
        .filter(Product.active.is_(True))
        .order_by(Product.name)
        .all()
    )


def get_sales_orders(db):
    return (
        db.query(SalesOrder)
        .order_by(SalesOrder.id.desc())
        .all()
    )


def reset_invoice_form():
    keys = [
        "invoice_customer",
        "invoice_sales_order",
        "invoice_date",
        "invoice_due_date",
        "invoice_tax",
        "invoice_notes",
        "invoice_items",
    ]

    for key in keys:
        if key in st.session_state:
            del st.session_state[key]


def initialise_invoice_items():
    if "invoice_items" not in st.session_state:
        st.session_state.invoice_items = [
            {
                "product_id": None,
                "product_name": "",
                "quantity": 1.0,
                "unit_price": 0.0,
            }
        ]


def calculate_items_total(items):
    total = 0.0

    for item in items:
        quantity = float(
            item.get("quantity", 0) or 0
        )

        unit_price = float(
            item.get("unit_price", 0) or 0
        )

        total += quantity * unit_price

    return total


# ============================================================
# INVOICE ITEMS EDITOR
# ============================================================

def invoice_items_editor(products):
    """
    Display invoice item entry interface.
    """

    initialise_invoice_items()

    st.subheader("Invoice Items")

    updated_items = []

    for index, item in enumerate(
        st.session_state.invoice_items
    ):

        with st.container(border=True):

            col1, col2, col3, col4, col5 = st.columns(
                [3, 1.3, 1.7, 1.7, 0.7]
            )

            product_options = [
                p.id for p in products
            ]

            product_labels = {
                p.id: (
                    f"{p.name}"
                    + (
                        f" ({p.sku})"
                        if p.sku
                        else ""
                    )
                )
                for p in products
            }

            current_product = item.get(
                "product_id"
            )

            if (
                current_product not in product_options
            ):
                current_product = (
                    product_options[0]
                    if product_options
                    else None
                )

            with col1:

                if products:

                    selected_product = st.selectbox(
                        "Product",
                        product_options,
                        index=(
                            product_options.index(
                                current_product
                            )
                            if current_product
                            in product_options
                            else 0
                        ),
                        format_func=lambda x:
                        product_labels.get(
                            x,
                            str(x),
                        ),
                        key=f"invoice_product_{index}",
                    )

                    product = next(
                        (
                            p
                            for p in products
                            if p.id == selected_product
                        ),
                        None,
                    )

                    product_name = (
                        product.name
                        if product
                        else ""
                    )

                else:

                    st.warning(
                        "No active products found."
                    )

                    selected_product = None
                    product_name = ""

            with col2:

                quantity = st.number_input(
                    "Qty",
                    min_value=0.01,
                    value=float(
                        item.get(
                            "quantity",
                            1.0,
                        )
                        or 1.0
                    ),
                    step=1.0,
                    key=f"invoice_qty_{index}",
                )

            with col3:

                default_price = float(
                    item.get(
                        "unit_price",
                        0.0,
                    )
                    or 0.0
                )

                if (
                    default_price == 0
                    and product
                ):
                    default_price = float(
                        product.selling_price
                        or 0
                    )

                unit_price = st.number_input(
                    "Unit Price",
                    min_value=0.0,
                    value=default_price,
                    step=100.0,
                    key=f"invoice_price_{index}",
                )

            line_total = (
                float(quantity)
                * float(unit_price)
            )

            with col4:

                st.metric(
                    "Line Total",
                    money(line_total),
                )

            with col5:

                remove = st.button(
                    "🗑️",
                    key=f"remove_invoice_item_{index}",
                    help="Remove item",
                )

            if not remove:

                updated_items.append(
                    {
                        "product_id": selected_product,
                        "product_name": product_name,
                        "quantity": float(quantity),
                        "unit_price": float(unit_price),
                    }
                )

    st.session_state.invoice_items = updated_items

    if st.button(
        "➕ Add Item",
        use_container_width=False,
    ):

        st.session_state.invoice_items.append(
            {
                "product_id": None,
                "product_name": "",
                "quantity": 1.0,
                "unit_price": 0.0,
            }
        )

        st.rerun()

    return st.session_state.invoice_items


# ============================================================
# CREATE INVOICE
# ============================================================

def create_invoice_page():

    st.subheader("Create Invoice")

    db = SessionLocal()

    try:

        customers = get_customers(db)
        products = get_products(db)
        sales_orders = get_sales_orders(db)

        if not customers:

            st.warning(
                "No active customers found. "
                "Create a customer first."
            )

            return

        customer_options = {
            customer.id: customer.name
            for customer in customers
        }

        customer_ids = list(
            customer_options.keys()
        )

        selected_customer = st.selectbox(
            "Customer",
            customer_ids,
            format_func=lambda x:
            customer_options[x],
            key="invoice_customer",
        )

        order_options = {
            None: "No Sales Order"
        }

        for order in sales_orders:

            customer_name = (
                order.customer.name
                if order.customer
                else "Unknown"
            )

            order_options[order.id] = (
                f"{order.order_number} | "
                f"{customer_name} | "
                f"{money(order.total_amount)}"
            )

        selected_order = st.selectbox(
            "Sales Order",
            list(order_options.keys()),
            format_func=lambda x:
            order_options[x],
            key="invoice_sales_order",
        )

        col1, col2 = st.columns(2)

        with col1:

            invoice_date = st.date_input(
                "Invoice Date",
                value=date.today(),
                key="invoice_date",
            )

        with col2:

            due_date = st.date_input(
                "Due Date",
                value=date.today()
                + timedelta(days=30),
                key="invoice_due_date",
            )

        st.markdown("### Items")

        items = invoice_items_editor(
            products
        )

        subtotal = calculate_items_total(
            items
        )

        col1, col2 = st.columns(2)

        with col1:

            tax_amount = st.number_input(
                "Tax Amount",
                min_value=0.0,
                value=0.0,
                step=100.0,
                key="invoice_tax",
            )

        with col2:

            total = (
                subtotal
                + float(tax_amount)
            )

            st.metric(
                "Invoice Total",
                money(total),
            )

        notes = st.text_area(
            "Notes",
            key="invoice_notes",
        )

        st.divider()

        if st.button(
            "💾 Save Draft Invoice",
            type="primary",
            use_container_width=True,
        ):

            valid_items = [
                item
                for item in items
                if item.get("product_name")
                and float(
                    item.get(
                        "quantity",
                        0,
                    )
                    or 0
                ) > 0
            ]

            if not valid_items:

                st.error(
                    "Add at least one valid "
                    "invoice item."
                )

                return

            try:

                invoice = create_invoice(
                    db=db,
                    customer_id=selected_customer,
                    items=valid_items,
                    invoice_date=invoice_date,
                    due_date=due_date,
                    sales_order_id=selected_order,
                    tax_amount=tax_amount,
                    notes=notes,
                )

                st.success(
                    f"Invoice "
                    f"{invoice.invoice_number} "
                    f"created successfully."
                )

                reset_invoice_form()

                st.rerun()

            except Exception as exc:

                db.rollback()

                st.error(
                    f"Could not create invoice: "
                    f"{exc}"
                )

    finally:

        db.close()


# ============================================================
# INVOICE DETAILS
# ============================================================

def invoice_details(invoice):

    st.subheader(
        f"Invoice {invoice.invoice_number}"
    )

    customer_name = (
        invoice.customer.name
        if invoice.customer
        else "Unknown Customer"
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Customer",
            customer_name,
        )

    with col2:
        st.metric(
            "Status",
            invoice.status,
        )

    with col3:
        st.metric(
            "Total",
            money(invoice.total_amount),
        )

    with col4:
        st.metric(
            "Balance",
            money(invoice.balance_due),
        )

    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.write(
            f"**Invoice Date:** "
            f"{invoice.invoice_date}"
        )

    with col2:
        st.write(
            f"**Due Date:** "
            f"{invoice.due_date or '-'}"
        )

    with col3:

        order_number = (
            invoice.sales_order.order_number
            if invoice.sales_order
            else "-"
        )

        st.write(
            f"**Sales Order:** "
            f"{order_number}"
        )

    st.subheader("Items")

    rows = []

    for item in invoice.items:

        rows.append(
            {
                "Product": item.product_name,
                "Quantity": item.quantity,
                "Unit Price": money(
                    item.unit_price
                ),
                "Total": money(
                    item.total
                ),
            }
        )

    if rows:
        st.dataframe(
            rows,
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Subtotal",
            money(invoice.subtotal),
        )

    with col2:
        st.metric(
            "Tax",
            money(invoice.tax_amount),
        )

    with col3:
        st.metric(
            "Grand Total",
            money(invoice.total_amount),
        )

    if invoice.notes:

        st.info(
            f"**Notes:** {invoice.notes}"
        )


# ============================================================
# VIEW INVOICE
# ============================================================

def view_invoice_page():

    st.subheader("View Invoice")

    db = SessionLocal()

    try:

        invoices = list_invoices(db)

        if not invoices:

            st.info(
                "No invoices have been created yet."
            )

            return

        invoice_options = {
            invoice.id: (
                f"{invoice.invoice_number} | "
                f"{invoice.customer.name if invoice.customer else 'Unknown'} | "
                f"{invoice.status} | "
                f"{money(invoice.total_amount)}"
            )
            for invoice in invoices
        }

        selected_id = st.selectbox(
            "Select Invoice",
            list(invoice_options.keys()),
            format_func=lambda x:
            invoice_options[x],
        )

        invoice = get_invoice(
            db,
            selected_id,
        )

        if invoice:

            invoice_details(invoice)

            st.divider()

            journal = get_invoice_journal(
                db,
                invoice.id,
            )

            if journal:

                st.subheader(
                    "Accounting Entry"
                )

                st.write(
                    f"**Journal:** "
                    f"{journal.entry_number}"
                )

                st.write(
                    f"**Date:** "
                    f"{journal.entry_date}"
                )

                st.write(
                    f"**Description:** "
                    f"{journal.description}"
                )

                journal_rows = []

                for line in journal.lines:

                    journal_rows.append(
                        {
                            "Account":
                            (
                                f"{line.account.code} - "
                                f"{line.account.name}"
                            ),
                            "Debit":
                            money(line.debit),
                            "Credit":
                            money(line.credit),
                        }
                    )

                st.dataframe(
                    journal_rows,
                    use_container_width=True,
                    hide_index=True,
                )

    finally:

        db.close()


# ============================================================
# EDIT INVOICE
# ============================================================

def edit_invoice_page():

    st.subheader("Edit Draft Invoice")

    db = SessionLocal()

    try:

        invoices = list_invoices(
            db,
            status="Draft",
        )

        if not invoices:

            st.info(
                "There are no draft invoices "
                "available for editing."
            )

            return

        invoice_options = {
            invoice.id: (
                f"{invoice.invoice_number} | "
                f"{invoice.customer.name if invoice.customer else 'Unknown'} | "
                f"{money(invoice.total_amount)}"
            )
            for invoice in invoices
        }

        selected_id = st.selectbox(
            "Select Draft Invoice",
            list(invoice_options.keys()),
            format_func=lambda x:
            invoice_options[x],
        )

        invoice = get_invoice(
            db,
            selected_id,
        )

        if not invoice:
            st.error(
                "Invoice could not be found."
            )
            return

        customers = get_customers(db)
        products = get_products(db)

        customer_options = {
            customer.id: customer.name
            for customer in customers
        }

        customer_ids = list(
            customer_options.keys()
        )

        current_customer = (
            invoice.customer_id
        )

        if current_customer not in customer_ids:
            customer_ids.append(
                current_customer
            )

        selected_customer = st.selectbox(
            "Customer",
            customer_ids,
            index=customer_ids.index(
                current_customer
            ),
            format_func=lambda x:
            customer_options.get(
                x,
                f"Customer #{x}",
            ),
        )

        col1, col2 = st.columns(2)

        with col1:

            new_invoice_date = st.date_input(
                "Invoice Date",
                value=safe_date(
                    invoice.invoice_date
                ),
            )

        with col2:

            new_due_date = st.date_input(
                "Due Date",
                value=safe_date(
                    invoice.due_date
                ),
            )

        # Prepare session items.
        st.session_state.invoice_items = [
            {
                "product_id": item.product_id,
                "product_name": item.product_name,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
            }
            for item in invoice.items
        ]

        edited_items = invoice_items_editor(
            products
        )

        subtotal = calculate_items_total(
            edited_items
        )

        new_tax = st.number_input(
            "Tax Amount",
            min_value=0.0,
            value=float(
                invoice.tax_amount or 0
            ),
            step=100.0,
        )

        new_total = (
            subtotal
            + float(new_tax)
        )

        st.metric(
            "New Invoice Total",
            money(new_total),
        )

        new_notes = st.text_area(
            "Notes",
            value=invoice.notes or "",
        )

        if st.button(
            "💾 Update Invoice",
            type="primary",
            use_container_width=True,
        ):

            valid_items = [
                item
                for item in edited_items
                if item.get("product_name")
                and float(
                    item.get(
                        "quantity",
                        0,
                    )
                    or 0
                ) > 0
            ]

            if not valid_items:

                st.error(
                    "Invoice must contain "
                    "at least one item."
                )

                return

            try:

                updated = update_invoice(
                    db=db,
                    invoice_id=invoice.id,
                    customer_id=selected_customer,
                    items=valid_items,
                    invoice_date=new_invoice_date,
                    due_date=new_due_date,
                    tax_amount=new_tax,
                    notes=new_notes,
                )

                st.success(
                    f"{updated.invoice_number} "
                    f"updated successfully."
                )

                reset_invoice_form()

                st.rerun()

            except Exception as exc:

                db.rollback()

                st.error(
                    f"Could not update invoice: "
                    f"{exc}"
                )

    finally:

        db.close()


# ============================================================
# POST INVOICE
# ============================================================

def post_invoice_page():

    st.subheader("Post Invoice")

    db = SessionLocal()

    try:

        invoices = list_invoices(
            db,
            status="Draft",
        )

        if not invoices:

            st.info(
                "No draft invoices are waiting "
                "to be posted."
            )

            return

        invoice_options = {
            invoice.id: (
                f"{invoice.invoice_number} | "
                f"{invoice.customer.name if invoice.customer else 'Unknown'} | "
                f"{money(invoice.total_amount)}"
            )
            for invoice in invoices
        }

        selected_id = st.selectbox(
            "Select Invoice",
            list(invoice_options.keys()),
            format_func=lambda x:
            invoice_options[x],
        )

        invoice = get_invoice(
            db,
            selected_id,
        )

        if invoice:

            invoice_details(invoice)

            st.warning(
                "Posting an invoice creates the "
                "Accounts Receivable and Sales "
                "Revenue journal entry. "
                "This action cannot be undone "
                "by editing the invoice."
            )

            if st.button(
                "📌 Post Invoice",
                type="primary",
                use_container_width=True,
            ):

                try:

                    posted = post_invoice(
                        db,
                        invoice.id,
                    )

                    st.success(
                        f"{posted.invoice_number} "
                        f"posted successfully."
                    )

                    st.rerun()

                except Exception as exc:

                    db.rollback()

                    st.error(
                        f"Could not post invoice: "
                        f"{exc}"
                    )

    finally:

        db.close()


# ============================================================
# VOID INVOICE
# ============================================================

def void_invoice_page():

    st.subheader("Void Invoice")

    db = SessionLocal()

    try:

        invoices = (
            db.query(Invoice)
            .filter(
                Invoice.status.in_(
                    ["Draft", "Posted"]
                )
            )
            .order_by(
                Invoice.id.desc()
            )
            .all()
        )

        if not invoices:

            st.info(
                "No invoices are available "
                "for voiding."
            )

            return

        invoice_options = {
            invoice.id: (
                f"{invoice.invoice_number} | "
                f"{invoice.status} | "
                f"{money(invoice.total_amount)}"
            )
            for invoice in invoices
        }

        selected_id = st.selectbox(
            "Select Invoice",
            list(invoice_options.keys()),
            format_func=lambda x:
            invoice_options[x],
        )

        invoice = get_invoice(
            db,
            selected_id,
        )

        if invoice:

            invoice_details(invoice)

            if invoice.status == "Posted":

                st.warning(
                    "This invoice is already posted. "
                    "Voiding it will create a "
                    "reversal journal entry."
                )

            else:

                st.warning(
                    "This is a Draft invoice. "
                    "It will be marked as Void."
                )

            confirmation = st.checkbox(
                "I confirm that I want to void this invoice."
            )

            if confirmation:

                if st.button(
                    "🚫 Void Invoice",
                    type="primary",
                    use_container_width=True,
                ):

                    try:

                        voided = void_invoice(
                            db,
                            invoice.id,
                        )

                        st.success(
                            f"{voided.invoice_number} "
                            f"has been voided."
                        )

                        st.rerun()

                    except Exception as exc:

                        db.rollback()

                        st.error(
                            f"Could not void invoice: "
                            f"{exc}"
                        )

    finally:

        db.close()


# ============================================================
# DASHBOARD
# ============================================================

def invoice_dashboard():

    db = SessionLocal()

    try:

        invoices = list_invoices(db)

        total_invoiced = sum(
            float(i.total_amount or 0)
            for i in invoices
            if i.status != "Void"
        )

        total_paid = sum(
            float(i.amount_paid or 0)
            for i in invoices
            if i.status != "Void"
        )

        total_outstanding = sum(
            float(i.balance_due or 0)
            for i in invoices
            if i.status == "Posted"
        )

        posted_count = sum(
            1
            for i in invoices
            if i.status == "Posted"
        )

        draft_count = sum(
            1
            for i in invoices
            if i.status == "Draft"
        )

        void_count = sum(
            1
            for i in invoices
            if i.status == "Void"
        )

        st.subheader(
            "Invoice Overview"
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Total Invoiced",
                money(total_invoiced),
            )

        with col2:
            st.metric(
                "Paid",
                money(total_paid),
            )

        with col3:
            st.metric(
                "Outstanding",
                money(total_outstanding),
            )

        with col4:
            st.metric(
                "Posted Invoices",
                posted_count,
            )

        st.divider()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Draft",
                draft_count,
            )

        with col2:
            st.metric(
                "Posted",
                posted_count,
            )

        with col3:
            st.metric(
                "Void",
                void_count,
            )

        if invoices:

            st.subheader(
                "Recent Invoices"
            )

            rows = []

            for invoice in invoices[:20]:

                rows.append(
                    {
                        "Invoice":
                        invoice.invoice_number,
                        "Customer":
                        (
                            invoice.customer.name
                            if invoice.customer
                            else "Unknown"
                        ),
                        "Date":
                        invoice.invoice_date,
                        "Status":
                        invoice.status,
                        "Total":
                        money(
                            invoice.total_amount
                        ),
                        "Paid":
                        money(
                            invoice.amount_paid
                        ),
                        "Balance":
                        money(
                            invoice.balance_due
                        ),
                    }
                )

            st.dataframe(
                rows,
                use_container_width=True,
                hide_index=True,
            )

    finally:

        db.close()


# ============================================================
# MAIN PAGE
# ============================================================

def invoices_page():
    """
    Main Sales & Distribution Invoice page.

    This function is imported by streamlit_app.py as:

        sales_invoices = safe_import(
            "modules.sales.invoices",
            "invoices_page"
        )
    """

    st.header("🧾 Invoices")

    menu = st.radio(
        "Invoice Module",
        [
            "Dashboard",
            "Create",
            "View",
            "Edit",
            "Post",
            "Void",
        ],
        horizontal=True,
    )

    st.divider()

    if menu == "Dashboard":

        invoice_dashboard()

    elif menu == "Create":

        create_invoice_page()

    elif menu == "View":

        view_invoice_page()

    elif menu == "Edit":

        edit_invoice_page()

    elif menu == "Post":

        post_invoice_page()

    elif menu == "Void":

        void_invoice_page()


# ============================================================
# COMPATIBILITY ALIAS
# ============================================================

invoice_page = invoices_page