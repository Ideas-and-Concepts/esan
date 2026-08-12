"""
Esan ERP
Payments Module

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System
"""

import streamlit as st

from datetime import date

from database import SessionLocal
from models import Customer, Invoice

from services.payment_service import (
    get_all_payments,
    get_payment,
    get_invoice_payments,
    create_payment,
    update_payment,
    post_payment,
    reverse_payment,
    get_invoice_balance,
    get_customer_outstanding_balance,
    get_payment_summary,
)


# ==========================================================
# HELPERS
# ==========================================================

def _get(obj, field, default=None):
    return getattr(obj, field, default)


def _money(value):
    try:
        return f"UGX {float(value):,.0f}"
    except Exception:
        return "UGX 0"


def _status(payment):
    return _get(
        payment,
        "status",
        "Draft",
    ) or "Draft"


def _status_icon(status):

    status = str(status).lower()

    if status == "draft":
        return "🟡"

    if status == "posted":
        return "🟢"

    if status in (
        "reversed",
        "void",
        "voided",
    ):
        return "🔴"

    return "⚪"


# ==========================================================
# MAIN PAGE
# ==========================================================

def payments_page():

    st.title("💳 Payments")

    st.caption(
        "Manage customer payments and Accounts Receivable."
    )

    db = SessionLocal()

    try:

        tab_create, tab_list, tab_manage = st.tabs(
            [
                "➕ Receive Payment",
                "📋 Payment Register",
                "⚙️ Manage Payment",
            ]
        )

        # ==================================================
        # CREATE PAYMENT
        # ==================================================

        with tab_create:

            st.subheader(
                "Receive Customer Payment"
            )

            invoices = (
                db.query(Invoice)
                .order_by(
                    Invoice.id.desc()
                )
                .all()
            )

            usable_invoices = []

            for invoice in invoices:

                status = str(
                    _get(
                        invoice,
                        "status",
                        "Draft",
                    )
                ).lower()

                if status in (
                    "void",
                    "voided",
                ):
                    continue

                try:

                    balance = get_invoice_balance(
                        db,
                        invoice.id,
                    )

                    if balance["balance"] > 0:
                        usable_invoices.append(
                            invoice
                        )

                except Exception:
                    continue

            if not usable_invoices:

                st.info(
                    "There are no invoices with "
                    "an outstanding balance."
                )

            else:

                invoice_map = {}

                for invoice in usable_invoices:

                    customer = (
                        db.query(Customer)
                        .filter(
                            Customer.id
                            == invoice.customer_id
                        )
                        .first()
                    )

                    customer_name = _get(
                        customer,
                        "name",
                        "Unknown Customer",
                    )

                    balance = (
                        get_invoice_balance(
                            db,
                            invoice.id,
                        )
                    )

                    label = (
                        f"INV-{invoice.id:05d} | "
                        f"{customer_name} | "
                        f"Balance: "
                        f"{_money(balance['balance'])}"
                    )

                    invoice_map[label] = invoice

                selected_label = st.selectbox(
                    "Invoice",
                    list(
                        invoice_map.keys()
                    ),
                )

                invoice = invoice_map[
                    selected_label
                ]

                balance = get_invoice_balance(
                    db,
                    invoice.id,
                )

                st.info(
                    f"Invoice total: "
                    f"{_money(balance['invoice_total'])}  |  "
                    f"Paid: "
                    f"{_money(balance['paid_amount'])}  |  "
                    f"Outstanding: "
                    f"{_money(balance['balance'])}"
                )

                amount = st.number_input(
                    "Payment Amount",
                    min_value=0.01,
                    max_value=float(
                        balance["balance"]
                    ),
                    value=float(
                        balance["balance"]
                    ),
                    step=1000.0,
                )

                payment_date = st.date_input(
                    "Payment Date",
                    value=date.today(),
                )

                payment_method = st.selectbox(
                    "Payment Method",
                    [
                        "Cash",
                        "Bank Transfer",
                        "Mobile Money",
                        "Cheque",
                        "Card",
                        "Other",
                    ],
                )

                reference = st.text_input(
                    "Reference",
                    placeholder=(
                        "Receipt number, bank reference, "
                        "transaction ID, etc."
                    ),
                )

                notes = st.text_area(
                    "Notes",
                )

                if st.button(
                    "Create Draft Payment",
                    type="primary",
                    use_container_width=True,
                ):

                    try:

                        payment = create_payment(
                            db=db,
                            invoice_id=invoice.id,
                            amount=amount,
                            payment_date=payment_date,
                            payment_method=payment_method,
                            reference=reference,
                            notes=notes,
                        )

                        st.session_state[
                            "selected_payment_id"
                        ] = payment.id

                        st.success(
                            f"Payment #{payment.id} "
                            "created successfully."
                        )

                        st.rerun()

                    except Exception as e:

                        st.error(
                            f"Could not create payment: {e}"
                        )

        # ==================================================
        # PAYMENT REGISTER
        # ==================================================

        with tab_list:

            st.subheader(
                "Payment Register"
            )

            summary = get_payment_summary(
                db
            )

            c1, c2, c3, c4 = st.columns(4)

            with c1:
                st.metric(
                    "Posted",
                    _money(
                        summary[
                            "total_posted"
                        ]
                    ),
                )

            with c2:
                st.metric(
                    "Draft",
                    _money(
                        summary[
                            "total_draft"
                        ]
                    ),
                )

            with c3:
                st.metric(
                    "Reversed",
                    _money(
                        summary[
                            "total_reversed"
                        ]
                    ),
                )

            with c4:
                st.metric(
                    "Transactions",
                    summary[
                        "payment_count"
                    ],
                )

            st.divider()

            payments = get_all_payments(
                db
            )

            if not payments:

                st.info(
                    "No payments have been created."
                )

            else:

                filter_status = st.selectbox(
                    "Status",
                    [
                        "All",
                        "Draft",
                        "Posted",
                        "Reversed",
                    ],
                    key="payment_status_filter",
                )

                for payment in payments:

                    status = _status(
                        payment
                    )

                    if (
                        filter_status != "All"
                        and status != filter_status
                    ):
                        continue

                    customer = (
                        db.query(Customer)
                        .filter(
                            Customer.id
                            == payment.customer_id
                        )
                        .first()
                    )

                    customer_name = _get(
                        customer,
                        "name",
                        "Unknown",
                    )

                    invoice_number = (
                        f"INV-{payment.invoice_id:05d}"
                        if payment.invoice_id
                        else "-"
                    )

                    with st.container(
                        border=True
                    ):

                        c1, c2, c3, c4, c5 = st.columns(
                            [
                                1.2,
                                2,
                                1.5,
                                1.5,
                                1.2,
                            ]
                        )

                        with c1:

                            payment_number = _get(
                                payment,
                                "payment_number",
                                f"PAY-{payment.id:05d}",
                            )

                            st.markdown(
                                f"### {payment_number}"
                            )

                        with c2:

                            st.write(
                                f"**{customer_name}**"
                            )

                            st.caption(
                                invoice_number
                            )

                        with c3:

                            st.write(
                                f"{_status_icon(status)} "
                                f"{status}"
                            )

                        with c4:

                            st.write(
                                _money(
                                    _get(
                                        payment,
                                        "amount",
                                        0,
                                    )
                                )
                            )

                        with c5:

                            if st.button(
                                "Open",
                                key=f"open_payment_{payment.id}",
                                use_container_width=True,
                            ):

                                st.session_state[
                                    "selected_payment_id"
                                ] = payment.id

                                st.rerun()

        # ==================================================
        # MANAGE PAYMENT
        # ==================================================

        with tab_manage:

            payment_id = st.session_state.get(
                "selected_payment_id"
            )

            if not payment_id:

                st.info(
                    "Select a payment from the "
                    "Payment Register."
                )

            else:

                payment = get_payment(
                    db,
                    payment_id,
                )

                if not payment:

                    st.error(
                        "Payment not found."
                    )

                else:

                    render_payment_manager(
                        db,
                        payment,
                    )

    finally:

        db.close()


