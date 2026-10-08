from alembic.config import Config

from alembic import command


def test_migration_matches_the_models(alembic_config: Config, migrated_database: None) -> None:
    command.check(alembic_config)


def test_migration_downgrades_and_upgrades_again(
    alembic_config: Config, migrated_database: None
) -> None:
    command.downgrade(alembic_config, "base")
    command.upgrade(alembic_config, "head")
    command.check(alembic_config)
