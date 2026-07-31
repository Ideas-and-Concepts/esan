"""
Finance Dashboard – uses finance_service
"""

import streamlit as st
import pandas as pd
from services.finance_service import (
    get_total_revenue, get_total_expenses, get_net_profit,
    get_monthly_revenue, get_monthly_expenses
)

def finance_dashboard():
    st.title("💰 Finance Dashboard")
    rev = get_total_revenue()
    exp = get_total_expenses()
    profit = get_net_profit()
    col1, col2, col3 = st.columns(3)
    col1.metric("Revenue", f"${rev:,.2f}")
    col2.metric("Expenses", f"${exp:,.2f}")
    col3.metric("Net Profit", f"${profit:,.2f}")

    st.markdown("---")
    st.subheader("Monthly Revenue vs Expenses")
    monthly_rev = get_monthly_revenue()
    monthly_exp = get_monthly_expenses()
    months = sorted(set(list(monthly_rev.keys()) + list(monthly_exp.keys())))
    chart_data = []
    for m in months:
        chart_data.append({
            "Month": m,
            "Revenue": monthly_rev.get(m, 0),
            "Expenses": monthly_exp.get(m, 0)
        })
    if chart_data:
        df = pd.DataFrame(chart_data).set_index("Month")
        st.line_chart(df)
