"""
Esan ERP User Service
Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System
"""

from database import SessionLocal
from models import User
from auth import hash_password, verify_password


# ============================================================
# CREATE DEFAULT ADMINISTRATOR
# ============================================================

def create_admin(db):
    """
    Create the default Esan ERP administrator if one
    does not already exist.

    Default credentials:
        Username: admin
        Password: admin123
    """

    admin = (
        db.query(User)
        .filter(User.username == "admin")
        .first()
    )

    if admin:
        return admin

    admin = User(
        username="admin",
        full_name="System Administrator",
        email="admin@nileharvest.com",
        password_hash=hash_password("admin123"),
        role="Administrator",
        active=True,
    )

    db.add(admin)
    db.commit()
    db.refresh(admin)

    return admin


# ============================================================
# CHANGE PASSWORD
# ============================================================

def change_password(
    username: str,
    old_password: str,
    new_password: str,
) -> bool:
    """
    Allow a user to change their own password.

    The old password must be verified before the new
    password is saved.

    Returns:
        True  -> password changed successfully
        False -> operation failed
    """

    db = SessionLocal()

    try:
        user = (
            db.query(User)
            .filter(User.username == username)
            .first()
        )

        # User does not exist
        if not user:
            return False

        # Verify current password
        if not verify_password(
            old_password,
            user.password_hash,
        ):
            return False

        # Basic validation
        if not new_password:
            return False

        if len(new_password) < 6:
            return False

        # Update password
        user.password_hash = hash_password(
            new_password
        )

        db.commit()

        return True

    except Exception:
        db.rollback()
        return False

    finally:
        db.close()