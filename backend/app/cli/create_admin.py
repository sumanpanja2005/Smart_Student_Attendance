import sys
import os
import getpass
from pathlib import Path
from datetime import datetime, timezone

# Ensure backend root directory is in Python path
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings
from app.db.mongo import db_manager
from app.core.security import hash_password


def create_admin():
    print("=" * 60)
    print(" Smart Attendance System - Initial Admin Bootstrap CLI")
    print("=" * 60)

    status = db_manager.connect()
    if status != "connected":
        print(
            f"ERROR: Cannot connect to MongoDB Atlas (Status: {status}). Please verify MONGODB_URI in .env"
        )
        sys.exit(1)

    db = db_manager.db

    # Check if an administrator already exists
    existing_admin = db.users.find_one({"role": "ADMIN"})
    if existing_admin:
        print(
            f"REFUSED: An Administrator account already exists ({existing_admin.get('email')})."
        )
        print(
            "For security reasons, creating duplicate admin accounts via CLI is prohibited."
        )
        sys.exit(0)

    # Read credentials from environment variables or prompt
    email = os.getenv("ADMIN_EMAIL")
    if not email:
        email = input("Enter Admin Email Address: ").strip()

    first_name = os.getenv("ADMIN_FIRST_NAME")
    if not first_name:
        first_name = input("Enter Admin First Name: ").strip()

    last_name = os.getenv("ADMIN_LAST_NAME")
    if not last_name:
        last_name = input("Enter Admin Last Name: ").strip()

    password = os.getenv("ADMIN_PASSWORD")
    if not password:
        password = getpass.getpass("Enter Admin Password (hidden): ").strip()
        confirm_pass = getpass.getpass("Confirm Admin Password (hidden): ").strip()
        if password != confirm_pass:
            print("ERROR: Passwords do not match. Aborting bootstrap.")
            sys.exit(1)

    if not email or not password or len(password) < 6:
        print(
            "ERROR: Valid Email address and Password (minimum 6 characters) are required."
        )
        sys.exit(1)

    now = datetime.now(timezone.utc)
    admin_user = {
        "email": email.lower(),
        "password_hash": hash_password(password),
        "role": "ADMIN",
        "first_name": first_name or "System",
        "last_name": last_name or "Administrator",
        "phone": None,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }

    try:
        res = db.users.insert_one(admin_user)
        print("=" * 60)
        print("SUCCESS: Administrator account created successfully!")
        print(f"User ID: {res.inserted_id}")
        print(f"Email:   {email.lower()}")
        print(f"Role:    ADMIN")
        print("=" * 60)
    except Exception as exc:
        print(f"ERROR: Failed to create admin user: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    create_admin()
