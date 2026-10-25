import os
import unittest
from datetime import timedelta

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("AUTH_SECRET_KEY", "test-secret-not-for-production-32-bytes")

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings, get_settings
from app.core.security import hash_password, utc_naive_now
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import (
    AssignmentSubmission,
    AuditLog,
    GroupFacilitator,
    GroupMembership,
    LearnerModuleReflection,
    LearningModule,
    MentorshipGroup,
    MentorshipSession,
    ProgrammeAssignment,
    SessionAttendance,
    SubmissionFeedback,
    SubmissionRevision,
    User,
)

TEST_SETTINGS = Settings(
    database_url="sqlite://",
    auth_secret_key="test-secret-not-for-production-32-bytes",
    cors_origins="http://testserver",
    app_base_url="http://testserver",
    app_env="test",
)
ORIGIN = {"Origin": "http://testserver"}
PASSWORD = "ProgrammePass9!"
PRIVATE_REFLECTION = "private-reflection-marker-not-for-staff"


class ProgrammeAccessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(
            bind=self.engine, autoflush=False, autocommit=False
        )
        self.db = self.session_factory()
        now = utc_naive_now()
        self.admin = self._user("admin@example.com", "administrator", now)
        self.supervisor = self._user("supervisor@example.com", "supervisor", now)
        self.facilitator = self._user("facilitator@example.com", "facilitator", now)
        self.other_facilitator = self._user(
            "other-facilitator@example.com", "facilitator", now
        )
        self.learner = self._user("learner@example.com", "learner", now)
        self.other_learner = self._user("other-learner@example.com", "learner", now)
        self.module = LearningModule(
            week_number=1,
            title="Test module",
            content_markdown="Lesson",
            learning_objectives=["Learn"],
            reflection_prompts=["Reflect privately"],
            is_published=True,
            created_at=now,
            updated_at=now,
        )
        self.db.add(self.module)
        self.db.flush()
        self.group = MentorshipGroup(
            name="Assigned group",
            description="",
            is_active=True,
            created_by_id=self.admin.id,
            created_at=now,
            updated_at=now,
        )
        self.other_group = MentorshipGroup(
            name="Other group",
            description="",
            is_active=True,
            created_by_id=self.admin.id,
            created_at=now,
            updated_at=now,
        )
        self.db.add_all([self.group, self.other_group])
        self.db.flush()
        self.db.add_all(
            [
                GroupFacilitator(
                    group_id=self.group.id,
                    facilitator_id=self.facilitator.id,
                    created_at=now,
                ),
                GroupMembership(
                    group_id=self.group.id,
                    learner_id=self.learner.id,
                    created_at=now,
                ),
                GroupFacilitator(
                    group_id=self.other_group.id,
                    facilitator_id=self.other_facilitator.id,
                    created_at=now,
                ),
                GroupMembership(
                    group_id=self.other_group.id,
                    learner_id=self.other_learner.id,
                    created_at=now,
                ),
            ]
        )
        self.session = MentorshipSession(
            group_id=self.group.id,
            module_id=self.module.id,
            title="Session one",
            facilitator_plan="Facilitator-only plan",
            starts_at=now + timedelta(days=1),
            ends_at=now + timedelta(days=1, hours=1),
            status="scheduled",
            created_by_id=self.admin.id,
            created_at=now,
            updated_at=now,
        )
        self.other_session = MentorshipSession(
            group_id=self.other_group.id,
            module_id=self.module.id,
            title="Other session",
            facilitator_plan="Other plan",
            starts_at=now + timedelta(days=2),
            ends_at=now + timedelta(days=2, hours=1),
            status="scheduled",
            created_by_id=self.admin.id,
            created_at=now,
            updated_at=now,
        )
        self.db.add_all([self.session, self.other_session])
        self.db.flush()
        self.assignment = ProgrammeAssignment(
            group_id=self.group.id,
            module_id=self.module.id,
            session_id=self.session.id,
            title="My assignment",
            instructions="Write about the fictional case.",
            due_at=now + timedelta(days=7),
            status="open",
            created_by_id=self.facilitator.id,
            created_at=now,
            updated_at=now,
        )
        self.other_assignment = ProgrammeAssignment(
            group_id=self.other_group.id,
            module_id=self.module.id,
            session_id=self.other_session.id,
            title="Other assignment",
            instructions="Write about another fictional case.",
            due_at=now + timedelta(days=7),
            status="open",
            created_by_id=self.other_facilitator.id,
            created_at=now,
            updated_at=now,
        )
        self.db.add_all([self.assignment, self.other_assignment])
        self.db.flush()
        self.submission = AssignmentSubmission(
            assignment_id=self.assignment.id,
            learner_id=self.learner.id,
            content="My submitted answer",
            status="submitted",
            submitted_at=now,
            created_at=now,
            updated_at=now,
        )
        self.other_submission = AssignmentSubmission(
            assignment_id=self.other_assignment.id,
            learner_id=self.other_learner.id,
            content="Other learner answer",
            status="submitted",
            submitted_at=now,
            created_at=now,
            updated_at=now,
        )
        self.db.add_all([self.submission, self.other_submission])
        self.db.flush()
        self.db.add(
            SubmissionFeedback(
                submission_id=self.submission.id,
                facilitator_id=self.facilitator.id,
                comments="Helpful feedback",
                score=80,
                created_at=now,
                updated_at=now,
            )
        )
        self.db.add(
            SessionAttendance(
                session_id=self.session.id,
                learner_id=self.learner.id,
                status="present",
                recorded_by_id=self.facilitator.id,
                created_at=now,
                updated_at=now,
            )
        )
        self.db.commit()

        def override_db():
            yield self.db

        app.dependency_overrides[get_db] = override_db
        app.dependency_overrides[get_settings] = lambda: TEST_SETTINGS
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.client.close()
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()
        app.dependency_overrides.clear()

    def _user(self, email: str, role: str, now):
        user = User(
            name=email.split("@")[0],
            email=email,
            password_hash=hash_password(PASSWORD),
            role=role,
            is_active=True,
            created_at=now,
        )
        self.db.add(user)
        self.db.flush()
        return user

    def _login(self, email: str) -> None:
        response = self.client.post(
            "/api/v1/auth/login",
            headers=ORIGIN,
            json={"email": email, "password": PASSWORD},
        )
        self.assertEqual(response.status_code, 200)

    def test_facilitator_access_is_limited_to_assigned_groups(self) -> None:
        self._login("facilitator@example.com")
        dashboard = self.client.get("/api/v1/facilitator/dashboard")
        self.assertEqual(dashboard.status_code, 200)
        self.assertEqual(
            [group["name"] for group in dashboard.json()["groups"]],
            ["Assigned group"],
        )
        self.assertEqual(len(dashboard.json()["submissions"]), 1)
        self.assertNotIn(PRIVATE_REFLECTION, dashboard.text)
        denied = self.client.put(
            f"/api/v1/facilitator/submissions/{self.other_submission.id}/feedback",
            headers=ORIGIN,
            json={"comments": "unauthorized", "score": 0},
        )
        self.assertEqual(denied.status_code, 404)
        denied_attendance = self.client.get(
            f"/api/v1/facilitator/sessions/{self.other_session.id}/attendance"
        )
        self.assertEqual(denied_attendance.status_code, 404)

    def test_learner_can_only_view_and_edit_own_group_assignment(self) -> None:
        self._login("learner@example.com")
        assignments = self.client.get("/api/v1/learner/assignments")
        self.assertEqual(assignments.status_code, 200)
        self.assertEqual(
            [item["id"] for item in assignments.json()],
            [self.assignment.id],
        )
        own = assignments.json()[0]
        self.assertEqual(own["submission_content"], "My submitted answer")
        self.assertEqual(own["feedback"], "Helpful feedback")

        denied = self.client.put(
            f"/api/v1/learner/assignments/{self.other_assignment.id}/submission",
            headers=ORIGIN,
            json={"content": "attempt to change another learner's assignment"},
        )
        self.assertEqual(denied.status_code, 404)
        attendance = self.client.get("/api/v1/learner/attendance")
        self.assertEqual(attendance.status_code, 200)
        self.assertEqual(attendance.json()[0]["status"], "present")

    def test_private_reflections_never_appear_in_staff_reports_or_views(self) -> None:
        self._login("learner@example.com")
        saved = self.client.put(
            f"/api/v1/learner/modules/{self.module.id}/reflections",
            headers=ORIGIN,
            json={"content": PRIVATE_REFLECTION},
        )
        self.assertEqual(saved.status_code, 200)
        self.assertEqual(
            self.db.scalar(select(LearnerModuleReflection)).content,
            PRIVATE_REFLECTION,
        )

        self._login("facilitator@example.com")
        facilitator_view = self.client.get("/api/v1/facilitator/dashboard")
        self.assertEqual(facilitator_view.status_code, 200)
        self.assertNotIn(PRIVATE_REFLECTION, facilitator_view.text)
        self.assertNotIn("reflection", facilitator_view.text.lower())

        self._login("supervisor@example.com")
        report = self.client.get("/api/v1/supervisor/reports")
        self.assertEqual(report.status_code, 200)
        self.assertNotIn(PRIVATE_REFLECTION, report.text)
        self.assertNotIn("reflection", report.text.lower())

    def test_facilitator_attendance_and_feedback_changes_are_audited(self) -> None:
        self._login("facilitator@example.com")
        attendance = self.client.put(
            f"/api/v1/facilitator/sessions/{self.session.id}/attendance",
            headers=ORIGIN,
            json={
                "records": [
                    {"learner_id": self.learner.id, "status": "late"}
                ]
            },
        )
        self.assertEqual(attendance.status_code, 200)
        self.assertEqual(attendance.json()[0]["status"], "late")

        feedback = self.client.put(
            f"/api/v1/facilitator/submissions/{self.submission.id}/feedback",
            headers=ORIGIN,
            json={"comments": "Second feedback", "score": 90},
        )
        self.assertEqual(feedback.status_code, 200)
        self.assertEqual(feedback.json()["status"], "reviewed")
        actions = set(self.db.scalars(select(AuditLog.action)).all())
        self.assertIn("attendance_corrected", actions)
        self.assertIn("submission_feedback_saved", actions)

    def test_learner_submission_revision_and_lock_enforcement(self) -> None:
        self._login("learner@example.com")
        saved = self.client.put(
            f"/api/v1/learner/assignments/{self.assignment.id}/submission?submit=true",
            headers=ORIGIN,
            json={"content": "A revised fictional-case answer."},
        )
        self.assertEqual(saved.status_code, 200)
        self.assertEqual(saved.json()["submission_status"], "submitted")
        self.assertEqual(
            self.db.scalar(select(SubmissionRevision)).action,
            "resubmitted",
        )

        self._login("facilitator@example.com")
        locked = self.client.put(
            f"/api/v1/facilitator/submissions/{self.submission.id}/lock",
            headers=ORIGIN,
        )
        self.assertEqual(locked.status_code, 200)
        self._login("learner@example.com")
        denied = self.client.put(
            f"/api/v1/learner/assignments/{self.assignment.id}/submission",
            headers=ORIGIN,
            json={"content": "cannot edit after facilitator lock"},
        )
        self.assertEqual(denied.status_code, 409)

    def test_removed_learner_keeps_history_but_cannot_submit(self) -> None:
        membership = self.db.scalar(
            select(GroupMembership).where(
                GroupMembership.group_id == self.group.id,
                GroupMembership.learner_id == self.learner.id,
            )
        )
        self.assertIsNotNone(membership)
        membership.is_active = False
        self.db.commit()

        self._login("learner@example.com")
        assignments = self.client.get("/api/v1/learner/assignments")
        self.assertEqual(assignments.status_code, 200)
        self.assertEqual(assignments.json()[0]["id"], self.assignment.id)

        denied = self.client.put(
            f"/api/v1/learner/assignments/{self.assignment.id}/submission",
            headers=ORIGIN,
            json={"content": "historical member cannot submit"},
        )
        self.assertEqual(denied.status_code, 404)

    def test_administrator_manages_roles_without_reflection_access(self) -> None:
        self._login("admin@example.com")
        groups = self.client.get("/api/v1/administrator/groups")
        self.assertEqual(groups.status_code, 200)
        users = self.client.get("/api/v1/administrator/users")
        self.assertEqual(users.status_code, 200)
        self.assertNotIn(PRIVATE_REFLECTION, users.text)
        changed = self.client.patch(
            f"/api/v1/administrator/users/{self.other_learner.id}",
            headers=ORIGIN,
            json={"role": "facilitator", "is_active": True},
        )
        self.assertEqual(changed.status_code, 200)
        self.assertEqual(changed.json()["role"], "facilitator")
        former_membership = self.db.scalar(
            select(GroupMembership).where(
                GroupMembership.learner_id == self.other_learner.id
            )
        )
        self.assertIsNotNone(former_membership)
        self.assertFalse(former_membership.is_active)


if __name__ == "__main__":
    unittest.main()
