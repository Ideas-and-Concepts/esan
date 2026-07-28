"""
AI Assistant Module
Esan ERP - Smart Query Interface
"""

import streamlit as st
import pandas as pd
from database import SessionLocal
from models import Invoice, Payment, Customer

def get_db():
    return SessionLocal()

def ai_assistant_page():
    st.title("🤖 AI Assistant (Beta)")
    st.markdown("Ask questions about your business data in plain English.")

    query = st.text_input("Your question", placeholder="e.g., 'Which customer has the highest outstanding balance?'")

    if query:
        db = get_db()
        try:
            # Very basic rule-based responses (replace with LLM later)
            response = ""
            if "outstanding" in query.lower() or "balance" in query.lower():
                invoices = db.query(Invoice).filter(Invoice.status != "Paid").all()
                if invoices:
                    balances = {}
                    for inv in invoices:
                        payments = db.query(Payment).filter(Payment.invoice_id == inv.id).all()
                        paid = sum(p.amount for p in payments)
                        bal = inv.amount - paid
                        cust = db.query(Customer).filter(Customer.id == inv.customer_id).first()
                        cname = cust.name if cust else inv.invoice_number
                        balances[cname] = balances.get(cname, 0) + bal
                    top = sorted(balances.items(), key=lambda x: x[1], reverse=True)
                    response = f"The highest outstanding balance belongs to **{top[0][0]}** with ${top[0][1]:,.2f}."
                else:
                    response = "No outstanding balances."
            elif "revenue" in query.lower():
                total = db.query(Payment).with_entities(
                    db.query(Payment).statement.with_only_columns(db.func.sum(Payment.amount))
                ).scalar() or 0
                response = f"Total revenue collected is **${total:,.2f}**."
            else:
                response = "I'm still learning. Try asking about 'outstanding balances' or 'revenue'."

            st.success(response)
        finally:
            db.close()