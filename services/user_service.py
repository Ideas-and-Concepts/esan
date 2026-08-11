from auth import hash_password
from models import User


def create_admin(db):

    admin = (
        db.query(User)
        .filter(User.username == "admin")
        .first()
    )

    if admin:
        return

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

def change_password(username, old_password, new_password):
    """
    Allow a user to change their own password by verifying the old one.
    Returns True if successful, False otherwise.
    """
    from auth import verify_password, hash_password
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return False
        if not verify_password(old_password, user.password_hash):
            return False
        user.password_hash = hash_password(new_password)
        db.commit()
        return True
    finally:
        db.close()