"""
Esan ERP Procurement Service

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Handles:
- Suppliers
- Supplier management
- Purchase Orders
- Purchases
- Purchase Order Items
- Status management
- Delete operations
"""

from datetime import datetime

from database import SessionLocal
from models import (
    Supplier,
    PurchaseOrder,
    PurchaseOrderItem,
)


# ============================================================
# SUPPLIERS
# ============================================================

def get_all_suppliers():
    """Return all suppliers."""

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
    """Return one supplier by ID."""

    db = SessionLocal()

    try:
        return (
            db.query(Supplier)
            .filter(
                Supplier.id == supplier_id
            )
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

    if not name or not name.strip():
        raise ValueError(
            "Supplier name is required."
        )

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

    if not name or not name.strip():
        raise ValueError(
            "Supplier name is required."
        )

    db = SessionLocal()

    try:
        supplier = (
            db.query(Supplier)
            .filter(
                Supplier.id == supplier_id
            )
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
            .filter(
                Supplier.id == supplier_id
            )
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


# ============================================================
# PURCHASE ORDERS
# ============================================================

def get_all_purchase_orders():
    """
    Get all purchase orders.

    Returns dictionaries rather than detached SQLAlchemy
    objects. This prevents DetachedInstanceError when
    accessing supplier information in Streamlit.
    """

    db = SessionLocal()

    try:

        orders = (
            db.query(PurchaseOrder)
            .order_by(
                PurchaseOrder.created_at.desc()
            )
            .all()
        )

        results = []

        for order in orders:

            supplier_name = (
                order.supplier.name
                if order.supplier
                else "Unknown Supplier"
            )

            results.append(
                {
                    "id": order.id,
                    "po_number": order.po_number,
                    "supplier_id": order.supplier_id,
                    "supplier_name": supplier_name,
                    "status": order.status,
                    "total_amount": (
                        order.total_amount or 0
                    ),
                    "created_at": order.created_at,
                }
            )

        return results

    finally:
        db.close()


def get_purchase_order(po_id):
    """Get a single purchase order."""

    db = SessionLocal()

    try:

        order = (
            db.query(PurchaseOrder)
            .filter(
                PurchaseOrder.id == po_id
            )
            .first()
        )

        if not order:
            return None

        supplier_name = (
            order.supplier.name
            if order.supplier
            else "Unknown Supplier"
        )

        return {
            "id": order.id,
            "po_number": order.po_number,
            "supplier_id": order.supplier_id,
            "supplier_name": supplier_name,
            "status": order.status,
            "total_amount": (
                order.total_amount or 0
            ),
            "created_at": order.created_at,
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
            "Purchase Order must contain at least one item."
        )

    db = SessionLocal()

    try:

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

        total = 0.0

        for item in items_data:

            product_name = str(
                item.get(
                    "product_name",
                    ""
                )
            ).strip()

            quantity = float(
                item.get(
                    "quantity",
                    0
                )
            )

            unit_price = float(
                item.get(
                    "unit_price",
                    0
                )
            )

            if not product_name:
                raise ValueError(
                    "Product name is required."
                )

            if quantity <= 0:
                raise ValueError(
                    f"Quantity for {product_name} "
                    "must be greater than zero."
                )

            if unit_price < 0:
                raise ValueError(
                    f"Unit price for {product_name} "
                    "cannot be negative."
                )

            total += (
                quantity * unit_price
            )

        # Generate PO number
        count = (
            db.query(PurchaseOrder).count()
        )

        po_number = (
            f"PO-"
            f"{datetime.utcnow().strftime('%Y%m')}-"
            f"{count + 1:04d}"
        )

        order = PurchaseOrder(
            po_number=po_number,
            supplier_id=supplier_id,
            status=status,
            total_amount=total,
            created_at=datetime.utcnow(),
        )

        db.add(order)
        db.flush()

        for item in items_data:

            quantity = float(
                item["quantity"]
            )

            unit_price = float(
                item["unit_price"]
            )

            order_item = PurchaseOrderItem(
                purchase_order_id=order.id,
                product_name=item[
                    "product_name"
                ],
                quantity=quantity,
                unit_price=unit_price,
                total=(
                    quantity *
                    unit_price
                ),
            )

            db.add(order_item)

        db.commit()

        return {
            "id": order.id,
            "po_number": order.po_number,
            "supplier_id": order.supplier_id,
            "supplier_name": supplier.name,
            "status": order.status,
            "total_amount": order.total_amount,
            "created_at": order.created_at,
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
    """Update Purchase Order status."""

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
            f"Invalid Purchase Order status: "
            f"{new_status}"
        )

    db = SessionLocal()

    try:

        order = (
            db.query(PurchaseOrder)
            .filter(
                PurchaseOrder.id == po_id
            )
            .first()
        )

        if not order:
            return None

        order.status = new_status

        db.commit()

        supplier_name = (
            order.supplier.name
            if order.supplier
            else "Unknown Supplier"
        )

        return {
            "id": order.id,
            "po_number": order.po_number,
            "supplier_id": order.supplier_id,
            "supplier_name": supplier_name,
            "status": order.status,
            "total_amount": (
                order.total_amount or 0
            ),
            "created_at": order.created_at,
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def delete_purchase_order(po_id):
    """Delete a Purchase Order and its items."""

    db = SessionLocal()

    try:

        order = (
            db.query(PurchaseOrder)
            .filter(
                PurchaseOrder.id == po_id
            )
            .first()
        )

        if not order:
            return False

        db.query(
            PurchaseOrderItem
        ).filter(
            PurchaseOrderItem.purchase_order_id
            == po_id
        ).delete(
            synchronize_session=False
        )

        db.delete(order)

        db.commit()

        return True

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


# ============================================================
# PURCHASES
# ============================================================

def get_all_purchases():
    """
    Return all purchases.

    Currently Esan ERP uses the PurchaseOrder model as the
    purchasing transaction record. This function provides a
    stable API for modules/procurement/purchases.py.
    """

    return get_all_purchase_orders()


def get_purchase(purchase_id):
    """Get a single purchase."""

    return get_purchase_order(
        purchase_id
    )


def create_purchase(
    supplier_id,
    items_data,
    status="Draft",
):
    """Create a purchase."""

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
        purchase_id=purchase_id,
        new_status=new_status,
    )


def delete_purchase(purchase_id):
    """Delete a purchase."""

    return delete_purchase_order(
        purchase_id
    )