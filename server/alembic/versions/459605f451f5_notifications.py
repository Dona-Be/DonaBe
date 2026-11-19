from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "459605f451f5"
down_revision: str | None = "a799e11515d6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("recipient_id", sa.Integer(), nullable=False),
        sa.Column(
            "type",
            sa.Enum(
                "intent_registered",
                "intent_cancelled",
                "intent_delivered",
                "intent_status_changed",
                name="notificationtype",
                native_enum=False,
                length=30,
            ),
            nullable=False,
        ),
        sa.Column("donation_intent_id", sa.Integer(), nullable=False),
        sa.Column("message", sa.String(), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["donation_intent_id"],
            ["donation_intents.id"],
            name=op.f("fk_notifications_donation_intent_id_donation_intents"),
        ),
        sa.ForeignKeyConstraint(
            ["recipient_id"], ["users.id"], name=op.f("fk_notifications_recipient_id_users")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_notifications")),
    )
    op.create_index(
        op.f("ix_notifications_donation_intent_id"),
        "notifications",
        ["donation_intent_id"],
        unique=False,
    )
    op.create_index(
        "ix_notifications_recipient_id_read_at",
        "notifications",
        ["recipient_id", "read_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_notifications_recipient_id_read_at", table_name="notifications")
    op.drop_index(op.f("ix_notifications_donation_intent_id"), table_name="notifications")
    op.drop_table("notifications")
