import asyncio
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.settings import settings
from app.db.session import SessionLocal
from app.db.models import User
from app.modules.auth.repository import AuthRepository
from app.modules.roles.repository import RoleRepository
from app.modules.roles.service import RoleService
from app.utils.bcrypt_util import BcryptUtil


async def seed_super_admin():
    db = SessionLocal()
    try:
        super_admin_email = settings.SUPER_ADMIN_EMAIL
        super_admin_password = settings.SUPER_ADMIN_PASSWORD

        if not super_admin_email or not super_admin_password:
            raise ValueError(
                "SUPERADMIN_EMAIL and SUPERADMIN_PASSWORD must be set in environment variables."
            )

        super_admin = db.query(User).filter_by(email=super_admin_email).first()
        if super_admin:
            print("Super admin already exists.")
            return

        auth_repo = AuthRepository(db)

        hashed_password = BcryptUtil.hash_password(super_admin_password)

        auth_repo.create_user(
            name="Super Admin",
            email=super_admin_email,
            hashed_password=hashed_password,
            is_super_admin=True,
        )

        print("Super admin seeded successfully.")

    except Exception as e:
        print(f"Error seeding super admin: {e}")
        raise
    finally:
        db.close()


async def seed_roles():
    db = SessionLocal()
    try:
        role_service = RoleService(RoleRepository(db))
        result = role_service.seed_default_roles()
        print(
            f"Roles seeded successfully. Created: {result['created']}, Updated: {result['updated']}."
        )
    except Exception as e:
        print(f"Error seeding roles: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(seed_super_admin())
    asyncio.run(seed_roles())