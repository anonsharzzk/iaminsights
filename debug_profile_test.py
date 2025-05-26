#!/usr/bin/env python3
"""
Debug Profile Update Issue
"""

import requests
import json

BACKEND_URL = "https://d602465a-6f1d-46f0-8a14-ab8451e05734.preview.emergentagent.com/api"

def debug_profile_update():
    """Debug the profile update issue"""
    print("🔍 DEBUGGING PROFILE UPDATE ISSUE")
    print("=" * 50)
    
    # Step 1: Login as admin and create a test user
    print("\n1. Creating test user...")
    admin_login = {"email": "adminn@iamsharan.com", "password": "Testing@123"}
    response = requests.post(f"{BACKEND_URL}/auth/login", json=admin_login, timeout=10)
    admin_token = response.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    user_data = {
        "email": "debugtest@company.com",
        "password": "TestPassword123",
        "role": "user"
    }
    response = requests.post(f"{BACKEND_URL}/users", headers=admin_headers, json=user_data, timeout=10)
    user_id = response.json()["id"]
    print(f"   Created user: {user_id}")
    
    # Step 2: Login as the test user
    print("\n2. Logging in as test user...")
    user_login = {"email": "debugtest@company.com", "password": "TestPassword123"}
    response = requests.post(f"{BACKEND_URL}/auth/login", json=user_login, timeout=10)
    user_token = response.json()["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}
    print(f"   User token received: {user_token[:50]}...")
    
    # Step 3: Verify token works
    print("\n3. Verifying token works...")
    response = requests.get(f"{BACKEND_URL}/auth/me", headers=user_headers, timeout=10)
    print(f"   /auth/me status: {response.status_code}")
    if response.status_code == 200:
        print(f"   User info: {response.json()}")
    
    # Step 4: Try profile update
    print("\n4. Attempting profile update...")
    profile_data = {"password": "NewPassword456"}
    response = requests.put(f"{BACKEND_URL}/auth/update-profile", headers=user_headers, json=profile_data, timeout=10)
    print(f"   Profile update status: {response.status_code}")
    print(f"   Response: {response.text}")
    
    # Step 5: Check if user was modified by admin
    print("\n5. Checking if user was modified...")
    response = requests.get(f"{BACKEND_URL}/users/all", headers=admin_headers, timeout=10)
    users = response.json()
    for user in users:
        if user["id"] == user_id:
            print(f"   Current user email: {user['email']}")
            break
    
    # Step 6: Try with fresh login after admin modification
    print("\n6. Testing with fresh login...")
    # First, admin updates the user email
    update_data = {"email": "debugtest_modified@company.com"}
    response = requests.put(f"{BACKEND_URL}/users/{user_id}", headers=admin_headers, json=update_data, timeout=10)
    print(f"   Admin update status: {response.status_code}")
    
    # Try to use old token
    response = requests.put(f"{BACKEND_URL}/auth/update-profile", headers=user_headers, json=profile_data, timeout=10)
    print(f"   Profile update with old token: {response.status_code}")
    
    # Login with new email
    new_login = {"email": "debugtest_modified@company.com", "password": "TestPassword123"}
    response = requests.post(f"{BACKEND_URL}/auth/login", json=new_login, timeout=10)
    if response.status_code == 200:
        new_token = response.json()["access_token"]
        new_headers = {"Authorization": f"Bearer {new_token}"}
        
        response = requests.put(f"{BACKEND_URL}/auth/update-profile", headers=new_headers, json=profile_data, timeout=10)
        print(f"   Profile update with new token: {response.status_code}")
    else:
        print(f"   New login failed: {response.status_code}")
    
    # Cleanup
    requests.delete(f"{BACKEND_URL}/users/{user_id}", headers=admin_headers, timeout=10)

if __name__ == "__main__":
    debug_profile_update()