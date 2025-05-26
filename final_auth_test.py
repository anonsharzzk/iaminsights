#!/usr/bin/env python3
"""
Final Comprehensive Authentication Test
"""

import requests
import json

BACKEND_URL = "https://d602465a-6f1d-46f0-8a14-ab8451e05734.preview.emergentagent.com/api"
DEFAULT_ADMIN_EMAIL = "adminn@iamsharan.com"
DEFAULT_ADMIN_PASSWORD = "Testing@123"

def test_comprehensive_auth_flow():
    """Test the complete authentication flow"""
    print("🔐 COMPREHENSIVE AUTHENTICATION FLOW TEST")
    print("=" * 60)
    
    results = {"passed": 0, "total": 0}
    
    # Test 1: Admin Login
    print("\n1. Testing Admin Login...")
    results["total"] += 1
    login_data = {"email": DEFAULT_ADMIN_EMAIL, "password": DEFAULT_ADMIN_PASSWORD}
    response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data, timeout=10)
    
    if response.status_code == 200 and "access_token" in response.json():
        admin_token = response.json()["access_token"]
        print("   ✅ Admin login successful")
        results["passed"] += 1
    else:
        print(f"   ❌ Admin login failed: {response.status_code}")
        return results
    
    # Test 2: Get Current User
    print("\n2. Testing Get Current User...")
    results["total"] += 1
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = requests.get(f"{BACKEND_URL}/auth/me", headers=headers, timeout=10)
    
    if response.status_code == 200 and response.json().get("email") == DEFAULT_ADMIN_EMAIL:
        print("   ✅ Get current user successful")
        results["passed"] += 1
    else:
        print(f"   ❌ Get current user failed: {response.status_code}")
    
    # Test 3: Create User (Admin Only)
    print("\n3. Testing Create User (Admin Only)...")
    results["total"] += 1
    user_data = {
        "email": "finaltest@company.com",
        "password": "TestPassword123",
        "role": "user"
    }
    response = requests.post(f"{BACKEND_URL}/users", headers=headers, json=user_data, timeout=10)
    
    if response.status_code == 200:
        user_id = response.json().get("id")
        print("   ✅ User creation successful")
        results["passed"] += 1
    else:
        print(f"   ❌ User creation failed: {response.status_code}")
        return results
    
    # Test 4: Login as Regular User
    print("\n4. Testing Regular User Login...")
    results["total"] += 1
    login_data = {"email": "finaltest@company.com", "password": "TestPassword123"}
    response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data, timeout=10)
    
    if response.status_code == 200 and "access_token" in response.json():
        user_token = response.json()["access_token"]
        print("   ✅ Regular user login successful")
        results["passed"] += 1
    else:
        print(f"   ❌ Regular user login failed: {response.status_code}")
        return results
    
    # Test 5: Non-Admin Access Restriction
    print("\n5. Testing Non-Admin Access Restriction...")
    results["total"] += 1
    user_headers = {"Authorization": f"Bearer {user_token}"}
    response = requests.get(f"{BACKEND_URL}/users/all", headers=user_headers, timeout=10)
    
    if response.status_code == 403:
        print("   ✅ Non-admin access correctly restricted")
        results["passed"] += 1
    else:
        print(f"   ❌ Non-admin access restriction failed: {response.status_code}")
    
    # Test 6: Get All Users (Admin Only)
    print("\n6. Testing Get All Users (Admin Only)...")
    results["total"] += 1
    response = requests.get(f"{BACKEND_URL}/users/all", headers=headers, timeout=10)
    
    if response.status_code == 200 and isinstance(response.json(), list):
        print(f"   ✅ Get all users successful ({len(response.json())} users)")
        results["passed"] += 1
    else:
        print(f"   ❌ Get all users failed: {response.status_code}")
    
    # Test 7: Update User (Admin Only)
    print("\n7. Testing Update User (Admin Only)...")
    results["total"] += 1
    update_data = {"email": "finaltest_updated@company.com"}
    response = requests.put(f"{BACKEND_URL}/users/{user_id}", headers=headers, json=update_data, timeout=10)
    
    if response.status_code == 200:
        print("   ✅ User update successful")
        results["passed"] += 1
    else:
        print(f"   ❌ User update failed: {response.status_code}")
    
    # Test 8: Update Own Profile
    print("\n8. Testing Update Own Profile...")
    results["total"] += 1
    profile_data = {"password": "NewPassword456"}
    response = requests.put(f"{BACKEND_URL}/auth/update-profile", headers=user_headers, json=profile_data, timeout=10)
    
    if response.status_code == 200:
        print("   ✅ Profile update successful")
        results["passed"] += 1
    else:
        print(f"   ❌ Profile update failed: {response.status_code}")
    
    # Test 9: Provider Samples (Authenticated)
    print("\n9. Testing Provider Samples (Authenticated)...")
    results["total"] += 1
    response = requests.get(f"{BACKEND_URL}/providers/samples", headers=headers, timeout=10)
    
    if response.status_code == 200 and "aws" in response.json():
        print("   ✅ Provider samples accessible with auth")
        results["passed"] += 1
    else:
        print(f"   ❌ Provider samples failed: {response.status_code}")
    
    # Test 10: Protected Endpoints with Auth
    print("\n10. Testing Protected Endpoints with Auth...")
    results["total"] += 1
    endpoints = ["/users", "/providers", "/analytics"]
    all_passed = True
    
    for endpoint in endpoints:
        response = requests.get(f"{BACKEND_URL}{endpoint}", headers=headers, timeout=10)
        if response.status_code != 200:
            all_passed = False
            print(f"    ❌ {endpoint}: {response.status_code}")
        else:
            print(f"    ✅ {endpoint}: accessible")
    
    if all_passed:
        print("   ✅ All protected endpoints accessible with auth")
        results["passed"] += 1
    else:
        print("   ❌ Some protected endpoints failed")
    
    # Test 11: Authentication Protection (Unauthenticated)
    print("\n11. Testing Authentication Protection...")
    results["total"] += 1
    protected_endpoints = ["/users", "/analytics", "/providers/samples"]
    all_protected = True
    
    for endpoint in protected_endpoints:
        response = requests.get(f"{BACKEND_URL}{endpoint}", timeout=10)
        if response.status_code not in [401, 403]:
            all_protected = False
            print(f"    ❌ {endpoint}: Expected 401/403, got {response.status_code}")
        else:
            print(f"    ✅ {endpoint}: protected ({response.status_code})")
    
    if all_protected:
        print("   ✅ All endpoints properly protected")
        results["passed"] += 1
    else:
        print("   ❌ Some endpoints not properly protected")
    
    # Test 12: Delete User (Admin Only)
    print("\n12. Testing Delete User (Admin Only)...")
    results["total"] += 1
    response = requests.delete(f"{BACKEND_URL}/users/{user_id}", headers=headers, timeout=10)
    
    if response.status_code == 200:
        print("   ✅ User deletion successful")
        results["passed"] += 1
    else:
        print(f"   ❌ User deletion failed: {response.status_code}")
    
    # Test 13: Admin Cannot Delete Self
    print("\n13. Testing Admin Cannot Delete Self...")
    results["total"] += 1
    
    # Get admin user ID first
    response = requests.get(f"{BACKEND_URL}/users/all", headers=headers, timeout=10)
    admin_user_id = None
    if response.status_code == 200:
        users = response.json()
        for user in users:
            if user.get("email") == DEFAULT_ADMIN_EMAIL:
                admin_user_id = user.get("id")
                break
    
    if admin_user_id:
        response = requests.delete(f"{BACKEND_URL}/users/{admin_user_id}", headers=headers, timeout=10)
        if response.status_code == 400:
            print("   ✅ Admin correctly prevented from deleting self")
            results["passed"] += 1
        else:
            print(f"   ❌ Admin self-deletion not prevented: {response.status_code}")
    else:
        print("   ❌ Could not find admin user ID")
    
    return results

if __name__ == "__main__":
    results = test_comprehensive_auth_flow()
    
    print("\n" + "=" * 60)
    print("🏁 FINAL AUTHENTICATION TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {results['total']}")
    print(f"✅ Passed: {results['passed']}")
    print(f"❌ Failed: {results['total'] - results['passed']}")
    
    success_rate = (results['passed'] / results['total']) * 100 if results['total'] > 0 else 0
    print(f"📊 Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print("🎉 EXCELLENT: Authentication system is working excellently!")
    elif success_rate >= 80:
        print("✅ VERY GOOD: Authentication system is working very well!")
    elif success_rate >= 70:
        print("✅ GOOD: Authentication system is working well with minor issues")
    else:
        print("⚠️ NEEDS IMPROVEMENT: Authentication system has some issues")