"""
Esan ERP - Procurement Service

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Handles:
- Suppliers
- Purchase Orders
- Purchase Order Items
- Add
- Edit
- Delete
- Status Changes
- Safe database/session handling
"""

from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import joinedload

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

    SQLAlchemy ORM objects are returned while the session
    is active. Basic supplier fields are loaded before the
    session closes.
    """

    db = SessionLocal()

    try:

        suppliers = (
            db.query(Supplier)
            .order_by(Supplier.name.asc())
            .all()
        )

        # Make sure required fields are loaded before
        # closing the database session.
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


def get_supplier(supplier_id):
    """
    Get one supplier by ID.
    """

    db = SessionLocal()

    try:

        supplier = (
            db.query(Supplier)
            .filter(Supplier.id == supplier_id)
            .first()
        )

        if supplier:

            # Load scalar fields before session closes.
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

    db = SessionLocal()

    try:

        name = name.strip() if name else ""

        if not name:
            raise ValueError(
                "Supplier name is required."
            )

        # Prevent duplicate supplier names.
        existing = (
            db.query(Supplier)
            .filter(
                func.lower(Supplier.name)
                == name.lower()
            )
            .first()
        )

        if existing:
            raise ValueError(
                f"Supplier '{name}' already exists."
            )

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
            .filter(
                Supplier.id == supplier_id
            )
            .first()
        )

        if not supplier:
            return None

        if name is not None:

            name = name.strip()

            if not name:
                raise ValueError(
                    "Supplier name cannot be empty."
                )

            duplicate = (
                db.query(Supplier)
                .filter(
                    func.lower(Supplier.name)
                    == name.lower(),
                    Supplier.id != supplier_id,
                )
                .first()
            )

            if duplicate:
                raise ValueError(
                    f"Supplier '{name}' already exists."
                )

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

    A supplier with existing purchase orders is protected
    from deletion to preserve procurement history.
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
                "purchase orders are linked to the supplier. "
                "Delete or archive the purchase orders first."
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
# PURCHASE ORDER HELPERS
# ==================================================


def _generate_po_number(db):
    """
    Generate a unique purchase order number.

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

            next_number = 1

    else:

        next_number = 1

    return (
        f"{prefix}{next_number:04d}"
    )


def _validate_items(items_data):
    """
    Validate purchase order items.
    """

    if not items_data:
        raise ValueError(
            "At least one purchase order item is required."
        )

    cleaned_items = []

    for index, item in enumerate(items_data, start=1):

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
                f"Product / raw material is required "
                f"for item {index}."
            )

        product_name = product_name.strip()

        if not product_name:

            raise ValueError(
                f"Product / raw material is required "
                f"for item {index}."
            )

        try:
            quantity = float(quantity)
        except (TypeError, ValueError):

            raise ValueError(
                f"Invalid quantity for item {index}."
            )

        try:
            unit_price = float(unit_price)
        except (TypeError, ValueError):

            raise ValueError(
                f"Invalid unit price for item {index}."
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
                "total": quantity * unit_price,
            }
        )

    return cleaned_items


# ==================================================
# PURCHASE ORDER READ
# ==================================================


def get_all_purchase_orders():
    """
    Return purchase orders as dictionaries.

    Supplier and item information is explicitly loaded
    while the database session is open.

    This prevents DetachedInstanceError in Streamlit.
    """

    db = SessionLocal()

    try:

        purchase_orders = (
            db.query(PurchaseOrder)
            .options(
                joinedload(
                    PurchaseOrder.supplier
                ),
                joinedload(
                    PurchaseOrder.items
                ),
            )
            .order_by(
                PurchaseOrder.created_at.desc()
            )
            .all()
        )

        result = []

        for po in purchase_orders:

            supplier_name = (
                po.supplier.name
                if po.supplier
                else "Unknown Supplier"
            )

            items = []

            for item in po.items:

                items.append(
                    {
                        "id": item.id,
                        "product_name":
                            item.product_name,
                        "quantity":
                            float(
                                item.quantity or 0
                            ),
                        "unit_price":
                            float(
                                item.unit_price or 0
                            ),
                        "total":
                            float(
                                item.total or 0
                            ),
                    }
                )

            result.append(
                {
                    "id": po.id,
                    "po_number": po.po_number,
                    "supplier_id":
                        po.supplier_id,
                    "supplier_name":
                        supplier_name,
                    "status": po.status,
                    "total_amount":
                        float(
                            po.total_amount or 0
                        ),
                    "created_date": (
                        po.created_at.strftime(
                            "%Y-%m-%d"
                        )
                        if po.created_at
                        else ""
                    ),
                    "created_at":
                        po.created_at,
                    "items": items,
                }
            )

        return result

    finally:

        db.close()


