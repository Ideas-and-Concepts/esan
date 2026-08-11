"""
Esan ERP Procurement Service

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Handles:
- Suppliers
- Purchase Orders
- Purchase Order Items
- Purchase management
- Status management
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
    name=None,
    phone=None,
    email=None,
    address=None,
    supplier_type=None,
    location=None,
    country=None,
    contact_person=None,
):
    """
    Update an existing supplier.

    Only supplied values are changed.
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

        if name is not None:
            supplier.name = name

        if phone is not None:
            supplier.phone = phone

        if email is not None:
            supplier.email = email

        if address is not None:
            supplier.address = address

        if supplier_type is not None:
            supplier.supplier_type = supplier_type

        if location is not None:
            supplier.location = location

        if country is not None:
            supplier.country = country

        if contact_person is not None:
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

    A supplier with existing purchase orders should normally
    not be deleted. The database will protect related records
    where foreign-key enforcement is enabled.
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

    PurchaseOrder objects are returned while the database
    session is active and relationships are eagerly loaded
    to prevent DetachedInstanceError in Streamlit.
    """

    db = SessionLocal()

    try:

        purchase_orders = (
            db.query(PurchaseOrder)
            .join(
                Supplier,
                PurchaseOrder.supplier_id == Supplier.id,
                isouter=True,
            )
            .order_by(PurchaseOrder.created_at.desc())
            .all()
        )

        # Load supplier information while the session is open.
        for po in purchase_orders:
            if po.supplier:
                po.supplier.name

        return purchase_orders

    finally:
        db.close()


# ==================================================
# BACKWARD-COMPATIBILITY FUNCTION
# ==================================================

def get_all_purchases():
    """
    Backward-compatible purchase getter.

    The current ERP database uses PurchaseOrder as the
    purchasing transaction model. Until a separate Purchase
    model is introduced, this function returns purchase orders.

    This prevents older modules/procurement/purchases.py
    from failing during import.
    """

    return get_all_purchase_orders()


def get_purchase_order(po_id):
    """
    Get one purchase order by ID.
    """

    db = SessionLocal()

    try:

        purchase_order = (
            db.query(PurchaseOrder)
            .filter(PurchaseOrder.id == po_id)
            .first()
        )

        if purchase_order and purchase_order.supplier:
            purchase_order.supplier.name

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

    db = SessionLocal()

    try:

        if not items_data:
            raise ValueError(
                "At least one purchase order item is required."
            )

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

            product_name = str(
                item.get("product_name", "")
            ).strip()

            quantity = float(
                item.get("quantity", 0)
            )

            unit_price = float(
                item.get("unit_price", 0)
            )

            if not product_name:
                raise ValueError(
                    "Product / raw material name is required."
                )

            if quantity <= 0:
                raise ValueError(
                    f"Quantity for {product_name} must be greater than zero."
                )

            if unit_price < 0:
                raise ValueError(
                    f"Unit price for {product_name} cannot be negative."
                )

            total += quantity * unit_price

        # Generate PO number.
        today = datetime.utcnow().strftime("%Y%m")

        existing_count = (
            db.query(PurchaseOrder)
            .filter(
                PurchaseOrder.po_number.like(
                    f"PO-{today}-%"
                )
            )
            .count()
        )

        po_number = (
            f"PO-{today}-{existing_count + 1:04d}"
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
                item["quantity"]
            )

            unit_price = float(
                item["unit_price"]
            )

            purchase_item = PurchaseOrderItem(
                purchase_order_id=purchase_order.id,
                product_name=item["product_name"],
                quantity=quantity,
                unit_price=unit_price,
                total=quantity * unit_price,
            )

            db.add(purchase_item)

        db.commit()
        db.refresh(purchase_order)

        # Make supplier available before session closes.
        purchase_order.supplier

        return purchase_order

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def update_purchase_order(
    po_id,
    supplier_id=None,
    items_data=None,
    status=None,
):
    """
    Edit an existing purchase order.

    If items_data is supplied, existing items are replaced.
    """

    db = SessionLocal()

    try:

        purchase_order = (
            db.query(PurchaseOrder)
            .filter(PurchaseOrder.id == po_id)
            .first()
        )

        if not purchase_order:
            return None

        if supplier_id is not None:

            supplier = (
                db.query(Supplier)
                .filter(Supplier.id == supplier_id)
                .first()
            )

            if not supplier:
                raise ValueError(
                    "Selected supplier does not exist."
                )

            purchase_order.supplier_id = supplier_id

        if status is not None:
            purchase_order.status = status

        if items_data is not None:

            if not items_data:
                raise ValueError(
                    "Purchase order must contain at least one item."
                )

            total = 0.0

            # Remove existing items.
            (
                db.query(PurchaseOrderItem)
                .filter(
                    PurchaseOrderItem.purchase_order_id
                    == purchase_order.id
                )
                .delete(
                    synchronize_session=False
                )
            )

            for item in items_data:

                product_name = str(
                    item.get("product_name", "")
                ).strip()

                quantity = float(
                    item.get("quantity", 0)
                )

                unit_price = float(
                    item.get("unit_price", 0)
                )

                if not product_name:
                    raise ValueError(
                        "Product / raw material name is required."
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

                item_total = (
                    quantity * unit_price
                )

                total += item_total

                purchase_item = PurchaseOrderItem(
                    purchase_order_id=purchase_order.id,
                    product_name=product_name,
                    quantity=quantity,
                    unit_price=unit_price,
                    total=item_total,
                )

                db.add(purchase_item)

            purchase_order.total_amount = total

        db.commit()
        db.refresh(purchase_order)

        purchase_order.supplier

        return purchase_order

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
    Update the status of a purchase order.
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
            f"Invalid purchase order status: {new_status}"
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
        db.refresh(purchase_order)

        purchase_order.supplier

        return purchase_order

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
            .filter(PurchaseOrder.id == po_id)
            .first()
        )

        if not purchase_order:
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

        db.delete(purchase_order)
        db.commit()

        return True

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
    Get all items belonging to a purchase order.
    """

    db = SessionLocal()

    try:

        return (
            db.query(PurchaseOrderItem)
            .filter(
                PurchaseOrderItem.purchase_order_id
                == po_id
            )
            .order_by(PurchaseOrderItem.id.asc())
            .all()
        )

    finally:
        db.close()