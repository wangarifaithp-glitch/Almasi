"""Add published curriculum and private learner module data.

Revision ID: 20261025_0003
Revises: 20261025_0002
Create Date: 2026-10-25
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision = "20261025_0003"
down_revision = "20261025_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "learning_modules",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("week_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column(
            "content_markdown",
            sa.Text().with_variant(mysql.MEDIUMTEXT(), "mysql"),
            nullable=False,
        ),
        sa.Column("learning_objectives", sa.JSON(), nullable=False),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("week_number BETWEEN 1 AND 12", name="ck_module_week_number"),
        sa.UniqueConstraint("week_number", name="uq_module_week_number"),
    )
    op.create_index(
        "ix_learning_modules_is_published",
        "learning_modules",
        ["is_published"],
        unique=False,
    )
    op.create_table(
        "module_questions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("module_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("prompt", sa.String(length=2000), nullable=False),
        sa.ForeignKeyConstraint(["module_id"], ["learning_modules.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("module_id", "position", name="uq_question_module_position"),
    )
    op.create_index("ix_module_questions_module_id", "module_questions", ["module_id"])
    op.create_table(
        "learner_module_notes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("learner_id", sa.Integer(), nullable=False),
        sa.Column("module_id", sa.Integer(), nullable=False),
        sa.Column(
            "content",
            sa.Text().with_variant(mysql.MEDIUMTEXT(), "mysql"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["learner_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["module_id"], ["learning_modules.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("learner_id", "module_id", name="uq_note_learner_module"),
        sa.CheckConstraint("length(content) <= 80000", name="ck_note_content_length"),
    )
    op.create_index("ix_learner_module_notes_learner_id", "learner_module_notes", ["learner_id"])
    op.create_index("ix_learner_module_notes_module_id", "learner_module_notes", ["module_id"])
    op.create_table(
        "learner_module_reflections",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("learner_id", sa.Integer(), nullable=False),
        sa.Column("module_id", sa.Integer(), nullable=False),
        sa.Column(
            "content",
            sa.Text().with_variant(mysql.MEDIUMTEXT(), "mysql"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["learner_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["module_id"], ["learning_modules.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("learner_id", "module_id", name="uq_reflection_learner_module"),
        sa.CheckConstraint("length(content) <= 80000", name="ck_reflection_content_length"),
    )
    op.create_index(
        "ix_learner_module_reflections_learner_id",
        "learner_module_reflections",
        ["learner_id"],
    )
    op.create_index(
        "ix_learner_module_reflections_module_id",
        "learner_module_reflections",
        ["module_id"],
    )
    op.create_table(
        "learner_module_submissions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("learner_id", sa.Integer(), nullable=False),
        sa.Column("module_id", sa.Integer(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["learner_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["module_id"], ["learning_modules.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("learner_id", "module_id", name="uq_submission_learner_module"),
    )
    op.create_index(
        "ix_learner_module_submissions_learner_id",
        "learner_module_submissions",
        ["learner_id"],
    )
    op.create_index(
        "ix_learner_module_submissions_module_id",
        "learner_module_submissions",
        ["module_id"],
    )
    op.create_table(
        "learner_question_answers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("submission_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["submission_id"], ["learner_module_submissions.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["question_id"], ["module_questions.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "submission_id", "question_id", name="uq_answer_submission_question"
        ),
        sa.CheckConstraint("length(answer) <= 40000", name="ck_answer_content_length"),
    )
    op.create_index(
        "ix_learner_question_answers_submission_id",
        "learner_question_answers",
        ["submission_id"],
    )
    op.create_index(
        "ix_learner_question_answers_question_id",
        "learner_question_answers",
        ["question_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_learner_question_answers_question_id", table_name="learner_question_answers")
    op.drop_index(
        "ix_learner_question_answers_submission_id", table_name="learner_question_answers"
    )
    op.drop_table("learner_question_answers")
    op.drop_index(
        "ix_learner_module_submissions_module_id", table_name="learner_module_submissions"
    )
    op.drop_index(
        "ix_learner_module_submissions_learner_id", table_name="learner_module_submissions"
    )
    op.drop_table("learner_module_submissions")
    op.drop_index(
        "ix_learner_module_reflections_module_id", table_name="learner_module_reflections"
    )
    op.drop_index(
        "ix_learner_module_reflections_learner_id", table_name="learner_module_reflections"
    )
    op.drop_table("learner_module_reflections")
    op.drop_index("ix_learner_module_notes_module_id", table_name="learner_module_notes")
    op.drop_index("ix_learner_module_notes_learner_id", table_name="learner_module_notes")
    op.drop_table("learner_module_notes")
    op.drop_index("ix_module_questions_module_id", table_name="module_questions")
    op.drop_table("module_questions")
    op.drop_index("ix_learning_modules_is_published", table_name="learning_modules")
    op.drop_table("learning_modules")
