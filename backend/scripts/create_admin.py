import sys
import os
import argparse

# Add parent directory to path so app modules can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal
from app.models import User
from app.utils.auth import get_password_hash, verify_password

def create_or_update_admin(name: str, email: str, password: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(email=email.strip().lower()).first()
        if user:
            print(f"User with email '{email}' already exists (Current Role: {user.role}).")
            user.role = "ADMIN"
            user.name = name.strip() or user.name
            if password:
                user.password_hash = get_password_hash(password.strip())
            db.commit()
            db.refresh(user)
            print(f"[SUCCESS] User '{user.email}' has been updated to ADMIN role.")
        else:
            if not password:
                print("[ERROR] Password is required to create a new admin user.")
                return False
            pwd_hash = get_password_hash(password.strip())
            new_admin = User(
                name=name.strip(),
                email=email.strip().lower(),
                password_hash=pwd_hash,
                role="ADMIN"
            )
            db.add(new_admin)
            db.commit()
            db.refresh(new_admin)
            print(f"[SUCCESS] New ADMIN user '{new_admin.name}' ({new_admin.email}) created successfully.")
        
        print("\n==================================================")
        print("  ADMIN CREDENTIALS")
        print("==================================================")
        print(f"  Name:     {name}")
        print(f"  Email:    {email.strip().lower()}")
        print(f"  Password: {password}")
        print(f"  Role:     ADMIN")
        print("==================================================")
        return True
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Failed to create/update admin user: {e}")
        return False
    finally:
        db.close()

def main():
    parser = argparse.ArgumentParser(description="Create or upgrade an Admin user for INGRES AI.")
    parser.add_argument("--name", type=str, default=None, help="Full Name of the admin")
    parser.add_argument("--email", type=str, default=None, help="Email address of the admin")
    parser.add_argument("--password", type=str, default=None, help="Password for the admin")

    args = parser.parse_args()

    name = args.name
    email = args.email
    password = args.password

    # Interactive prompt if parameters are omitted
    if not email:
        email = input("Enter Admin Email (e.g. admin@ingres.gov.in): ").strip()
    if not name:
        name = input("Enter Admin Full Name (default: INGRES Administrator): ").strip() or "INGRES Administrator"
    if not password:
        password = input("Enter Admin Password: ").strip()

    if not email or not password:
        print("[ERROR] Email and Password cannot be empty.")
        sys.exit(1)

    success = create_or_update_admin(name, email, password)
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
