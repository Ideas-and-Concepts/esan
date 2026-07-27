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
    """Main warehouse dashboard."""
    st.title("📦 Warehouse Management")
    
    db = get_db()
    
    try:
        # Quick stats
        col1, col2, col3, col4 = st.columns(4)
        
        total_products = db.query(Product).count()
        total_warehouses = db.query(Warehouse).count()
        total_stock = db.query(Product).with_entities(
            db.func.sum(Product.quantity)
        ).scalar() or 0
        
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
            st.metric("Movements (7 days)", recent_movements)
        
        st.markdown("---")
        
        # Tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "Inventory Overview", 
            "Stock Movements", 
            "Warehouses", 
            "Low Stock Alert"
        ])
        
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
    """Display current inventory."""
    st.subheader("Current Inventory")
    
    products = db.query(Product).order_by(Product.category, Product.name).all()
    
    if products:
        data = []
        for product in products:
            data.append({
                'Product': product.name,
                'Category': product.category or 'Uncategorized',
                'Unit': product.unit,
                'Quantity': product.quantity,
                'Cost Price': f"${product.cost_price:,.2f}" if product.cost_price else 'N/A',
                'Selling Price': f"${product.selling_price:,.2f}" if product.selling_price else 'N/A',
                'Stock Value': f"${product.quantity * product.cost_price:,.2f}" if product.cost_price else 'N/A'
            })
        
        df = pd.DataFrame(data)
        
        # Search
        search = st.text_input("Search Products")
        if search:
            df = df[df['Product'].str.contains(search, case=False)]
        
        # Category filter
        categories = ['All'] + list(set(p['Category'] for p in data))
        selected_category = st.selectbox("Filter by Category", categories)
        if selected_category != 'All':
            df = df[df['Category'] == selected_category]
        
        st.dataframe(df, use_container_width=True)
        
        # Category summary
        st.markdown("---")
        st.subheader("Stock by Category")
        
        category_summary = {}
        for product in products:
            cat = product.category or 'Uncategorized'
            if cat not in category_summary:
                category_summary[cat] = {'quantity': 0, 'value': 0}
            category_summary[cat]['quantity'] += product.quantity or 0
            category_summary[cat]['value'] += (product.quantity or 0) * (product.cost_price or 0)
        
        summary_data = []
        for cat, vals in category_summary.items():
            summary_data.append({
                'Category': cat,
                'Total Quantity': f"{vals['quantity']:,.1f}",
                'Total Value': f"${vals['value']:,.2f}"
            })
        
        st.dataframe(pd.DataFrame(summary_data), use_container_width=True)
    else:
        st.info("No products in inventory.")

def stock_movements_view(db):
    """View stock movement history."""
    st.subheader("Stock Movements")
    
    movements = db.query(StockMovement).order_by(StockMovement.created_at.desc()).limit(100).all()
    
    if movements:
        data = []
        for move in movements:
            product = db.query(Product).filter(Product.id == move.product_id).first()
            data.append({
                'Date': move.created_at.strftime('%Y-%m-%d %H:%M') if move.created_at else 'N/A',
                'Product': product.name if product else 'Unknown',
                'Type': move.movement_type,
                'Quantity': move.quantity,
                'Reference': move.reference or 'N/A'
            })
        
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
        
        # Movement type filter
        types = list(set(m['Type'] for m in data))
        selected_types = st.multiselect("Filter by Movement Type", types, default=types)
        if selected_types:
            df = df[df['Type'].isin(selected_types)]
            st.dataframe(df, use_container_width=True)
    else:
        st.info("No stock movements recorded.")

def warehouses_view(db):
    """View warehouse information."""
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
                    st.markdown(f"**Capacity:** {wh.capacity:,.1f} units" if wh.capacity else "**Capacity:** Not set")
                    st.markdown(f"**Created:** {wh.created_at.strftime('%Y-%m-%d') if wh.created_at else 'N/A'}")
    else:
        st.info("No warehouses configured.")
        
        # Option to add warehouse
        with st.form("add_warehouse_form"):
            st.markdown("**Add New Warehouse**")
            name = st.text_input("Warehouse Name")
            location = st.text_input("Location")
            capacity = st.number_input("Capacity", min_value=0.0)
            
            if st.form_submit_button("Add Warehouse"):
                if name:
                    new_wh = Warehouse(
                        name=name,
                        location=location,
                        capacity=capacity,
                        created_at=datetime.utcnow()
                    )
                    db.add(new_wh)
                    db.commit()
                    st.success(f"Warehouse {name} added!")
                    st.rerun()

def low_stock_alert(db):
    """Show products with low stock."""
    st.subheader("Low Stock Alert")
    
    # Products with quantity less than threshold
    threshold = st.number_input("Low Stock Threshold", min_value=0.0, value=100.0, step=10.0)
    
    products = db.query(Product).filter(Product.quantity <= threshold).all()
    
    if products:
        data = []
        for product in products:
            data.append({
                'Product': product.name,
                'Category': product.category or 'Uncategorized',
                'Current Quantity': product.quantity,
                'Unit': product.unit,
                'Status': '⚠️ Critical' if product.quantity == 0 else '🔸 Low'
            })
        
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
        
        st.warning(f"⚠️ {len(products)} products are below the threshold of {threshold:,.1f} units.")
    else:
        st.success(f"✅ All products have stock above {threshold:,.1f} units.")