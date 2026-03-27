import asyncio

from app.core.settings import settings
from app.db.session import SessionLocal
from app.db.models import User
from app.modules.auth.repository import AuthRepository
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


if __name__ == "__main__":
    asyncio.run(seed_super_admin())