"""
Esan ERP Sales Service

Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Sales Services:
- Customer management
- Customer search
- Customer creation
- Customer editing
- Customer deletion
- Customer activation/deactivation
"""

from datetime import datetime

from database import SessionLocal
from models import Customer


# ==================================================
# CUSTOMER SERVICES
# ==================================================

def get_all_customers():
    """Return all customers ordered by name."""

    db = SessionLocal()

    try:
        return (
            db.query(Customer)
            .order_by(Customer.name.asc())
            .all()
        )

    finally:
        db.close()


def get_customer(customer_id):
    """Return one customer by ID."""

    db = SessionLocal()

    try:
        return (
            db.query(Customer)
            .filter(Customer.id == customer_id)
            .first()
        )

    finally:
        db.close()


def search_customers(search_term):
    """Search customers by name, phone, email or address."""

    db = SessionLocal()

    try:

        term = f"%{search_term.strip()}%"

        return (
            db.query(Customer)
            .filter(
                (Customer.name.ilike(term))
                | (Customer.phone.ilike(term))
                | (Customer.email.ilike(term))
                | (Customer.address.ilike(term))
            )
            .order_by(Customer.name.asc())
            .all()
        )

    finally:
        db.close()


def create_customer(
    name,
    phone=None,
    email=None,
    address=None,
    customer_type="Retail",
    location=None,
    country=None,
    contact_person=None,
):
    """Create a new customer."""

    if not name or not name.strip():
        raise ValueError(
            "Customer name is required."
        )

    db = SessionLocal()

    try:

        customer = Customer(
            name=name.strip(),
            phone=phone,
            email=email,
            address=address,
            customer_type=customer_type,
            location=location,
            country=country,
            contact_person=contact_person,
            created_at=datetime.utcnow(),
        )

        db.add(customer)

        db.commit()

        db.refresh(customer)

        return customer

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()


def update_customer(
    customer_id,
    name=None,
    phone=None,
    email=None,
    address=None,
    customer_type=None,
    location=None,
    country=None,
    contact_person=None,
):
    """Update an existing customer."""

    db = SessionLocal()

    try:

        customer = (
            db.query(Customer)
            .filter(Customer.id == customer_id)
            .first()
        )

        if not customer:
            return None

        if name is not None:
            if not name.strip():
                raise ValueError(
                    "Customer name cannot be empty."
                )

            customer.name = name.strip()

        if phone is not None:
            customer.phone = phone

        if email is not None:
            customer.email = email

        if address is not None:
            customer.address = address

        if customer_type is not None:
            customer.customer_type = customer_type

        if location is not None:
            customer.location = location

        if country is not None:
            customer.country = country

        if contact_person is not None:
            customer.contact_person = contact_person

        db.commit()

        db.refresh(customer)

        return customer

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()


def delete_customer(customer_id):
    """Delete a customer."""

    db = SessionLocal()

    try:

        customer = (
            db.query(Customer)
            .filter(Customer.id == customer_id)
            .first()
        )

        if not customer:
            return False

        db.delete(customer)

        db.commit()

        return True

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()


def set_customer_status(customer_id, active):
    """
    Activate or deactivate a customer.

    This function expects the Customer model to have
    an 'active' field.
    """

    db = SessionLocal()

    try:

        customer = (
            db.query(Customer)
            .filter(Customer.id == customer_id)
            .first()
        )

        if not customer:
            return None

        if hasattr(customer, "active"):
            customer.active = bool(active)
        else:
            raise AttributeError(
                "Customer model does not have an 'active' field."
            )

        db.commit()

        db.refresh(customer)

        return customer

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()