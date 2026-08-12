"""
Esan ERP - Sales Payments Module

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Version 1.4.0 Alpha

Features:
- Create payments
- View payments
- Edit draft payments
- Post payments
- Reverse payments
- Invoice balance tracking
- Finance journal integration
"""

from datetime import date

import streamlit as st

from database import SessionLocal

from models import (
    Invoice,
    Payment,
)

from services.payment_service import (
    create_payment,
    update_payment,
    get_payment,
    list_payments,
    post_payment,
    reverse_payment,
    get_payment_journal,
    get_invoice_payment_summary,
)


# ============================================================
# HELPERS
# ============================================================

def money(value):
    """Format amount as UGX."""

    try:
        return f"UGX {float(value or 0):,.2f}"
    except Exception:
        return "UGX 0.00"


def get_invoices(db):
    """
    Return invoices that can receive payments.

    Posted and Paid invoices are included because a
    payment can be entered against a Posted invoice.
    """

    return (
        db.query(Invoice)
        .filter(
            Invoice.status.in_(
                ["Posted", "Paid"]
            )
        )
        .order_by(
            Invoice.id.desc()
        )
        .all()
    )


def payment_status_badge(status):
    """Return a visual payment status."""

    if status == "Posted":
        return "🟢 Posted"

    if status == "Draft":
        return "🟡 Draft"

    if status == "Reversed":
        return "🔴 Reversed"

    return status or "Unknown"


# ============================================================
# PAYMENT DASHBOARD
# ============================================================

def payment_dashboard():
    """Payment overview."""

    db = SessionLocal()

    try:

        payments = list_payments(db)

        posted_payments = [
            payment
            for payment in payments
            if payment.status == "Posted"
        ]

        draft_payments = [
            payment
            for payment in payments
            if payment.status == "Draft"
        ]

        reversed_payments = [
            payment
            for payment in payments
            if payment.status == "Reversed"
        ]

        total_received = sum(
            float(payment.amount or 0)
            for payment in posted_payments
        )

        total_drafts = sum(
            float(payment.amount or 0)
            for payment in draft_payments
        )

        total_reversed = sum(
            float(payment.amount or 0)
            for payment in reversed_payments
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                "Payments Received",
                money(total_received),
            )

        with col2:

            st.metric(
                "Draft Payments",
                money(total_drafts),
            )

        with col3:

            st.metric(
                "Reversed",
                money(total_reversed),
            )

        with col4:

            st.metric(
                "Posted Transactions",
                len(posted_payments),
            )

        st.divider()

        if payments:

            st.subheader(
                "Recent Payments"
            )

            rows = []

            for payment in payments[:25]:

                invoice = payment.invoice

                customer_name = (
                    invoice.customer.name
                    if invoice
                    and invoice.customer
                    else "Unknown"
                )

                rows.append(
                    {
                        "Payment":
                            payment.payment_number,
                        "Invoice":
                            (
                                invoice.invoice_number
                                if invoice
                                else "-"
                            ),
                        "Customer":
                            customer_name,
                        "Date":
                            payment.payment_date,
                        "Method":
                            payment.payment_method,
                        "Amount":
                            money(payment.amount),
                        "Status":
                            payment.status,
                    }
                )

            st.dataframe(
                rows,
                use_container_width=True,
                hide_index=True,
            )

        else:

            st.info(
                "No payments have been recorded yet."
            )

    finally:

        db.close()


# ============================================================
# CREATE PAYMENT
# ============================================================

