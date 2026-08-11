"""
Esan ERP Procurement Service

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Handles:
- Suppliers
- Purchase Orders
- Purchase Order Items
- Purchase Order Status
"""

from datetime import datetime

from sqlalchemy.orm import joinedload

from database import SessionLocal
from models import (
    Supplier,
    PurchaseOrder,
    PurchaseOrderItem,
)


# ==================================================
# SUPPLIERS
# ==================================================

def get_all_suppliers():
    """
    Return all suppliers ordered alphabetically.
    """

    db = SessionLocal()

    try:
        return (
            db.query(Supplier)
            .order_by(Supplier.name)
            .all()
        )

    finally:
        db.close()


def create_supplier(
    name,
    phone=None,
    email=None,
    address=None,
    supplier_type="Agricultural Supplier",
    location=None,
    country=None,
    contact_person=None,
):
    """
    Create a new supplier.
    """

    db = SessionLocal()

    try:

        supplier = Supplier(
            name=name,
            phone=phone,
            email=email,
            address=address,
            supplier_type=supplier_type,
            location=location,
            country=country,
            contact_person=contact_person,
            created_at=datetime.utcnow(),
        )

        db.add(supplier)
        db.commit()
        db.refresh(supplier)

        return supplier

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()


# ==================================================
# PURCHASE ORDERS
# ==================================================

def get_all_purchase_orders():
    """
    Return all purchase orders with their suppliers
    eagerly loaded.

    This prevents SQLAlchemy DetachedInstanceError
    when the Streamlit page accesses po.supplier after
    the database session has been closed.
    """

    db = SessionLocal()

    try:

        purchase_orders = (
            db.query(PurchaseOrder)
            .options(
                joinedload(PurchaseOrder.supplier)
            )
            .order_by(
                PurchaseOrder.created_at.desc()
            )
            .all()
        )

        return purchase_orders

    finally:

        db.close()


def get_purchase_order(po_id):
    """
    Get one purchase order with its supplier and items
    already loaded.
    """

    db = SessionLocal()

    try:

        purchase_order = (
            db.query(PurchaseOrder)
            .options(
                joinedload(PurchaseOrder.supplier),
                joinedload(PurchaseOrder.items),
            )
            .filter(
                PurchaseOrder.id == po_id
            )
            .first()
        )

        return purchase_order

    finally:

        db.close()


# ==================================================
# CREATE PURCHASE ORDER
# ==================================================

def create_purchase_order(
    supplier_id,
    items_data,
    status="Draft",
):
    """
    Create a Purchase Order and its items.

    items_data format:

    [
        {
            "product_name": "Maize Grain",
            "quantity": 10,
            "unit_price": 40000
        }
    ]
    """

    if not items_data:
        raise ValueError(
            "At least one purchase order item is required."
        )

    db = SessionLocal()

    try:

        # ------------------------------------------
        # Validate supplier
        # ------------------------------------------

        supplier = (
            db.query(Supplier)
            .filter(
                Supplier.id == supplier_id
            )
            .first()
        )

        if not supplier:
            raise ValueError(
                "Selected supplier does not exist."
            )

        # ------------------------------------------
        # Calculate total
        # ------------------------------------------

        total = 0.0

        for item in items_data:

            quantity = float(
                item.get("quantity", 0)
            )

            unit_price = float(
                item.get("unit_price", 0)
            )

            if quantity <= 0:
                raise ValueError(
                    f"Invalid quantity for "
                    f"{item.get('product_name', 'item')}."
                )

            if unit_price < 0:
                raise ValueError(
                    f"Invalid unit price for "
                    f"{item.get('product_name', 'item')}."
                )

            total += quantity * unit_price

        # ------------------------------------------
        # Generate PO number
        # ------------------------------------------

        count = (
            db.query(PurchaseOrder)
            .count()
        )

        po_number = (
            f"PO-"
            f"{datetime.utcnow().strftime('%Y%m')}-"
            f"{count + 1:04d}"
        )

        # ------------------------------------------
        # Create Purchase Order
        # ------------------------------------------

        purchase_order = PurchaseOrder(
            po_number=po_number,
            supplier_id=supplier_id,
            status=status,
            total_amount=total,
            created_at=datetime.utcnow(),
        )

        db.add(purchase_order)

        # Flush so purchase_order.id is available
        db.flush()

        # ------------------------------------------
        # Create Purchase Order Items
        # ------------------------------------------

        for item in items_data:

            quantity = float(
                item["quantity"]
            )

            unit_price = float(
                item["unit_price"]
            )

            item_total = (
                quantity * unit_price
            )

            purchase_order_item = PurchaseOrderItem(
                purchase_order_id=purchase_order.id,
                product_name=item["product_name"],
                quantity=quantity,
                unit_price=unit_price,
                total=item_total,
            )

            db.add(
                purchase_order_item
            )

        # ------------------------------------------
        # Commit
        # ------------------------------------------

        db.commit()

        # ------------------------------------------
        # Reload PO with supplier attached
        # ------------------------------------------

        purchase_order = (
            db.query(PurchaseOrder)
            .options(
                joinedload(
                    PurchaseOrder.supplier
                ),
                joinedload(
                    PurchaseOrder.items
                ),
            )
            .filter(
                PurchaseOrder.id
                == purchase_order.id
            )
            .first()
        )

        return purchase_order

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()


# ==================================================
# UPDATE PURCHASE ORDER STATUS
# ==================================================

def update_purchase_order_status(
    po_id,
    new_status,
):
    """
    Update the status of a Purchase Order.
    """

    allowed_statuses = [
        "Draft",
        "Pending Approval",
        "Approved",
        "Ordered",
        "Partially Received",
        "Received",
        "Cancelled",
    ]

    if new_status not in allowed_statuses:

        raise ValueError(
            "Invalid Purchase Order status."
        )

    db = SessionLocal()

    try:

        purchase_order = (
            db.query(PurchaseOrder)
            .filter(
                PurchaseOrder.id == po_id
            )
            .first()
        )

        if not purchase_order:
            return None

        purchase_order.status = new_status

        db.commit()

        # Reload relationships before closing
        purchase_order = (
            db.query(PurchaseOrder)
            .options(
                joinedload(
                    PurchaseOrder.supplier
                ),
                joinedload(
                    PurchaseOrder.items
                ),
            )
            .filter(
                PurchaseOrder.id == po_id
            )
            .first()
        )

        return purchase_order

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()