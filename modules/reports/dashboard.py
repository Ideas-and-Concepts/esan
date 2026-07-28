"""
Reports & Analytics Dashboard
Esan ERP - Business Intelligence
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from database import SessionLocal
from models import Invoice, Payment, FinanceTransaction, Customer, Product
from sqlalchemy import func

def get_db():
    return SessionLocal()

def reports_dashboard():
    st.title("📊 Reports & Analytics")
    db = get_db()
    try:
        # Sales by customer
        st.subheader("Revenue by Customer")
        payments = db.query(Payment).all()
        customer_rev = {}
        for p in payments:
            inv = db.query(Invoice).filter(Invoice.id == p.invoice_id).first()
            if inv:
                cust = db.query(Customer).filter(Customer.id == inv.customer_id).first()
                cname = cust.name if cust else 'Unknown'
                customer_rev[cname] = customer_rev.get(cname, 0) + p.amount
        if customer_rev:
            df_cust = pd.DataFrame(list(customer_rev.items()), columns=['Customer', 'Revenue'])
            fig = px.pie(df_cust, values='Revenue', names='Customer', title='Revenue Distribution')
            st.plotly_chart(fig, use_container_width=True)

        # Monthly revenue trend
        st.subheader("Monthly Revenue")
        monthly = {}
        for p in payments:
            month = p.created_at.strftime('%Y-%m')
            monthly[month] = monthly.get(month, 0) + p.amount
        if monthly:
            df_month = pd.DataFrame(list(monthly.items()), columns=['Month', 'Revenue']).sort_values('Month')
            fig = px.line(df_month, x='Month', y='Revenue', markers=True)
            st.plotly_chart(fig, use_container_width=True)

        # Stock overview
        st.subheader("Inventory Levels")
        products = db.query(Product).all()
        if products:
            stock_data = [{'Product': p.name, 'Quantity': p.quantity} for p in products]
            df_stock = pd.DataFrame(stock_data)
            fig = px.bar(df_stock, x='Product', y='Quantity', color='Product')
            st.plotly_chart(fig, use_container_width=True)

    finally:
        db.close()