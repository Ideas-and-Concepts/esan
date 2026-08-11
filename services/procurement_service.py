"""
Esan ERP Procurement Service

Nile Harvest Foods Ltd.

Provides database operations for:

- Suppliers
- Purchase Orders
- Purchase Order Items
- Purchases
"""

from datetime import datetime

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
    """Return all suppliers ordered alphabetically."""

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
    """Return a supplier by ID."""

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
    """Create a new supplier."""

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
    """Update an existing supplier."""

    db = SessionLocal()

    try:
        supplier = (
            db.query(Supplier)
            .filter(Supplier.id == supplier_id)
            .first()
        )

        if not supplier:
            return None

        supplier.name = name
        supplier.phone = phone
        supplier.email = email
        supplier.address = address
        supplier.supplier_type = supplier_type
        supplier.location = location
        supplier.country = country
        supplier.contact_person = contact_person

        db.commit()
        db.refresh(supplier)

        return supplier

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def delete_supplier(supplier_id):
    """Delete a supplier."""

    db = SessionLocal()

    try:
        supplier = (
            db.query(Supplier)
            .filter(Supplier.id == supplier_id)
            .first()
        )

        if not supplier:
            return False

        db.delete(supplier)
        db.commit()

        return True

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

    Supplier information is accessed while the session is active
    so Streamlit will not encounter DetachedInstanceError.
    """

    db = SessionLocal()

    try:
        purchase_orders = (
            db.query(PurchaseOrder)
            .order_by(PurchaseOrder.created_at.desc())
            .all()
        )

        results = []

        for po in purchase_orders:
            results.append(
                {
                    "id": po.id,
                    "po_number": po.po_number,
                    "supplier_id": po.supplier_id,
                    "supplier_name": (
                        po.supplier.name
                        if po.supplier
                        else "Unknown Supplier"
                    ),
                    "status": po.status,
                    "total_amount": po.total_amount or 0,
                    "created_at": po.created_at,
                }
            )

        return results

    finally:
        db.close()


def get_purchase_order(po_id):
    """Return one purchase order as a detached-safe dictionary."""

    db = SessionLocal()

    try:
        po = (
            db.query(PurchaseOrder)
            .filter(PurchaseOrder.id == po_id)
            .first()
        )

        if not po:
            return None

        return {
            "id": po.id,
            "po_number": po.po_number,
            "supplier_id": po.supplier_id,
            "supplier_name": (
                po.supplier.name
                if po.supplier
                else "Unknown Supplier"
            ),
            "status": po.status,
            "total_amount": po.total_amount or 0,
            "created_at": po.created_at,
        }

    finally:
        db.close()


def create_purchase_order(
    supplier_id,
    items_data,
    status="Draft",
):
    """
    Create a purchase order.

    items_data must contain:
        product_name
        quantity
        unit_price
    """

    if not items_data:
        raise ValueError(
            "A purchase order must contain at least one item."
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
                    "Purchase quantity must be greater than zero."
                )

            if unit_price < 0:
                raise ValueError(
                    "Unit price cannot be negative."
                )

            total += quantity * unit_price

        count = (
            db.query(PurchaseOrder).count()
        )

        po_number = (
            f"PO-{datetime.utcnow().strftime('%Y%m')}-"
            f"{count + 1:04d}"
        )

        po = PurchaseOrder(
            po_number=po_number,
            supplier_id=supplier_id,
            status=status,
            total_amount=total,
            created_at=datetime.utcnow(),
        )

        db.add(po)
        db.flush()

        for item in items_data:

            quantity = float(
                item["quantity"]
            )

            unit_price = float(
                item["unit_price"]
            )

            purchase_item = PurchaseOrderItem(
                purchase_order_id=po.id,
                product_name=item["product_name"],
                quantity=quantity,
                unit_price=unit_price,
                total=quantity * unit_price,
            )

            db.add(purchase_item)

        db.commit()

        return {
            "id": po.id,
            "po_number": po.po_number,
            "supplier_id": po.supplier_id,
            "supplier_name": supplier.name,
            "status": po.status,
            "total_amount": po.total_amount,
            "created_at": po.created_at,
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def update_purchase_order_status(
    po_id,
    new_status,
):
    """Update the status of a purchase order."""

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
            f"Invalid purchase order status: {new_status}"
        )

    db = SessionLocal()

    try:
        po = (
            db.query(PurchaseOrder)
            .filter(PurchaseOrder.id == po_id)
            .first()
        )

        if not po:
            return None

        po.status = new_status

        db.commit()

        supplier_name = (
            po.supplier.name
            if po.supplier
            else "Unknown Supplier"
        )

        return {
            "id": po.id,
            "po_number": po.po_number,
            "supplier_id": po.supplier_id,
            "supplier_name": supplier_name,
            "status": po.status,
            "total_amount": po.total_amount or 0,
            "created_at": po.created_at,
        }

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
        po = (
            db.query(PurchaseOrder)
            .filter(PurchaseOrder.id == po_id)
            .first()
        )

        if not po:
            return False

        (
            db.query(PurchaseOrderItem)
            .filter(
                PurchaseOrderItem.purchase_order_id
                == po_id
            )
            .delete(
                synchronize_session=False
            )
        )

        db.delete(po)
        db.commit()

        return True

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


# ==================================================
# PURCHASES
# ==================================================

def get_all_purchases():
    """
    Return purchase records.

    In the current Esan ERP database structure, purchases are
    represented by Purchase Orders. Therefore this function
    provides a compatibility layer for the Purchases module.
    """

    return get_all_purchase_orders()


def get_purchase(purchase_id):
    """Get one purchase."""

    return get_purchase_order(purchase_id)


def create_purchase(
    supplier_id,
    items_data,
    status="Draft",
):
    """
    Create a purchase using the existing PurchaseOrder structure.
    """

    return create_purchase_order(
        supplier_id=supplier_id,
        items_data=items_data,
        status=status,
    )


def update_purchase_status(
    purchase_id,
    new_status,
):
    """Update purchase status."""

    return update_purchase_order_status(
        purchase_id,
        new_status,
    )


def delete_purchase(purchase_id):
    """Delete a purchase."""

    return delete_purchase_order(
        purchase_id
    )