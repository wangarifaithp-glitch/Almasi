"""Add original local illustrations and accessible metadata to modules.

Revision ID: 20261028_0003
Revises: 20261027_0002
Create Date: 2026-10-28
"""

from alembic import op
import sqlalchemy as sa


revision = "20261028_0003"
down_revision = "20261027_0002"
branch_labels = None
depends_on = None


ILLUSTRATIONS = (
    (1, "/curriculum/week-01-self-worth.svg", "A girl looking confidently into a mirror while recognising her strengths."),
    (2, "/curriculum/week-02-comparison.svg", "Girls with different strengths celebrating one another's achievements."),
    (3, "/curriculum/week-03-emotions.svg", "A girl naming different emotions and choosing a calm response."),
    (4, "/curriculum/week-04-peace.svg", "A girl reflecting calmly while receiving support from a trusted mentor."),
    (5, "/curriculum/week-05-peer-pressure.svg", "A girl making a thoughtful decision while friends listen respectfully."),
    (6, "/curriculum/week-06-boundaries.svg", "A girl confidently communicating a respectful personal boundary."),
    (7, "/curriculum/week-07-safety.svg", "A child-safety illustration showing personal space and trusted adults."),
    (8, "/curriculum/week-08-online-safety.svg", "A girl using a laptop safely while checking online privacy choices."),
    (9, "/curriculum/week-09-dreams.svg", "A girl planning a future goal with a notebook and pathway markers."),
    (10, "/curriculum/week-10-responsibility.svg", "A learner organising assignments, responsibilities, and time for rest."),
    (11, "/curriculum/week-11-friendships.svg", "Friends supporting one another respectfully during a conversation."),
    (12, "/curriculum/week-12-leadership.svg", "A young girl leading a positive community activity with others."),
)


def upgrade() -> None:
    op.add_column(
        "learning_modules", sa.Column("image_url", sa.String(length=500), nullable=False, server_default="")
    )
    op.add_column(
        "learning_modules", sa.Column("image_alt", sa.String(length=500), nullable=False, server_default="")
    )
    modules = sa.table(
        "learning_modules",
        sa.column("week_number", sa.Integer),
        sa.column("image_url", sa.String(500)),
        sa.column("image_alt", sa.String(500)),
    )
    connection = op.get_bind()
    for week_number, image_url, image_alt in ILLUSTRATIONS:
        connection.execute(
            modules.update()
            .where(modules.c.week_number == week_number)
            .values(image_url=image_url, image_alt=image_alt)
        )
    with op.batch_alter_table("learning_modules") as batch_op:
        batch_op.alter_column("image_url", server_default=None)
        batch_op.alter_column("image_alt", server_default=None)


def downgrade() -> None:
    with op.batch_alter_table("learning_modules") as batch_op:
        batch_op.drop_column("image_alt")
        batch_op.drop_column("image_url")
