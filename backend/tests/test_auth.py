import os
import unittest
from datetime import timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import parse_qs, urlparse

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("AUTH_SECRET_KEY", "test-secret-not-for-production-32-bytes")
os.environ.setdefault("RESEND_API_KEY", "test-resend-key")
os.environ.setdefault("RESEND_FROM_EMAIL", "ALMASI <accounts@example.test>")

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.routes import auth as auth_routes
from app.core.config import BACKEND_ENV_FILE, Settings, get_settings
from app.core.security import utc_naive_now
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import PasswordResetToken, User

TEST_SETTINGS = Settings(
    database_url="sqlite://",
    auth_secret_key="test-secret-not-for-production-32-bytes",
    resend_api_key="test-resend-key",
    resend_from_email="ALMASI <accounts@example.test>",
    cors_origins="http://testserver",
    app_base_url="http://testserver",
    app_env="test",
)
TEST_ORIGIN = {"Origin": "http://testserver"}
STRONG_PASSWORD = "StrongPass9!"


class AuthenticationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(cls.engine)
        cls.session_factory = sessionmaker(
            bind=cls.engine, autoflush=False, autocommit=False
        )

    @classmethod
    def tearDownClass(cls) -> None:
        Base.metadata.drop_all(cls.engine)
        cls.engine.dispose()

    def setUp(self) -> None:
        self.db = self.session_factory()
        self.db.query(PasswordResetToken).delete()
        self.db.query(User).delete()
        self.db.commit()

        def override_db():
            yield self.db

        app.dependency_overrides[get_db] = override_db
        app.dependency_overrides[get_settings] = lambda: TEST_SETTINGS
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.client.close()
        self.db.close()
        app.dependency_overrides.clear()

    def register(self, **extra: object):
        payload = {
            "name": "Learner",
            "email": "learner@example.com",
            "password": STRONG_PASSWORD,
            **extra,
        }
        return self.client.post(
            "/api/v1/auth/register", headers=TEST_ORIGIN, json=payload
        )

    def test_signup_hashes_password_and_never_accepts_self_assigned_role(self) -> None:
        response = self.register(role="supervisor")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["role"], "learner")
        self.assertNotIn("password_hash", response.json())
        self.assertNotIn(STRONG_PASSWORD, response.text)
        self.assertIn("httponly", response.headers["set-cookie"].lower())
        user = self.db.scalar(select(User))
        self.assertIsNotNone(user)
        self.assertNotEqual(user.password_hash, STRONG_PASSWORD)
        self.assertTrue(user.password_hash.startswith("$argon2"))

    def test_health_registration_login_and_current_user_flow(self) -> None:
        health = self.client.get("/api/v1/health")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(
            health.json(), {"status": "healthy", "database": "connected"}
        )

        registration = self.register()
        self.assertEqual(registration.status_code, 201)
        self.assertEqual(registration.json()["role"], "learner")
        self.assertNotIn("password_hash", registration.json())

        current_user = self.client.get("/api/v1/auth/me")
        self.assertEqual(current_user.status_code, 200)
        self.assertEqual(current_user.json()["email"], "learner@example.com")
        self.assertNotIn("password_hash", current_user.json())

        self.client.post("/api/v1/auth/logout", headers=TEST_ORIGIN)
        login = self.client.post(
            "/api/v1/auth/login",
            headers=TEST_ORIGIN,
            json={"email": "learner@example.com", "password": STRONG_PASSWORD},
        )
        self.assertEqual(login.status_code, 200)
        self.assertEqual(login.json()["role"], "learner")
        self.assertEqual(self.client.get("/api/v1/auth/me").status_code, 200)

    def test_cors_allows_configured_frontend_credentials(self) -> None:
        response = self.client.options(
            "/api/v1/auth/login",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers["access-control-allow-origin"], "http://localhost:5173"
        )
        self.assertEqual(response.headers["access-control-allow-credentials"], "true")

    def test_health_reports_missing_database_tables(self) -> None:
        empty_engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}
        )
        empty_session_factory = sessionmaker(bind=empty_engine)

        def override_db():
            with empty_session_factory() as db:
                yield db

        app.dependency_overrides[get_db] = override_db
        try:
            response = self.client.get("/api/v1/health")
        finally:
            app.dependency_overrides[get_db] = lambda: self.db
            empty_engine.dispose()

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["database"], "not_ready")
        self.assertIn("users", response.json()["missing_tables"])

    def test_health_reports_mysql_access_denied_without_secrets(self) -> None:
        unavailable_database = MagicMock()
        unavailable_database.execute.side_effect = OperationalError(
            "SELECT 1",
            {},
            Exception(1045, "Access denied for secret-user using secret-value"),
        )

        def unavailable_db():
            yield unavailable_database

        app.dependency_overrides[get_db] = unavailable_db
        try:
            response = self.client.get("/api/v1/health")
        finally:
            app.dependency_overrides[get_db] = lambda: self.db

        self.assertEqual(response.status_code, 503)
        self.assertIn("permitted host", response.json()["detail"])
        self.assertNotIn("secret-user", response.text)
        self.assertNotIn("secret-value", response.text)

    def test_backend_dotenv_path_is_independent_of_working_directory(self) -> None:
        self.assertEqual(
            BACKEND_ENV_FILE,
            (Path(__file__).resolve().parents[1] / ".env"),
        )

    def test_signup_rejects_weak_passwords_and_duplicate_accounts(self) -> None:
        weak = self.register(password="abcdefg1")
        self.assertEqual(weak.status_code, 422)

        self.assertEqual(self.register().status_code, 201)
        duplicate = self.register()
        self.assertEqual(duplicate.status_code, 409)

    def test_login_requires_trusted_origin_and_returns_only_user_profile(self) -> None:
        self.register()
        bad_origin = self.client.post(
            "/api/v1/auth/login",
            headers={"Origin": "https://untrusted.example"},
            json={"email": "learner@example.com", "password": STRONG_PASSWORD},
        )
        self.assertEqual(bad_origin.status_code, 403)

        login = self.client.post(
            "/api/v1/auth/login",
            headers=TEST_ORIGIN,
            json={"email": "learner@example.com", "password": STRONG_PASSWORD},
        )
        self.assertEqual(login.status_code, 200)
        self.assertEqual(login.json()["role"], "learner")
        self.assertNotIn("password_hash", login.json())

    def test_unknown_and_known_email_reset_responses_are_indistinguishable(self) -> None:
        self.register()
        unknown = self.client.post(
            "/api/v1/auth/forgot-password",
            headers=TEST_ORIGIN,
            json={"email": "unknown@example.com"},
        )
        with patch.object(auth_routes, "send_password_reset_email", new_callable=AsyncMock):
            known = self.client.post(
                "/api/v1/auth/forgot-password",
                headers=TEST_ORIGIN,
                json={"email": "learner@example.com"},
            )
        self.assertEqual(unknown.status_code, 200)
        self.assertEqual(known.status_code, 200)
        self.assertEqual(unknown.json(), known.json())

    def test_reset_token_is_single_use_expires_and_revokes_sessions(self) -> None:
        self.register()
        with patch.object(
            auth_routes, "send_password_reset_email", new_callable=AsyncMock
        ) as send_email:
            request = self.client.post(
                "/api/v1/auth/forgot-password",
                headers=TEST_ORIGIN,
                json={"email": "learner@example.com"},
            )
            self.assertEqual(request.status_code, 200)
            reset_url = send_email.await_args.args[3]

        token = parse_qs(urlparse(reset_url).query)["token"][0]
        changed = self.client.post(
            "/api/v1/auth/reset-password",
            headers=TEST_ORIGIN,
            json={"token": token, "password": "NewPass9!Secure"},
        )
        self.assertEqual(changed.status_code, 200)
        self.assertEqual(self.client.get("/api/v1/auth/me").status_code, 401)
        replay = self.client.post(
            "/api/v1/auth/reset-password",
            headers=TEST_ORIGIN,
            json={"token": token, "password": "OtherPass9!Secure"},
        )
        self.assertEqual(replay.status_code, 400)
        login = self.client.post(
            "/api/v1/auth/login",
            headers=TEST_ORIGIN,
            json={"email": "learner@example.com", "password": "NewPass9!Secure"},
        )
        self.assertEqual(login.status_code, 200)

        token_record = self.db.scalar(select(PasswordResetToken))
        token_record.expires_at = utc_naive_now() - timedelta(seconds=1)
        self.db.commit()
        expired = self.client.post(
            "/api/v1/auth/reset-password",
            headers=TEST_ORIGIN,
            json={"token": token, "password": "OtherPass9!Secure"},
        )
        self.assertEqual(expired.status_code, 400)

    def test_private_workspace_requires_authentication_and_role(self) -> None:
        unauthenticated = self.client.get("/api/v1/workspaces/learner")
        self.assertEqual(unauthenticated.status_code, 401)

        self.register(role="supervisor")
        learner = self.client.get("/api/v1/workspaces/learner")
        self.assertEqual(
            learner.json(), {"role": "learner", "workspace": "learner"}
        )
        facilitator = self.client.get("/api/v1/workspaces/facilitator")
        self.assertEqual(facilitator.status_code, 403)
        supervisor = self.client.get("/api/v1/workspaces/supervisor")
        self.assertEqual(supervisor.status_code, 403)

        self.db.query(User).filter_by(email="learner@example.com").update(
            {"role": "facilitator"}
        )
        self.db.commit()
        self.client.post("/api/v1/auth/logout", headers=TEST_ORIGIN)
        login = self.client.post(
            "/api/v1/auth/login",
            headers=TEST_ORIGIN,
            json={"email": "learner@example.com", "password": STRONG_PASSWORD},
        )
        self.assertEqual(login.status_code, 200)
        self.assertEqual(
            self.client.get("/api/v1/workspaces/facilitator").json(),
            {"role": "facilitator", "workspace": "facilitator"},
        )
        self.assertEqual(
            self.client.get("/api/v1/workspaces/supervisor").status_code, 403
        )
        self.db.query(User).filter_by(email="learner@example.com").update(
            {"role": "supervisor"}
        )
        self.db.commit()
        self.client.post("/api/v1/auth/logout", headers=TEST_ORIGIN)
        login = self.client.post(
            "/api/v1/auth/login",
            headers=TEST_ORIGIN,
            json={"email": "learner@example.com", "password": STRONG_PASSWORD},
        )
        self.assertEqual(login.status_code, 200)
        self.assertEqual(
            self.client.get("/api/v1/workspaces/supervisor").json(),
            {"role": "supervisor", "workspace": "supervisor"},
        )


if __name__ == "__main__":
    unittest.main()
