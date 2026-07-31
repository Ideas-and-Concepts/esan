"""
Reports Dashboard – uses report_service
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from services.report_service import (
    revenue_by_customer,
    monthly_revenue,
    inventory_levels,
    expense_categories,
    order_status_summary
)

def reports_dashboard():
    st.title("📊 Reports")
    st.subheader("Revenue by Customer")
    cust_rev = revenue_by_customer()
    if cust_rev:
        df = pd.DataFrame(list(cust_rev.items()), columns=["Customer", "Revenue"])
        fig = px.pie(df, values="Revenue", names="Customer")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Monthly Revenue")
    monthly = monthly_revenue()
    if monthly:
        df = pd.DataFrame(list(monthly.items()), columns=["Month", "Revenue"])
        fig = px.line(df, x="Month", y="Revenue", markers=True)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Inventory Levels")
    inv = inventory_levels()
    if inv:
        df = pd.DataFrame(inv)
        fig = px.bar(df, x="name", y="quantity", color="category")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Order Status Summary")
    orders = order_status_summary()
    if orders:
        df = pd.DataFrame(list(orders.items()), columns=["Status", "Count"])
        fig = px.bar(df, x="Status", y="Count")
        st.plotly_chart(fig, use_container_width=True)
