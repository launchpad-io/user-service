# alembic/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool, text
from alembic import context
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Import your models and settings
from app.core.config import settings
from app.core.database import Base
# Import all models to ensure they're registered
from app.models import (
    User, UserToken, CreatorAudienceDemographics, CreatorBadge
)

# this is the Alembic Config object
config = context.config

# Set database URL from settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Model's MetaData object for autogenerate
target_metadata = Base.metadata

# Schema configuration
SCHEMAS = ['users', 'campaigns', 'analytics', 'payments', 'integrations', 'public']

def include_schemas(names):
    """Helper to include our schemas in migrations"""
    def include_schema(name, reflected, opts):
        return name in names
    return include_schema

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        include_object=include_schemas(SCHEMAS),
        version_table_schema='public',
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    
    # Create custom engine with schema creation
    def create_engine_with_schemas():
        engine = engine_from_config(
            config.get_section(config.config_ini_section),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
            connect_args={
                "options": "-csearch_path=users,public"
            }
        )
        
        # Ensure schemas exist before running migrations
        with engine.connect() as connection:
            for schema in SCHEMAS:
                if schema != 'public':  # public always exists
                    connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
                    connection.commit()
            
            # Ensure extensions
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\""))
            connection.commit()
            
        return engine
    
    connectable = create_engine_with_schemas()

    with connectable.connect() as connection:
        # Set search path for the migration
        connection.execute(text("SET search_path TO users, public"))
        
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            include_object=include_schemas(SCHEMAS),
            version_table_schema='public',  # Keep alembic version table in public
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()