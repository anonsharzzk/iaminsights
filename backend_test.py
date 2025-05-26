#!/usr/bin/env python3
"""
Comprehensive Backend Authentication and User Management Testing
Tests all authentication features and protected endpoints
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, Any, Optional

# Configuration
BACKEND_URL = "https://d602465a-6f1d-46f0-8a14-ab8451e05734.preview.emergentagent.com/api"
DEFAULT_ADMIN_EMAIL = "adminn@iamsharan.com"
DEFAULT_ADMIN_PASSWORD = "Testing@123"

class AuthenticationTester:
    def __init__(self):
        self.admin_token = None
        self.user_token = None
        self.test_user_id = None
        self.results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "errors": []
        }
    
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test results"""
        self.results["total_tests"] += 1
        if passed:
            self.results["passed"] += 1
            print(f"✅ {test_name}: PASSED {details}")
        else:
            self.results["failed"] += 1
            self.results["errors"].append(f"{test_name}: {details}")
            print(f"❌ {test_name}: FAILED {details}")
    
    def make_request(self, method: str, endpoint: str, headers: Dict = None, data: Dict = None, files: Dict = None) -> requests.Response:
        """Make HTTP request with error handling"""
        url = f"{BACKEND_URL}{endpoint}"
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=30)
            elif method.upper() == "POST":
                if files:
                    response = requests.post(url, headers=headers, files=files, timeout=30)
                else:
                    response = requests.post(url, headers=headers, json=data, timeout=30)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json=data, timeout=30)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            return response
        except requests.exceptions.RequestException as e:
            print(f"Request error for {method} {url}: {e}")
            raise
    
    def test_1_default_admin_login(self):
        """Test 1: Login with default admin credentials"""
        print("\n=== Test 1: Default Admin Login ===")
        
        login_data = {
            "email": DEFAULT_ADMIN_EMAIL,
            "password": DEFAULT_ADMIN_PASSWORD
        }
        
        try:
            response = self.make_request("POST", "/auth/login", data=login_data)
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data and "user" in data:
                    self.admin_token = data["access_token"]
                    user_info = data["user"]
                    
                    # Verify admin role
                    if user_info.get("role") == "admin" and user_info.get("email") == DEFAULT_ADMIN_EMAIL:
                        self.log_test("Default Admin Login", True, f"Token received, role: {user_info.get('role')}")
                    else:
                        self.log_test("Default Admin Login", False, f"Invalid user role or email: {user_info}")
                else:
                    self.log_test("Default Admin Login", False, f"Missing token or user in response: {data}")
            else:
                self.log_test("Default Admin Login", False, f"Status: {response.status_code}, Response: {response.text}")
        
        except Exception as e:
            self.log_test("Default Admin Login", False, f"Exception: {str(e)}")
    
    def test_2_get_current_user(self):
        """Test 2: Get current user info with JWT token"""
        print("\n=== Test 2: Get Current User Info ===")
        
        if not self.admin_token:
            self.log_test("Get Current User", False, "No admin token available")
            return
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            response = self.make_request("GET", "/auth/me", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("email") == DEFAULT_ADMIN_EMAIL and data.get("role") == "admin":
                    self.log_test("Get Current User", True, f"User info retrieved: {data.get('email')}")
                else:
                    self.log_test("Get Current User", False, f"Invalid user data: {data}")
            else:
                self.log_test("Get Current User", False, f"Status: {response.status_code}, Response: {response.text}")
        
        except Exception as e:
            self.log_test("Get Current User", False, f"Exception: {str(e)}")
    
    def test_3_unauthenticated_access(self):
        """Test 3: Verify protected endpoints require authentication"""
        print("\n=== Test 3: Unauthenticated Access Protection ===")
        
        protected_endpoints = [
            "/users",
            "/search/alice@company.com",
            "/providers",
            "/analytics",
            "/providers/samples"
        ]
        
        passed_count = 0
        for endpoint in protected_endpoints:
            try:
                response = self.make_request("GET", endpoint)
                
                if response.status_code == 401:
                    passed_count += 1
                    print(f"  ✅ {endpoint}: Correctly returns 401")
                else:
                    print(f"  ❌ {endpoint}: Expected 401, got {response.status_code}")
            
            except Exception as e:
                print(f"  ❌ {endpoint}: Exception: {str(e)}")
        
        if passed_count == len(protected_endpoints):
            self.log_test("Unauthenticated Access Protection", True, f"All {len(protected_endpoints)} endpoints protected")
        else:
            self.log_test("Unauthenticated Access Protection", False, f"Only {passed_count}/{len(protected_endpoints)} endpoints protected")
    
    def test_4_create_user_admin_only(self):
        """Test 4: Create new user (admin only)"""
        print("\n=== Test 4: Create User (Admin Only) ===")
        
        if not self.admin_token:
            self.log_test("Create User", False, "No admin token available")
            return
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        user_data = {
            "email": "testuser@company.com",
            "password": "TestPassword123",
            "role": "user"
        }
        
        try:
            response = self.make_request("POST", "/users", headers=headers, data=user_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("email") == user_data["email"] and data.get("role") == "user":
                    self.test_user_id = data.get("id")
                    self.log_test("Create User", True, f"User created: {data.get('email')}, ID: {self.test_user_id}")
                else:
                    self.log_test("Create User", False, f"Invalid user data returned: {data}")
            else:
                self.log_test("Create User", False, f"Status: {response.status_code}, Response: {response.text}")
        
        except Exception as e:
            self.log_test("Create User", False, f"Exception: {str(e)}")
    
    def test_5_login_regular_user(self):
        """Test 5: Login with regular user credentials"""
        print("\n=== Test 5: Regular User Login ===")
        
        login_data = {
            "email": "testuser@company.com",
            "password": "TestPassword123"
        }
        
        try:
            response = self.make_request("POST", "/auth/login", data=login_data)
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data and "user" in data:
                    self.user_token = data["access_token"]
                    user_info = data["user"]
                    
                    if user_info.get("role") == "user" and user_info.get("email") == "testuser@company.com":
                        self.log_test("Regular User Login", True, f"User logged in, role: {user_info.get('role')}")
                    else:
                        self.log_test("Regular User Login", False, f"Invalid user role or email: {user_info}")
                else:
                    self.log_test("Regular User Login", False, f"Missing token or user in response: {data}")
            else:
                self.log_test("Regular User Login", False, f"Status: {response.status_code}, Response: {response.text}")
        
        except Exception as e:
            self.log_test("Regular User Login", False, f"Exception: {str(e)}")
    
    def test_6_non_admin_access_restriction(self):
        """Test 6: Verify non-admin users cannot access admin endpoints"""
        print("\n=== Test 6: Non-Admin Access Restriction ===")
        
        if not self.user_token:
            self.log_test("Non-Admin Access Restriction", False, "No user token available")
            return
        
        headers = {"Authorization": f"Bearer {self.user_token}"}
        admin_endpoints = [
            ("/users/all", "GET"),
            ("/users", "POST"),
        ]
        
        passed_count = 0
        for endpoint, method in admin_endpoints:
            try:
                if method == "GET":
                    response = self.make_request("GET", endpoint, headers=headers)
                else:
                    response = self.make_request("POST", endpoint, headers=headers, data={"email": "test@test.com", "password": "test", "role": "user"})
                
                if response.status_code == 403:
                    passed_count += 1
                    print(f"  ✅ {method} {endpoint}: Correctly returns 403")
                else:
                    print(f"  ❌ {method} {endpoint}: Expected 403, got {response.status_code}")
            
            except Exception as e:
                print(f"  ❌ {method} {endpoint}: Exception: {str(e)}")
        
        if passed_count == len(admin_endpoints):
            self.log_test("Non-Admin Access Restriction", True, f"All {len(admin_endpoints)} admin endpoints restricted")
        else:
            self.log_test("Non-Admin Access Restriction", False, f"Only {passed_count}/{len(admin_endpoints)} admin endpoints restricted")
    
    def test_7_get_all_users_admin(self):
        """Test 7: Get all system users (admin only)"""
        print("\n=== Test 7: Get All System Users (Admin Only) ===")
        
        if not self.admin_token:
            self.log_test("Get All Users", False, "No admin token available")
            return
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            response = self.make_request("GET", "/users/all", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) >= 2:  # Should have admin + test user
                    emails = [user.get("email") for user in data]
                    if DEFAULT_ADMIN_EMAIL in emails and "testuser@company.com" in emails:
                        self.log_test("Get All Users", True, f"Retrieved {len(data)} users including admin and test user")
                    else:
                        self.log_test("Get All Users", False, f"Missing expected users. Found: {emails}")
                else:
                    self.log_test("Get All Users", False, f"Invalid response format or insufficient users: {data}")
            else:
                self.log_test("Get All Users", False, f"Status: {response.status_code}, Response: {response.text}")
        
        except Exception as e:
            self.log_test("Get All Users", False, f"Exception: {str(e)}")
    
    def test_8_update_user_admin(self):
        """Test 8: Update user (admin only)"""
        print("\n=== Test 8: Update User (Admin Only) ===")
        
        if not self.admin_token or not self.test_user_id:
            self.log_test("Update User", False, "No admin token or test user ID available")
            return
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        update_data = {
            "email": "updateduser@company.com"
        }
        
        try:
            response = self.make_request("PUT", f"/users/{self.test_user_id}", headers=headers, data=update_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("email") == "updateduser@company.com":
                    self.log_test("Update User", True, f"User updated successfully: {data.get('email')}")
                else:
                    self.log_test("Update User", False, f"Email not updated correctly: {data}")
            else:
                self.log_test("Update User", False, f"Status: {response.status_code}, Response: {response.text}")
        
        except Exception as e:
            self.log_test("Update User", False, f"Exception: {str(e)}")
    
    def test_9_update_own_profile(self):
        """Test 9: Update own profile"""
        print("\n=== Test 9: Update Own Profile ===")
        
        if not self.user_token:
            self.log_test("Update Own Profile", False, "No user token available")
            return
        
        headers = {"Authorization": f"Bearer {self.user_token}"}
        update_data = {
            "password": "NewPassword123"
        }
        
        try:
            response = self.make_request("PUT", "/auth/update-profile", headers=headers, data=update_data)
            
            if response.status_code == 200:
                data = response.json()
                if "email" in data:
                    self.log_test("Update Own Profile", True, f"Profile updated for: {data.get('email')}")
                else:
                    self.log_test("Update Own Profile", False, f"Invalid response format: {data}")
            else:
                self.log_test("Update Own Profile", False, f"Status: {response.status_code}, Response: {response.text}")
        
        except Exception as e:
            self.log_test("Update Own Profile", False, f"Exception: {str(e)}")
    
    def test_10_provider_samples_authenticated(self):
        """Test 10: Get provider samples (authenticated)"""
        print("\n=== Test 10: Provider Samples (Authenticated) ===")
        
        if not self.admin_token:
            self.log_test("Provider Samples", False, "No admin token available")
            return
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            # Test all provider samples
            response = self.make_request("GET", "/providers/samples", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                expected_providers = ["aws", "gcp", "azure", "okta"]
                if all(provider in data for provider in expected_providers):
                    self.log_test("All Provider Samples", True, f"Retrieved samples for: {list(data.keys())}")
                else:
                    self.log_test("All Provider Samples", False, f"Missing providers. Found: {list(data.keys())}")
            else:
                self.log_test("All Provider Samples", False, f"Status: {response.status_code}, Response: {response.text}")
            
            # Test specific provider sample
            response = self.make_request("GET", "/providers/samples/aws", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("provider") == "aws" and "sample_format" in data:
                    self.log_test("Specific Provider Sample", True, f"AWS sample retrieved with format")
                else:
                    self.log_test("Specific Provider Sample", False, f"Invalid AWS sample format: {data}")
            else:
                self.log_test("Specific Provider Sample", False, f"Status: {response.status_code}, Response: {response.text}")
        
        except Exception as e:
            self.log_test("Provider Samples", False, f"Exception: {str(e)}")
    
    def test_11_protected_endpoints_with_auth(self):
        """Test 11: Access protected endpoints with authentication"""
        print("\n=== Test 11: Protected Endpoints with Authentication ===")
        
        if not self.admin_token:
            self.log_test("Protected Endpoints with Auth", False, "No admin token available")
            return
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        endpoints_to_test = [
            "/users",
            "/providers",
            "/analytics"
        ]
        
        passed_count = 0
        for endpoint in endpoints_to_test:
            try:
                response = self.make_request("GET", endpoint, headers=headers)
                
                if response.status_code == 200:
                    passed_count += 1
                    print(f"  ✅ {endpoint}: Successfully accessed")
                else:
                    print(f"  ❌ {endpoint}: Status {response.status_code}")
            
            except Exception as e:
                print(f"  ❌ {endpoint}: Exception: {str(e)}")
        
        if passed_count == len(endpoints_to_test):
            self.log_test("Protected Endpoints with Auth", True, f"All {len(endpoints_to_test)} endpoints accessible with auth")
        else:
            self.log_test("Protected Endpoints with Auth", False, f"Only {passed_count}/{len(endpoints_to_test)} endpoints accessible")
    
    def test_12_invalid_token(self):
        """Test 12: Test with invalid JWT token"""
        print("\n=== Test 12: Invalid JWT Token ===")
        
        headers = {"Authorization": "Bearer invalid_token_here"}
        
        try:
            response = self.make_request("GET", "/auth/me", headers=headers)
            
            if response.status_code == 401:
                self.log_test("Invalid Token", True, "Invalid token correctly rejected")
            else:
                self.log_test("Invalid Token", False, f"Expected 401, got {response.status_code}")
        
        except Exception as e:
            self.log_test("Invalid Token", False, f"Exception: {str(e)}")
    
    def test_13_delete_user_admin(self):
        """Test 13: Delete user (admin only) - Run last to clean up"""
        print("\n=== Test 13: Delete User (Admin Only) ===")
        
        if not self.admin_token or not self.test_user_id:
            self.log_test("Delete User", False, "No admin token or test user ID available")
            return
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            response = self.make_request("DELETE", f"/users/{self.test_user_id}", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "deleted" in data["message"].lower():
                    self.log_test("Delete User", True, f"User deleted successfully: {data.get('message')}")
                else:
                    self.log_test("Delete User", False, f"Unexpected response: {data}")
            else:
                self.log_test("Delete User", False, f"Status: {response.status_code}, Response: {response.text}")
        
        except Exception as e:
            self.log_test("Delete User", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all authentication and user management tests"""
        print("🚀 Starting Comprehensive Authentication and User Management Testing")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Testing with admin credentials: {DEFAULT_ADMIN_EMAIL}")
        
        # Run tests in order
        self.test_1_default_admin_login()
        self.test_2_get_current_user()
        self.test_3_unauthenticated_access()
        self.test_4_create_user_admin_only()
        self.test_5_login_regular_user()
        self.test_6_non_admin_access_restriction()
        self.test_7_get_all_users_admin()
        self.test_8_update_user_admin()
        self.test_9_update_own_profile()
        self.test_10_provider_samples_authenticated()
        self.test_11_protected_endpoints_with_auth()
        self.test_12_invalid_token()
        self.test_13_delete_user_admin()
        
        # Print summary
        print("\n" + "="*60)
        print("🏁 AUTHENTICATION TESTING SUMMARY")
        print("="*60)
        print(f"Total Tests: {self.results['total_tests']}")
        print(f"✅ Passed: {self.results['passed']}")
        print(f"❌ Failed: {self.results['failed']}")
        
        if self.results['failed'] > 0:
            print("\n❌ FAILED TESTS:")
            for error in self.results['errors']:
                print(f"  - {error}")
        
        success_rate = (self.results['passed'] / self.results['total_tests']) * 100 if self.results['total_tests'] > 0 else 0
        print(f"\n📊 Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("🎉 EXCELLENT: Authentication system is working very well!")
        elif success_rate >= 75:
            print("✅ GOOD: Authentication system is mostly working with minor issues")
        elif success_rate >= 50:
            print("⚠️  MODERATE: Authentication system has some significant issues")
        else:
            print("🚨 CRITICAL: Authentication system has major problems")
        
        return success_rate >= 75

if __name__ == "__main__":
    tester = AuthenticationTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)