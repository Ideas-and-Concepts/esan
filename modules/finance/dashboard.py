"""
Finance Dashboard Module
Nile Harvest Foods Ltd.
Esan ERP - Financial Management Dashboard
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from database import SessionLocal
from models import Invoice, Payment, FinanceTransaction, Customer

def get_db():
    return SessionLocal()

def finance_dashboard():
    st.title("💰 Finance Dashboard")
    db = get_db()
    try:
        invoices = db.query(Invoice).all()
        payments = db.query(Payment).all()
        total_invoiced = sum(inv.amount for inv in invoices)
        total_collected = sum(p.amount for p in payments)
        outstanding = total_invoiced - total_collected
        collection_rate = (total_collected / total_invoiced * 100) if total_invoiced > 0 else 0

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Invoiced", f"${total_invoiced:,.2f}")
        with col2:
            st.metric("Total Collected", f"${total_collected:,.2f}")
        with col3:
            st.metric("Outstanding", f"${outstanding:,.2f}")
        with col4:
            st.metric("Collection Rate", f"{collection_rate:.1f}%")

        st.markdown("---")
        tab1, tab2, tab3, tab4 = st.tabs(["Revenue", "Receivables", "Transactions", "Reports"])
        with tab1:
            revenue_overview(db, payments)
        with tab2:
            accounts_receivable(db)
        with tab3:
            transactions_view(db)
        with tab4:
            financial_reports(db, payments)
    finally:
        db.close()

def revenue_overview(db, payments):
    st.subheader("Revenue Overview")
    if payments:
        monthly = {}
        for p in payments:
            month = p.created_at.strftime('%Y-%m')
            monthly[month] = monthly.get(month, 0) + p.amount
        rev_df = pd.DataFrame(list(monthly.items()), columns=['Month', 'Revenue']).sort_values('Month')
        st.line_chart(rev_df.set_index('Month'))

        st.subheader("By Method")
        method_rev = {}
        for p in payments:
            method_rev[p.payment_method] = method_rev.get(p.payment_method, 0) + p.amount
        method_df = pd.DataFrame(list(method_rev.items()), columns=['Method', 'Amount'])
        st.bar_chart(method_df.set_index('Method'))
    else:
        st.info("No revenue yet.")

def accounts_receivable(db):
    st.subheader("Accounts Receivable")
    unpaid = db.query(Invoice).filter(Invoice.status != "Paid").all()
    if unpaid:
        data = []
        today = datetime.utcnow()
        for inv in unpaid:
            customer = db.query(Customer).filter(Customer.id == inv.customer_id).first()
            payments = db.query(Payment).filter(Payment.invoice_id == inv.id).all()
            paid = sum(p.amount for p in payments)
            balance = inv.amount - paid
            age = (today - inv.created_at).days if inv.created_at else 0
            if age <= 30:
                aging = "0-30"
            elif age <= 60:
                aging = "31-60"
            elif age <= 90:
                aging = "61-90"
            else:
                aging = "90+"
            data.append({
                'Customer': customer.name if customer else 'N/A',
                'Invoice': inv.invoice_number,
                'Total': f"${inv.amount:,.2f}",
                'Paid': f"${paid:,.2f}",
                'Balance': f"${balance:,.2f}",
                'Age': age,
                'Aging': aging
            })
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)

        aging_totals = df.groupby('Aging').apply(
            lambda x: sum(float(v.replace('$','').replace(',','')) for v in x['Balance'])
        )
        st.bar_chart(aging_totals)
    else:
        st.success("All invoices paid.")

def transactions_view(db):
    st.subheader("Recent Transactions")
    trans = db.query(FinanceTransaction).order_by(FinanceTransaction.created_at.desc()).limit(50).all()
    if trans:
        data = []
        for t in trans:
            data.append({
                'Date': t.created_at.strftime('%Y-%m-%d'),
                'Type': t.transaction_type,
                'Category': t.category or '',
                'Description': t.description or '',
                'Amount': f"${t.amount:,.2f}" if t.amount else '$0.00',
                'Reference': t.reference or ''
            })
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No transactions recorded.")
        with st.expander("Add Transaction"):
            with st.form("add_trans"):
                trans_type = st.selectbox("Type", ["Income", "Expense", "Transfer", "Other"])
                category = st.text_input("Category")
                description = st.text_area("Description")
                amount = st.number_input("Amount", min_value=0.0, step=0.01)
                reference = st.text_input("Reference")
                if st.form_submit_button("Add"):
                    if amount > 0:
                        db.add(FinanceTransaction(
                            transaction_type=trans_type,
                            category=category,
                            description=description,
                            amount=amount,
                            reference=reference,
                            created_at=datetime.utcnow()
                        ))
                        db.commit()
                        st.success("Added!")
                        st.rerun()

def financial_reports(db, payments):
    st.subheader("Financial Reports")
    income_trans = db.query(FinanceTransaction).filter(FinanceTransaction.transaction_type == "Income").all()
    expense_trans = db.query(FinanceTransaction).filter(FinanceTransaction.transaction_type == "Expense").all()
    total_income = sum(t.amount for t in income_trans) + sum(p.amount for p in payments)
    total_expenses = sum(t.amount for t in expense_trans)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Income", f"${total_income:,.2f}")
    with col2:
        st.metric("Total Expenses", f"${total_expenses:,.2f}")
    with col3:
        st.metric("Net Profit", f"${total_income - total_expenses:,.2f}")

    if expense_trans:
        st.subheader("Expense Breakdown")
        cat_exp = {}
        for t in expense_trans:
            cat = t.category or 'Other'
            cat_exp[cat] = cat_exp.get(cat, 0) + (t.amount or 0)
        exp_df = pd.DataFrame(list(cat_exp.items()), columns=['Category', 'Amount'])
        st.bar_chart(exp_df.set_index('Category'))

    # Cash flow
    st.subheader("Cash Flow")
    monthly = {}
    for p in payments:
        month = p.created_at.strftime('%Y-%m')
        if month not in monthly:
            monthly[month] = {'in': 0, 'out': 0}
        monthly[month]['in'] += p.amount
    for t in expense_trans:
        month = t.created_at.strftime('%Y-%m') if t.created_at else 'Unknown'
        if month not in monthly:
            monthly[month] = {'in': 0, 'out': 0}
        monthly[month]['out'] += (t.amount or 0)

    flow_data = []
    for month, flows in sorted(monthly.items()):
        flow_data.append({'Month': month, 'Inflow': flows['in'], 'Outflow': flows['out']})
    if flow_data:
        flow_df = pd.DataFrame(flow_data)
        st.line_chart(flow_df.set_index('Month'))