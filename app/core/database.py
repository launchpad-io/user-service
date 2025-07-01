# app/core/database.py
from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import Pool
from typing import Generator
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Create engine with schema support
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.DEBUG,  # Log SQL in debug mode
    connect_args={
        "options": "-csearch_path=users"  # Set default schema search path
    }
)

# Event listener to ensure schema exists and set search path
@event.listens_for(Pool, "connect")
def set_schema_search_path(dbapi_conn, connection_record):
    """Set schema search path for each connection"""
    with dbapi_conn.cursor() as cursor:
        # Ensure users schema exists
        cursor.execute("CREATE SCHEMA IF NOT EXISTS users")
        # Ensure UUID extension is available
        cursor.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
        # Set search path to prioritize users schema
        cursor.execute("SET search_path TO users")
    logger.debug("Schema search path set to: users")

# Create SessionLocal class
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Create Base class
Base = declarative_base()

# Dependency to get DB session
def get_db() -> Generator:
    """
    Dependency function that yields database sessions.
    Ensures proper cleanup after request completion.
    """
    db = SessionLocal()
    try:
        # Set schema for this session
        db.execute(text("SET search_path TO users"))
        yield db
    finally:
        db.close()

# Database initialization function
def init_db():
    """Initialize database with required schemas and extensions"""
    with engine.begin() as conn:
        # Create schemas
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS users"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS campaigns"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS analytics"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS payments"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS integrations"))
        
        # Create extensions
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\""))
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"pgcrypto\""))
        
        # Create custom types in users schema
        conn.execute(text("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role' AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'users')) THEN
                    CREATE TYPE users.user_role AS ENUM ('agency', 'creator', 'brand', 'admin');
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'gender_type' AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'users')) THEN
                    CREATE TYPE users.gender_type AS ENUM ('male', 'female', 'non_binary', 'prefer_not_to_say');
                END IF;
            END
            $$;
        """))
        
        logger.info("Database schemas and types initialized successfully")

# Function to verify database setup
def verify_db_setup():
    """Verify that all required schemas and types exist"""
    with engine.begin() as conn:
        # Check schemas
        result = conn.execute(text("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name IN ('users', 'campaigns', 'analytics', 'payments', 'integrations')
        """))
        schemas = [row[0] for row in result]
        
        missing_schemas = {'users', 'campaigns', 'analytics', 'payments', 'integrations'} - set(schemas)
        if missing_schemas:
            logger.warning(f"Missing schemas: {missing_schemas}")
            init_db()
        
        # Check enum types
        result = conn.execute(text("""
            SELECT t.typname, n.nspname
            FROM pg_type t
            JOIN pg_namespace n ON n.oid = t.typnamespace
            WHERE t.typname IN ('user_role', 'gender_type')
            AND n.nspname = 'users'
        """))
        types = [(row[0], row[1]) for row in result]
        
        if len(types) < 2:
            logger.warning("Missing enum types, reinitializing...")
            init_db()
        
        logger.info("Database setup verified successfully")