"""
Esan ERP - Delivery Service

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Version 1.4.0 Alpha

Responsibilities:
- Delivery Notes
- Sales Order fulfilment
- Delivery items
- Delivery status management
- Delivery number generation
- Delivery validation
"""

from datetime import date, datetime

from sqlalchemy.orm import joinedload

from database import SessionLocal
from models import (
    Delivery,
    SalesOrder,
    SalesOrderItem,
)


# ============================================================
# DELIVERY STATUSES
# ============================================================

DELIVERY_STATUSES = [
    "Draft",
    "Pending",
    "Dispatched",
    "Partially Delivered",
    "Delivered",
    "Cancelled",
]


# ============================================================
# INTERNAL HELPERS
# ============================================================

def _has_field(model, field_name):
    """Check whether a SQLAlchemy model contains a field."""

    return hasattr(
        model,
        field_name,
    )


def _set_if_exists(
    obj,
    field_name,
    value,
):
    """
    Set a model field only when that field exists.

    This keeps the service compatible with incremental
    database/model development.
    """

    if hasattr(
        obj,
        field_name,
    ):

        setattr(
            obj,
            field_name,
            value,
        )

        return True

    return False


def _generate_delivery_number(db):
    """
    Generate the next Delivery Note number.

    Format:

        DN-00001
        DN-00002
        DN-00003
    """

    last_delivery = (
        db.query(Delivery)
        .order_by(
            Delivery.id.desc()
        )
        .first()
    )

    if not last_delivery:

        next_number = 1

    else:

        existing_number = getattr(
            last_delivery,
            "delivery_number",
            None,
        )

        if not existing_number:

            existing_number = getattr(
                last_delivery,
                "dn_number",
                None,
            )

        try:

            next_number = (
                int(
                    str(
                        existing_number
                    ).split("-")[-1]
                )
                + 1
            )

        except (
            ValueError,
            TypeError,
        ):

            next_number = (
                last_delivery.id + 1
            )

    return (
        f"DN-{next_number:05d}"
    )


def _get_sales_order_item(
    db,
    item_id,
):
    """Return a Sales Order Item."""

    return (
        db.query(SalesOrderItem)
        .filter(
            SalesOrderItem.id
            == item_id
        )
        .first()
    )


# ============================================================
# DELIVERY RETRIEVAL
# ============================================================

def get_all_deliveries(
    status=None,
):
    """
    Return all Delivery Notes.

    Customer, Sales Order and delivery items are eagerly loaded
    where the relationships exist.
    """

    db = SessionLocal()

    try:

        options = []

        if hasattr(
            Delivery,
            "sales_order",
        ):

            options.append(
                joinedload(
                    Delivery.sales_order
                )
            )

        if hasattr(
            Delivery,
            "items",
        ):

            options.append(
                joinedload(
                    Delivery.items
                )
            )

        query = (
            db.query(Delivery)
            .options(*options)
        )

        if status:

            query = query.filter(
                Delivery.status
                == status
            )

        return (
            query
            .order_by(
                Delivery.id.desc()
            )
            .all()
        )

    finally:

        db.close()


def get_delivery(
    delivery_id,
):
    """
    Return one Delivery Note with its related data.
    """

    db = SessionLocal()

    try:

        options = []

        if hasattr(
            Delivery,
            "sales_order",
        ):

            options.append(
                joinedload(
                    Delivery.sales_order
                )
            )

        if hasattr(
            Delivery,
            "items",
        ):

            options.append(
                joinedload(
                    Delivery.items
                )
            )

        return (
            db.query(Delivery)
            .options(*options)
            .filter(
                Delivery.id
                == delivery_id
            )
            .first()
        )

    finally:

        db.close()


# ============================================================
# DELIVERY CREATION
# ============================================================

