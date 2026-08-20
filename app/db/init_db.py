"""Creates tables and seeds a default admin account.

Usage:
    python -m app.db.init_db
"""
from app.core.security import hash_password
from app.db.base import Base, SessionLocal, engine
from app.models.user import User  # noqa: F401  (importing models registers them)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        if db.query(User).filter(User.role == "admin").first() is None:
            admin = User(
                full_name="System Administrator",
                email="admin@bookstore.com",
                username="admin",
                hashed_password=hash_password("admin123"),
                role="admin",
            )
            db.add(admin)
            db.commit()
            print("[OK] Admin account created: admin@bookstore.com / admin123")
        else:
            print("[INFO] Admin account already exists")
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
