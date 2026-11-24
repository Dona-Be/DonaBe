from collections.abc import Sequence

from alembic import op

revision: str = "c443bdbda40f"
down_revision: str | None = "87fc760b8643"
branch_labels: str | Sequence[str] | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")


def downgrade() -> None:
    # Keep this extension if another database feature already depends on it.
    pass
