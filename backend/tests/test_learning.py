import os
import unittest

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("AUTH_SECRET_KEY", "test-secret-not-for-production-32-bytes")
os.environ.setdefault("RESEND_API_KEY", "test-resend-key")
os.environ.setdefault("RESEND_FROM_EMAIL", "ALMASI <accounts@example.test>")

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings, get_settings
from app.core.security import create_session_token, hash_password, utc_naive_now
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import (
    LearnerModuleNote,
    LearnerModuleReflection,
    LearnerModuleSubmission,
    LearnerQuestionAnswer,
    LearningModule,
    ModuleQuestion,
    PasswordResetToken,
    User,
)

TEST_SECRET = "test-secret-not-for-production-32-bytes"
TEST_SETTINGS = Settings(
    database_url="sqlite://",
    auth_secret_key=TEST_SECRET,
    resend_api_key="test-resend-key",
    resend_from_email="ALMASI <accounts@example.test>",
    cors_origins="http://testserver",
    app_base_url="http://testserver",
    app_env="test",
)
DELETE_ORDER = (
    LearnerQuestionAnswer,
    LearnerModuleSubmission,
    LearnerModuleReflection,
    LearnerModuleNote,
    ModuleQuestion,
    LearningModule,
    PasswordResetToken,
    User,
)


