# alembic/env.py - Fixed Migration Configuration
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool, text
from alembic import context
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Import your models and settings
try:
    from app.core.config import settings
    from app.core.database import Base
    
    # Import all models to ensure they're registered
    # User Service Models
    from app.models.user import User, UserRole, GenderType
    from app.models.user_token import (
        UserToken, 
        TokenType,
        CreatorAudienceDemographics,
        CreatorBadge,
        BadgeType
    )
    
    # Campaign Service Models (if running from campaign service)
    try:
        from app.models.campaign import (
            Campaign, 
            CampaignApplication, 
            Deliverable,
            CampaignStatus,
            PayoutModel,
            TrackingMethod,
            ApplicationStatus,
            DeliverableStatus
        )
    except ImportError:
        # Models not available in this service
        pass
        
except ImportError as e:
    print(f"Warning: Could not import some models: {e}")
    # Fallback configuration for development
    import os
    class MockSettings:
        DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost/launchpaid_db")
    settings = MockSettings()
    
    from sqlalchemy.ext.declarative import declarative_base
    Base = declarative_base()

# This is the Alembic Config object
config = context.config

# Set database URL from settings
if hasattr(settings, 'DATABASE_URL'):
    config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Model's MetaData object for autogenerate
target_metadata = Base.metadata

# Schema configuration for microservices
SCHEMAS = ['users', 'campaigns', 'analytics', 'payments', 'integrations']

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
        version_table_schema='public',  # Store migration version in public schema
        compare_type=True,
        compare_server_default=True,
        render_as_batch=False,
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    
    def create_engine_with_schemas():
        """Create engine and ensure schemas exist"""
        engine = engine_from_config(
            config.get_section(config.config_ini_section),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )
        
        # Create schemas if they don't exist
        with engine.connect() as connection:
            for schema in SCHEMAS:
                try:
                    connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
                    connection.commit()
                except Exception as e:
                    print(f"Warning: Could not create schema {schema}: {e}")
                    connection.rollback()
        
        return engine

    # Create engine with schema initialization
    connectable = create_engine_with_schemas()

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            include_object=include_schemas(SCHEMAS),
            version_table_schema='public',
            compare_type=True,
            compare_server_default=True,
            render_as_batch=False,
        )

        with context.begin_transaction():
            context.run_migrations()

# Run migrations based on context
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()