from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "87fc760b8643"
down_revision: str | None = "459605f451f5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "donation_intents", sa.Column("contacted_at", sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("donation_intents", "contacted_at")
