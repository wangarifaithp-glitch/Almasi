"""add explicit facilitator submission review statuses

Revision ID: 20261028_0004
Revises: 20261028_0003
"""

from alembic import op
import sqlalchemy as sa


revision = "20261028_0004"
down_revision = "20261028_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("submissions") as batch_op:
        batch_op.alter_column(
            "status",
            existing_type=sa.String(length=20),
            type_=sa.String(length=32),
            existing_nullable=False,
        )
        batch_op.drop_constraint("ck_submission_status", type_="check")
        batch_op.create_check_constraint(
            "ck_submission_status",
            "status IN ('draft', 'submitted', 'approved', 'returned_for_improvement', 'locked')",
        )
    op.execute(
        sa.text(
            "UPDATE submissions SET status = 'approved' WHERE status = 'reviewed'"
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE submissions SET status = 'reviewed' WHERE status = 'approved'"
        )
    )
    with op.batch_alter_table("submissions") as batch_op:
        batch_op.drop_constraint("ck_submission_status", type_="check")
        batch_op.create_check_constraint(
            "ck_submission_status",
            "status IN ('draft', 'submitted', 'reviewed', 'locked')",
        )
        batch_op.alter_column(
            "status",
            existing_type=sa.String(length=32),
            type_=sa.String(length=20),
            existing_nullable=False,
        )
