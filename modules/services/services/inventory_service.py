"""
Esan ERP Inventory Service
Nile Harvest Foods Ltd.

Handles:
- Product stock checking
- Stock reservation
- Stock movement recording
- Inventory updates
"""

from datetime import datetime

from database import SessionLocal

from models import (
    Product,
    StockMovement,
    StockReservation,
    SalesOrder
)



# =====================================
# PRODUCTS
# =====================================

def get_all_products():

    db = SessionLocal()

    try:

        return (
            db.query(Product)
            .order_by(Product.name)
            .all()
        )

    finally:

        db.close()



def get_product(product_id):

    db = SessionLocal()

    try:

        return (
            db.query(Product)
            .filter(
                Product.id == product_id
            )
            .first()
        )

    finally:

        db.close()



# =====================================
# STOCK CHECK
# =====================================

def check_stock(
        product_id,
        quantity
):

    db = SessionLocal()

    try:

        product = (
            db.query(Product)
            .filter(
                Product.id == product_id
            )
            .first()
        )


        if not product:

            return False


        return product.quantity >= quantity


    finally:

        db.close()



# =====================================
# RESERVE STOCK
# =====================================

def reserve_stock(
        sales_order_id,
        product_id,
        quantity
):

    db = SessionLocal()

    try:

        product = (
            db.query(Product)
            .filter(
                Product.id == product_id
            )
            .first()
        )


        if not product:

            raise Exception(
                "Product not found"
            )


        if product.quantity < quantity:

            raise Exception(
                "Insufficient stock"
            )



        reservation = StockReservation(

            sales_order_id=sales_order_id,

            product_id=product_id,

            quantity=quantity,

            status="Reserved"

        )


        db.add(reservation)


        movement = StockMovement(

            product_id=product_id,

            movement_type="Reservation",

            quantity=quantity,

            reference=f"SO-{sales_order_id}"

        )


        db.add(movement)


        db.commit()


        db.refresh(reservation)


        return reservation


    except Exception:

        db.rollback()

        raise


    finally:

        db.close()



# =====================================
# RELEASE RESERVED STOCK
# =====================================

def release_stock(
        reservation_id
):

    db = SessionLocal()

    try:

        reservation = (
            db.query(StockReservation)
            .filter(
                StockReservation.id == reservation_id
            )
            .first()
        )


        if reservation:

            reservation.status = "Released"


            db.commit()


            return reservation


    finally:

        db.close()



# =====================================
# CONFIRM STOCK USAGE
# =====================================

def deduct_stock(
        product_id,
        quantity,
        reference
):

    db = SessionLocal()

    try:

        product = (
            db.query(Product)
            .filter(
                Product.id == product_id
            )
            .first()
        )


        if not product:

            raise Exception(
                "Product not found"
            )


        if product.quantity < quantity:

            raise Exception(
                "Not enough stock"
            )


        product.quantity -= quantity



        movement = StockMovement(

            product_id=product_id,

            movement_type="OUT",

            quantity=quantity,

            reference=reference,

            created_at=datetime.utcnow()

        )


        db.add(movement)


        db.commit()


        return product


    except Exception:

        db.rollback()

        raise


    finally:

        db.close()



# =====================================
# STOCK ADDITION
# =====================================

def add_stock(
        product_id,
        quantity,
        reference="Purchase"
):

    db = SessionLocal()

    try:

        product = (
            db.query(Product)
            .filter(
                Product.id == product_id
            )
            .first()
        )


        if not product:

            raise Exception(
                "Product not found"
            )


        product.quantity += quantity



        movement = StockMovement(

            product_id=product_id,

            movement_type="IN",

            quantity=quantity,

            reference=reference

        )


        db.add(movement)


        db.commit()


        return product


    finally:

        db.close()



# =====================================
# INVENTORY SUMMARY
# =====================================

def inventory_summary():

    db = SessionLocal()

    try:

        products = (
            db.query(Product)
            .all()
        )


        return {

            "products": len(products),

            "total_quantity": sum(
                p.quantity or 0
                for p in products
            ),

            "inventory_value": sum(
                (p.quantity or 0)
                *
                (p.cost_price or 0)
                for p in products
            )

        }


    finally:

        db.close()