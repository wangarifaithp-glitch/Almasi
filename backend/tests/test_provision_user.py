import unittest

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.core.security import utc_naive_now, verify_password
from app.db.base import Base
from app.models import AuditLog, User
from app.provision_user import provision_staff_account


class StaffProvisioningTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)

    def tearDown(self) -> None:
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_provisions_staff_with_hashed_password_and_audit_record(self) -> None:
        user = provision_staff_account(
            self.db,
            name="  Facilitator  ",
            email="Staff@Example.org",
            role="facilitator",
            password="SecurePass9!",
        )

        self.assertEqual(user.name, "Facilitator")
        self.assertEqual(user.email, "staff@example.org")
        self.assertEqual(user.role, "facilitator")
        self.assertTrue(user.is_active)
        self.assertNotEqual(user.password_hash, "SecurePass9!")
        self.assertTrue(verify_password("SecurePass9!", user.password_hash))
        self.assertEqual(
            self.db.scalar(select(func.count()).select_from(AuditLog)),
            1,
        )

    def test_provisioning_existing_user_changes_role_and_revokes_sessions(self) -> None:
        user = User(
            name="Learner",
            email="staff@example.org",
            password_hash="old-hash",
            role="learner",
            is_active=False,
            session_version=4,
            created_at=utc_naive_now(),
        )
        self.db.add(user)
        self.db.commit()

        updated = provision_staff_account(
            self.db,
            name="Supervisor",
            email="staff@example.org",
            role="supervisor",
            password="SecurePass9!",
        )

        self.assertEqual(updated.id, user.id)
        self.assertEqual(updated.role, "supervisor")
        self.assertTrue(updated.is_active)
        self.assertEqual(updated.session_version, 5)
        self.assertTrue(verify_password("SecurePass9!", updated.password_hash))

    def test_public_learner_role_cannot_be_provisioned(self) -> None:
        with self.assertRaises(ValueError):
            provision_staff_account(
                self.db,
                name="Learner",
                email="learner@example.org",
                role="learner",
                password="SecurePass9!",
            )
        self.assertIsNone(self.db.scalar(select(User)))


if __name__ == "__main__":
    unittest.main()
