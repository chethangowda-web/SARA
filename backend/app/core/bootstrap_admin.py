import asyncio
import os
import sys
import getpass
import argparse
from sqlalchemy.future import select

# Set python path to allow imports of app module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.models.staff_authorization import StaffAuthorization

async def bootstrap_admin(email: str, password: str):
    email = email.lower().strip()
    
    async with SessionLocal() as db:
        # 1. Ensure StaffAuthorization exists for the admin
        res_auth = await db.execute(select(StaffAuthorization).where(StaffAuthorization.email == email))
        auth = res_auth.scalars().first()
        if not auth:
            auth = StaffAuthorization(
                email=email,
                role=UserRole.ADMIN,
                is_active=True
            )
            db.add(auth)
            print(f"[BOOTSTRAP] Added staff authorization for {email} as ADMIN")
        else:
            auth.role = UserRole.ADMIN
            auth.is_active = True
            auth.revoked_at = None
            print(f"[BOOTSTRAP] Staff authorization for {email} already exists. Enforced ADMIN role.")

        # 2. Ensure User account exists
        res_user = await db.execute(select(User).where(User.email == email))
        user = res_user.scalars().first()
        if not user:
            user = User(
                email=email,
                full_name="System Administrator",
                password_hash=hash_password(password),
                role=UserRole.ADMIN,
                is_active=True,
                email_verified=True,
                auth_provider="credentials"
            )
            db.add(user)
            print(f"[BOOTSTRAP] Created User account for {email}")
        else:
            user.password_hash = hash_password(password)
            user.role = UserRole.ADMIN
            user.is_active = True
            user.email_verified = True
            print(f"[BOOTSTRAP] User account for {email} already exists. Updated password to new hashed value.")
            
        await db.commit()
        print(f"[BOOTSTRAP] Success: Securely bootstrapped Administrator {email}.")

def main():
    parser = argparse.ArgumentParser(description="Secure SARA Administrator Bootstrapping tool")
    parser.add_argument("--email", type=str, default="iamchethen2813@gmail.com", help="Email for the administrator")
    parser.add_argument("--password", type=str, help="Password for the administrator (optional, defaults to prompt or env)")
    
    args = parser.parse_args()
    
    email = args.email
    password = args.password or os.getenv("ADMIN_PASSWORD")
    
    if not password:
        if sys.stdin.isatty():
            password = getpass.getpass("Enter password for administrator: ")
            confirm = getpass.getpass("Confirm password: ")
            if password != confirm:
                print("Error: Passwords do not match.")
                sys.exit(1)
        else:
            # Non-interactive fallback
            print("Error: Running in non-interactive shell and no password was provided via environment variable ADMIN_PASSWORD or --password argument.")
            sys.exit(1)
            
    if len(password) < 12:
        print("Error: Password must be at least 12 characters.")
        sys.exit(1)
        
    asyncio.run(bootstrap_admin(email, password))

if __name__ == "__main__":
    main()
