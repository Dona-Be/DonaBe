from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geography
from sqlalchemy.dialects import postgresql

revision: str = "fdb360768a1d"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("picture_url", sa.String(), nullable=True),
        sa.Column(
            "role",
            sa.Enum("donor", "manager", name="role", native_enum=False, length=30),
            nullable=False,
        ),
        sa.Column("session_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )
    op.create_geospatial_table(
        "institutions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cnpj", sa.String(length=14), nullable=False),
        sa.Column("legal_name", sa.String(), nullable=False),
        sa.Column("trade_name", sa.String(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column(
            "causes",
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
        sa.Column("street", sa.String(), nullable=False),
        sa.Column("number", sa.String(), nullable=False),
        sa.Column("complement", sa.String(), nullable=True),
        sa.Column("neighborhood", sa.String(), nullable=False),
        sa.Column("city", sa.String(), nullable=False),
        sa.Column("state", sa.String(length=2), nullable=False),
        sa.Column("postal_code", sa.String(length=8), nullable=False),
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
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("contact_email", sa.String(), nullable=True),
        sa.Column("website", sa.String(), nullable=True),
        sa.Column("instagram", sa.String(), nullable=True),
        sa.Column("facebook", sa.String(), nullable=True),
        sa.Column("pix_key", sa.String(), nullable=True),
        sa.Column(
            "verdict",
            sa.Enum(
                "likely_charity",
                "nonprofit",
                "inactive",
                "unlikely",
                name="verdict",
                native_enum=False,
                length=30,
            ),
            nullable=False,
        ),
        sa.Column("reasons", postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column("cnpj_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("manager_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["manager_id"], ["users.id"], name=op.f("fk_institutions_manager_id_users")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_institutions")),
        sa.UniqueConstraint("cnpj", name=op.f("uq_institutions_cnpj")),
    )
    op.create_geospatial_index(
        "idx_institutions_location",
        "institutions",
        ["location"],
        unique=False,
        postgresql_using="gist",
        postgresql_ops={},
    )
    op.create_index(
        "ix_institutions_causes", "institutions", ["causes"], unique=False, postgresql_using="gin"
    )
    op.create_index(
        op.f("ix_institutions_manager_id"), "institutions", ["manager_id"], unique=False
    )
    op.create_table(
        "needs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("institution_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column(
            "type",
            sa.Enum("items", "volunteers", "money", name="needtype", native_enum=False, length=30),
            nullable=False,
        ),
        sa.Column("quantity", sa.String(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("open", "fulfilled", "closed", name="needstatus", native_enum=False, length=30),
            nullable=False,
        ),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["institution_id"],
            ["institutions.id"],
            name=op.f("fk_needs_institution_id_institutions"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_needs")),
    )
    op.create_index(
        "ix_needs_institution_id_status", "needs", ["institution_id", "status"], unique=False
    )
    op.create_index(op.f("ix_needs_type"), "needs", ["type"], unique=False)
    op.create_table(
        "donation_intents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("need_id", sa.Integer(), nullable=False),
        sa.Column("donor_id", sa.Integer(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "registered",
                "in_contact",
                "completed",
                "cancelled",
                name="donationintentstatus",
                native_enum=False,
                length=30,
            ),
            nullable=False,
        ),
        sa.Column("donor_name", sa.String(), nullable=True),
        sa.Column("donor_email", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("message", sa.String(), nullable=True),
        sa.Column("consented_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("data_retention_deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("data_deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["donor_id"], ["users.id"], name=op.f("fk_donation_intents_donor_id_users")
        ),
        sa.ForeignKeyConstraint(
            ["need_id"], ["needs.id"], name=op.f("fk_donation_intents_need_id_needs")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_donation_intents")),
    )
    op.create_index(
        op.f("ix_donation_intents_data_retention_deadline"),
        "donation_intents",
        ["data_retention_deadline"],
        unique=False,
    )
    op.create_index(
        op.f("ix_donation_intents_donor_id"), "donation_intents", ["donor_id"], unique=False
    )
    op.create_index(
        op.f("ix_donation_intents_need_id"), "donation_intents", ["need_id"], unique=False
    )
    op.create_index(
        "uq_donation_intents_active_per_donor",
        "donation_intents",
        ["need_id", "donor_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('in_contact', 'registered')"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_donation_intents_active_per_donor",
        table_name="donation_intents",
        postgresql_where=sa.text("status IN ('in_contact', 'registered')"),
    )
    op.drop_index(op.f("ix_donation_intents_need_id"), table_name="donation_intents")
    op.drop_index(op.f("ix_donation_intents_donor_id"), table_name="donation_intents")
    op.drop_index(
        op.f("ix_donation_intents_data_retention_deadline"), table_name="donation_intents"
    )
    op.drop_table("donation_intents")
    op.drop_index(op.f("ix_needs_type"), table_name="needs")
    op.drop_index("ix_needs_institution_id_status", table_name="needs")
    op.drop_table("needs")
    op.drop_index(op.f("ix_institutions_manager_id"), table_name="institutions")
    op.drop_index("ix_institutions_causes", table_name="institutions", postgresql_using="gin")
    op.drop_geospatial_index(
        "idx_institutions_location",
        table_name="institutions",
        postgresql_using="gist",
        column_name="location",
    )
    op.drop_geospatial_table("institutions")
    op.drop_table("users")
