import os
import sys
from logging.config import fileConfig
from app.db.base import Base
from app.db.models.user import User
from app.db.models.conversation import ChatConversation, ChatMessage

# Add project root directory to the python search path
sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
)

from sqlalchemy import pool
from alembic import context
import asyncio

# Import all models and Base to ensure they are registered on Metadata
from app.db.base import Base
from app.db.session import engine
from app.core.config import settings


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata for autogenerate support
target_metadata = Base.metadata

# Set sqlalchemy.url from our application configuration dynamically
config.set_main_option("sqlalchemy.url", "postgresql+asyncpg://postgres:Ai%405605@127.0.0.1:5433/aiclone".replace("%", "%%"))


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    async def run_async():
        async with engine.connect() as connection:
            await connection.run_sync(do_run_migrations)

    asyncio.run(run_async())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