def create_delivery(
    sales_order_id,
    delivery_date=None,
    items=None,
    status="Draft",
    vehicle_number=None,
    driver_name=None,
    delivery_address=None,
    notes=None,
):
    """
    Create a Delivery Note against a Sales Order.

    Expected items format:

    [
        {
            "sales_order_item_id": 1,
            "product_name": "Maize Flour 25Kg",
            "quantity": 10,
            "unit_price": 50000,
            "total": 500000,
        }
    ]
    """

    if not items:

        raise ValueError(
            "At least one delivery item is required."
        )

    if status not in DELIVERY_STATUSES:

        raise ValueError(
            f"Invalid delivery status: {status}"
        )

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # Sales Order
        # ----------------------------------------------------

        sales_order = (
            db.query(SalesOrder)
            .options(
                joinedload(
                    SalesOrder.items
                )
            )
            .filter(
                SalesOrder.id
                == sales_order_id
            )
            .first()
        )

        if not sales_order:

            raise ValueError(
                "Sales Order not found."
            )

        if sales_order.status == "Cancelled":

            raise ValueError(
                "A cancelled Sales Order "
                "cannot be delivered."
            )

        # ----------------------------------------------------
        # Delivery
        # ----------------------------------------------------

        delivery_number = (
            _generate_delivery_number(db)
        )

        delivery_kwargs = {}

        # Required relationship
        delivery_kwargs[
            "sales_order_id"
        ] = sales_order_id

        # Number
        if _has_field(
            Delivery,
            "delivery_number",
        ):

            delivery_kwargs[
                "delivery_number"
            ] = delivery_number

        elif _has_field(
            Delivery,
            "dn_number",
        ):

            delivery_kwargs[
                "dn_number"
            ] = delivery_number

        # Status
        if _has_field(
            Delivery,
            "status",
        ):

            delivery_kwargs[
                "status"
            ] = status

        # Total
        if _has_field(
            Delivery,
            "total_amount",
        ):

            delivery_kwargs[
                "total_amount"
            ] = 0

        # Delivery date
        if (
            delivery_date is not None
            and _has_field(
                Delivery,
                "delivery_date",
            )
        ):

            delivery_kwargs[
                "delivery_date"
            ] = delivery_date

        # Vehicle
        if vehicle_number is not None:

            if _has_field(
                Delivery,
                "vehicle_number",
            ):

                delivery_kwargs[
                    "vehicle_number"
                ] = vehicle_number

            elif _has_field(
                Delivery,
                "vehicle",
            ):

                delivery_kwargs[
                    "vehicle"
                ] = vehicle_number

        # Driver
        if driver_name is not None:

            if _has_field(
                Delivery,
                "driver_name",
            ):

                delivery_kwargs[
                    "driver_name"
                ] = driver_name

            elif _has_field(
                Delivery,
                "driver",
            ):

                delivery_kwargs[
                    "driver"
                ] = driver_name

        # Address
        if delivery_address is not None:

            if _has_field(
                Delivery,
                "delivery_address",
            ):

                delivery_kwargs[
                    "delivery_address"
                ] = delivery_address

            elif _has_field(
                Delivery,
                "address",
            ):

                delivery_kwargs[
                    "address"
                ] = delivery_address

        # Notes
        if notes is not None:

            if _has_field(
                Delivery,
                "notes",
            ):

                delivery_kwargs[
                    "notes"
                ] = notes

        delivery = Delivery(
            **delivery_kwargs
        )

        db.add(delivery)

        db.flush()

        # ----------------------------------------------------
        # Create Delivery Items
        # ----------------------------------------------------

        total_amount = 0.0

        for item_data in items:

            quantity = float(
                item_data.get(
                    "quantity",
                    0,
                )
            )

            unit_price = float(
                item_data.get(
                    "unit_price",
                    0,
                )
            )

            if quantity <= 0:

                raise ValueError(
                    "Delivery quantity must "
                    "be greater than zero."
                )

            sales_order_item_id = (
                item_data.get(
                    "sales_order_item_id"
                )
            )

            sales_order_item = None

            if sales_order_item_id:

                sales_order_item = (
                    _get_sales_order_item(
                        db,
                        sales_order_item_id,
                    )
                )

                if not sales_order_item:

                    raise ValueError(
                        "Sales Order Item "
                        f"{sales_order_item_id} "
                        "was not found."
                    )

                if (
                    sales_order_item.sales_order_id
                    != sales_order_id
                ):

                    raise ValueError(
                        "Delivery item does not "
                        "belong to the selected "
                        "Sales Order."
                    )

                ordered_quantity = float(
                    sales_order_item.quantity
                    or 0
                )

                if quantity > ordered_quantity:

                    raise ValueError(
                        "Delivery quantity cannot "
                        "exceed the Sales Order "
                        "quantity."
                    )

            item_total = (
                quantity
                * unit_price
            )

            # ------------------------------------------------
            # Find Delivery Item model dynamically.
            # ------------------------------------------------

            delivery_item_model = None

            try:

                from models import DeliveryItem

                delivery_item_model = (
                    DeliveryItem
                )

            except ImportError:

                delivery_item_model = None

            if delivery_item_model:

                item_kwargs = {}

                # Delivery relationship
                if _has_field(
                    delivery_item_model,
                    "delivery_id",
                ):

                    item_kwargs[
                        "delivery_id"
                    ] = delivery.id

                # Sales Order Item
                if (
                    sales_order_item_id
                    and _has_field(
                        delivery_item_model,
                        "sales_order_item_id",
                    )
                ):

                    item_kwargs[
                        "sales_order_item_id"
                    ] = (
                        sales_order_item_id
                    )

                # Product
                if _has_field(
                    delivery_item_model,
                    "product_id",
                ):

                    item_kwargs[
                        "product_id"
                    ] = item_data.get(
                        "product_id"
                    )

                # Product name
                if _has_field(
                    delivery_item_model,
                    "product_name",
                ):

                    item_kwargs[
                        "product_name"
                    ] = item_data.get(
                        "product_name",
                        "",
                    )

                # Quantity
                if _has_field(
                    delivery_item_model,
                    "quantity",
                ):

                    item_kwargs[
                        "quantity"
                    ] = quantity

                # Unit price
                if _has_field(
                    delivery_item_model,
                    "unit_price",
                ):

                    item_kwargs[
                        "unit_price"
                    ] = unit_price

                # Total
                if _has_field(
                    delivery_item_model,
                    "total",
                ):

                    item_kwargs[
                        "total"
                    ] = item_total

                elif _has_field(
                    delivery_item_model,
                    "total_amount",
                ):

                    item_kwargs[
                        "total_amount"
                    ] = item_total

                delivery_item = (
                    delivery_item_model(
                        **item_kwargs
                    )
                )

                db.add(
                    delivery_item
                )

            total_amount += (
                item_total
            )

        # ----------------------------------------------------
        # Delivery total
        # ----------------------------------------------------

        if _has_field(
            Delivery,
            "total_amount",
        ):

            delivery.total_amount = (
                total_amount
            )

        elif _has_field(
            Delivery,
            "total",
        ):

            delivery.total = (
                total_amount
            )

        # ----------------------------------------------------
        # Update Sales Order status
        # ----------------------------------------------------

        if status == "Delivered":

            sales_order.status = (
                "Delivered"
            )

        elif status in [
            "Dispatched",
            "Pending",
            "Partially Delivered",
        ]:

            sales_order.status = (
                "Processing"
            )

        db.commit()

        db.refresh(
            delivery
        )

        return delivery

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()


