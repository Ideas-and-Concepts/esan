"""
Esan ERP - Procurement Service

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Handles:
- Suppliers
- Supplier CRUD
- Purchase Orders
- Purchase Order Items
- Purchase Order CRUD
- Purchase Order status management
- Safe SQLAlchemy session handling
- Eager loading of relationships
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

    Objects are fully loaded before the database session
    closes so Streamlit pages do not encounter
    DetachedInstanceError.
    """

    db = SessionLocal()

    try:

        suppliers = (
            db.query(Supplier)
            .order_by(Supplier.name.asc())
            .all()
        )

        return suppliers

    finally:

        db.close()


def get_supplier(supplier_id):
    """
    Get a single supplier by ID.
    """

    db = SessionLocal()

    try:

        supplier = (
            db.query(Supplier)
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

    db = SessionLocal()

    try:

        # --------------------------------------------------
        # Basic validation
        # --------------------------------------------------

        if not name or not name.strip():
            raise ValueError(
                "Supplier name is required."
            )

        # --------------------------------------------------
        # Check duplicate supplier
        # --------------------------------------------------

        existing = (
            db.query(Supplier)
            .filter(
                Supplier.name.ilike(name.strip())
            )
            .first()
        )

        if existing:

            raise ValueError(
                f"Supplier '{name.strip()}' already exists."
            )

        # --------------------------------------------------
        # Create supplier
        # --------------------------------------------------

        supplier = Supplier(
            name=name.strip(),
            phone=phone,
            email=email,
            address=address,
            supplier_type=supplier_type
            or "Agricultural Supplier",
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

        if not name or not name.strip():
            raise ValueError(
                "Supplier name is required."
            )

        # --------------------------------------------------
        # Prevent duplicate names
        # --------------------------------------------------

        duplicate = (
            db.query(Supplier)
            .filter(
                Supplier.name.ilike(name.strip()),
                Supplier.id != supplier_id,
            )
            .first()
        )

        if duplicate:

            raise ValueError(
                f"Another supplier named "
                f"'{name.strip()}' already exists."
            )

        # --------------------------------------------------
        # Update fields
        # --------------------------------------------------

        supplier.name = name.strip()
        supplier.phone = phone
        supplier.email = email
        supplier.address = address
        supplier.supplier_type = (
            supplier_type
            or "Agricultural Supplier"
        )
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

    A supplier with existing purchase orders is not deleted
    because doing so could break procurement history.
    """

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

        # --------------------------------------------------
        # Protect procurement history
        # --------------------------------------------------

        purchase_order_count = (
            db.query(PurchaseOrder)
            .filter(
                PurchaseOrder.supplier_id
                == supplier_id
            )
            .count()
        )

        if purchase_order_count > 0:

            raise ValueError(
                "This supplier cannot be deleted because "
                "purchase orders already exist for this supplier. "
                "Keep the supplier for historical procurement records."
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

    The Supplier relationship is eagerly loaded to prevent:

    DetachedInstanceError:
    Parent instance is not bound to a Session

    after the database session closes.
    """

    db = SessionLocal()

    try:

        purchase_orders = (
            db.query(PurchaseOrder)
            .options(
                joinedload(
                    PurchaseOrder.supplier
                )
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
    Get a single purchase order with its supplier
    and items already loaded.
    """

    db = SessionLocal()

    try:

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

    finally:

        db.close()


def generate_po_number(db):
    """
    Generate a purchase order number.

    Example:
        PO-202608-0001
    """

    prefix = (
        f"PO-{datetime.utcnow().strftime('%Y%m')}-"
    )

    last_po = (
        db.query(PurchaseOrder)
        .filter(
            PurchaseOrder.po_number.like(
                f"{prefix}%"
            )
        )
        .order_by(
            PurchaseOrder.id.desc()
        )
        .first()
    )

    if last_po and last_po.po_number:

        try:

            last_number = int(
                last_po.po_number.split("-")[-1]
            )

            next_number = last_number + 1

        except (ValueError, IndexError):

            next_number = (
                db.query(PurchaseOrder).count()
                + 1
            )

    else:

        next_number = 1

    return f"{prefix}{next_number:04d}"


def create_purchase_order(
    supplier_id,
    items_data,
    status="Draft",
):
    """
    Create a Purchase Order.

    items_data format:

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

        # --------------------------------------------------
        # Validate supplier
        # --------------------------------------------------

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

        # --------------------------------------------------
        # Validate items
        # --------------------------------------------------

        if not items_data:

            raise ValueError(
                "At least one purchase order item is required."
            )

        cleaned_items = []

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
                    f"Quantity for '{product_name}' "
                    "must be greater than zero."
                )

            if unit_price < 0:

                raise ValueError(
                    f"Unit price for '{product_name}' "
                    "cannot be negative."
                )

            item_total = (
                quantity * unit_price
            )

            cleaned_items.append(
                {
                    "product_name": product_name,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "total": item_total,
                }
            )

        # --------------------------------------------------
        # Calculate total
        # --------------------------------------------------

        total_amount = sum(
            item["total"]
            for item in cleaned_items
        )

        # --------------------------------------------------
        # Generate PO number
        # --------------------------------------------------

        po_number = generate_po_number(db)

        # --------------------------------------------------
        # Create purchase order
        # --------------------------------------------------

        purchase_order = PurchaseOrder(
            po_number=po_number,
            supplier_id=supplier_id,
            status=status or "Draft",
            total_amount=total_amount,
            created_at=datetime.utcnow(),
        )

        db.add(purchase_order)
        db.flush()

        # --------------------------------------------------
        # Create purchase order items
        # --------------------------------------------------

        for item in cleaned_items:

            purchase_order_item = (
                PurchaseOrderItem(
                    purchase_order_id=purchase_order.id,
                    product_name=item["product_name"],
                    quantity=item["quantity"],
                    unit_price=item["unit_price"],
                    total=item["total"],
                )
            )

            db.add(purchase_order_item)

        db.commit()

        # --------------------------------------------------
        # Reload with relationships before session closes
        # --------------------------------------------------

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


def update_purchase_order(
    po_id,
    supplier_id,
    items_data,
    status="Draft",
):
    """
    Edit an existing Purchase Order.

    Existing items are replaced with the
    supplied items_data.
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

        # --------------------------------------------------
        # Validate supplier
        # --------------------------------------------------

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

        if not items_data:

            raise ValueError(
                "At least one purchase order item is required."
            )

        # --------------------------------------------------
        # Validate and calculate items
        # --------------------------------------------------

        cleaned_items = []

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
                    f"Quantity for '{product_name}' "
                    "must be greater than zero."
                )

            if unit_price < 0:

                raise ValueError(
                    f"Unit price for '{product_name}' "
                    "cannot be negative."
                )

            cleaned_items.append(
                {
                    "product_name": product_name,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "total":
                        quantity * unit_price,
                }
            )

        total_amount = sum(
            item["total"]
            for item in cleaned_items
        )

        # --------------------------------------------------
        # Update PO
        # --------------------------------------------------

        purchase_order.supplier_id = supplier_id
        purchase_order.status = (
            status or "Draft"
        )
        purchase_order.total_amount = total_amount

        # --------------------------------------------------
        # Remove old items
        # --------------------------------------------------

        for item in list(
            purchase_order.items
        ):

            db.delete(item)

        db.flush()

        # --------------------------------------------------
        # Add new items
        # --------------------------------------------------

        for item in cleaned_items:

            purchase_order_item = (
                PurchaseOrderItem(
                    purchase_order_id=purchase_order.id,
                    product_name=item["product_name"],
                    quantity=item["quantity"],
                    unit_price=item["unit_price"],
                    total=item["total"],
                )
            )

            db.add(purchase_order_item)

        db.commit()

        # --------------------------------------------------
        # Reload safely
        # --------------------------------------------------

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


def delete_purchase_order(po_id):
    """
    Delete a purchase order and its items.
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
            return False

        # --------------------------------------------------
        # Delete items first
        # --------------------------------------------------

        db.query(PurchaseOrderItem).filter(
            PurchaseOrderItem.purchase_order_id
            == po_id
        ).delete(
            synchronize_session=False
        )

        # --------------------------------------------------
        # Delete purchase order
        # --------------------------------------------------

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
    Update the status of a purchase order.

    Supported statuses:

    Draft
    Pending Approval
    Approved
    Ordered
    Partially Received
    Received
    Cancelled
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
            f"Invalid purchase order status: "
            f"{new_status}"
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

        # --------------------------------------------------
        # Reload relationships before returning
        # --------------------------------------------------

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
                == po_id
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


# ==================================================
# PROCUREMENT SUMMARY
# ==================================================


def get_procurement_summary():
    """
    Return basic procurement statistics for dashboards.
    """

    db = SessionLocal()

    try:

        total_suppliers = (
            db.query(Supplier).count()
        )

        total_purchase_orders = (
            db.query(PurchaseOrder).count()
        )

        draft_orders = (
            db.query(PurchaseOrder)
            .filter(
                PurchaseOrder.status
                == "Draft"
            )
            .count()
        )

        pending_orders = (
            db.query(PurchaseOrder)
            .filter(
                PurchaseOrder.status
                == "Pending Approval"
            )
            .count()
        )

        approved_orders = (
            db.query(PurchaseOrder)
            .filter(
                PurchaseOrder.status
                == "Approved"
            )
            .count()
        )

        ordered_orders = (
            db.query(PurchaseOrder)
            .filter(
                PurchaseOrder.status
                == "Ordered"
            )
            .count()
        )

        received_orders = (
            db.query(PurchaseOrder)
            .filter(
                PurchaseOrder.status
                == "Received"
            )
            .count()
        )

        return {
            "suppliers": total_suppliers,
            "purchase_orders":
                total_purchase_orders,
            "draft_orders": draft_orders,
            "pending_orders":
                pending_orders,
            "approved_orders":
                approved_orders,
            "ordered_orders":
                ordered_orders,
            "received_orders":
                received_orders,
        }

    finally:

        db.close()