from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "804500cbdbee"
down_revision: str | None = "fdb360768a1d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Nothing creates institutions yet, so the table is empty and the new column needs no default.
    op.add_column(
        "institutions",
        sa.Column(
            "type",
            sa.Enum(
                "association",
                "foundation",
                "religious_organization",
                name="institutiontype",
                native_enum=False,
                length=30,
            ),
            nullable=False,
        ),
    )
    op.drop_column("institutions", "pix_key")


def downgrade() -> None:
    op.add_column("institutions", sa.Column("pix_key", sa.String(), nullable=True))
    op.drop_column("institutions", "type")
