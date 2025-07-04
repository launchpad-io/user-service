# test_imports.py
try:
    import fastapi
    import sqlalchemy
    import pydantic
    import redis
    import jose
    import passlib
    print("✅ All core imports successful!")
    print(f"FastAPI: {fastapi.__version__}")
    print(f"SQLAlchemy: {sqlalchemy.__version__}")
    print(f"Pydantic: {pydantic.__version__}")
except ImportError as e:
    print(f"❌ Import error: {e}")