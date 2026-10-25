from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class LearningModule(Base):
    __tablename__ = "learning_modules"
    __table_args__ = (
        CheckConstraint("week_number BETWEEN 1 AND 12", name="ck_module_week_number"),
        UniqueConstraint("week_number", name="uq_module_week_number"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    week_number: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200))
    content_markdown: Mapped[str] = mapped_column(
        Text().with_variant(MEDIUMTEXT(), "mysql"), default=""
    )
    learning_objectives: Mapped[list[str]] = mapped_column(JSON, default=list)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    reflection_prompts: Mapped[list[str]] = mapped_column(JSON, default=list)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewed_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    questions: Mapped[list["ModuleQuestion"]] = relationship(
        back_populates="module", cascade="all, delete-orphan", order_by="ModuleQuestion.position"
    )


class ModuleQuestion(Base):
    __tablename__ = "module_questions"
    __table_args__ = (
        UniqueConstraint("module_id", "position", name="uq_question_module_position"),
        CheckConstraint("kind IN ('case_study', 'assignment', 'quiz')", name="ck_question_kind"),
        CheckConstraint("position > 0", name="ck_question_position"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    module_id: Mapped[int] = mapped_column(
        ForeignKey("learning_modules.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int] = mapped_column(Integer)
    kind: Mapped[str] = mapped_column(String(20), default="case_study")
    prompt: Mapped[str] = mapped_column(String(2000))
    module: Mapped[LearningModule] = relationship(back_populates="questions")


class LearnerModuleNote(Base):
    __tablename__ = "learner_module_notes"
    __table_args__ = (
        UniqueConstraint("learner_id", "module_id", name="uq_note_learner_module"),
        CheckConstraint("length(content) <= 80000", name="ck_note_content_length"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    learner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    module_id: Mapped[int] = mapped_column(
        ForeignKey("learning_modules.id", ondelete="CASCADE"), index=True
    )
    content: Mapped[str] = mapped_column(
        Text().with_variant(MEDIUMTEXT(), "mysql"), default=""
    )
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class LearnerModuleReflection(Base):
    __tablename__ = "learner_module_reflections"
    __table_args__ = (
        UniqueConstraint("learner_id", "module_id", name="uq_reflection_learner_module"),
        CheckConstraint("length(content) <= 80000", name="ck_reflection_content_length"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    learner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    module_id: Mapped[int] = mapped_column(
        ForeignKey("learning_modules.id", ondelete="CASCADE"), index=True
    )
    content: Mapped[str] = mapped_column(
        Text().with_variant(MEDIUMTEXT(), "mysql"), default=""
    )
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class LearnerModuleSubmission(Base):
    __tablename__ = "learner_module_submissions"
    __table_args__ = (
        UniqueConstraint("learner_id", "module_id", name="uq_submission_learner_module"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    learner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    module_id: Mapped[int] = mapped_column(
        ForeignKey("learning_modules.id", ondelete="CASCADE"), index=True
    )
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    answers: Mapped[list["LearnerQuestionAnswer"]] = relationship(
        back_populates="submission", cascade="all, delete-orphan"
    )


class LearnerQuestionAnswer(Base):
    __tablename__ = "learner_question_answers"
    __table_args__ = (
        UniqueConstraint("submission_id", "question_id", name="uq_answer_submission_question"),
        CheckConstraint("length(answer) <= 40000", name="ck_answer_content_length"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    submission_id: Mapped[int] = mapped_column(
        ForeignKey("learner_module_submissions.id", ondelete="CASCADE"), index=True
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("module_questions.id", ondelete="CASCADE"), index=True
    )
    answer: Mapped[str] = mapped_column(Text)
    submission: Mapped[LearnerModuleSubmission] = relationship(back_populates="answers")
