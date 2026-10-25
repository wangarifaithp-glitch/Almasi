"""Add constrained account roles.

Revision ID: 20261025_0002
Revises: 20261025_0001
Create Date: 2026-10-25
"""

from alembic import op
import sqlalchemy as sa

revision = "20261025_0002"
down_revision = "20261025_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(
            sa.Column(
                "role",
                sa.String(length=20),
                server_default="learner",
                nullable=False,
            )
        )
        batch_op.create_check_constraint(
            "ck_users_role",
            "role IN ('learner', 'facilitator', 'supervisor')",
        )


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_constraint("ck_users_role", type_="check")
        batch_op.drop_column("role")
