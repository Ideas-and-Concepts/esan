"""
Esan ERP Procurement Service

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Handles:
- Suppliers
- Purchase Orders
- Purchases / Receiving
- Status management
- Edit / Delete operations
"""

from datetime import datetime

from sqlalchemy.orm import joinedload

from database import SessionLocal

from models import (
    Supplier,
    PurchaseOrder,
    PurchaseOrderItem,
    Purchase,
    PurchaseItem,
)


# ==================================================
# SUPPLIERS
# ==================================================

def get_all_suppliers():
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
    db = SessionLocal()

    try:

        supplier = (
            db.query(Supplier)
            .filter(Supplier.id == supplier_id)
            .first()
        )

        if not supplier:
            return False

        existing_po = (
            db.query(PurchaseOrder)
            .filter(
                PurchaseOrder.supplier_id == supplier_id
            )
            .first()
        )

        existing_purchase = (
            db.query(Purchase)
            .filter(
                Purchase.supplier_id == supplier_id
            )
            .first()
        )

        if existing_po or existing_purchase:
            raise ValueError(
                "This supplier cannot be deleted because "
                "purchase records already exist for this supplier."
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
    db = SessionLocal()

    try:

        return (
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

    finally:
        db.close()


def get_purchase_order(po_id):
    db = SessionLocal()

    try:

        return (
            db.query(PurchaseOrder)
            .options(
                joinedload(PurchaseOrder.supplier),
                joinedload(PurchaseOrder.items),
            )
            .filter(PurchaseOrder.id == po_id)
            .first()
        )

    finally:
        db.close()


def create_purchase_order(
    supplier_id,
    items_data,
    status="Draft",
):
    db = SessionLocal()

    try:

        if not items_data:
            raise ValueError(
                "Purchase Order must contain at least one item."
            )

        total = sum(
            float(item["quantity"])
            * float(item["unit_price"])
            for item in items_data
        )

        count = db.query(
            PurchaseOrder
        ).count()

        po_number = (
            f"PO-"
            f"{datetime.utcnow().strftime('%Y%m%d')}-"
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
                item["quantity"]
            )

            unit_price = float(
                item["unit_price"]
            )

            purchase_order_item = PurchaseOrderItem(
                purchase_order_id=purchase_order.id,
                product_name=item["product_name"],
                quantity=quantity,
                unit_price=unit_price,
                total=quantity * unit_price,
            )

            db.add(purchase_order_item)

        db.commit()

        db.refresh(purchase_order)

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

        return purchase_order

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def delete_purchase_order(po_id):
    db = SessionLocal()

    try:

        purchase_order = (
            db.query(PurchaseOrder)
            .filter(PurchaseOrder.id == po_id)
            .first()
        )

        if not purchase_order:
            return False

        existing_purchase = (
            db.query(Purchase)
            .filter(
                Purchase.purchase_order_id == po_id
            )
            .first()
        )

        if existing_purchase:
            raise ValueError(
                "This Purchase Order cannot be deleted "
                "because a purchase/receiving record is linked to it."
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
# PURCHASES / RECEIVING
# ==================================================

def get_all_purchases():
    db = SessionLocal()

    try:

        return (
            db.query(Purchase)
            .options(
                joinedload(Purchase.supplier),
                joinedload(Purchase.purchase_order),
                joinedload(Purchase.items),
            )
            .order_by(
                Purchase.created_at.desc()
            )
            .all()
        )

    finally:
        db.close()


def get_purchase(purchase_id):
    db = SessionLocal()

    try:

        return (
            db.query(Purchase)
            .options(
                joinedload(Purchase.supplier),
                joinedload(Purchase.purchase_order),
                joinedload(Purchase.items),
            )
            .filter(Purchase.id == purchase_id)
            .first()
        )

    finally:
        db.close()


def create_purchase(
    supplier_id,
    items_data,
    purchase_order_id=None,
    status="Received",
    received_date=None,
    warehouse=None,
    notes=None,
):
    db = SessionLocal()

    try:

        if not items_data:
            raise ValueError(
                "Purchase must contain at least one item."
            )

        total = sum(
            float(item["quantity"])
            * float(item["unit_price"])
            for item in items_data
        )

        count = db.query(Purchase).count()

        purchase_number = (
            f"PUR-"
            f"{datetime.utcnow().strftime('%Y%m%d')}-"
            f"{count + 1:04d}"
        )

        purchase = Purchase(
            purchase_number=purchase_number,
            purchase_order_id=purchase_order_id,
            supplier_id=supplier_id,
            status=status,
            total_amount=total,
            received_date=(
                received_date
                or datetime.utcnow()
            ),
            warehouse=warehouse,
            notes=notes,
            created_at=datetime.utcnow(),
        )

        db.add(purchase)
        db.flush()

        for item in items_data:

            quantity = float(
                item["quantity"]
            )

            unit_price = float(
                item["unit_price"]
            )

            purchase_item = PurchaseItem(
                purchase_id=purchase.id,
                product_name=item["product_name"],
                quantity=quantity,
                unit_price=unit_price,
                total=quantity * unit_price,
            )

            db.add(purchase_item)

        db.commit()

        db.refresh(purchase)

        return purchase

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def update_purchase_status(
    purchase_id,
    new_status,
):
    db = SessionLocal()

    try:

        purchase = (
            db.query(Purchase)
            .filter(Purchase.id == purchase_id)
            .first()
        )

        if not purchase:
            return None

        purchase.status = new_status

        db.commit()
        db.refresh(purchase)

        return purchase

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def update_purchase(
    purchase_id,
    supplier_id,
    items_data,
    purchase_order_id=None,
    status="Received",
    received_date=None,
    warehouse=None,
    notes=None,
):
    db = SessionLocal()

    try:

        purchase = (
            db.query(Purchase)
            .options(
                joinedload(Purchase.items)
            )
            .filter(Purchase.id == purchase_id)
            .first()
        )

        if not purchase:
            return None

        if not items_data:
            raise ValueError(
                "Purchase must contain at least one item."
            )

        total = sum(
            float(item["quantity"])
            * float(item["unit_price"])
            for item in items_data
        )

        purchase.supplier_id = supplier_id
        purchase.purchase_order_id = purchase_order_id
        purchase.status = status
        purchase.total_amount = total
        purchase.received_date = (
            received_date
            or purchase.received_date
        )
        purchase.warehouse = warehouse
        purchase.notes = notes

        purchase.items.clear()

        for item in items_data:

            quantity = float(
                item["quantity"]
            )

            unit_price = float(
                item["unit_price"]
            )

            purchase.items.append(
                PurchaseItem(
                    product_name=item["product_name"],
                    quantity=quantity,
                    unit_price=unit_price,
                    total=quantity * unit_price,
                )
            )

        db.commit()
        db.refresh(purchase)

        return purchase

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def delete_purchase(purchase_id):
    db = SessionLocal()

    try:

        purchase = (
            db.query(Purchase)
            .filter(Purchase.id == purchase_id)
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