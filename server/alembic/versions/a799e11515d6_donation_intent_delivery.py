from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a799e11515d6"
down_revision: str | None = "798b64781db8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UNIQUE_ACTIVE_INTENT_INDEX = "uq_donation_intents_active_per_donor"
OLD_ACTIVE_INTENT_CONDITION = "status IN ('in_contact', 'registered')"
NEW_ACTIVE_INTENT_CONDITION = (
    "status IN ('delivered', 'delivery_scheduled', 'in_contact', 'registered')"
)


def upgrade() -> None:
    # Nothing creates donation intents yet, so the table is empty.
    op.drop_index(
        op.f("ix_donation_intents_data_retention_deadline"), table_name="donation_intents"
    )
    op.drop_column("donation_intents", "donor_name")
    op.drop_column("donation_intents", "donor_email")
    op.drop_column("donation_intents", "phone")
    op.drop_column("donation_intents", "consented_at")
    op.drop_column("donation_intents", "completed_at")
    op.drop_column("donation_intents", "data_retention_deadline")
    op.drop_column("donation_intents", "data_deleted_at")
    op.add_column(
        "donation_intents", sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "donation_intents", sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "donation_intents", sa.Column("received_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "donation_intents", sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "donation_intents",
        sa.Column(
            "cancelled_by",
            sa.Enum("donor", "manager", name="role", native_enum=False, length=30),
            nullable=True,
        ),
    )
    op.alter_column("donation_intents", "donor_id", existing_type=sa.INTEGER(), nullable=False)
    # Autogenerate does not compare index conditions, so this is hand-written.
    replace_active_intent_index(NEW_ACTIVE_INTENT_CONDITION)


def downgrade() -> None:
    # Assumes an empty table too: consented_at comes back as required.
    replace_active_intent_index(OLD_ACTIVE_INTENT_CONDITION)
    op.alter_column("donation_intents", "donor_id", existing_type=sa.INTEGER(), nullable=True)
    op.drop_column("donation_intents", "cancelled_by")
    op.drop_column("donation_intents", "cancelled_at")
    op.drop_column("donation_intents", "received_at")
    op.drop_column("donation_intents", "delivered_at")
    op.drop_column("donation_intents", "scheduled_for")
    op.add_column(
        "donation_intents",
        sa.Column("data_deleted_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
    )
    op.add_column(
        "donation_intents",
        sa.Column("data_retention_deadline", postgresql.TIMESTAMP(timezone=True), nullable=True),
    )
    op.add_column(
        "donation_intents",
        sa.Column("completed_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
    )
    op.add_column(
        "donation_intents",
        sa.Column("consented_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
    )
    op.add_column("donation_intents", sa.Column("phone", sa.VARCHAR(), nullable=True))
    op.add_column("donation_intents", sa.Column("donor_email", sa.VARCHAR(), nullable=True))
    op.add_column("donation_intents", sa.Column("donor_name", sa.VARCHAR(), nullable=True))
    op.create_index(
        op.f("ix_donation_intents_data_retention_deadline"),
        "donation_intents",
        ["data_retention_deadline"],
        unique=False,
    )


def replace_active_intent_index(condition: str) -> None:
    op.drop_index(UNIQUE_ACTIVE_INTENT_INDEX, table_name="donation_intents")
    op.create_index(
        UNIQUE_ACTIVE_INTENT_INDEX,
        "donation_intents",
        ["need_id", "donor_id"],
        unique=True,
        postgresql_where=sa.text(condition),
    )
