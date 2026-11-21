from collections.abc import Sequence

from alembic import op

revision: str = "d2fab64bd59e"
down_revision: str | None = "87fc760b8643"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")


def downgrade() -> None:
    op.execute("DROP EXTENSION IF EXISTS unaccent")
