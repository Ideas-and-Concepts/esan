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