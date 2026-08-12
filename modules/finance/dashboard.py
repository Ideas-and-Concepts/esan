"""
Esan ERP
Finance Dashboard

Nile Harvest Foods Ltd.
Enterprise Resource Planning System

Version 1.4.0 Alpha
"""

from datetime import datetime
from decimal import Decimal

import streamlit as st
from sqlalchemy import func

from database import SessionLocal

from models import (
    Account,
    JournalEntry,
    JournalEntryLine,
)


# ==========================================================
# HELPERS
# ==========================================================

def decimal_value(value):
    try:
        return Decimal(str(value or 0))
    except Exception:
        return Decimal("0")


def money(value):
    """
    Format financial amounts in UGX.
    """
    value = decimal_value(value)

    return f"UGX {value:,.0f}"


def safe_attr(obj, name, default=None):
    return getattr(obj, name, default)


def get_account_type(account):
    return str(
        safe_attr(
            account,
            "account_type",
            "",
        )
    ).strip().lower()


# ==========================================================
# FINANCE DATA
# ==========================================================

def load_finance_data():
    """
    Load Finance information from the database.
    """

    db = SessionLocal()

    try:

        accounts = (
            db.query(Account)
            .order_by(
                Account.code.asc()
            )
            .all()
        )

        journal_entries = (
            db.query(JournalEntry)
            .order_by(
                JournalEntry.id.desc()
            )
            .all()
        )

        posted_entries = (
            db.query(JournalEntry)
            .filter(
                func.lower(
                    JournalEntry.status
                ) == "posted"
            )
            .order_by(
                JournalEntry.id.desc()
            )
            .all()
        )

        lines = (
            db.query(JournalEntryLine)
            .join(
                JournalEntry,
                JournalEntry.id
                == JournalEntryLine.journal_entry_id,
            )
            .filter(
                func.lower(
                    JournalEntry.status
                ) == "posted"
            )
            .all()
        )

        return (
            accounts,
            journal_entries,
            posted_entries,
            lines,
        )

    finally:
        db.close()


# ==========================================================
# CALCULATE ACCOUNT BALANCES
# ==========================================================

def calculate_account_balances(lines):
    """
    Calculate debit/credit balances from posted
    journal entries.

    Returns:

        {
            account_id: {
                debit,
                credit,
                balance
            }
        }
    """

    balances = {}

    for line in lines:

        account_id = safe_attr(
            line,
            "account_id",
        )

        if account_id is None:
            continue

        if account_id not in balances:

            balances[account_id] = {
                "debit": Decimal("0"),
                "credit": Decimal("0"),
                "balance": Decimal("0"),
            }

        debit = decimal_value(
            safe_attr(
                line,
                "debit",
                0,
            )
        )

        credit = decimal_value(
            safe_attr(
                line,
                "credit",
                0,
            )
        )

        balances[account_id]["debit"] += debit
        balances[account_id]["credit"] += credit

        balances[account_id]["balance"] += (
            debit - credit
        )

    return balances


# ==========================================================
# FINANCE DASHBOARD
# ==========================================================

