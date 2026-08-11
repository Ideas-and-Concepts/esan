"""
Esan ERP - Warehouse Dashboard

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Functions:
- Warehouse KPIs
- Inventory summary
- Stock value
- Low-stock monitoring
- Recent stock movements
"""

import streamlit as st
import pandas as pd
from sqlalchemy import func

from database import SessionLocal
from models import Product, StockMovement, Warehouse


# ==================================================
# WAREHOUSE DASHBOARD
# ==================================================

def warehouse_dashboard():

    st.title("📦 Warehouse Management")
    st.caption("Inventory, stock control and warehouse operations")

    db = SessionLocal()

    try:
        # ==================================================
        # KPI CALCULATIONS
        # ==================================================

        total_products = db.query(Product).count()

        total_stock = (
            db.query(func.coalesce(func.sum(Product.quantity), 0))
            .scalar()
            or 0
        )

        stock_value = (
            db.query(
                func.coalesce(
                    func.sum(Product.quantity * Product.cost_price),
                    0
                )
            )
            .scalar()
            or 0
        )

        total_warehouses = db.query(Warehouse).count()

        total_movements = db.query(StockMovement).count()

        # ==================================================
        # LOW STOCK
        # ==================================================

        low_stock_products = (
            db.query(Product)
            .filter(Product.quantity <= 10)
            .order_by(Product.quantity.asc())
            .all()
        )

        # ==================================================
        # KPI CARDS
        # ==================================================

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Products",
            f"{total_products:,}"
        )

        col2.metric(
            "Total Stock",
            f"{total_stock:,.1f} Kg"
        )

        col3.metric(
            "Stock Value",
            f"UGX {stock_value:,.0f}"
        )

        col4.metric(
            "Warehouses",
            f"{total_warehouses:,}"
        )

        st.divider()

        # ==================================================
        # SECOND KPI ROW
        # ==================================================

        col5, col6, col7, col8 = st.columns(4)

        col5.metric(
            "Stock Movements",
            f"{total_movements:,}"
        )

        col6.metric(
            "Low Stock Items",
            f"{len(low_stock_products):,}"
        )

        # Total inventory cost
        total_cost = (
            db.query(
                func.coalesce(
                    func.sum(Product.quantity * Product.cost_price),
                    0
                )
            )
            .scalar()
            or 0
        )

        col7.metric(
            "Inventory Cost",
            f"UGX {total_cost:,.0f}"
        )

        # Potential sales value
        total_sales_value = (
            db.query(
                func.coalesce(
                    func.sum(Product.quantity * Product.selling_price),
                    0
                )
            )
            .scalar()
            or 0
        )

        col8.metric(
            "Potential Sales Value",
            f"UGX {total_sales_value:,.0f}"
        )

        st.divider()

        # ==================================================
        # LOW STOCK SECTION
        # ==================================================

        st.subheader("⚠️ Low Stock Monitoring")

        if low_stock_products:

            low_stock_data = []

            for product in low_stock_products:

                low_stock_data.append(
                    {
                        "Product": product.name,
                        "Category": product.category or "",
                        "Quantity": f"{product.quantity:,.1f}",
                        "Unit": product.unit or "Kg",
                        "Cost Price": f"UGX {product.cost_price:,.0f}",
                        "Selling Price": (
                            f"UGX {product.selling_price:,.0f}"
                        ),
                    }
                )

            low_stock_df = pd.DataFrame(low_stock_data)

            st.dataframe(
                low_stock_df,
                use_container_width=True,
                hide_index=True,
            )

        else:

            st.success(
                "✅ No products are currently below the low-stock threshold."
            )

        st.divider()

        # ==================================================
        # INVENTORY SUMMARY
        # ==================================================

        st.subheader("📦 Inventory Summary")

        products = (
            db.query(Product)
            .order_by(Product.name.asc())
            .all()
        )

        if products:

            inventory_data = []

            for product in products:

                quantity = product.quantity or 0
                cost_price = product.cost_price or 0
                selling_price = product.selling_price or 0

                inventory_data.append(
                    {
                        "Product": product.name,
                        "Category": product.category or "",
                        "Stock": quantity,
                        "Unit": product.unit or "Kg",
                        "Cost Price": cost_price,
                        "Selling Price": selling_price,
                        "Stock Value": quantity * cost_price,
                        "Sales Value": quantity * selling_price,
                    }
                )

            inventory_df = pd.DataFrame(inventory_data)

            st.dataframe(
                inventory_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Stock": st.column_config.NumberColumn(
                        format="%.1f"
                    ),
                    "Cost Price": st.column_config.NumberColumn(
                        "Cost Price",
                        format="UGX %d"
                    ),
                    "Selling Price": st.column_config.NumberColumn(
                        "Selling Price",
                        format="UGX %d"
                    ),
                    "Stock Value": st.column_config.NumberColumn(
                        "Stock Value",
                        format="UGX %d"
                    ),
                    "Sales Value": st.column_config.NumberColumn(
                        "Sales Value",
                        format="UGX %d"
                    ),
                },
            )

        else:

            st.info(
                "No products have been registered in the warehouse yet."
            )

        st.divider()

        # ==================================================
        # RECENT STOCK MOVEMENTS
        # ==================================================

        st.subheader("🔄 Recent Stock Movements")

        movements = (
            db.query(StockMovement)
            .order_by(StockMovement.created_at.desc())
            .limit(20)
            .all()
        )

        if movements:

            movement_data = []

            for movement in movements:

                product = (
                    db.query(Product)
                    .filter(Product.id == movement.product_id)
                    .first()
                )

                movement_data.append(
                    {
                        "Product": (
                            product.name
                            if product
                            else "Unknown Product"
                        ),
                        "Movement": (
                            movement.movement_type
                            or ""
                        ),
                        "Quantity": (
                            movement.quantity
                            or 0
                        ),
                        "Reference": (
                            movement.reference
                            or ""
                        ),
                        "Date": (
                            movement.created_at.strftime(
                                "%Y-%m-%d %H:%M"
                            )
                            if movement.created_at
                            else ""
                        ),
                    }
                )

            movement_df = pd.DataFrame(movement_data)

            st.dataframe(
                movement_df,
                use_container_width=True,
                hide_index=True,
            )

        else:

            st.info(
                "No stock movements have been recorded yet."
            )

    except Exception as e:

        st.error(
            "Unable to load Warehouse Dashboard."
        )

        st.exception(e)

    finally:

        db.close()


# ==================================================
# STANDALONE EXECUTION
# ==================================================

if __name__ == "__main__":
    warehouse_dashboard()