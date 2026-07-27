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
    """Main finance dashboard."""
    st.title("💰 Finance Dashboard")
    
    db = get_db()
    
    try:
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        # Total invoiced
        invoices = db.query(Invoice).all()
        total_invoiced = sum(inv.amount for inv in invoices)
        
        # Total collected
        payments = db.query(Payment).all()
        total_collected = sum(p.amount for p in payments)
        
        # Outstanding
        outstanding = total_invoiced - total_collected
        
        # Collection rate
        collection_rate = (total_collected / total_invoiced * 100) if total_invoiced > 0 else