def finance_dashboard():

    st.title("💰 Finance")

    st.caption(
        "Financial management, accounting and "
        "general ledger"
    )

    # ------------------------------------------------------
    # LOAD DATA
    # ------------------------------------------------------

    try:

        (
            accounts,
            journal_entries,
            posted_entries,
            lines,
        ) = load_finance_data()

    except Exception as e:

        st.error(
            "Unable to load Finance data."
        )

        st.exception(e)

        return

    balances = calculate_account_balances(
        lines
    )

    # ------------------------------------------------------
    # ACCOUNT BALANCES
    # ------------------------------------------------------

    revenue = Decimal("0")
    receivables = Decimal("0")
    cash = Decimal("0")
    bank = Decimal("0")
    expenses = Decimal("0")
    assets = Decimal("0")
    liabilities = Decimal("0")
    equity = Decimal("0")

    account_rows = []

    for account in accounts:

        account_id = safe_attr(
            account,
            "id",
        )

        balance_data = balances.get(
            account_id,
            {
                "debit": Decimal("0"),
                "credit": Decimal("0"),
                "balance": Decimal("0"),
            },
        )

        debit = balance_data["debit"]
        credit = balance_data["credit"]

        account_type = get_account_type(
            account
        )

        # Accounting presentation.
        if account_type in (
            "asset",
            "assets",
        ):

            balance = debit - credit
            assets += balance

        elif account_type in (
            "liability",
            "liabilities",
        ):

            balance = credit - debit
            liabilities += balance

        elif account_type in (
            "equity",
            "capital",
        ):

            balance = credit - debit
            equity += balance

        elif account_type in (
            "revenue",
            "income",
            "sales",
        ):

            balance = credit - debit
            revenue += balance

        elif account_type in (
            "expense",
            "expenses",
            "cost",
        ):

            balance = debit - credit
            expenses += balance

        else:

            balance = debit - credit

        name = safe_attr(
            account,
            "name",
            "",
        )

        code = safe_attr(
            account,
            "code",
            "",
        )

        name_lower = str(
            name
        ).lower()

        # Detect common accounts.
        if (
            "receivable" in name_lower
            or "accounts receivable"
            in name_lower
            or "debtors" in name_lower
        ):
            receivables += balance

        if (
            name_lower == "cash"
            or "cash account" in name_lower
            or "cash on hand" in name_lower
        ):
            cash += balance

        if (
            "bank" in name_lower
        ):
            bank += balance

        account_rows.append(
            {
                "Code": code,
                "Account": name,
                "Type": safe_attr(
                    account,
                    "account_type",
                    "",
                ),
                "Debit": debit,
                "Credit": credit,
                "Balance": balance,
            }
        )

    net_profit = revenue - expenses

    total_cash = cash + bank

    # ------------------------------------------------------
    # KPI CARDS
    # ------------------------------------------------------

    st.markdown(
        "### Financial Overview"
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Revenue",
            money(revenue),
        )

    with col2:

        st.metric(
            "Accounts Receivable",
            money(receivables),
        )

    with col3:

        st.metric(
            "Cash & Bank",
            money(total_cash),
        )

    with col4:

        st.metric(
            "Net Profit",
            money(net_profit),
        )

    st.divider()

    # ------------------------------------------------------
    # SECONDARY KPIs
    # ------------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Expenses",
            money(expenses),
        )

    with col2:

        st.metric(
            "Assets",
            money(assets),
        )

    with col3:

        st.metric(
            "Liabilities",
            money(liabilities),
        )

    with col4:

        st.metric(
            "Equity",
            money(equity),
        )

    st.divider()

    # ======================================================
    # NAVIGATION
    # ======================================================

    finance_menu = st.radio(
        "Finance Module",
        [
            "Dashboard",
            "Chart of Accounts",
            "Journal Entries",
            "General Ledger",
        ],
        horizontal=True,
    )

    # ======================================================
    # DASHBOARD
    # ======================================================

    if finance_menu == "Dashboard":

        st.subheader(
            "📊 Financial Summary"
        )

        col1, col2 = st.columns(2)

        with col1:

            st.markdown(
                "#### Financial Position"
            )

            position_data = {
                "Assets": money(assets),
                "Liabilities": money(
                    liabilities
                ),
                "Equity": money(equity),
            }

            for label, value in position_data.items():

                st.write(
                    f"**{label}:** {value}"
                )

        with col2:

            st.markdown(
                "#### Income Statement"
            )

            income_data = {
                "Revenue": money(revenue),
                "Expenses": money(expenses),
                "Net Profit": money(
                    net_profit
                ),
            }

            for label, value in income_data.items():

                st.write(
                    f"**{label}:** {value}"
                )

        st.divider()

        # --------------------------------------------------
        # ACCOUNTING HEALTH
        # --------------------------------------------------

        st.subheader(
            "⚖️ Accounting Control"
        )

        total_debits = sum(
            (
                decimal_value(
                    safe_attr(
                        line,
                        "debit",
                        0,
                    )
                )
                for line in lines
            ),
            Decimal("0"),
        )

        total_credits = sum(
            (
                decimal_value(
                    safe_attr(
                        line,
                        "credit",
                        0,
                    )
                )
                for line in lines
            ),
            Decimal("0"),
        )

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "Posted Entries",
                len(posted_entries),
            )

        with col2:

            st.metric(
                "Total Debits",
                money(total_debits),
            )

        with col3:

            st.metric(
                "Total Credits",
                money(total_credits),
            )

        if total_debits == total_credits:

            st.success(
                "✓ General Ledger is balanced."
            )

        else:

            difference = (
                total_debits
                - total_credits
            )

            st.error(
                "⚠ General Ledger is out of balance: "
                + money(abs(difference))
            )

        st.divider()

        # --------------------------------------------------
        # RECENT ACTIVITY
        # --------------------------------------------------

        st.subheader(
            "🧾 Recent Journal Activity"
        )

        if not journal_entries:

            st.info(
                "No journal entries have been created yet."
            )

        else:

            rows = []

            for entry in journal_entries[:10]:

                rows.append(
                    {
                        "Entry": safe_attr(
                            entry,
                            "entry_number",
                            f"JE-{entry.id}",
                        ),
                        "Date": safe_attr(
                            entry,
                            "entry_date",
                            "",
                        ),
                        "Description": safe_attr(
                            entry,
                            "description",
                            "",
                        ),
                        "Reference": (
                            f"{safe_attr(entry, 'reference_type', '')} "
                            f"{safe_attr(entry, 'reference_id', '')}"
                        ),
                        "Status": safe_attr(
                            entry,
                            "status",
                            "",
                        ),
                    }
                )

            st.dataframe(
                rows,
                use_container_width=True,
                hide_index=True,
            )

    # ======================================================
    # CHART OF ACCOUNTS
    # ======================================================

    elif finance_menu == "Chart of Accounts":

        st.subheader(
            "📚 Chart of Accounts"
        )

        col1, col2 = st.columns(
            [3, 1]
        )

        with col1:

            search = st.text_input(
                "Search accounts",
                placeholder=(
                    "Search by code or account name"
                ),
            )

        with col2:

            active_only = st.checkbox(
                "Active accounts only",
                value=True,
            )

        filtered_accounts = []

        for account in accounts:

            name = str(
                safe_attr(
                    account,
                    "name",
                    "",
                )
            )

            code = str(
                safe_attr(
                    account,
                    "code",
                    "",
                )
            )

            active = safe_attr(
                account,
                "active",
                True,
            )

            if active_only and not active:
                continue

            if search:

                search_lower = search.lower()

                if (
                    search_lower not in name.lower()
                    and search_lower not in code.lower()
                ):
                    continue

            filtered_accounts.append(
                account
            )

        if not filtered_accounts:

            st.info(
                "No accounts found."
            )

        else:

            rows = []

            for account in filtered_accounts:

                account_id = safe_attr(
                    account,
                    "id",
                )

                balance_data = balances.get(
                    account_id,
                    {
                        "debit": Decimal("0"),
                        "credit": Decimal("0"),
                        "balance": Decimal("0"),
                    },
                )

                rows.append(
                    {
                        "Code": safe_attr(
                            account,
                            "code",
                            "",
                        ),
                        "Account": safe_attr(
                            account,
                            "name",
                            "",
                        ),
                        "Type": safe_attr(
                            account,
                            "account_type",
                            "",
                        ),
                        "Debit": money(
                            balance_data[
                                "debit"
                            ]
                        ),
                        "Credit": money(
                            balance_data[
                                "credit"
                            ]
                        ),
                        "Balance": money(
                            balance_data[
                                "balance"
                            ]
                        ),
                        "Active": (
                            "Yes"
                            if safe_attr(
                                account,
                                "active",
                                True,
                            )
                            else "No"
                        ),
                    }
                )

            st.dataframe(
                rows,
                use_container_width=True,
                hide_index=True,
            )

    # ======================================================
    # JOURNAL ENTRIES
    # ======================================================

    elif finance_menu == "Journal Entries":

        st.subheader(
            "🧾 Journal Entries"
        )

        if not journal_entries:

            st.info(
                "No journal entries found."
            )

        else:

            for entry in journal_entries:

                entry_number = safe_attr(
                    entry,
                    "entry_number",
                    f"JE-{entry.id}",
                )

                status = safe_attr(
                    entry,
                    "status",
                    "Draft",
                )

                description = safe_attr(
                    entry,
                    "description",
                    "",
                )

                entry_date = safe_attr(
                    entry,
                    "entry_date",
                    "",
                )

                with st.expander(
                    f"{entry_number} • "
                    f"{status} • "
                    f"{description}"
                ):

                    st.write(
                        f"**Date:** {entry_date}"
                    )

                    st.write(
                        f"**Reference:** "
                        f"{safe_attr(entry, 'reference_type', '')} "
                        f"{safe_attr(entry, 'reference_id', '')}"
                    )

                    entry_lines = [
                        line
                        for line in lines
                        if safe_attr(
                            line,
                            "journal_entry_id",
                        )
                        == entry.id
                    ]

                    if not entry_lines:

                        st.info(
                            "No journal lines found."
                        )

                    else:

                        rows = []

                        for line in entry_lines:

                            account = next(
                                (
                                    a
                                    for a in accounts
                                    if a.id
                                    == line.account_id
                                ),
                                None,
                            )

                            rows.append(
                                {
                                    "Account": (
                                        safe_attr(
                                            account,
                                            "code",
                                            "",
                                        )
                                        + " - "
                                        + safe_attr(
                                            account,
                                            "name",
                                            "",
                                        )
                                        if account
                                        else str(
                                            line.account_id
                                        )
                                    ),
                                    "Debit": money(
                                        safe_attr(
                                            line,
                                            "debit",
                                            0,
                                        )
                                    ),
                                    "Credit": money(
                                        safe_attr(
                                            line,
                                            "credit",
                                            0,
                                        )
                                    ),
                                    "Description": safe_attr(
                                        line,
                                        "description",
                                        "",
                                    ),
                                }
                            )

                        st.dataframe(
                            rows,
                            use_container_width=True,
                            hide_index=True,
                        )

    # ======================================================
    # GENERAL LEDGER
    # ======================================================

    elif finance_menu == "General Ledger":

        st.subheader(
            "📖 General Ledger"
        )

        if not lines:

            st.info(
                "No posted transactions are available."
            )

        else:

            selected_account = st.selectbox(
                "Account",
                accounts,
                format_func=lambda account: (
                    f"{safe_attr(account, 'code', '')} - "
                    f"{safe_attr(account, 'name', '')}"
                ),
            )

            if selected_account:

                selected_lines = [
                    line
                    for line in lines
                    if safe_attr(
                        line,
                        "account_id",
                    )
                    == selected_account.id
                ]

                if not selected_lines:

                    st.info(
                        "No posted transactions "
                        "exist for this account."
                    )

                else:

                    running_balance = Decimal(
                        "0"
                    )

                    rows = []

                    for line in reversed(
                        selected_lines
                    ):

                        debit = decimal_value(
                            safe_attr(
                                line,
                                "debit",
                                0,
                            )
                        )

                        credit = decimal_value(
                            safe_attr(
                                line,
                                "credit",
                                0,
                            )
                        )

                        running_balance += (
                            debit - credit
                        )

                        entry = next(
                            (
                                e
                                for e in posted_entries
                                if e.id
                                == line.journal_entry_id
                            ),
                            None,
                        )

                        rows.append(
                            {
                                "Date": (
                                    safe_attr(
                                        entry,
                                        "entry_date",
                                        "",
                                    )
                                    if entry
                                    else ""
                                ),
                                "Entry": (
                                    safe_attr(
                                        entry,
                                        "entry_number",
                                        "",
                                    )
                                    if entry
                                    else ""
                                ),
                                "Description": safe_attr(
                                    line,
                                    "description",
                                    (
                                        safe_attr(
                                            entry,
                                            "description",
                                            "",
                                        )
                                        if entry
                                        else ""
                                    ),
                                ),
                                "Debit": money(
                                    debit
                                ),
                                "Credit": money(
                                    credit
                                ),
                                "Balance": money(
                                    running_balance
                                ),
                            }
                        )

                    rows.reverse()

                    st.dataframe(
                        rows,
                        use_container_width=True,
                        hide_index=True,
                    )

                    st.divider()

                    account_balance = balances.get(
                        selected_account.id,
                        {
                            "debit": Decimal("0"),
                            "credit": Decimal("0"),
                            "balance": Decimal("0"),
                        },
                    )

                    col1, col2, col3 = st.columns(
                        3
                    )

                    with col1:

                        st.metric(
                            "Total Debit",
                            money(
                                account_balance[
                                    "debit"
                                ]
                            ),
                        )

                    with col2:

                        st.metric(
                            "Total Credit",
                            money(
                                account_balance[
                                    "credit"
                                ]
                            ),
                        )

                    with col3:

                        st.metric(
                            "Balance",
                            money(
                                account_balance[
                                    "balance"
                                ]
                            ),
                        )


# ==========================================================
# OPTIONAL ALIAS
# ==========================================================

def dashboard():
    """
    Compatibility alias.
    """

    finance_dashboard()