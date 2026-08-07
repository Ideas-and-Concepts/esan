"""
Esan ERP Procurement Service
Nile Harvest Foods Ltd.

Handles:
- Suppliers
- Purchase Orders
- Purchase Order Items
- Receiving agricultural materials
"""

from datetime import datetime

from database import SessionLocal

from models import (
    Supplier,
    PurchaseOrder,
    PurchaseOrderItem,
    Product,
    StockMovement
)



# =====================================
# SUPPLIERS
# =====================================

def get_all_suppliers():

    db = SessionLocal()

    try:

        return (
            db.query(Supplier)
            .order_by(Supplier.name)
            .all()
        )

    finally:

        db.close()



def create_supplier(
        name,
        phone=None,
        email=None,
        address=None,
        location=None,
        country=None
):

    db = SessionLocal()

    try:

        supplier = Supplier(

            name=name,

            phone=phone,

            email=email,

            address=address,

            location=location,

            country=country

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



# =====================================
# PURCHASE ORDERS
# =====================================

def get_all_purchase_orders():

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



def create_purchase_order(
        supplier_id,
        items
):

    db = SessionLocal()

    try:

        po_number = (
            "PO-"
            +
            datetime.now()
            .strftime("%Y%m%d%H%M%S")
        )


        total = 0


        purchase_order = PurchaseOrder(

            po_number=po_number,

            supplier_id=supplier_id,

            status="Draft",

            total_amount=0

        )


        db.add(purchase_order)

        db.flush()



        for item in items:

            item_total = (
                item["quantity"]
                *
                item["unit_price"]
            )


            total += item_total


            po_item = PurchaseOrderItem(

                purchase_order_id=
                purchase_order.id,

                product_name=
                item["product_name"],

                quantity=
                item["quantity"],

                unit_price=
                item["unit_price"],

                total=item_total

            )


            db.add(po_item)



        purchase_order.total_amount = total


        db.commit()

        db.refresh(purchase_order)


        return purchase_order



    except Exception:

        db.rollback()

        raise


    finally:

        db.close()



# =====================================
# UPDATE PURCHASE ORDER STATUS
# =====================================

def update_purchase_order_status(
        po_id,
        status
):

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


        po.status = status


        db.commit()

        db.refresh(po)


        return po


    finally:

        db.close()



# =====================================
# RECEIVE GOODS INTO INVENTORY
# =====================================

def receive_purchase_order(
        po_id
):

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

            raise Exception(
                "Purchase order not found"
            )


        items = (
            db.query(PurchaseOrderItem)
            .filter(
                PurchaseOrderItem.purchase_order_id
                ==
                po.id
            )
            .all()
        )


        for item in items:


            product = (
                db.query(Product)
                .filter(
                    Product.name ==
                    item.product_name
                )
                .first()
            )


            if product:

                product.quantity += item.quantity


            else:

                product = Product(

                    name=item.product_name,

                    quantity=item.quantity,

                    cost_price=item.unit_price

                )

                db.add(product)

                db.flush()



            movement = StockMovement(

                product_id=product.id,

                movement_type="IN",

                quantity=item.quantity,

                reference=po.po_number,

                created_at=datetime.utcnow()

            )


            db.add(movement)



        po.status = "Received"


        db.commit()


        return po



    except Exception:

        db.rollback()

        raise


    finally:

        db.close()