class LearnerModuleTests(unittest.TestCase):
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
        for model in DELETE_ORDER:
            self.db.execute(delete(model))
        self.db.commit()
        self.learner = self.create_user("learner@example.com", "learner")
        self.other_learner = self.create_user("other@example.com", "learner")
        self.supervisor = self.create_user("supervisor@example.com", "supervisor")
        self.draft = self.create_module(published=False)
        self.module = self.create_module(published=True, week_number=2)
        self.client = TestClient(app)
        self.authenticate(self.client, self.learner)

        def override_db():
            yield self.db

        app.dependency_overrides[get_db] = override_db
        app.dependency_overrides[get_settings] = lambda: TEST_SETTINGS

    def tearDown(self) -> None:
        self.client.close()
        self.db.close()
        app.dependency_overrides.clear()

    def create_user(self, email: str, role: str) -> User:
        user = User(
            name="Test User",
            email=email,
            password_hash=hash_password("StrongPass9!"),
            role=role,
            session_version=0,
            created_at=utc_naive_now(),
        )
        self.db.add(user)
        self.db.commit()
        return user

    def create_module(self, published: bool, week_number: int = 1) -> LearningModule:
        module = LearningModule(
            week_number=week_number,
            title=f"Approved module {week_number}",
            content_markdown="Approved lesson content.",
            learning_objectives=["Understand approved material."],
            reflection_prompts=["What is one takeaway from this lesson?"],
            is_published=published,
            created_at=utc_naive_now(),
            updated_at=utc_naive_now(),
            questions=[
                ModuleQuestion(position=1, prompt="What did you learn?"),
                ModuleQuestion(position=2, prompt="How will you apply it?"),
            ],
        )
        self.db.add(module)
        self.db.commit()
        self.db.refresh(module)
        return module

    def authenticate(self, client: TestClient, user: User) -> None:
        client.cookies.set(
            "almasi_session",
            create_session_token(user.id, user.session_version, TEST_SECRET),
        )

    def test_published_modules_only_and_private_data_is_owned_by_learner(self) -> None:
        response = self.client.get("/api/v1/learner/modules")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id"] for item in response.json()], [self.module.id])
        self.assertEqual(response.json()[0]["is_completed"], False)

        draft = self.client.get(f"/api/v1/learner/modules/{self.draft.id}")
        self.assertEqual(draft.status_code, 404)

        note_url = f"/api/v1/learner/modules/{self.module.id}/notes"
        reflection_url = f"/api/v1/learner/modules/{self.module.id}/reflections"
        self.assertEqual(
            self.client.put(note_url, json={"content": "First note"}).status_code, 200
        )
        self.assertEqual(
            self.client.put(note_url, json={"content": "Updated note"}).status_code, 200
        )
        self.assertEqual(
            self.client.put(reflection_url, json={"content": "Private thought"}).status_code,
            200,
        )

        detail = self.client.get(f"/api/v1/learner/modules/{self.module.id}")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["note"], "Updated note")
        self.assertEqual(detail.json()["reflection"], "Private thought")
        self.assertEqual(
            detail.json()["reflection_prompts"],
            ["What is one takeaway from this lesson?"],
        )
        supervisor_client = TestClient(app)
        self.authenticate(supervisor_client, self.supervisor)
        supervisor_modules = supervisor_client.get("/api/v1/supervisor/modules")
        self.assertEqual(supervisor_modules.status_code, 200)
        self.assertNotIn("Private thought", supervisor_modules.text)
        self.assertNotIn("Updated note", supervisor_modules.text)
        supervisor_client.close()

        other_client = TestClient(app)
        self.authenticate(other_client, self.other_learner)
        other_detail = other_client.get(f"/api/v1/learner/modules/{self.module.id}")
        self.assertEqual(other_detail.status_code, 200)
        self.assertEqual(other_detail.json()["note"], "")
        self.assertEqual(other_detail.json()["reflection"], "")
        self.assertEqual(other_detail.json()["answers"], {})
        other_client.close()

        self.db.refresh(self.module)
        self.assertEqual(
            self.db.scalar(
                select(LearnerModuleReflection).where(
                    LearnerModuleReflection.learner_id == self.other_learner.id
                )
            ),
            None,
        )

    def test_submission_requires_every_module_question_and_persists_completion(self) -> None:
        url = f"/api/v1/learner/modules/{self.module.id}/submit"
        draft_answer = self.client.put(
            f"/api/v1/learner/modules/{self.module.id}/answers",
            json={
                "answers": [
                    {
                        "question_id": self.module.questions[0].id,
                        "answer": "Saved draft answer",
                    }
                ],
            },
        )
        self.assertEqual(draft_answer.status_code, 200)
        self.assertEqual(draft_answer.json()["saved_answer_count"], 1)
        self.assertFalse(draft_answer.json()["is_completed"])
        draft_detail = self.client.get(f"/api/v1/learner/modules/{self.module.id}")
        self.assertEqual(
            draft_detail.json()["answers"][str(self.module.questions[0].id)],
            "Saved draft answer",
        )
        self.assertFalse(draft_detail.json()["is_completed"])
        other_client = TestClient(app)
        self.authenticate(other_client, self.other_learner)
        other_answers = other_client.get(f"/api/v1/learner/modules/{self.module.id}")
        self.assertEqual(other_answers.json()["answers"], {})
        other_client.close()

        incomplete = self.client.post(
            url,
            json={"answers": [{"question_id": self.module.questions[0].id, "answer": "Answer"}]},
        )
        self.assertEqual(incomplete.status_code, 422)

        wrong_question = self.client.post(
            url,
            json={
                "answers": [
                    {"question_id": self.module.questions[0].id, "answer": "Answer"},
                    {"question_id": 99999, "answer": "Answer"},
                ],
            },
        )
        self.assertEqual(wrong_question.status_code, 422)

        submitted = self.client.post(
            url,
            json={
                "answers": [
                    {"question_id": question.id, "answer": f"Answer {question.position}"}
                    for question in self.module.questions
                ],
            },
        )
        self.assertEqual(submitted.status_code, 201)
        self.assertTrue(submitted.json()["is_completed"])
        self.assertIn("submitted", submitted.json()["confirmation"].lower())
        self.assertEqual(
            self.client.get(f"/api/v1/learner/modules/{self.module.id}").json()[
                "is_completed"
            ],
            True,
        )
        self.assertEqual(
            self.client.get("/api/v1/learner/modules").json()[0]["is_completed"], True
        )
        self.assertEqual(
            self.db.scalar(
                select(LearnerModuleSubmission).where(
                    LearnerModuleSubmission.learner_id == self.learner.id,
                    LearnerModuleSubmission.module_id == self.module.id,
                )
            )
            is not None,
            True,
        )
        answer_count = self.db.scalar(
            select(func.count())
            .select_from(LearnerQuestionAnswer)
            .join(LearnerModuleSubmission)
            .where(
                LearnerModuleSubmission.learner_id == self.learner.id,
                LearnerModuleSubmission.module_id == self.module.id,
            )
        )
        self.assertEqual(answer_count, len(self.module.questions))
        duplicate = self.client.post(
            url,
            json={
                "answers": [
                    {"question_id": question.id, "answer": "Updated"}
                    for question in self.module.questions
                ],
            },
        )
        self.assertEqual(duplicate.status_code, 409)
        save_after_completion = self.client.put(
            f"/api/v1/learner/modules/{self.module.id}/answers",
            json={
                "answers": [
                    {"question_id": question.id, "answer": "Changed"}
                    for question in self.module.questions
                ],
            },
        )
        self.assertEqual(save_after_completion.status_code, 409)

    def test_only_supervisors_can_create_and_publish_complete_modules(self) -> None:
        forbidden = self.client.post(
            "/api/v1/supervisor/modules",
            json={
                "week_number": 3,
                "title": "Another module",
                "content_markdown": "Content",
                "learning_objectives": ["Objective"],
                "reflection_prompts": ["What is one takeaway?"],
                "questions": [{"position": 1, "prompt": "Question?"}],
            },
        )
        self.assertEqual(forbidden.status_code, 403)

        supervisor_client = TestClient(app)
        self.authenticate(supervisor_client, self.supervisor)
        created = supervisor_client.post(
            "/api/v1/supervisor/modules",
            json={
                "week_number": 3,
                "title": "Another module",
                "content_markdown": "Content",
                "learning_objectives": ["Objective"],
                "reflection_prompts": ["What is one takeaway?"],
                "questions": [
                    {
                        "position": 1,
                        "kind": "case_study",
                        "prompt": "What could the learner do?",
                    },
                    {
                        "position": 2,
                        "kind": "assignment",
                        "prompt": "What will the learner practise?",
                    },
                ],
            },
        )
        self.assertEqual(created.status_code, 201)
        module_id = created.json()["id"]
        blocked_publish = supervisor_client.post(
            f"/api/v1/supervisor/modules/{module_id}/publish"
        )
        self.assertEqual(blocked_publish.status_code, 409)
        invalid_review = supervisor_client.post(
            f"/api/v1/supervisor/modules/{module_id}/review",
            json={"confirm_review": False},
        )
        self.assertEqual(invalid_review.status_code, 422)
        reviewed = supervisor_client.post(
            f"/api/v1/supervisor/modules/{module_id}/review",
            json={"confirm_review": True},
        )
        self.assertEqual(reviewed.status_code, 200)
        self.assertTrue(reviewed.json()["is_reviewed"])
        self.assertEqual(reviewed.json()["reviewed_by_id"], self.supervisor.id)
        unpublished = supervisor_client.post(
            f"/api/v1/supervisor/modules/{module_id}/publish"
        )
        self.assertEqual(unpublished.status_code, 200)
        self.assertTrue(unpublished.json()["is_published"])
        self.assertEqual(
            self.client.get("/api/v1/learner/modules").json()[-1]["id"], module_id
        )

        incomplete = supervisor_client.post(
            "/api/v1/supervisor/modules",
            json={
                "week_number": 4,
                "title": "Incomplete review module",
                "content_markdown": "Content",
                "learning_objectives": ["Objective"],
                "reflection_prompts": ["What is one takeaway?"],
                "questions": [
                    {"position": 1, "kind": "case_study", "prompt": "Question?"}
                ],
            },
        )
        self.assertEqual(incomplete.status_code, 201)
        incomplete_review = supervisor_client.post(
            f"/api/v1/supervisor/modules/{incomplete.json()['id']}/review",
            json={"confirm_review": True},
        )
        self.assertEqual(incomplete_review.status_code, 422)
        supervisor_client.close()

    def test_note_validation_authentication_and_reflection_privacy(self) -> None:
        note_url = f"/api/v1/learner/modules/{self.module.id}/notes"
        too_long = self.client.put(note_url, json={"content": "x" * 20_001})
        self.assertEqual(too_long.status_code, 422)
        max_length_unicode = self.client.put(
            note_url, json={"content": "\U0001f642" * 20_000}
        )
        self.assertEqual(max_length_unicode.status_code, 200)

        self.client.cookies.clear()
        unauthenticated = self.client.get("/api/v1/learner/modules")
        self.assertEqual(unauthenticated.status_code, 401)

        supervisor_client = TestClient(app)
        self.authenticate(supervisor_client, self.supervisor)
        self.assertEqual(
            supervisor_client.get(f"/api/v1/learner/modules/{self.module.id}").status_code,
            403,
        )
        self.assertEqual(supervisor_client.get("/api/v1/supervisor/modules").status_code, 200)
        supervisor_client.close()


if __name__ == "__main__":
    unittest.main()
