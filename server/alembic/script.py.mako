<%!
    def strip_alembic_comments(commands):
        lines = [line for line in commands.splitlines() if not line.lstrip().startswith("#")]
        return "\n".join(lines).strip()
%>\
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
${imports if imports else ""}

revision: str = ${repr(up_revision)}
down_revision: str | None = ${repr(down_revision)}
branch_labels: str | Sequence[str] | None = ${repr(branch_labels)}
depends_on: str | Sequence[str] | None = ${repr(depends_on)}


def upgrade() -> None:
    ${strip_alembic_comments(upgrades or "") or "pass"}


def downgrade() -> None:
    ${strip_alembic_comments(downgrades or "") or "pass"}
