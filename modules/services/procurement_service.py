"""
Esan ERP Procurement Service

Nile Harvest Foods Ltd.

Handles:
- Suppliers
- Purchase Orders
- Purchase Order Items
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
    Return one supplier by ID.
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


# ==================================================
# PURCHASE ORDERS
# ==================================================

def get_all_purchase_orders():
    """
    Return all purchase orders,
    newest first.
    """

    db = SessionLocal()

    try:

        return (
            db.query(PurchaseOrder)
            .order_by(
                PurchaseOrder.created_at.desc()
            )
            .all()
        )

    finally:

        db.close()


def get_purchase_order(po_id):
    """
    Return a purchase order by ID.
    """

    db = SessionLocal()

    try:

        return (
            db.query(PurchaseOrder)
            .filter(
                PurchaseOrder.id == po_id
            )
            .first()
        )

    finally:

        db.close()


def create_purchase_order(
    supplier_id,
    items_data,
    status="Draft",
):
    """
    Create a purchase order.

    items_data must be a list of dictionaries:

    [
        {
            "product_name": "Maize",
            "quantity": 1000,
            "unit_price": 1500
        }
    ]
    """

    if not supplier_id:
        raise ValueError(
            "Supplier is required."
        )

    if not items_data:
        raise ValueError(
            "At least one purchase order item is required."
        )

    db = SessionLocal()

    try:

        # ------------------------------------------
        # VERIFY SUPPLIER
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
        # VALIDATE ITEMS
        # ------------------------------------------

        total = 0

        for item in items_data:

            product_name = item.get(
                "product_name"
            )

            quantity = float(
                item.get("quantity", 0)
            )

            unit_price = float(
                item.get("unit_price", 0)
            )

            if not product_name:
                raise ValueError(
                    "Every purchase item must "
                    "have a product name."
                )

            if quantity <= 0:
                raise ValueError(
                    f"Quantity for "
                    f"'{product_name}' must "
                    "be greater than zero."
                )

            if unit_price < 0:
                raise ValueError(
                    f"Unit price for "
                    f"'{product_name}' "
                    "cannot be negative."
                )

            total += (
                quantity * unit_price
            )

        # ------------------------------------------
        # GENERATE PO NUMBER
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
        # CREATE PURCHASE ORDER
        # ------------------------------------------

        po = PurchaseOrder(
            po_number=po_number,
            supplier_id=supplier_id,
            status=status,
            total_amount=total,
            created_at=datetime.utcnow(),
        )

        db.add(po)
        db.flush()

        # ------------------------------------------
        # CREATE ITEMS
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

            purchase_item = PurchaseOrderItem(
                purchase_order_id=po.id,
                product_name=item[
                    "product_name"
                ],
                quantity=quantity,
                unit_price=unit_price,
                total=item_total,
            )

            db.add(purchase_item)

        db.commit()
        db.refresh(po)

        return po

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()


# ==================================================
# PURCHASE ORDER STATUS
# ==================================================

def update_purchase_order_status(
    po_id,
    new_status,
):
    """
    Update purchase order status.
    """

    allowed_statuses = [
        "Draft",
        "Pending",
        "Approved",
        "Ordered",
        "Received",
        "Cancelled",
    ]

    if new_status not in allowed_statuses:
        raise ValueError(
            "Invalid purchase order status."
        )

    db = SessionLocal()

    try:

        po = (
            db.query(PurchaseOrder)
            .filter(
                PurchaseOrder.id == po_id
            )
            .first()
        )

        if not po:
            return None

        po.status = new_status

        db.commit()
        db.refresh(po)

        return po

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()