def create_payment_page():
    """Create a new payment."""

    st.subheader("Create Payment")

    db = SessionLocal()

    try:

        invoices = get_invoices(db)

        if not invoices:

            st.warning(
                "There are no Posted invoices "
                "available for payment."
            )

            return

        invoice_options = {}

        for invoice in invoices:

            customer_name = (
                invoice.customer.name
                if invoice.customer
                else "Unknown Customer"
            )

            invoice_options[invoice.id] = (
                f"{invoice.invoice_number} | "
                f"{customer_name} | "
                f"Balance: "
                f"{money(invoice.balance_due)}"
            )

        selected_invoice_id = st.selectbox(
            "Invoice",
            list(invoice_options.keys()),
            format_func=lambda x:
            invoice_options[x],
        )

        invoice = (
            db.query(Invoice)
            .filter(
                Invoice.id
                == selected_invoice_id
            )
            .first()
        )

        if not invoice:
            st.error(
                "Invoice could not be found."
            )
            return

        st.markdown("### Invoice Information")

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                "Invoice",
                invoice.invoice_number,
            )

        with col2:

            st.metric(
                "Invoice Total",
                money(
                    invoice.total_amount
                ),
            )

        with col3:

            st.metric(
                "Paid",
                money(
                    invoice.amount_paid
                ),
            )

        with col4:

            st.metric(
                "Balance",
                money(
                    invoice.balance_due
                ),
            )

        if float(
            invoice.balance_due or 0
        ) <= 0:

            st.success(
                "This invoice is fully paid."
            )

            return

        st.divider()

        max_amount = float(
            invoice.balance_due or 0
        )

        amount = st.number_input(
            "Payment Amount",
            min_value=0.01,
            max_value=max_amount,
            value=max_amount,
            step=1000.0,
        )

        payment_method = st.selectbox(
            "Payment Method",
            [
                "Cash",
                "Bank Transfer",
                "Mobile Money",
                "Cheque",
                "Other",
            ],
        )

        payment_date = st.date_input(
            "Payment Date",
            value=date.today(),
        )

        reference = st.text_input(
            "Payment Reference",
            placeholder=(
                "Receipt number, transaction ID, "
                "cheque number, etc."
            ),
        )

        notes = st.text_area(
            "Notes",
            placeholder="Optional notes...",
        )

        st.divider()

        if st.button(
            "💾 Save Payment",
            type="primary",
            use_container_width=True,
        ):

            try:

                payment = create_payment(
                    db=db,
                    invoice_id=invoice.id,
                    amount=amount,
                    payment_method=payment_method,
                    payment_date=payment_date,
                    reference=reference,
                    notes=notes,
                )

                st.success(
                    f"Payment "
                    f"{payment.payment_number} "
                    f"created successfully."
                )

                st.info(
                    "The payment is currently Draft. "
                    "Post it to update the invoice "
                    "and Finance."
                )

                st.rerun()

            except Exception as exc:

                db.rollback()

                st.error(
                    f"Could not create payment: "
                    f"{exc}"
                )

    finally:

        db.close()


# ============================================================
# VIEW PAYMENT
# ============================================================

