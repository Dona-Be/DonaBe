from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "394ee7ff2a66"
down_revision: str | None = "804500cbdbee"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index(op.f("ix_needs_type"), table_name="needs")
    op.drop_column("needs", "type")


def downgrade() -> None:
    # Every need is an item need, so the existing rows get "items" before the default is removed.
    op.add_column(
        "needs",
        sa.Column(
            "type",
            sa.Enum("items", "volunteers", "money", name="needtype", native_enum=False, length=30),
            server_default="items",
            nullable=False,
        ),
    )
    op.alter_column("needs", "type", server_default=None)
    op.create_index(op.f("ix_needs_type"), "needs", ["type"], unique=False)