# ============================================================
# DELIVERY STATUS
# ============================================================

def update_delivery_status(
    delivery_id,
    status,
):
    """
    Update a Delivery Note status.

    The related Sales Order is updated automatically.
    """

    if status not in DELIVERY_STATUSES:

        raise ValueError(
            f"Invalid delivery status: {status}"
        )

    db = SessionLocal()

    try:

        delivery = (
            db.query(Delivery)
            .options(
                joinedload(
                    Delivery.sales_order
                )
            )
            .filter(
                Delivery.id
                == delivery_id
            )
            .first()
        )

        if not delivery:

            return None

        delivery.status = status

        sales_order = getattr(
            delivery,
            "sales_order",
            None,
        )

        if sales_order:

            if status == "Delivered":

                sales_order.status = (
                    "Delivered"
                )

            elif status == "Cancelled":

                # Do not cancel the Sales Order
                # automatically. The Sales Order
                # may have other deliveries.
                pass

            elif status in [
                "Dispatched",
                "Pending",
                "Partially Delivered",
            ]:

                sales_order.status = (
                    "Processing"
                )

        db.commit()

        db.refresh(
            delivery
        )

        return delivery

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()


# ============================================================
# DELIVERY STATISTICS
# ============================================================

def get_delivery_statistics():
    """
    Return simple delivery statistics for dashboards.
    """

    db = SessionLocal()

    try:

        deliveries = (
            db.query(Delivery)
            .all()
        )

        total = len(
            deliveries
        )

        pending = len(
            [
                delivery
                for delivery in deliveries
                if delivery.status
                in [
                    "Draft",
                    "Pending",
                    "Dispatched",
                ]
            ]
        )

        partial = len(
            [
                delivery
                for delivery in deliveries
                if delivery.status
                == "Partially Delivered"
            ]
        )

        completed = len(
            [
                delivery
                for delivery in deliveries
                if delivery.status
                == "Delivered"
            ]
        )

        cancelled = len(
            [
                delivery
                for delivery in deliveries
                if delivery.status
                == "Cancelled"
            ]
        )

        return {
            "total": total,
            "pending": pending,
            "partially_delivered": partial,
            "completed": completed,
            "cancelled": cancelled,
        }

    finally:

        db.close()


# ============================================================
# DELETE DELIVERY
# ============================================================

def delete_delivery(
    delivery_id,
):
    """
    Delete a Delivery Note.

    Delivered documents should normally not be deleted
    in a production ERP. This function is therefore
    intended mainly for Draft documents.
    """

    db = SessionLocal()

    try:

        delivery = (
            db.query(Delivery)
            .filter(
                Delivery.id
                == delivery_id
            )
            .first()
        )

        if not delivery:

            return False

        if delivery.status == "Delivered":

            raise ValueError(
                "Delivered Delivery Notes "
                "cannot be deleted."
            )

        db.delete(
            delivery
        )

        db.commit()

        return True

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()