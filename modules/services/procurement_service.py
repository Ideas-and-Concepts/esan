"""
Esan ERP - Procurement Service

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Handles:
- Suppliers
- Purchase Orders
- Purchase Order Items
- Create
- Read
- Update
- Delete
- Status management
- Safe SQLAlchemy session handling
"""

from datetime import datetime

from sqlalchemy.orm import Session

from database import SessionLocal
from models import (
    Supplier,
    PurchaseOrder,
    PurchaseOrderItem,
)


# ==================================================
# SUPPLIER MANAGEMENT
# ==================================================

def get_all_suppliers():
    """
    Return all suppliers ordered alphabetically.

    Objects are converted into detached-safe data by
    loading all required fields before closing the session.
    """

    db = SessionLocal()

    try:
        suppliers = (
            db.query(Supplier)
            .order_by(Supplier.name.asc())
            .all()
        )

        # Force required attributes to load while session
        # is still active.
        for supplier in suppliers:
            _ = supplier.id
            _ = supplier.name
            _ = supplier.phone
            _ = supplier.email
            _ = supplier.address
            _ = supplier.supplier_type
            _ = supplier.location
            _ = supplier.country
            _ = supplier.contact_person
            _ = supplier.created_at

        return suppliers

    finally:
        db.close()


def get_supplier_by_id(supplier_id):
    """
    Return a single supplier by ID.
    """

    db = SessionLocal()

    try:

        supplier = (
            db.query(Supplier)
            .filter(Supplier.id == supplier_id)
            .first()
        )

        if supplier:
            _ = supplier.id
            _ = supplier.name
            _ = supplier.phone
            _ = supplier.email
            _ = supplier.address
            _ = supplier.supplier_type
            _ = supplier.location
            _ = supplier.country
            _ = supplier.contact_person
            _ = supplier.created_at

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
            phone=phone.strip() if phone else None,
            email=email.strip() if email else None,
            address=address.strip() if address else None,
            supplier_type=supplier_type,
            location=location.strip() if location else None,
            country=country.strip() if country else None,
            contact_person=(
                contact_person.strip()
                if contact_person
                else None
            ),
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
            if not name.strip():
                raise ValueError(
                    "Supplier name cannot be empty."
                )

            supplier.name = name.strip()

        if phone is not None:
            supplier.phone = (
                phone.strip() if phone.strip() else None
            )

        if email is not None:
            supplier.email = (
                email.strip() if email.strip() else None
            )

        if address is not None:
            supplier.address = (
                address.strip()
                if address.strip()
                else None
            )

        if supplier_type is not None:
            supplier.supplier_type = supplier_type

        if location is not None:
            supplier.location = (
                location.strip()
                if location.strip()
                else None
            )

        if country is not None:
            supplier.country = (
                country.strip()
                if country.strip()
                else None
            )

        if contact_person is not None:
            supplier.contact_person = (
                contact_person.strip()
                if contact_person.strip()
                else None
            )

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

    A supplier with existing purchase orders cannot be deleted.
    This protects procurement history.
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

        existing_orders = (
            db.query(PurchaseOrder)
            .filter(
                PurchaseOrder.supplier_id == supplier_id
            )
            .count()
        )

        if existing_orders > 0:

            raise ValueError(
                "This supplier cannot be deleted because "
                "purchase orders already exist for this supplier."
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
# PURCHASE ORDER MANAGEMENT
# ==================================================

def get_all_purchase_orders():
    """
    Return purchase orders with supplier information.

    IMPORTANT:
    Supplier name is loaded using the same database session
    before the session closes.

    This prevents:

    DetachedInstanceError:
    Parent instance is not bound to a Session
    """

    db = SessionLocal()

    try:

        results = (
            db.query(
                PurchaseOrder,
                Supplier.name.label("supplier_name"),
            )
            .outerjoin(
                Supplier,
                PurchaseOrder.supplier_id == Supplier.id,
            )
            .order_by(
                PurchaseOrder.created_at.desc()
            )
            .all()
        )

        purchase_orders = []

        for po, supplier_name in results:

            # Attach supplier name as a normal Python attribute.
            po.supplier_name = (
                supplier_name
                if supplier_name
                else "Unknown Supplier"
            )

            # Force all fields to load.
            _ = po.id
            _ = po.po_number
            _ = po.supplier_id
            _ = po.status
            _ = po.total_amount
            _ = po.created_at

            purchase_orders.append(po)

        return purchase_orders

    finally:

        db.close()


def get_purchase_order_by_id(purchase_order_id):
    """
    Return a purchase order with supplier information
    and its items safely loaded.
    """

    db = SessionLocal()

    try:

        result = (
            db.query(
                PurchaseOrder,
                Supplier.name.label("supplier_name"),
            )
            .outerjoin(
                Supplier,
                PurchaseOrder.supplier_id == Supplier.id,
            )
            .filter(
                PurchaseOrder.id == purchase_order_id
            )
            .first()
        )

        if not result:
            return None

        po, supplier_name = result

        po.supplier_name = (
            supplier_name
            if supplier_name
            else "Unknown Supplier"
        )

        # Load items while session is active.
        items = (
            db.query(PurchaseOrderItem)
            .filter(
                PurchaseOrderItem.purchase_order_id
                == po.id
            )
            .all()
        )

        # Attach detached-safe item collection.
        po.loaded_items = []

        for item in items:

            po.loaded_items.append(
                {
                    "id": item.id,
                    "purchase_order_id": (
                        item.purchase_order_id
                    ),
                    "product_name": item.product_name,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "total": item.total,
                }
            )

        return po

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

    if not supplier_id:
        raise ValueError(
            "A supplier must be selected."
        )

    if not items_data:
        raise ValueError(
            "At least one purchase order item is required."
        )

    db = SessionLocal()

    try:

        # Verify supplier exists.
        supplier = (
            db.query(Supplier)
            .filter(Supplier.id == supplier_id)
            .first()
        )

        if not supplier:
            raise ValueError(
                "Selected supplier does not exist."
            )

        # ------------------------------------------
        # Validate items
        # ------------------------------------------

        total = 0.0

        for item in items_data:

            product_name = (
                item.get("product_name")
                if isinstance(item, dict)
                else None
            )

            quantity = (
                item.get("quantity")
                if isinstance(item, dict)
                else None
            )

            unit_price = (
                item.get("unit_price")
                if isinstance(item, dict)
                else None
            )

            if not product_name:
                raise ValueError(
                    "Every purchase order item "
                    "must have a product name."
                )

            if quantity is None or float(quantity) <= 0:
                raise ValueError(
                    f"Quantity for {product_name} "
                    "must be greater than zero."
                )

            if unit_price is None or float(unit_price) < 0:
                raise ValueError(
                    f"Unit price for {product_name} "
                    "cannot be negative."
                )

            total += (
                float(quantity)
                * float(unit_price)
            )

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
        # Create PO
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
        # Create PO items
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
                product_name=(
                    item["product_name"].strip()
                ),
                quantity=quantity,
                unit_price=unit_price,
                total=item_total,
            )

            db.add(purchase_item)

        db.commit()

        # Load scalar fields before closing session.
        db.refresh(po)

        _ = po.id
        _ = po.po_number
        _ = po.supplier_id
        _ = po.status
        _ = po.total_amount
        _ = po.created_at

        # Attach supplier name safely.
        po.supplier_name = supplier.name

        return po

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()


