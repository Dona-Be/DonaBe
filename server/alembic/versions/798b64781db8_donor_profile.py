from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geography
from sqlalchemy.dialects import postgresql

revision: str = "798b64781db8"
down_revision: str | None = "394ee7ff2a66"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("phone", sa.String(length=11), nullable=True))
    op.add_column("users", sa.Column("postal_code", sa.String(length=8), nullable=True))
    # Autogenerate does not render check constraints, so these two are written by hand.
    op.create_check_constraint(
        op.f("ck_users_phone_has_10_or_11_digits"), "users", "phone ~ '^[0-9]{10,11}$'"
    )
    op.create_check_constraint(
        op.f("ck_users_postal_code_has_8_digits"), "users", "postal_code ~ '^[0-9]{8}$'"
    )
    op.add_geospatial_column(
        "users",
        sa.Column(
            "location",
            Geography(
                geometry_type="POINT",
                srid=4326,
                dimension=2,
                spatial_index=False,
                from_text="ST_GeogFromText",
                name="geography",
            ),
            nullable=True,
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "preferred_causes",
            postgresql.ARRAY(
                sa.Enum(
                    "children_and_teenagers",
                    "elderly",
                    "people_with_disabilities",
                    "health",
                    "education",
                    "hunger_relief",
                    "homeless_people",
                    "women",
                    "animals",
                    "environment",
                    name="cause",
                    native_enum=False,
                    length=30,
                )
            ),
            server_default="{}",
            nullable=False,
        ),
    )
    op.create_geospatial_index(
        "idx_users_location",
        "users",
        ["location"],
        unique=False,
        postgresql_using="gist",
        postgresql_ops={},
    )


def downgrade() -> None:
    op.drop_geospatial_index(
        "idx_users_location",
        table_name="users",
        postgresql_using="gist",
        column_name="location",
    )
    op.drop_column("users", "preferred_causes")
    op.drop_geospatial_column("users", "location")
    # Dropping a column also drops its check constraint.
    op.drop_column("users", "postal_code")
    op.drop_column("users", "phone")