def view_payment_page():
    """View payment details."""

    st.subheader("View Payment")

    db = SessionLocal()

    try:

        payments = list_payments(db)

        if not payments:

            st.info(
                "No payments have been recorded."
            )

            return

        payment_options = {}

        for payment in payments:

            invoice = payment.invoice

            invoice_number = (
                invoice.invoice_number
                if invoice
                else "-"
            )

            payment_options[payment.id] = (
                f"{payment.payment_number} | "
                f"{invoice_number} | "
                f"{money(payment.amount)} | "
                f"{payment.status}"
            )

        selected_id = st.selectbox(
            "Select Payment",
            list(payment_options.keys()),
            format_func=lambda x:
            payment_options[x],
        )

        payment = get_payment(
            db,
            selected_id,
        )

        if not payment:
            st.error(
                "Payment not found."
            )
            return

        invoice = payment.invoice

        customer_name = (
            invoice.customer.name
            if invoice
            and invoice.customer
            else "Unknown"
        )

        st.subheader(
            payment.payment_number
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.metric(
                "Amount",
                money(payment.amount),
            )

        with col2:

            st.metric(
                "Method",
                payment.payment_method,
            )

        with col3:

            st.metric(
                "Status",
                payment.status,
            )

        with col4:

            st.metric(
                "Customer",
                customer_name,
            )

        st.divider()

        col1, col2 = st.columns(2)

        with col1:

            st.write(
                f"**Invoice:** "
                f"{invoice.invoice_number if invoice else '-'}"
            )

            st.write(
                f"**Payment Date:** "
                f"{payment.payment_date}"
            )

        with col2:

            st.write(
                f"**Reference:** "
                f"{payment.reference or '-'}"
            )

            st.write(
                f"**Notes:** "
                f"{payment.notes or '-'}"
            )

        st.divider()

        if invoice:

            st.subheader(
                "Invoice Payment Summary"
            )

            summary = (
                get_invoice_payment_summary(
                    db,
                    invoice.id,
                )
            )

            col1, col2, col3 = st.columns(3)

            with col1:

                st.metric(
                    "Invoice Total",
                    money(
                        summary[
                            "invoice_total"
                        ]
                    ),
                )

            with col2:

                st.metric(
                    "Total Paid",
                    money(
                        summary[
                            "total_paid"
                        ]
                    ),
                )

            with col3:

                st.metric(
                    "Balance Due",
                    money(
                        summary[
                            "balance_due"
                        ]
                    ),
                )

        journal = get_payment_journal(
            db,
            payment.id,
        )

        if journal:

            st.divider()

            st.subheader(
                "Finance Journal"
            )

            st.write(
                f"**Journal:** "
                f"{journal.entry_number}"
            )

            st.write(
                f"**Description:** "
                f"{journal.description}"
            )

            rows = []

            for line in journal.lines:

                account_name = (
                    line.account.name
                    if line.account
                    else "Unknown"
                )

                account_code = (
                    line.account.code
                    if line.account
                    else "-"
                )

                rows.append(
                    {
                        "Account":
                            f"{account_code} - "
                            f"{account_name}",
                        "Debit":
                            money(line.debit),
                        "Credit":
                            money(line.credit),
                        "Description":
                            line.description or "",
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
# EDIT PAYMENT
# ============================================================

def edit_payment_page():
    """Edit a Draft payment."""

    st.subheader("Edit Draft Payment")

    db = SessionLocal()

    try:

        payments = list_payments(
            db,
            status="Draft",
        )

        if not payments:

            st.info(
                "There are no Draft payments "
                "available for editing."
            )

            return

        payment_options = {}

        for payment in payments:

            invoice = payment.invoice

            payment_options[payment.id] = (
                f"{payment.payment_number} | "
                f"{invoice.invoice_number if invoice else '-'} | "
                f"{money(payment.amount)}"
            )

        selected_id = st.selectbox(
            "Select Draft Payment",
            list(payment_options.keys()),
            format_func=lambda x:
            payment_options[x],
        )

        payment = get_payment(
            db,
            selected_id,
        )

        if not payment:
            st.error(
                "Payment not found."
            )
            return

        invoice = payment.invoice

        if not invoice:
            st.error(
                "Payment invoice not found."
            )
            return

        st.info(
            f"Invoice balance: "
            f"{money(invoice.balance_due)}"
        )

        amount = st.number_input(
            "Payment Amount",
            min_value=0.01,
            max_value=float(
                invoice.balance_due or 0
            ),
            value=float(
                payment.amount or 0
            ),
            step=1000.0,
        )

        methods = [
            "Cash",
            "Bank Transfer",
            "Mobile Money",
            "Cheque",
            "Other",
        ]

        current_method = (
            payment.payment_method
            or "Cash"
        )

        if current_method not in methods:
            methods.append(
                current_method
            )

        payment_method = st.selectbox(
            "Payment Method",
            methods,
            index=methods.index(
                current_method
            ),
        )

        payment_date = st.date_input(
            "Payment Date",
            value=(
                payment.payment_date
                or date.today()
            ),
        )

        reference = st.text_input(
            "Payment Reference",
            value=payment.reference or "",
        )

        notes = st.text_area(
            "Notes",
            value=payment.notes or "",
        )

        if st.button(
            "💾 Update Payment",
            type="primary",
            use_container_width=True,
        ):

            try:

                updated = update_payment(
                    db=db,
                    payment_id=payment.id,
                    amount=amount,
                    payment_method=payment_method,
                    payment_date=payment_date,
                    reference=reference,
                    notes=notes,
                )

                st.success(
                    f"{updated.payment_number} "
                    f"updated successfully."
                )

                st.rerun()

            except Exception as exc:

                db.rollback()

                st.error(
                    f"Could not update payment: "
                    f"{exc}"
                )

    finally:

        db.close()


# ============================================================
# POST PAYMENT
# ============================================================

def post_payment_page():
    """Post a Draft payment."""

    st.subheader("Post Payment")

    db = SessionLocal()

    try:

        payments = list_payments(
            db,
            status="Draft",
        )

        if not payments:

            st.info(
                "There are no Draft payments "
                "waiting to be posted."
            )

            return

        payment_options = {}

        for payment in payments:

            invoice = payment.invoice

            payment_options[payment.id] = (
                f"{payment.payment_number} | "
                f"{invoice.invoice_number if invoice else '-'} | "
                f"{money(payment.amount)}"
            )

        selected_id = st.selectbox(
            "Select Payment",
            list(payment_options.keys()),
            format_func=lambda x:
            payment_options[x],
        )

        payment = get_payment(
            db,
            selected_id,
        )

        if not payment:
            st.error(
                "Payment not found."
            )
            return

        invoice = payment.invoice

        st.subheader(
            payment.payment_number
        )

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "Payment",
                money(payment.amount),
            )

        with col2:

            st.metric(
                "Invoice",
                (
                    invoice.invoice_number
                    if invoice
                    else "-"
                ),
            )

        with col3:

            st.metric(
                "Invoice Balance",
                money(
                    invoice.balance_due
                    if invoice
                    else 0
                ),
            )

        st.warning(
            "Posting this payment will:"
        )

        st.markdown(
            """
            - Update the invoice amount paid.
            - Reduce the invoice balance.
            - Mark the payment as Posted.
            - Create the Cash/Bank → Accounts Receivable journal entry.
            - Mark the invoice as Paid if the balance reaches zero.
            """
        )

        confirmation = st.checkbox(
            "I confirm that this payment is valid "
            "and should be posted."
        )

        if confirmation:

            if st.button(
                "📌 Post Payment",
                type="primary",
                use_container_width=True,
            ):

                try:

                    posted = post_payment(
                        db,
                        payment.id,
                    )

                    st.success(
                        f"{posted.payment_number} "
                        f"posted successfully."
                    )

                    st.rerun()

                except Exception as exc:

                    db.rollback()

                    st.error(
                        f"Could not post payment: "
                        f"{exc}"
                    )

    finally:

        db.close()


# ============================================================
# REVERSE PAYMENT
# ============================================================

def reverse_payment_page():
    """Reverse a posted payment."""

    st.subheader("Reverse Payment")

    db = SessionLocal()

    try:

        payments = list_payments(
            db,
            status="Posted",
        )

        if not payments:

            st.info(
                "There are no posted payments "
                "available for reversal."
            )

            return

        payment_options = {}

        for payment in payments:

            invoice = payment.invoice

            payment_options[payment.id] = (
                f"{payment.payment_number} | "
                f"{invoice.invoice_number if invoice else '-'} | "
                f"{money(payment.amount)}"
            )

        selected_id = st.selectbox(
            "Select Payment",
            list(payment_options.keys()),
            format_func=lambda x:
            payment_options[x],
        )

        payment = get_payment(
            db,
            selected_id,
        )

        if not payment:
            st.error(
                "Payment not found."
            )
            return

        invoice = payment.invoice

        st.subheader(
            payment.payment_number
        )

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "Payment Amount",
                money(payment.amount),
            )

        with col2:

            st.metric(
                "Invoice",
                (
                    invoice.invoice_number
                    if invoice
                    else "-"
                ),
            )

        with col3:

            st.metric(
                "Payment Method",
                payment.payment_method,
            )

        st.error(
            "Reversing a payment will restore "
            "the customer's Accounts Receivable "
            "balance and create a reversing "
            "Finance journal entry."
        )

        confirmation = st.checkbox(
            "I confirm that this payment "
            "should be reversed."
        )

        if confirmation:

            if st.button(
                "↩️ Reverse Payment",
                type="primary",
                use_container_width=True,
            ):

                try:

                    reversed_payment = (
                        reverse_payment(
                            db,
                            payment.id,
                        )
                    )

                    st.success(
                        f"{reversed_payment.payment_number} "
                        f"has been reversed."
                    )

                    st.rerun()

                except Exception as exc:

                    db.rollback()

                    st.error(
                        f"Could not reverse payment: "
                        f"{exc}"
                    )

    finally:

        db.close()


# ============================================================
# MAIN PAGE
# ============================================================

def payments_page():
    """
    Main Payments page.

    Designed for integration with streamlit_app.py.
    """

    st.header("💳 Payments")

    menu = st.radio(
        "Payment Module",
        [
            "Dashboard",
            "Create",
            "View",
            "Edit",
            "Post",
            "Reverse",
        ],
        horizontal=True,
    )

    st.divider()

    if menu == "Dashboard":

        payment_dashboard()

    elif menu == "Create":

        create_payment_page()

    elif menu == "View":

        view_payment_page()

    elif menu == "Edit":

        edit_payment_page()

    elif menu == "Post":

        post_payment_page()

    elif menu == "Reverse":

        reverse_payment_page()


# ============================================================
# COMPATIBILITY ALIAS
# ============================================================

payment_page = payments_page