def update_purchase_order(
    purchase_order_id,
    supplier_id=None,
    total_amount=None,
    status=None,
    items_data=None,
):
    """
    Update a purchase order.

    Can update:
    - Supplier
    - Status
    - Total
    - Items

    If items_data is supplied, existing items are replaced.
    """

    db = SessionLocal()

    try:

        po = (
            db.query(PurchaseOrder)
            .filter(
                PurchaseOrder.id
                == purchase_order_id
            )
            .first()
        )

        if not po:
            return None

        # ------------------------------------------
        # Supplier
        # ------------------------------------------

        if supplier_id is not None:

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

            po.supplier_id = supplier_id

        # ------------------------------------------
        # Status
        # ------------------------------------------

        if status is not None:
            po.status = status

        # ------------------------------------------
        # Items
        # ------------------------------------------

        if items_data is not None:

            if not items_data:
                raise ValueError(
                    "A purchase order must contain "
                    "at least one item."
                )

            total = 0.0

            # Remove old items.
            db.query(
                PurchaseOrderItem
            ).filter(
                PurchaseOrderItem.purchase_order_id
                == po.id
            ).delete(
                synchronize_session=False
            )

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

                item_total = (
                    quantity * unit_price
                )

                total += item_total

                purchase_item = PurchaseOrderItem(
                    purchase_order_id=po.id,
                    product_name=product_name.strip(),
                    quantity=quantity,
                    unit_price=unit_price,
                    total=item_total,
                )

                db.add(purchase_item)

            po.total_amount = total

        # ------------------------------------------
        # Direct total update
        # ------------------------------------------

        elif total_amount is not None:

            if float(total_amount) < 0:
                raise ValueError(
                    "Purchase order total "
                    "cannot be negative."
                )

            po.total_amount = float(
                total_amount
            )

        db.commit()
        db.refresh(po)

        # Load supplier name before session closes.
        supplier = (
            db.query(Supplier)
            .filter(
                Supplier.id == po.supplier_id
            )
            .first()
        )

        po.supplier_name = (
            supplier.name
            if supplier
            else "Unknown Supplier"
        )

        return po

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
    Update only the status of a purchase order.
    """

    if not new_status:
        raise ValueError(
            "Purchase order status is required."
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

        # Load supplier name safely.
        supplier = (
            db.query(Supplier)
            .filter(
                Supplier.id == po.supplier_id
            )
            .first()
        )

        po.supplier_name = (
            supplier.name
            if supplier
            else "Unknown Supplier"
        )

        return po

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()


def delete_purchase_order(
    purchase_order_id,
):
    """
    Delete a purchase order and all of its items.

    Purchase order items are deleted first to avoid
    foreign-key constraint problems.
    """

    db = SessionLocal()

    try:

        po = (
            db.query(PurchaseOrder)
            .filter(
                PurchaseOrder.id
                == purchase_order_id
            )
            .first()
        )

        if not po:
            return False

        # Delete items first.
        db.query(
            PurchaseOrderItem
        ).filter(
            PurchaseOrderItem.purchase_order_id
            == po.id
        ).delete(
            synchronize_session=False
        )

        # Delete PO.
        db.delete(po)

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

def get_purchase_order_items(
    purchase_order_id,
):
    """
    Return purchase order items as detached-safe
    dictionaries.
    """

    db = SessionLocal()

    try:

        items = (
            db.query(PurchaseOrderItem)
            .filter(
                PurchaseOrderItem.purchase_order_id
                == purchase_order_id
            )
            .order_by(
                PurchaseOrderItem.id.asc()
            )
            .all()
        )

        return [
            {
                "id": item.id,
                "purchase_order_id": (
                    item.purchase_order_id
                ),
                "product_name": item.product_name,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "total": item.total,
            }
            for item in items
        ]

    finally:

        db.close()


def delete_purchase_order_item(
    item_id,
):
    """
    Delete a single purchase order item and
    recalculate the purchase order total.
    """

    db = SessionLocal()

    try:

        item = (
            db.query(PurchaseOrderItem)
            .filter(
                PurchaseOrderItem.id == item_id
            )
            .first()
        )

        if not item:
            return False

        purchase_order_id = (
            item.purchase_order_id
        )

        db.delete(item)
        db.flush()

        # Recalculate PO total.
        remaining_items = (
            db.query(PurchaseOrderItem)
            .filter(
                PurchaseOrderItem.purchase_order_id
                == purchase_order_id
            )
            .all()
        )

        new_total = sum(
            (item.total or 0)
            for item in remaining_items
        )

        po = (
            db.query(PurchaseOrder)
            .filter(
                PurchaseOrder.id
                == purchase_order_id
            )
            .first()
        )

        if po:
            po.total_amount = new_total

        db.commit()

        return True

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()