# test_db_connection.py
from app.core.database import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("Database connected successfully!")
        
        # Check if users table exists
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'users'
            );
        """))
        table_exists = result.scalar()
        print(f"Users table exists: {table_exists}")
        
except Exception as e:
    print(f"Database connection failed: {e}")