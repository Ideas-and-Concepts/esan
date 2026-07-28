"""
Profitability Module
Esan ERP - Profit Analysis
"""

import streamlit as st
import pandas as pd
from database import SessionLocal
from models import Payment, FinanceTransaction
from sqlalchemy import func

def get_db():
    return SessionLocal()

def profitability_page():
    st.title("📈 Profitability Analysis")
    db = get_db()
    try:
        # Total revenue (from payments)
        total_revenue = db.query(func.sum(Payment.amount)).scalar() or 0
        # Total expenses (from expense transactions)
        total_expenses = db.query(func.sum(FinanceTransaction.amount)).filter(
            FinanceTransaction.transaction_type == "Expense"
        ).scalar() or 0
        net_profit = total_revenue - total_expenses

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Revenue", f"${total_revenue:,.2f}")
        col2.metric("Total Expenses", f"${total_expenses:,.2f}")
        col3.metric("Net Profit", f"${net_profit:,.2f}",
                     delta=f"${net_profit:,.2f}")

        st.markdown("---")
        st.subheader("Monthly Profit Trend")
        # Revenue by month
        payments = db.query(Payment).all()
        monthly_rev = {}
        for p in payments:
            month = p.created_at.strftime('%Y-%m')
            monthly_rev[month] = monthly_rev.get(month, 0) + p.amount
        # Expenses by month
        expenses = db.query(FinanceTransaction).filter(FinanceTransaction.transaction_type == "Expense").all()
        monthly_exp = {}
        for e in expenses:
            month = e.created_at.strftime('%Y-%m')
            monthly_exp[month] = monthly_exp.get(month, 0) + e.amount

        months = sorted(set(list(monthly_rev.keys()) + list(monthly_exp.keys())))
        chart_data = []
        for m in months:
            rev = monthly_rev.get(m, 0)
            exp = monthly_exp.get(m, 0)
            chart_data.append({'Month': m, 'Revenue': rev, 'Expenses': exp, 'Profit': rev - exp})
        if chart_data:
            df = pd.DataFrame(chart_data).set_index('Month')
            st.line_chart(df[['Revenue', 'Expenses', 'Profit']])
    finally:
        db.close()