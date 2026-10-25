"""Seed the approved 12-week module outline as unpublished drafts.

Revision ID: 20261025_0004
Revises: 20261025_0003
Create Date: 2026-10-25
"""

from datetime import UTC, datetime

from alembic import op
import sqlalchemy as sa

revision = "20261025_0004"
down_revision = "20261025_0003"
branch_labels = None
depends_on = None

MODULES = (
    (
        1,
        "I Am Important",
        "Psalm 139:14",
        "self-worth, identity, dignity and recognising personal strengths.",
    ),
    (
        2,
        "Handling Comparison",
        "Galatians 6:4",
        "recognising comparison, appreciating differences and focusing on personal growth.",
    ),
    (
        3,
        "Understanding My Emotions",
        "Psalm 34:18",
        "identifying emotions, understanding emotional responses and expressing feelings appropriately.",
    ),
    (
        4,
        "Finding Peace in Difficult Moments",
        "Matthew 11:28",
        "coping with stress, calming strategies, problem-solving and seeking appropriate support.",
    ),
    (
        5,
        "Understanding Peer Pressure",
        "1 Corinthians 15:33",
        "recognising peer influence, making thoughtful decisions and responding to pressure.",
    ),
    (
        6,
        "Saying NO with Confidence",
        "Proverbs 4:23",
        "assertive communication, personal boundaries and making safe choices.",
    ),
    (
        7,
        "Protecting My Body",
        "1 Corinthians 6:19",
        "body dignity, personal boundaries, safety and seeking help from trusted adults.",
    ),
    (
        8,
        "Online and Social Media Awareness",
        "Philippians 4:8",
        "responsible online behaviour, privacy, digital safety and evaluating online content.",
    ),
    (
        9,
        "My Dreams Matter",
        "Jeremiah 29:11",
        "identifying aspirations, setting realistic goals and planning for the future.",
    ),
    (
        10,
        "Hard Work and Responsibility",
        "Proverbs 14:23",
        "responsibility, effort, time management, discipline and balancing work with rest.",
    ),
    (
        11,
        "Friendships That Build Me",
        "Proverbs 13:20",
        "healthy friendships, trust, communication, boundaries and recognising harmful behaviour.",
    ),
    (
        12,
        "Becoming an Almasi Girl",
        "Matthew 5:14",
        "reflecting on growth, practising positive values, everyday leadership and making a personal growth plan.",
    ),
)


def upgrade() -> None:
    now = datetime.now(UTC).replace(tzinfo=None)
    modules = sa.table(
        "learning_modules",
        sa.column("week_number", sa.Integer()),
        sa.column("title", sa.String(200)),
        sa.column("content_markdown", sa.Text()),
        sa.column("learning_objectives", sa.JSON()),
        sa.column("is_published", sa.Boolean()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    op.bulk_insert(
        modules,
        [
            {
                "week_number": week,
                "title": title,
                "content_markdown": (
                    f"Bible reference: {reference}\n\nApproved focus: {focus}"
                ),
                "learning_objectives": [],
                "is_published": False,
                "created_at": now,
                "updated_at": now,
            }
            for week, title, reference, focus in MODULES
        ],
    )


def downgrade() -> None:
    for week, title, _, _ in MODULES:
        op.get_bind().execute(
            sa.text(
                "DELETE FROM learning_modules "
                "WHERE week_number = :week AND title = :title "
                "AND is_published = 0 "
                "AND NOT EXISTS ("
                "SELECT 1 FROM learner_module_notes "
                "WHERE learner_module_notes.module_id = learning_modules.id"
                ") AND NOT EXISTS ("
                "SELECT 1 FROM learner_module_reflections "
                "WHERE learner_module_reflections.module_id = learning_modules.id"
                ") AND NOT EXISTS ("
                "SELECT 1 FROM learner_module_submissions "
                "WHERE learner_module_submissions.module_id = learning_modules.id"
                ")"
            ),
            {"week": week, "title": title},
        )
