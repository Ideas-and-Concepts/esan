"""
Warehouse Dashboard Module
Nile Harvest Foods Ltd.
Esan ERP - Warehouse Management
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from database import SessionLocal
from models import Warehouse, Product, StockMovement

def get_db():
    return SessionLocal()

def warehouse_dashboard():
    st.title("📦 Warehouse Management")
    db = get_db()
    try:
        col1, col2, col3, col4 = st.columns(4)
        total_products = db.query(Product).count()
        total_warehouses = db.query(Warehouse).count()
        total_stock = db.query(Product).with_entities(db.func.sum(Product.quantity)).scalar() or 0
        recent_movements = db.query(StockMovement).filter(
            StockMovement.created_at >= datetime.utcnow() - timedelta(days=7)
        ).count()
        with col1:
            st.metric("Warehouses", total_warehouses)
        with col2:
            st.metric("Products", total_products)
        with col3:
            st.metric("Total Stock", f"{total_stock:,.1f} Kg")
        with col4:
            st.metric("Movements (7d)", recent_movements)
        st.markdown("---")
        tab1, tab2, tab3, tab4 = st.tabs(["Inventory", "Movements", "Warehouses", "Low Stock"])
        with tab1:
            inventory_overview(db)
        with tab2:
            stock_movements_view(db)
        with tab3:
            warehouses_view(db)
        with tab4:
            low_stock_alert(db)
    finally:
        db.close()

def inventory_overview(db):
    st.subheader("Current Inventory")
    products = db.query(Product).order_by(Product.category, Product.name).all()
    if products:
        data = []
        for p in products:
            data.append({
                'Product': p.name,
                'Category': p.category or 'N/A',
                'Unit': p.unit,
                'Quantity': p.quantity,
                'Cost Price': f"${p.cost_price:,.2f}" if p.cost_price else 'N/A',
                'Selling Price': f"${p.selling_price:,.2f}" if p.selling_price else 'N/A'
            })
        df = pd.DataFrame(data)
        search = st.text_input("Search")
        if search:
            df = df[df['Product'].str.contains(search, case=False)]
        categories = ['All'] + list(set(p.category or 'N/A' for p in products))
        cat_filter = st.selectbox("Category", categories)
        if cat_filter != 'All':
            df = df[df['Category'] == cat_filter]
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No products.")

def stock_movements_view(db):
    st.subheader("Recent Stock Movements")
    movements = db.query(StockMovement).order_by(StockMovement.created_at.desc()).limit(100).all()
    if movements:
        data = []
        for m in movements:
            product = db.query(Product).filter(Product.id == m.product_id).first()
            data.append({
                'Date': m.created_at.strftime('%Y-%m-%d %H:%M'),
                'Product': product.name if product else '?',
                'Type': m.movement_type,
                'Quantity': m.quantity,
                'Reference': m.reference or ''
            })
        df = pd.DataFrame(data)
        types = list(set(m.movement_type for m in movements))
        type_filter = st.multiselect("Movement Type", types, default=types)
        if type_filter:
            df = df[df['Type'].isin(type_filter)]
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No movements.")

def warehouses_view(db):
    st.subheader("Warehouses")
    warehouses = db.query(Warehouse).all()
    if warehouses:
        for wh in warehouses:
            with st.expander(f"🏭 {wh.name} - {wh.location or 'No location'}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Name:** {wh.name}")
                    st.markdown(f"**Location:** {wh.location or 'N/A'}")
                with col2:
                    st.markdown(f"**Capacity:** {wh.capacity:,.1f}" if wh.capacity else "Capacity not set")
                    st.markdown(f"**Created:** {wh.created_at.strftime('%Y-%m-%d') if wh.created_at else 'N/A'}")
    else:
        st.info("No warehouses.")
        with st.form("add_warehouse"):
            name = st.text_input("Warehouse Name")
            location = st.text_input("Location")
            capacity = st.number_input("Capacity", min_value=0.0)
            if st.form_submit_button("Add"):
                if name:
                    db.add(Warehouse(name=name, location=location, capacity=capacity, created_at=datetime.utcnow()))
                    db.commit()
                    st.success("Added!")
                    st.rerun()

def low_stock_alert(db):
    st.subheader("Low Stock Alert")
    threshold = st.number_input("Threshold", min_value=0.0, value=100.0)
    products = db.query(Product).filter(Product.quantity <= threshold).all()
    if products:
        data = []
        for p in products:
            data.append({
                'Product': p.name,
                'Category': p.category or 'N/A',
                'Quantity': p.quantity,
                'Unit': p.unit,
                'Status': '⚠️ Critical' if p.quantity == 0 else '🔸 Low'
            })
        st.dataframe(pd.DataFrame(data), use_container_width=True)
        st.warning(f"{len(products)} products below threshold.")
    else:
        st.success("All products well stocked.")