def get_purchase_order(po_id):
    """
    Return one purchase order as a safe dictionary.
    """

    db = SessionLocal()

    try:

        po = (
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

        if not po:
            return None

        supplier_name = (
            po.supplier.name
            if po.supplier
            else "Unknown Supplier"
        )

        items = []

        for item in po.items:

            items.append(
                {
                    "id": item.id,
                    "product_name":
                        item.product_name,
                    "quantity":
                        float(
                            item.quantity or 0
                        ),
                    "unit_price":
                        float(
                            item.unit_price or 0
                        ),
                    "total":
                        float(
                            item.total or 0
                        ),
                }
            )

        return {
            "id": po.id,
            "po_number": po.po_number,
            "supplier_id":
                po.supplier_id,
            "supplier_name":
                supplier_name,
            "status":
                po.status,
            "total_amount":
                float(
                    po.total_amount or 0
                ),
            "created_date": (
                po.created_at.strftime(
                    "%Y-%m-%d"
                )
                if po.created_at
                else ""
            ),
            "created_at":
                po.created_at,
            "items":
                items,
        }

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
    Create a purchase order and its items.
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

            raise ValueError(
                "Selected supplier does not exist."
            )

        cleaned_items = _validate_items(
            items_data
        )

        total = sum(
            item["total"]
            for item in cleaned_items
        )

        po_number = _generate_po_number(db)

        purchase_order = PurchaseOrder(
            po_number=po_number,
            supplier_id=supplier_id,
            status=status,
            total_amount=total,
            created_at=datetime.utcnow(),
        )

        db.add(purchase_order)
        db.flush()

        for item in cleaned_items:

            purchase_order_item = (
                PurchaseOrderItem(
                    purchase_order_id=
                        purchase_order.id,
                    product_name=
                        item["product_name"],
                    quantity=
                        item["quantity"],
                    unit_price=
                        item["unit_price"],
                    total=
                        item["total"],
                )
            )

            db.add(
                purchase_order_item
            )

        db.commit()

        return {
            "id":
                purchase_order.id,
            "po_number":
                purchase_order.po_number,
            "supplier_id":
                purchase_order.supplier_id,
            "status":
                purchase_order.status,
            "total_amount":
                purchase_order.total_amount,
        }

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()


# ==================================================
# UPDATE PURCHASE ORDER
# ==================================================


def update_purchase_order(
    po_id,
    supplier_id=None,
    items_data=None,
    status=None,
):
    """
    Edit an existing purchase order.

    Existing purchase order items are replaced with the
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

        # ------------------------------------------
        # Supplier
        # ------------------------------------------

        if supplier_id is not None:

            supplier = (
                db.query(Supplier)
                .filter(
                    Supplier.id
                    == supplier_id
                )
                .first()
            )

            if not supplier:

                raise ValueError(
                    "Selected supplier does not exist."
                )

            purchase_order.supplier_id = (
                supplier_id
            )

        # ------------------------------------------
        # Status
        # ------------------------------------------

        if status is not None:

            purchase_order.status = status

        # ------------------------------------------
        # Items
        # ------------------------------------------

        if items_data is not None:

            cleaned_items = _validate_items(
                items_data
            )

            total = sum(
                item["total"]
                for item in cleaned_items
            )

            # Delete existing items.
            db.query(
                PurchaseOrderItem
            ).filter(
                PurchaseOrderItem.purchase_order_id
                == po_id
            ).delete(
                synchronize_session=False
            )

            # Add new items.
            for item in cleaned_items:

                purchase_order_item = (
                    PurchaseOrderItem(
                        purchase_order_id=
                            purchase_order.id,
                        product_name=
                            item["product_name"],
                        quantity=
                            item["quantity"],
                        unit_price=
                            item["unit_price"],
                        total=
                            item["total"],
                    )
                )

                db.add(
                    purchase_order_item
                )

            purchase_order.total_amount = (
                total
            )

        db.commit()

        return get_purchase_order(po_id)

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
    Change only the status of a purchase order.
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

        return get_purchase_order(
            po_id
        )

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()


# ==================================================
# DELETE PURCHASE ORDER
# ==================================================


def delete_purchase_order(po_id):
    """
    Delete a purchase order and all its items.
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

        # Delete purchase order items first.
        db.query(
            PurchaseOrderItem
        ).filter(
            PurchaseOrderItem.purchase_order_id
            == po_id
        ).delete(
            synchronize_session=False
        )

        db.delete(
            purchase_order
        )

        db.commit()

        return True

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()


# ==================================================
# PURCHASE ORDER SUMMARY
# ==================================================


def get_purchase_order_summary():
    """
    Return basic procurement KPIs.
    """

    db = SessionLocal()

    try:

        total_orders = (
            db.query(
                PurchaseOrder
            ).count()
        )

        total_value = (
            db.query(
                func.sum(
                    PurchaseOrder.total_amount
                )
            ).scalar()
            or 0
        )

        draft_orders = (
            db.query(
                PurchaseOrder
            )
            .filter(
                PurchaseOrder.status
                == "Draft"
            )
            .count()
        )

        pending_orders = (
            db.query(
                PurchaseOrder
            )
            .filter(
                PurchaseOrder.status
                == "Pending Approval"
            )
            .count()
        )

        approved_orders = (
            db.query(
                PurchaseOrder
            )
            .filter(
                PurchaseOrder.status
                == "Approved"
            )
            .count()
        )

        ordered_orders = (
            db.query(
                PurchaseOrder
            )
            .filter(
                PurchaseOrder.status
                == "Ordered"
            )
            .count()
        )

        received_orders = (
            db.query(
                PurchaseOrder
            )
            .filter(
                PurchaseOrder.status
                == "Received"
            )
            .count()
        )

        return {
            "total_orders":
                total_orders,

            "total_value":
                float(total_value),

            "draft_orders":
                draft_orders,

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