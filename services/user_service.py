from auth import hash_password
from models import User


def create_admin(db):

    existing = db.query(User).filter(
        User.username == "admin"
    ).first()


    if not existing:

        admin = User(
            username="admin",
            full_name="System Administrator",
            password_hash=hash_password(
                "admin123"
            ),
            role="Administrator"
        )

        db.add(admin)
        db.commit()