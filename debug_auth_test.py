#!/usr/bin/env python3
"""
Debug Authentication Issues
"""

import requests
import json

BACKEND_URL = "https://d602465a-6f1d-46f0-8a14-ab8451e05734.preview.emergentagent.com/api"
DEFAULT_ADMIN_EMAIL = "adminn@iamsharan.com"
DEFAULT_ADMIN_PASSWORD = "Testing@123"

def test_unauthenticated_access():
    """Test unauthenticated access - 403 vs 401"""
    print("=== Testing Unauthenticated Access ===")
    
    endpoints = ["/users", "/search/alice@company.com", "/providers", "/analytics"]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BACKEND_URL}{endpoint}", timeout=10)
            print(f"{endpoint}: Status {response.status_code}")
            if response.status_code not in [200, 401, 403]:
                print(f"  Response: {response.text[:200]}")
        except Exception as e:
            print(f"{endpoint}: Error - {e}")

def test_invalid_token_handling():
    """Test invalid token handling"""
    print("\n=== Testing Invalid Token Handling ===")
    
    invalid_tokens = [
        "invalid_token",
        "Bearer invalid_token", 
        "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid",
        ""
    ]
    
    for token in invalid_tokens:
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(f"{BACKEND_URL}/auth/me", headers=headers, timeout=10)
            print(f"Token '{token[:20]}...': Status {response.status_code}")
            if response.status_code == 500:
                print(f"  Error Response: {response.text[:200]}")
        except Exception as e:
            print(f"Token '{token[:20]}...': Error - {e}")

def test_profile_update_flow():
    """Test the profile update flow to understand the 401 issue"""
    print("\n=== Testing Profile Update Flow ===")
    
    # Login as admin
    login_data = {"email": DEFAULT_ADMIN_EMAIL, "password": DEFAULT_ADMIN_PASSWORD}
    response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data, timeout=10)
    
    if response.status_code != 200:
        print(f"Admin login failed: {response.status_code}")
        return
    
    admin_token = response.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Create a test user
    user_data = {
        "email": "profiletest@company.com",
        "password": "TestPassword123",
        "role": "user"
    }
    
    response = requests.post(f"{BACKEND_URL}/users", headers=admin_headers, json=user_data, timeout=10)
    if response.status_code != 200:
        print(f"User creation failed: {response.status_code}")
        return
    
    user_id = response.json()["id"]
    print(f"Created user with ID: {user_id}")
    
    # Login as the test user
    login_data = {"email": "profiletest@company.com", "password": "TestPassword123"}
    response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data, timeout=10)
    
    if response.status_code != 200:
        print(f"User login failed: {response.status_code}")
        return
    
    user_token = response.json()["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}
    
    # Test profile update
    update_data = {"password": "NewPassword456"}
    response = requests.put(f"{BACKEND_URL}/auth/update-profile", headers=user_headers, json=update_data, timeout=10)
    print(f"Profile update: Status {response.status_code}")
    if response.status_code != 200:
        print(f"  Response: {response.text}")
    
    # Clean up - delete the test user
    requests.delete(f"{BACKEND_URL}/users/{user_id}", headers=admin_headers, timeout=10)

def test_missing_auth_header():
    """Test requests with missing Authorization header"""
    print("\n=== Testing Missing Auth Header ===")
    
    try:
        response = requests.get(f"{BACKEND_URL}/auth/me", timeout=10)
        print(f"No auth header: Status {response.status_code}")
        print(f"  Response: {response.text[:200]}")
    except Exception as e:
        print(f"No auth header: Error - {e}")

if __name__ == "__main__":
    test_unauthenticated_access()
    test_invalid_token_handling()
    test_profile_update_flow()
    test_missing_auth_header()