"""End-to-end functional test for the Book Store API.

Runs against a local SQLite database (no Postgres needed):
  1. Create tables
  2. Register a regular user + login
  3. Verify a regular user CANNOT create products (403)
  4. Seed an admin, login as admin
  5. Admin creates/updates/lists/deletes a product and a service
  6. Public listing endpoints
  7. Contact form + forgot/reset password flow
"""
import os

# Force a local SQLite database BEFORE importing the app
DB_FILE = "./_test_bookstore.db"
if os.path.exists(DB_FILE):
    os.remove(DB_FILE)
os.environ["DATABASE_URL"] = f"sqlite:///{DB_FILE}"
os.environ["SECRET_KEY"] = "test-secret-key"

import sys  # noqa: E402
from pathlib import Path  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.db.base import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import User  # noqa: E402

# Ensure tables exist (TestClient triggers lifespan too, but be explicit)
Base.metadata.create_all(bind=engine)

# Seed an admin account
db = SessionLocal()
if db.query(User).filter(User.role == "admin").first() is None:
    db.add(User(
        full_name="Admin",
        email="admin@test.com",
        username="admin",
        hashed_password=hash_password("admin123"),
        role="admin",
    ))
    db.commit()
db.close()

client = TestClient(app)

failures = []


def check(name, cond, extra=""):
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {name} {extra}")
    if not cond:
        failures.append(name)


# 1. Health
r = client.get("/health")
check("health endpoint", r.status_code == 200 and r.json()["status"] == "ok")

# 2. Register user
r = client.post("/api/v1/auth/register", json={
    "full_name": "John Doe",
    "email": "john@test.com",
    "username": "johndoe",
    "password": "secret123",
})
check("register user", r.status_code == 201, f"got {r.status_code}: {r.text[:200]}")

# 3. Duplicate email rejected
r = client.post("/api/v1/auth/register", json={
    "full_name": "John Doe",
    "email": "john@test.com",
    "username": "johndoe2",
    "password": "secret123",
})
check("duplicate email rejected", r.status_code == 400)

# 4. Login as user (form data)
r = client.post("/api/v1/auth/login", data={"username": "john@test.com", "password": "secret123"})
check("user login", r.status_code == 200 and "access_token" in r.json())
user_token = r.json()["access_token"]

# 5. Auth /me
r = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {user_token}"})
check("auth/me", r.status_code == 200 and r.json()["email"] == "john@test.com")

# 6. Regular user blocked from creating product (403)
r = client.post("/api/v1/products", headers={"Authorization": f"Bearer {user_token}"}, json={
    "name": "Hacked Product", "price": 1.0,
})
check("user cannot create product (403)", r.status_code == 403, f"got {r.status_code}")

# 7. Unauthenticated product create (401)
r = client.post("/api/v1/products", json={"name": "X", "price": 1.0})
check("anon cannot create product (401)", r.status_code == 401)

# 8. Admin login
r = client.post("/api/v1/auth/login", data={"username": "admin@test.com", "password": "admin123"})
check("admin login", r.status_code == 200)
admin_token = r.json()["access_token"]
admin_headers = {"Authorization": f"Bearer {admin_token}"}

# 9. Admin creates product
r = client.post("/api/v1/products", headers=admin_headers, json={
    "name": "C Programming Book",
    "description": "Learn C",
    "price": 12.5,
    "stock": 10,
})
check("admin create product", r.status_code == 201, f"got {r.status_code}: {r.text[:200]}")
product_id = r.json().get("id") if r.status_code == 201 else None

# 10. Admin updates product
r = client.put(f"/api/v1/products/{product_id}", headers=admin_headers, json={"price": 15.0})
check("admin update product", r.status_code == 200 and r.json()["price"] == 15.0)

# 11. Public product list
r = client.get("/api/v1/products")
check("public product list", r.status_code == 200 and r.json()["total"] == 1)

# 12. Admin creates service
r = client.post("/api/v1/services", headers=admin_headers, json={
    "title": "Web Design",
    "price": 99.0,
    "duration": "7 days",
})
check("admin create service", r.status_code == 201)
service_id = r.json().get("id")

# 13. Public service list
r = client.get("/api/v1/services")
check("public service list", r.status_code == 200 and r.json()["total"] == 1)

# 14. Contact form
r = client.post("/api/v1/contacts", json={
    "name": "Jane",
    "email": "jane@test.com",
    "subject": "Hello",
    "message": "I want to know more",
})
check("submit contact", r.status_code == 201)

# 15. Admin dashboard stats
r = client.get("/api/v1/dashboard/stats", headers=admin_headers)
check("dashboard stats", r.status_code == 200
      and r.json()["total_users"] == 2
      and r.json()["total_products"] == 1
      and r.json()["total_services"] == 1
      and r.json()["total_contacts"] == 1)

# 16. Admin deletes product
r = client.delete(f"/api/v1/products/{product_id}", headers=admin_headers)
check("admin delete product", r.status_code == 200)

# 17. Forgot password (demo token)
r = client.post("/api/v1/auth/forgot-password", json={"email": "john@test.com"})
check("forgot password returns token", r.status_code == 200 and r.json().get("reset_token"))
reset_token = r.json().get("reset_token")

# 18. Reset password with token
r = client.post("/api/v1/auth/reset-password", json={
    "token": reset_token,
    "new_password": "newsecret456",
})
check("reset password", r.status_code == 200)

# 19. Login with new password
r = client.post("/api/v1/auth/login", data={"username": "john@test.com", "password": "newsecret456"})
check("login with new password", r.status_code == 200)

# 20. User list admin only
r = client.get("/api/v1/users", headers=admin_headers)
check("admin list users", r.status_code == 200 and r.json()["total"] == 2)
r = client.get("/api/v1/users", headers={"Authorization": f"Bearer {user_token}"})
check("user blocked from user list (403)", r.status_code == 403)

print()
if failures:
    print(f"RESULT: {len(failures)} FAILURES -> {failures}")
    sys.exit(1)
else:
    print("RESULT: ALL CHECKS PASSED (20/20)")
    sys.exit(0)


