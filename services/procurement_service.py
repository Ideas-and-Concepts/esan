"""
Esan ERP Procurement Service
Nile Harvest Foods Ltd.

Handles:
    - Suppliers
    - Purchase Orders
    - Purchase Order Items
    - Actual Purchases / Goods Received
    - Add / Edit / Delete operations
    - Status management
"""

from datetime import datetime

from sqlalchemy.orm import joinedload

from database import SessionLocal
from models import (
    Supplier,
    PurchaseOrder,
    PurchaseOrderItem,
    Purchase,
)


# ==================================================
# SUPPLIERS
# ==================================================

def get_all_suppliers():
    """
    Return all suppliers ordered alphabetically.
    Supplier records are fully loaded before the session closes.
    """
    db = SessionLocal()

    try:
        suppliers = (
            db.query(Supplier)
            .options(
                joinedload(Supplier.purchase_orders),
                joinedload(Supplier.purchases),
            )
            .order_by(Supplier.name.asc())
            .all()
        )

        return suppliers

    finally:
        db.close()


def get_supplier(supplier_id):
    """
    Get one supplier by ID.
    """
    db = SessionLocal()

    try:
        supplier = (
            db.query(Supplier)
            .options(
                joinedload(Supplier.purchase_orders),
                joinedload(Supplier.purchases),
            )
            .filter(Supplier.id == supplier_id)
            .first()
        )

        return supplier

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
        raise ValueError("Supplier name is required.")

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
    """
    Update an existing supplier.
    """

    if not name or not name.strip():
        raise ValueError("Supplier name is required.")

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

        return supplier

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def delete_supplier(supplier_id):
    """
    Delete a supplier.

    A supplier with existing purchase orders or purchases
    is not deleted in order to protect ERP transaction history.

    Returns:
        True  - deleted
        False - supplier not found
        Raises ValueError if transaction history exists.
    """

    db = SessionLocal()

    try:

        supplier = (
            db.query(Supplier)
            .filter(Supplier.id == supplier_id)
            .first()
        )

        if not supplier:
            return False

        purchase_order_count = (
            db.query(PurchaseOrder)
            .filter(
                PurchaseOrder.supplier_id == supplier_id
            )
            .count()
        )

        purchase_count = (
            db.query(Purchase)
            .filter(
                Purchase.supplier_id == supplier_id
            )
            .count()
        )

        if purchase_order_count > 0 or purchase_count > 0:
            raise ValueError(
                "This supplier cannot be deleted because "
                "purchase orders or purchases are linked to it."
            )

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

    Supplier and items are eagerly loaded to prevent
    DetachedInstanceError after the database session closes.
    """

    db = SessionLocal()

    try:

        purchase_orders = (
            db.query(PurchaseOrder)
            .options(
                joinedload(PurchaseOrder.supplier),
                joinedload(PurchaseOrder.items),
                joinedload(PurchaseOrder.purchases),
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
    Get a single purchase order with supplier,
    items and linked purchases loaded.
    """

    db = SessionLocal()

    try:

        purchase_order = (
            db.query(PurchaseOrder)
            .options(
                joinedload(PurchaseOrder.supplier),
                joinedload(PurchaseOrder.items),
                joinedload(PurchaseOrder.purchases),
            )
            .filter(PurchaseOrder.id == po_id)
            .first()
        )

        return purchase_order

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
                "product_name": "Maize Grain",
                "quantity": 10,
                "unit_price": 40000
            }
        ]
    """

    if not supplier_id:
        raise ValueError("Supplier is required.")

    if not items_data:
        raise ValueError(
            "At least one purchase order item is required."
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

        total = 0

        for item in items_data:

            product_name = (
                item.get("product_name") or ""
            ).strip()

            quantity = float(
                item.get("quantity", 0)
            )

            unit_price = float(
                item.get("unit_price", 0)
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

            quantity = float(
                item.get("quantity", 0)
            )

            unit_price = float(
                item.get("unit_price", 0)
            )

            item_total = (
                quantity * unit_price
            )

            purchase_order_item = PurchaseOrderItem(
                purchase_order_id=purchase_order.id,
                product_name=(
                    item["product_name"].strip()
                ),
                quantity=quantity,
                unit_price=unit_price,
                total=item_total,
            )

            db.add(purchase_order_item)

        db.commit()

        # Reload with relationships attached
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
    status=None,
):
    """
    Update an existing purchase order.

    Existing PO items are replaced with the
    newly submitted items.
    """

    if not supplier_id:
        raise ValueError("Supplier is required.")

    if not items_data:
        raise ValueError(
            "At least one purchase order item is required."
        )

    db = SessionLocal()

    try:

        purchase_order = (
            db.query(PurchaseOrder)
            .filter(PurchaseOrder.id == po_id)
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

        total = 0

        for item in items_data:

            product_name = (
                item.get("product_name") or ""
            ).strip()

            quantity = float(
                item.get("quantity", 0)
            )

            unit_price = float(
                item.get("unit_price", 0)
            )

            if not product_name:
                raise ValueError(
                    "Product name is required."
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

        purchase_order.supplier_id = supplier_id
        purchase_order.total_amount = total

        if status is not None:
            purchase_order.status = status

        # Remove old items
        purchase_order.items.clear()

        # Add new items
        for item in items_data:

            quantity = float(
                item.get("quantity", 0)
            )

            unit_price = float(
                item.get("unit_price", 0)
            )

            purchase_order.items.append(
                PurchaseOrderItem(
                    product_name=(
                        item["product_name"].strip()
                    ),
                    quantity=quantity,
                    unit_price=unit_price,
                    total=quantity * unit_price,
                )
            )

        db.commit()

        purchase_order = (
            db.query(PurchaseOrder)
            .options(
                joinedload(PurchaseOrder.supplier),
                joinedload(PurchaseOrder.items),
                joinedload(PurchaseOrder.purchases),
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


def delete_purchase_order(po_id):
    """
    Delete a purchase order.

    Purchase orders that already have actual purchases
    recorded against them cannot be physically deleted.
    """

    db = SessionLocal()

    try:

        purchase_order = (
            db.query(PurchaseOrder)
            .filter(PurchaseOrder.id == po_id)
            .first()
        )

        if not purchase_order:
            return False

        linked_purchases = (
            db.query(Purchase)
            .filter(
                Purchase.purchase_order_id == po_id
            )
            .count()
        )

        if linked_purchases > 0:
            raise ValueError(
                "This purchase order cannot be deleted "
                "because actual purchases are linked to it."
            )

        db.delete(purchase_order)
        db.commit()

        return True

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

    allowed_statuses = [
        "Draft",
        "Approved",
        "Ordered",
        "Partially Received",
        "Received",
        "Cancelled",
    ]

    if new_status not in allowed_statuses:
        raise ValueError(
            "Invalid purchase order status."
        )

    db = SessionLocal()

    try:

        purchase_order = (
            db.query(PurchaseOrder)
            .filter(PurchaseOrder.id == po_id)
            .first()
        )

        if not purchase_order:
            return None

        purchase_order.status = new_status

        db.commit()

        purchase_order = (
            db.query(PurchaseOrder)
            .options(
                joinedload(PurchaseOrder.supplier),
                joinedload(PurchaseOrder.items),
                joinedload(PurchaseOrder.purchases),
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


# ==================================================
# ACTUAL PURCHASES
# ==================================================

def get_all_purchases():
    """
    Return all actual purchases.

    Supplier and purchase order are eagerly loaded.
    """

    db = SessionLocal()

    try:

        purchases = (
            db.query(Purchase)
            .options(
                joinedload(Purchase.supplier),
                joinedload(Purchase.purchase_order),
            )
            .order_by(
                Purchase.purchase_date.desc()
            )
            .all()
        )

        return purchases

    finally:
        db.close()


def get_purchase(purchase_id):
    """
    Get one purchase.
    """

    db = SessionLocal()

    try:

        purchase = (
            db.query(Purchase)
            .options(
                joinedload(Purchase.supplier),
                joinedload(Purchase.purchase_order),
            )
            .filter(
                Purchase.id == purchase_id
            )
            .first()
        )

        return purchase

    finally:
        db.close()


def create_purchase(
    supplier_id,
    product_name,
    quantity,
    unit_price,
    purchase_order_id=None,
    status="Received",
    purchase_date=None,
):
    """
    Record an actual purchase / goods received.
    """

    if not supplier_id:
        raise ValueError(
            "Supplier is required."
        )

    if not product_name or not product_name.strip():
        raise ValueError(
            "Product name is required."
        )

    quantity = float(quantity)
    unit_price = float(unit_price)

    if quantity <= 0:
        raise ValueError(
            "Quantity must be greater than zero."
        )

    if unit_price < 0:
        raise ValueError(
            "Unit price cannot be negative."
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

        if purchase_order_id:

            purchase_order = (
                db.query(PurchaseOrder)
                .filter(
                    PurchaseOrder.id
                    == purchase_order_id
                )
                .first()
            )

            if not purchase_order:
                raise ValueError(
                    "Selected purchase order does not exist."
                )

        count = (
            db.query(Purchase)
            .count()
        )

        purchase_number = (
            f"PUR-"
            f"{datetime.utcnow().strftime('%Y%m')}-"
            f"{count + 1:04d}"
        )

        total_amount = (
            quantity * unit_price
        )

        purchase = Purchase(
            purchase_number=purchase_number,
            supplier_id=supplier_id,
            purchase_order_id=purchase_order_id,
            product_name=product_name.strip(),
            quantity=quantity,
            unit_price=unit_price,
            total_amount=total_amount,
            status=status,
            purchase_date=(
                purchase_date
                or datetime.utcnow()
            ),
            created_at=datetime.utcnow(),
        )

        db.add(purchase)
        db.commit()

        purchase = (
            db.query(Purchase)
            .options(
                joinedload(Purchase.supplier),
                joinedload(Purchase.purchase_order),
            )
            .filter(
                Purchase.id == purchase.id
            )
            .first()
        )

        return purchase

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def update_purchase(
    purchase_id,
    supplier_id,
    product_name,
    quantity,
    unit_price,
    purchase_order_id=None,
    status=None,
    purchase_date=None,
):
    """
    Update an existing actual purchase.
    """

    if not supplier_id:
        raise ValueError(
            "Supplier is required."
        )

    if not product_name or not product_name.strip():
        raise ValueError(
            "Product name is required."
        )

    quantity = float(quantity)
    unit_price = float(unit_price)

    if quantity <= 0:
        raise ValueError(
            "Quantity must be greater than zero."
        )

    if unit_price < 0:
        raise ValueError(
            "Unit price cannot be negative."
        )

    db = SessionLocal()

    try:

        purchase = (
            db.query(Purchase)
            .filter(
                Purchase.id == purchase_id
            )
            .first()
        )

        if not purchase:
            return None

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

        if purchase_order_id:

            purchase_order = (
                db.query(PurchaseOrder)
                .filter(
                    PurchaseOrder.id
                    == purchase_order_id
                )
                .first()
            )

            if not purchase_order:
                raise ValueError(
                    "Selected purchase order does not exist."
                )

        purchase.supplier_id = supplier_id
        purchase.purchase_order_id = (
            purchase_order_id
        )
        purchase.product_name = (
            product_name.strip()
        )
        purchase.quantity = quantity
        purchase.unit_price = unit_price
        purchase.total_amount = (
            quantity * unit_price
        )

        if status is not None:
            purchase.status = status

        if purchase_date is not None:
            purchase.purchase_date = purchase_date

        db.commit()

        purchase = (
            db.query(Purchase)
            .options(
                joinedload(Purchase.supplier),
                joinedload(Purchase.purchase_order),
            )
            .filter(
                Purchase.id == purchase_id
            )
            .first()
        )

        return purchase

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def delete_purchase(purchase_id):
    """
    Delete an actual purchase.
    """

    db = SessionLocal()

    try:

        purchase = (
            db.query(Purchase)
            .filter(
                Purchase.id == purchase_id
            )
            .first()
        )

        if not purchase:
            return False

        db.delete(purchase)
        db.commit()

        return True

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def update_purchase_status(
    purchase_id,
    new_status,
):
    """
    Update actual purchase status.
    """

    allowed_statuses = [
        "Draft",
        "Received",
        "Partially Received",
        "Completed",
        "Cancelled",
    ]

    if new_status not in allowed_statuses:
        raise ValueError(
            "Invalid purchase status."
        )

    db = SessionLocal()

    try:

        purchase = (
            db.query(Purchase)
            .filter(
                Purchase.id == purchase_id
            )
            .first()
        )

        if not purchase:
            return None

        purchase.status = new_status

        db.commit()

        purchase = (
            db.query(Purchase)
            .options(
                joinedload(Purchase.supplier),
                joinedload(Purchase.purchase_order),
            )
            .filter(
                Purchase.id == purchase_id
            )
            .first()
        )

        return purchase

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


# ==================================================
# PROCUREMENT SUMMARY
# ==================================================

def get_procurement_summary():
    """
    Return basic procurement statistics.
    """

    db = SessionLocal()

    try:

        supplier_count = (
            db.query(Supplier).count()
        )

        purchase_order_count = (
            db.query(PurchaseOrder).count()
        )

        purchase_count = (
            db.query(Purchase).count()
        )

        purchase_order_value = (
            db.query(
                PurchaseOrder.total_amount
            )
            .all()
        )

        purchase_value = (
            db.query(
                Purchase.total_amount
            )
            .all()
        )

        total_po_value = sum(
            float(row[0] or 0)
            for row in purchase_order_value
        )

        total_purchase_value = sum(
            float(row[0] or 0)
            for row in purchase_value
        )

        return {
            "suppliers": supplier_count,
            "purchase_orders": purchase_order_count,
            "purchases": purchase_count,
            "purchase_order_value": total_po_value,
            "purchase_value": total_purchase_value,
        }

    finally:
        db.close()