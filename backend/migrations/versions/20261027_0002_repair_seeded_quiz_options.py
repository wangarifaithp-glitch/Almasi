"""Repair seeded true/false quiz options to satisfy the four-option contract.

Revision ID: 20261027_0002
Revises: 20261027_0001
Create Date: 2026-10-27
"""

import sqlalchemy as sa
from alembic import op


revision = "20261027_0002"
down_revision = "20261027_0001"
branch_labels = None
depends_on = None


REPAIRS = (
    (3, 2, ["True", "False", "It depends on popularity", "Only at school"]),
    (9, 5, ["True", "False", "Only when others approve", "Only when the goal is difficult"]),
    (11, 4, ["True", "False", "Only if it happens in public", "Only if both people agree"]),
    (12, 5, ["True", "False", "Only in a group", "Only when they volunteer"]),
)


def upgrade() -> None:
    connection = op.get_bind()
    modules = sa.table(
        "learning_modules",
        sa.column("id", sa.Integer),
        sa.column("week_number", sa.Integer),
    )
    questions = sa.table(
        "module_quiz_questions",
        sa.column("module_id", sa.Integer),
        sa.column("position", sa.Integer),
        sa.column("options", sa.JSON),
    )
    for week_number, position, options in REPAIRS:
        module_id = connection.execute(
            sa.select(modules.c.id).where(modules.c.week_number == week_number)
        ).scalar_one()
        connection.execute(
            questions.update()
            .where(
                questions.c.module_id == module_id,
                questions.c.position == position,
            )
            .values(options=options)
        )


def downgrade() -> None:
    connection = op.get_bind()
    modules = sa.table(
        "learning_modules",
        sa.column("id", sa.Integer),
        sa.column("week_number", sa.Integer),
    )
    questions = sa.table(
        "module_quiz_questions",
        sa.column("module_id", sa.Integer),
        sa.column("position", sa.Integer),
        sa.column("options", sa.JSON),
    )
    for week_number, position, _ in REPAIRS:
        module_id = connection.execute(
            sa.select(modules.c.id).where(modules.c.week_number == week_number)
        ).scalar_one()
        connection.execute(
            questions.update()
            .where(
                questions.c.module_id == module_id,
                questions.c.position == position,
            )
            .values(options=["True", "False"])
        )
