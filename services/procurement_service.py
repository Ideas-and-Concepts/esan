"""
Esan ERP Procurement Service

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Handles:
- Suppliers
- Purchase Orders
- Purchase Order Items
- Add / Edit / Delete
- Status management
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
            .order_by(Supplier.name.asc())
            .all()
        )

    finally:
        db.close()


def get_supplier(supplier_id):
    """
    Get a single supplier by ID.
    """

    db = SessionLocal()

    try:
        return (
            db.query(Supplier)
            .filter(Supplier.id == supplier_id)
            .first()
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
            name=name.strip(),
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

        # Detach object safely before closing session
        db.expunge(supplier)

        return supplier

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def update_supplier(
    supplier_id,
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
    Update an existing supplier.
    """

    db = SessionLocal()

    try:

        supplier = (
            db.query(Supplier)
            .filter(Supplier.id == supplier_id)
            .first()
        )

        if not supplier:
            return None

        supplier.name = name.strip()
        supplier.phone = phone
        supplier.email = email
        supplier.address = address
        supplier.supplier_type = supplier_type
        supplier.location = location
        supplier.country = country
        supplier.contact_person = contact_person

        db.commit()
        db.refresh(supplier)

        db.expunge(supplier)

        return supplier

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def delete_supplier(supplier_id):
    """
    Delete a supplier.

    A supplier with existing purchase orders is not deleted
    in order to preserve procurement history.
    """

    db = SessionLocal()

    try:

        supplier = (
            db.query(Supplier)
            .filter(Supplier.id == supplier_id)
            .first()
        )

        if not supplier:
            return False, "Supplier not found."

        purchase_count = (
            db.query(PurchaseOrder)
            .filter(
                PurchaseOrder.supplier_id == supplier_id
            )
            .count()
        )

        if purchase_count > 0:

            return (
                False,
                "Supplier cannot be deleted because "
                f"{purchase_count} purchase order(s) are linked to it.",
            )

        db.delete(supplier)
        db.commit()

        return True, "Supplier deleted successfully."

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
    Return all purchase orders.

    joinedload() prevents DetachedInstanceError when the
    supplier relationship is accessed after the session closes.
    """

    db = SessionLocal()

    try:

        orders = (
            db.query(PurchaseOrder)
            .options(
                joinedload(PurchaseOrder.supplier),
                joinedload(PurchaseOrder.items),
            )
            .order_by(
                PurchaseOrder.created_at.desc()
            )
            .all()
        )

        # Detach complete object graph from session
        for order in orders:

            if order.supplier:
                db.expunge(order.supplier)

            for item in order.items:
                db.expunge(item)

            db.expunge(order)

        return orders

    finally:
        db.close()


def get_purchase_order(po_id):
    """
    Get one purchase order with supplier and items loaded.
    """

    db = SessionLocal()

    try:

        order = (
            db.query(PurchaseOrder)
            .options(
                joinedload(PurchaseOrder.supplier),
                joinedload(PurchaseOrder.items),
            )
            .filter(PurchaseOrder.id == po_id)
            .first()
        )

        if not order:
            return None

        if order.supplier:
            db.expunge(order.supplier)

        for item in order.items:
            db.expunge(item)

        db.expunge(order)

        return order

    finally:
        db.close()


def create_purchase_order(
    supplier_id,
    items_data,
    status="Draft",
):
    """
    Create a purchase order.

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
            "Purchase order must contain at least one item."
        )

    db = SessionLocal()

    try:

        supplier = (
            db.query(Supplier)
            .filter(Supplier.id == supplier_id)
            .first()
        )

        if not supplier:
            raise ValueError(
                "Selected supplier does not exist."
            )

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
                    "Quantity must be greater than zero."
                )

            if unit_price < 0:
                raise ValueError(
                    "Unit price cannot be negative."
                )

            total += quantity * unit_price

        # Generate PO number
        count = (
            db.query(PurchaseOrder)
            .count()
        )

        po_number = (
            f"PO-"
            f"{datetime.utcnow().strftime('%Y%m')}-"
            f"{count + 1:04d}"
        )

        purchase_order = PurchaseOrder(
            po_number=po_number,
            supplier_id=supplier_id,
            status=status,
            total_amount=total,
            created_at=datetime.utcnow(),
        )

        db.add(purchase_order)
        db.flush()

        for item in items_data:

            product_name = (
                item.get("product_name", "")
                .strip()
            )

            if not product_name:
                raise ValueError(
                    "Product name cannot be empty."
                )

            quantity = float(
                item["quantity"]
            )

            unit_price = float(
                item["unit_price"]
            )

            purchase_item = PurchaseOrderItem(
                purchase_order_id=purchase_order.id,
                product_name=product_name,
                quantity=quantity,
                unit_price=unit_price,
                total=quantity * unit_price,
            )

            db.add(purchase_item)

        db.commit()

        # Reload with relationships
        purchase_order = (
            db.query(PurchaseOrder)
            .options(
                joinedload(PurchaseOrder.supplier),
                joinedload(PurchaseOrder.items),
            )
            .filter(
                PurchaseOrder.id == purchase_order.id
            )
            .first()
        )

        db.expunge(purchase_order)

        if purchase_order.supplier:
            db.expunge(
                purchase_order.supplier
            )

        for item in purchase_order.items:
            db.expunge(item)

        return purchase_order

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def update_purchase_order(
    po_id,
    supplier_id,
    items_data,
    status="Draft",
):
    """
    Edit an existing purchase order.

    Existing items are replaced with the supplied items.
    """

    if not items_data:
        raise ValueError(
            "Purchase order must contain at least one item."
        )

    db = SessionLocal()

    try:

        purchase_order = (
            db.query(PurchaseOrder)
            .options(
                joinedload(PurchaseOrder.items)
            )
            .filter(
                PurchaseOrder.id == po_id
            )
            .first()
        )

        if not purchase_order:
            return None

        supplier = (
            db.query(Supplier)
            .filter(Supplier.id == supplier_id)
            .first()
        )

        if not supplier:
            raise ValueError(
                "Selected supplier does not exist."
            )

        total = 0.0

        for item in items_data:

            quantity = float(
                item.get("quantity", 0)
            )

            unit_price = float(
                item.get("unit_price", 0)
            )

            product_name = (
                item.get("product_name", "")
                .strip()
            )

            if not product_name:
                raise ValueError(
                    "Product name cannot be empty."
                )

            if quantity <= 0:
                raise ValueError(
                    "Quantity must be greater than zero."
                )

            if unit_price < 0:
                raise ValueError(
                    "Unit price cannot be negative."
                )

            total += quantity * unit_price

        # Update header
        purchase_order.supplier_id = supplier_id
        purchase_order.status = status
        purchase_order.total_amount = total

        # Remove old items
        for old_item in list(
            purchase_order.items
        ):
            db.delete(old_item)

        db.flush()

        # Add new items
        for item in items_data:

            quantity = float(
                item["quantity"]
            )

            unit_price = float(
                item["unit_price"]
            )

            new_item = PurchaseOrderItem(
                purchase_order_id=purchase_order.id,
                product_name=item["product_name"].strip(),
                quantity=quantity,
                unit_price=unit_price,
                total=quantity * unit_price,
            )

            db.add(new_item)

        db.commit()

        return get_purchase_order(po_id)

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def update_purchase_order_status(
    po_id,
    new_status,
):
    """
    Update purchase order status.
    """

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

        return get_purchase_order(po_id)

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def delete_purchase_order(po_id):
    """
    Delete a purchase order and its items.
    """

    db = SessionLocal()

    try:

        purchase_order = (
            db.query(PurchaseOrder)
            .options(
                joinedload(PurchaseOrder.items)
            )
            .filter(
                PurchaseOrder.id == po_id
            )
            .first()
        )

        if not purchase_order:
            return False, "Purchase Order not found."

        for item in list(
            purchase_order.items
        ):
            db.delete(item)

        db.delete(purchase_order)

        db.commit()

        return (
            True,
            "Purchase Order deleted successfully.",
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


# ==================================================
# PURCHASE ORDER ITEMS
# ==================================================

def get_purchase_order_items(po_id):
    """
    Return all items belonging to a purchase order.
    """

    db = SessionLocal()

    try:

        return (
            db.query(PurchaseOrderItem)
            .filter(
                PurchaseOrderItem.purchase_order_id
                == po_id
            )
            .order_by(
                PurchaseOrderItem.id.asc()
            )
            .all()
        )

    finally:
        db.close()