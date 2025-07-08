# app/core/database.py
from sqlalchemy import create_engine, event, text, inspect
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

# Database initialization function - SAFE VERSION
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
        
        # Create enum types ONLY if they don't exist
        # DO NOT use CASCADE as it drops all dependent tables!
        conn.execute(text("""
            DO $$ 
            BEGIN
                -- Only create if not exists
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role' AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'users')) THEN
                    CREATE TYPE users.user_role AS ENUM ('agency', 'creator', 'brand', 'admin');
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'gender_type' AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'users')) THEN
                    CREATE TYPE users.gender_type AS ENUM ('male', 'female', 'non_binary', 'prefer_not_to_say');
                END IF;
            END $$;
        """))
        
        logger.info("Database schemas and types initialized successfully")
        
        # Ensure tables exist
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names(schema='users')
        
        if 'users' not in existing_tables:
            logger.info("Creating database tables...")
            from app.models import Base
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created successfully")
        else:
            # IMPORTANT: Ensure role column exists without dropping anything
            logger.info("Ensuring role column exists in users table...")
            conn.execute(text("""
                ALTER TABLE users.users 
                ADD COLUMN IF NOT EXISTS role users.user_role NOT NULL DEFAULT 'creator'
            """))
            
            # Add any other missing columns
            conn.execute(text("""
                ALTER TABLE users.users
                ADD COLUMN IF NOT EXISTS first_name VARCHAR(100),
                ADD COLUMN IF NOT EXISTS last_name VARCHAR(100),
                ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            """))
            
            logger.info("Database structure verified and updated")

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
        
        logger.info(f"Found schemas: {schemas}")
        
        # Check if users table exists and has role column
        result = conn.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'users' 
            AND table_name = 'users'
            AND column_name = 'role'
        """))
        
        if result.rowcount == 0:
            logger.warning("Role column missing - adding it now...")
            conn.execute(text("""
                ALTER TABLE users.users 
                ADD COLUMN IF NOT EXISTS role users.user_role NOT NULL DEFAULT 'creator'
            """))
            logger.info("Role column added successfully")
        else:
            logger.info("Role column exists")
        
        # Check enum types and their values
        result = conn.execute(text("""
            SELECT 
                t.typname,
                array_agg(e.enumlabel ORDER BY e.enumsortorder) as enum_values
            FROM pg_type t 
            JOIN pg_enum e ON t.oid = e.enumtypid
            JOIN pg_namespace n ON n.oid = t.typnamespace
            WHERE t.typname IN ('user_role', 'gender_type')
            AND n.nspname = 'users'
            GROUP BY t.typname
        """))
        
        for row in result:
            logger.info(f"Enum {row[0]} has values: {row[1]}")
        
        logger.info("Database setup verified successfully")

# DANGER ZONE - Only use these for development
def recreate_tables():
    """Drop and recreate all tables - USE WITH CAUTION!"""
    response = input("⚠️  WARNING: This will DELETE all data. Type 'yes' to confirm: ")
    if response.lower() != 'yes':
        logger.info("Operation cancelled")
        return
    
    from app.models import Base
    
    with engine.begin() as conn:
        # Drop all tables
        Base.metadata.drop_all(bind=engine)
        logger.info("All tables dropped")
        
        # Recreate all tables
        Base.metadata.create_all(bind=engine)
        logger.info("All tables created")

def fix_enum_types():
    """Fix enum types if they have wrong values - DO NOT USE IN PRODUCTION"""
    logger.warning("This function should not be used in production as it drops tables!")
    response = input("⚠️  WARNING: This may DELETE data. Type 'yes' to confirm: ")
    if response.lower() != 'yes':
        logger.info("Operation cancelled")
        return
    
    with engine.begin() as conn:
        try:
            # Check current enum values
            result = conn.execute(text("""
                SELECT enumlabel 
                FROM pg_enum e 
                JOIN pg_type t ON e.enumtypid = t.oid 
                JOIN pg_namespace n ON t.typnamespace = n.oid
                WHERE t.typname = 'user_role' AND n.nspname = 'users'
            """))
            
            values = [row[0] for row in result]
            logger.info(f"Current user_role values: {values}")
            
            # If values are uppercase, we need to recreate the type
            if any(v.isupper() for v in values):
                logger.info("Found uppercase values, recreating enum types...")
                
                # First, we need to drop the tables that use these types
                conn.execute(text("DROP TABLE IF EXISTS users.creator_badges CASCADE"))
                conn.execute(text("DROP TABLE IF EXISTS users.creator_audience_demographics CASCADE"))
                conn.execute(text("DROP TABLE IF EXISTS users.user_tokens CASCADE"))
                conn.execute(text("DROP TABLE IF EXISTS users.users CASCADE"))
                
                # Now drop and recreate the types
                conn.execute(text("DROP TYPE IF EXISTS users.user_role CASCADE"))
                conn.execute(text("DROP TYPE IF EXISTS users.gender_type CASCADE"))
                
                # Recreate with lowercase values
                conn.execute(text("CREATE TYPE users.user_role AS ENUM ('agency', 'creator', 'brand', 'admin')"))
                conn.execute(text("CREATE TYPE users.gender_type AS ENUM ('male', 'female', 'non_binary', 'prefer_not_to_say')"))
                
                logger.info("Enum types recreated with lowercase values")
                
                # Now recreate the tables
                from app.models import Base
                Base.metadata.create_all(bind=engine)
                logger.info("Tables recreated")
                
        except Exception as e:
            logger.error(f"Error fixing enum types: {str(e)}")
            raise