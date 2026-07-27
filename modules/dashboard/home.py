"""
Esan ERP Executive Dashboard
Nile Harvest Foods Ltd.
"""

import streamlit as st

from database import SessionLocal

from models import (
    Customer,
    SalesOrder,
    Invoice,
    Payment,
    Product,
    MillingBatch,
    PackagingBatch,
    FinanceTransaction
)



def dashboard_home():


    st.header(
        "📊 Executive Dashboard"
    )


    db = SessionLocal()


    try:


        # ===============================
        # DATABASE COUNTS
        # ===============================


        customers = (
            db.query(Customer)
            .count()
        )


        orders = (
            db.query(SalesOrder)
            .count()
        )


        invoices = (
            db.query(Invoice)
            .count()
        )


        payments = (
            db.query(Payment)
            .count()
        )


        products = (
            db.query(Product)
            .count()
        )


        milling = (
            db.query(MillingBatch)
            .count()
        )


        packaging = (
            db.query(PackagingBatch)
            .count()
        )


        revenue = (

            db.query(
                FinanceTransaction
            )

            .filter(
                FinanceTransaction.transaction_type
                == "Income"
            )

            .all()

        )


        total_revenue = sum(

            item.amount or 0

            for item in revenue

        )



        # ===============================
        # KPI CARDS
        # ===============================


        col1, col2, col3, col4 = st.columns(4)



        with col1:

            st.metric(

                "👥 Customers",

                customers

            )



        with col2:

            st.metric(

                "🚚 Sales Orders",

                orders

            )



        with col3:

            st.metric(

                "📦 Products",

                products

            )



        with col4:

            st.metric(

                "💰 Revenue",

                f"UGX {total_revenue:,.0f}"

            )



        st.divider()



        # ===============================
        # PRODUCTION SUMMARY
        # ===============================


        st.subheader(
            "🏭 Production Overview"
        )


        p1, p2, p3 = st.columns(3)


        with p1:

            st.metric(

                "🌾 Milling Batches",

                milling

            )


        with p2:

            st.metric(

                "📦 Packaging Batches",

                packaging

            )


        with p3:

            st.metric(

                "🧾 Invoices",

                invoices

            )



        st.divider()



        # ===============================
        # FINANCE SUMMARY
        # ===============================


        st.subheader(
            "💰 Finance Overview"
        )


        f1, f2, f3 = st.columns(3)



        with f1:

            st.metric(

                "Payments Received",

                payments

            )



        with f2:

            st.metric(

                "Outstanding Invoices",

                invoices - payments

            )



        with f3:

            st.metric(

                "Sales Value",

                f"UGX {total_revenue:,.0f}"

            )



        st.divider()



        # ===============================
        # FACTORY STATUS
        # ===============================


        st.subheader(
            "🏭 Factory Status"
        )


        st.success(
            "🟢 Milling Operations Connected"
        )


        st.success(
            "🟢 Warehouse System Online"
        )


        st.success(
            "🟢 Sales & Distribution Active"
        )


        st.info(
            "Production, inventory and finance modules will update automatically as transactions are recorded."
        )



    except Exception as e:


        st.error(
            "Dashboard loading error"
        )

        st.exception(e)



    finally:

        db.close()