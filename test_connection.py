# user-service/test_connection.py
# Quick test to verify frontend-backend connection

import requests
import json

# Test configuration
BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Health Check: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_register():
    """Test registration endpoint"""
    try:
        data = {
            "email": "test@example.com",
            "password": "password123",
            "firstName": "Test",
            "lastName": "User",
            "username": "testuser",
            "role": "creator"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/register",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Register: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code in [200, 201, 400]  # 400 if user exists
    except Exception as e:
        print(f"Register test failed: {e}")
        return False

def test_login():
    """Test login endpoint"""
    try:
        data = {
            "email": "test@example.com",
            "password": "password123"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Login: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code in [200, 401]  # 401 if email not verified
    except Exception as e:
        print(f"Login test failed: {e}")
        return False

def test_cors():
    """Test CORS headers"""
    try:
        response = requests.options(
            f"{BASE_URL}/api/v1/auth/login",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            }
        )
        
        print(f"CORS: {response.status_code}")
        print(f"CORS Headers: {dict(response.headers)}")
        return "access-control-allow-origin" in response.headers
    except Exception as e:
        print(f"CORS test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing User Service Connection...")
    print("=" * 50)
    
    # Run tests
    tests = [
        ("Health Check", test_health),
        ("CORS", test_cors),
        ("Register", test_register),
        ("Login", test_login),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n🔍 Testing {name}...")
        success = test_func()
        results.append((name, success))
        print(f"{'✅' if success else '❌'} {name}: {'PASS' if success else 'FAIL'}")
    
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    for name, success in results:
        print(f"{'✅' if success else '❌'} {name}")
    
    all_passed = all(success for _, success in results)
    print(f"\n{'🎉 All tests passed!' if all_passed else '⚠️  Some tests failed'}")
    
    if not all_passed:
        print("\n💡 Troubleshooting tips:")
        print("1. Make sure your user service is running: uvicorn app.main:app --reload")
        print("2. Check database connection")
        print("3. Verify CORS configuration")
        print("4. Check endpoint paths match frontend expectations")