"""
Esan ERP
Customer Service

Business logic for customer management.
Nile Harvest Foods Ltd.
"""

from datetime import datetime

from models import Customer


def get_all_customers(db):
    """Return all customers ordered by newest first."""
    return (
        db.query(Customer)
        .order_by(Customer.id.desc())
        .all()
    )


def get_customer(db, customer_id):
    """Return a single customer."""
    return (
        db.query(Customer)
        .filter(Customer.id == customer_id)
        .first()
    )


def create_customer(
    db,
    name,
    phone=None,
    email=None,
    address=None,
    customer_type="Retail",
):
    """Create a new customer."""

    customer = Customer(
        name=name.strip(),
        phone=phone.strip() if phone else None,
        email=email.strip() if email else None,
        address=address.strip() if address else None,
        customer_type=customer_type,
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer


def update_customer(
    db,
    customer_id,
    name,
    phone=None,
    email=None,
    address=None,
    customer_type="Retail",
):
    """Update an existing customer."""

    customer = get_customer(db, customer_id)

    if not customer:
        return None

    customer.name = name.strip()
    customer.phone = phone.strip() if phone else None
    customer.email = email.strip() if email else None
    customer.address = address.strip() if address else None
    customer.customer_type = customer_type

    db.commit()
    db.refresh(customer)

    return customer


def delete_customer(db, customer_id):
    """
    Delete a customer.

    Returns False if the customer does not exist.
    """

    customer = get_customer(db, customer_id)

    if not customer:
        return False

    db.delete(customer)
    db.commit()

    return True