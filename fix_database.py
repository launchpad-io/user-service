# fix_database.py - Run this script to fix the enum issues
import sys
import os

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine, fix_enum_types, verify_db_setup
from app.models import Base
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Fix the database enum issues"""
    try:
        logger.info("Starting database fix...")
        
        # First, let's check the current state
        verify_db_setup()
        
        # Fix the enum types
        fix_enum_types()
        
        # Verify the fix
        verify_db_setup()
        
        logger.info("Database fix completed successfully!")
        
    except Exception as e:
        logger.error(f"Failed to fix database: {str(e)}")
        raise

if __name__ == "__main__":
    main()