# ==========================================================
# PAYMENT MANAGER
# ==========================================================

def render_payment_manager(
    db,
    payment,
):

    status = _status(payment)

    invoice = (
        db.query(Invoice)
        .filter(
            Invoice.id
            == payment.invoice_id
        )
        .first()
    )

    customer = (
        db.query(Customer)
        .filter(
            Customer.id
            == payment.customer_id
        )
        .first()
    )

    customer_name = _get(
        customer,
        "name",
        "Unknown",
    )

    payment_number = _get(
        payment,
        "payment_number",
        f"PAY-{payment.id:05d}",
    )

    st.subheader(
        payment_number
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        st.metric(
            "Customer",
            customer_name,
        )

    with c2:

        st.metric(
            "Invoice",
            (
                f"INV-{payment.invoice_id:05d}"
                if payment.invoice_id
                else "-"
            ),
        )

    with c3:

        st.metric(
            "Status",
            status,
        )

    with c4:

        st.metric(
            "Amount",
            _money(
                _get(
                    payment,
                    "amount",
                    0,
                )
            ),
        )

    st.divider()

    # ======================================================
    # INVOICE BALANCE
    # ======================================================

    if invoice:

        try:

            balance = get_invoice_balance(
                db,
                invoice.id,
            )

            c1, c2, c3 = st.columns(3)

            with c1:

                st.metric(
                    "Invoice Total",
                    _money(
                        balance[
                            "invoice_total"
                        ]
                    ),
                )

            with c2:

                st.metric(
                    "Paid",
                    _money(
                        balance[
                            "paid_amount"
                        ]
                    ),
                )

            with c3:

                st.metric(
                    "Outstanding",
                    _money(
                        balance[
                            "balance"
                        ]
                    ),
                )

        except Exception as e:

            st.warning(
                f"Could not calculate invoice balance: {e}"
            )

    # ======================================================
    # EDIT DRAFT
    # ======================================================

    if status.lower() == "draft":

        st.markdown(
            "### ✏️ Edit Payment"
        )

        amount = st.number_input(
            "Payment Amount",
            min_value=0.01,
            value=float(
                _get(
                    payment,
                    "amount",
                    0,
                )
                or 0.01
            ),
            step=1000.0,
            key=f"payment_amount_{payment.id}",
        )

        existing_date = _get(
            payment,
            "payment_date",
            None,
        )

        if hasattr(
            existing_date,
            "date",
        ):
            existing_date = (
                existing_date.date()
            )

        if not existing_date:
            existing_date = date.today()

        payment_date = st.date_input(
            "Payment Date",
            value=existing_date,
            key=f"payment_date_{payment.id}",
        )

        current_method = _get(
            payment,
            "payment_method",
            "Cash",
        ) or "Cash"

        methods = [
            "Cash",
            "Bank Transfer",
            "Mobile Money",
            "Cheque",
            "Card",
            "Other",
        ]

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
            key=f"payment_method_{payment.id}",
        )

        reference = st.text_input(
            "Reference",
            value=_get(
                payment,
                "reference",
                "",
            )
            or "",
            key=f"payment_reference_{payment.id}",
        )

        notes = st.text_area(
            "Notes",
            value=_get(
                payment,
                "notes",
                "",
            )
            or "",
            key=f"payment_notes_{payment.id}",
        )

        if st.button(
            "Save Payment Changes",
            type="primary",
            use_container_width=True,
            key=f"save_payment_{payment.id}",
        ):

            try:

                update_payment(
                    db=db,
                    payment_id=payment.id,
                    amount=amount,
                    payment_date=payment_date,
                    payment_method=payment_method,
                    reference=reference,
                    notes=notes,
                )

                st.success(
                    "Payment updated successfully."
                )

                st.rerun()

            except Exception as e:

                st.error(
                    f"Could not update payment: {e}"
                )

    # ======================================================
    # PAYMENT DETAILS
    # ======================================================

    st.markdown(
        "### 📄 Payment Details"
    )

    c1, c2 = st.columns(2)

    with c1:

        st.write(
            f"**Payment Method:** "
            f"{_get(payment, 'payment_method', '-')}"
        )

        st.write(
            f"**Reference:** "
            f"{_get(payment, 'reference', '-') or '-'}"
        )

    with c2:

        st.write(
            f"**Payment Date:** "
            f"{_get(payment, 'payment_date', '-')}"
        )

        st.write(
            f"**Notes:** "
            f"{_get(payment, 'notes', '-') or '-'}"
        )

    # ======================================================
    # ACTIONS
    # ======================================================

    st.divider()

    st.markdown(
        "### ⚙️ Payment Actions"
    )

    if status.lower() == "draft":

        if st.button(
            "📌 Post Payment",
            type="primary",
            use_container_width=True,
            key=f"post_payment_{payment.id}",
        ):

            try:

                post_payment(
                    db=db,
                    payment_id=payment.id,
                )

                st.success(
                    "Payment posted successfully."
                )

                st.rerun()

            except Exception as e:

                st.error(
                    f"Could not post payment: {e}"
                )

    elif status.lower() == "posted":

        st.warning(
            "A posted payment should not be deleted. "
            "Reverse it to preserve the financial audit trail."
        )

        reversal_reason = st.text_input(
            "Reversal reason",
            key=f"reversal_reason_{payment.id}",
        )

        if st.button(
            "↩️ Reverse Payment",
            use_container_width=True,
            key=f"reverse_payment_{payment.id}",
        ):

            try:

                reverse_payment(
                    db=db,
                    payment_id=payment.id,
                    reason=reversal_reason,
                )

                st.success(
                    "Payment reversed successfully."
                )

                st.rerun()

            except Exception as e:

                st.error(
                    f"Could not reverse payment: {e}"
                )

    elif status.lower() == "reversed":

        st.info(
            "This payment has been reversed and "
            "can no longer be posted."
        )

    # ======================================================
    # CUSTOMER BALANCE
    # ======================================================

    if payment.customer_id:

        try:

            customer_balance = (
                get_customer_outstanding_balance(
                    db,
                    payment.customer_id,
                )
            )

            st.divider()

            st.metric(
                "Customer Outstanding Balance",
                _money(customer_balance),
            )

        except Exception as e:

            st.warning(
                f"Could not calculate customer balance: {e}"
            )


# ==========================================================
# COMPATIBILITY ALIAS
# ==========================================================

def payments():
    payments_page()