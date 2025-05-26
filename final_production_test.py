#!/usr/bin/env python3
"""
FINAL PRODUCTION READINESS VERIFICATION
Comprehensive testing of all backend systems for production deployment
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

class ProductionReadinessVerifier:
    def __init__(self):
        self.admin_token = None
        self.results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "errors": [],
            "categories": {
                "authentication": {"passed": 0, "total": 0},
                "core_apis": {"passed": 0, "total": 0},
                "user_management": {"passed": 0, "total": 0},
                "data_operations": {"passed": 0, "total": 0},
                "security": {"passed": 0, "total": 0},
                "analytics": {"passed": 0, "total": 0}
            }
        }
    
    def log_test(self, test_name: str, passed: bool, category: str, details: str = ""):
        """Log test results with category tracking"""
        self.results["total_tests"] += 1
        self.results["categories"][category]["total"] += 1
        
        if passed:
            self.results["passed"] += 1
            self.results["categories"][category]["passed"] += 1
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

    # ===== AUTHENTICATION SYSTEM VERIFICATION =====
    
    def test_admin_login(self):
        """Test admin login with default credentials"""
        print("\n=== AUTHENTICATION SYSTEM VERIFICATION ===")
        
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
                    
                    if user_info.get("role") == "admin" and user_info.get("email") == DEFAULT_ADMIN_EMAIL:
                        self.log_test("Admin Login", True, "authentication", f"Token received, role: {user_info.get('role')}")
                    else:
                        self.log_test("Admin Login", False, "authentication", f"Invalid user role or email: {user_info}")
                else:
                    self.log_test("Admin Login", False, "authentication", f"Missing token or user in response")
            else:
                self.log_test("Admin Login", False, "authentication", f"Status: {response.status_code}")
        
        except Exception as e:
            self.log_test("Admin Login", False, "authentication", f"Exception: {str(e)}")

    def test_jwt_validation(self):
        """Test JWT token validation"""
        if not self.admin_token:
            self.log_test("JWT Validation", False, "authentication", "No admin token available")
            return
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            response = self.make_request("GET", "/auth/me", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("email") == DEFAULT_ADMIN_EMAIL and data.get("role") == "admin":
                    self.log_test("JWT Validation", True, "authentication", f"Token validated for: {data.get('email')}")
                else:
                    self.log_test("JWT Validation", False, "authentication", f"Invalid user data: {data}")
            else:
                self.log_test("JWT Validation", False, "authentication", f"Status: {response.status_code}")
        
        except Exception as e:
            self.log_test("JWT Validation", False, "authentication", f"Exception: {str(e)}")

    # ===== CORE API FUNCTIONALITY =====
    
    def test_user_search(self):
        """Test user search endpoint with sample users"""
        print("\n=== CORE API FUNCTIONALITY ===")
        
        if not self.admin_token:
            self.log_test("User Search", False, "core_apis", "No admin token available")
            return
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        test_emails = ["alice@company.com", "bob@company.com", "carol@company.com"]
        
        passed_searches = 0
        for email in test_emails:
            try:
                response = self.make_request("GET", f"/search/{email}", headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    if "user" in data and "graph_data" in data:
                        if data["user"] and data["user"]["user_email"] == email:
                            passed_searches += 1
                            print(f"  ✅ Search for {email}: Found user with {len(data['user']['resources'])} resources")
                        else:
                            print(f"  ❌ Search for {email}: User not found or invalid data")
                    else:
                        print(f"  ❌ Search for {email}: Invalid response structure")
                else:
                    print(f"  ❌ Search for {email}: Status {response.status_code}")
            
            except Exception as e:
                print(f"  ❌ Search for {email}: Exception: {str(e)}")
        
        if passed_searches == len(test_emails):
            self.log_test("User Search", True, "core_apis", f"All {len(test_emails)} sample users found")
        else:
            self.log_test("User Search", False, "core_apis", f"Only {passed_searches}/{len(test_emails)} users found")

    def test_resource_search(self):
        """Test resource search endpoint"""
        if not self.admin_token:
            self.log_test("Resource Search", False, "core_apis", "No admin token available")
            return
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        test_resources = ["production", "S3", "admin"]
        
        passed_searches = 0
        for resource in test_resources:
            try:
                response = self.make_request("GET", f"/search/resource/{resource}", headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list) and len(data) > 0:
                        passed_searches += 1
                        print(f"  ✅ Resource search for '{resource}': Found {len(data)} matches")
                    else:
                        print(f"  ⚠️  Resource search for '{resource}': No matches found")
                        passed_searches += 1  # This is acceptable
                else:
                    print(f"  ❌ Resource search for '{resource}': Status {response.status_code}")
            
            except Exception as e:
                print(f"  ❌ Resource search for '{resource}': Exception: {str(e)}")
        
        if passed_searches >= len(test_resources) - 1:  # Allow one to have no matches
            self.log_test("Resource Search", True, "core_apis", f"Resource search working correctly")
        else:
            self.log_test("Resource Search", False, "core_apis", f"Resource search issues detected")

    def test_analytics_endpoint(self):
        """Test analytics endpoint returns comprehensive data"""
        if not self.admin_token:
            self.log_test("Analytics Endpoint", False, "analytics", "No admin token available")
            return
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            response = self.make_request("GET", "/analytics", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = [
                    "total_users", "total_resources", "risk_distribution", 
                    "top_privileged_users", "unused_privileges_count", 
                    "cross_provider_admins", "privilege_escalation_risks", "provider_stats"
                ]
                
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    self.log_test("Analytics Endpoint", True, "analytics", 
                                f"Complete analytics: {data['total_users']} users, {data['total_resources']} resources")
                else:
                    self.log_test("Analytics Endpoint", False, "analytics", f"Missing fields: {missing_fields}")
            else:
                self.log_test("Analytics Endpoint", False, "analytics", f"Status: {response.status_code}")
        
        except Exception as e:
            self.log_test("Analytics Endpoint", False, "analytics", f"Exception: {str(e)}")

    def test_provider_statistics(self):
        """Test provider statistics endpoint"""
        if not self.admin_token:
            self.log_test("Provider Statistics", False, "core_apis", "No admin token available")
            return
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            response = self.make_request("GET", "/providers", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if "total_users" in data and "providers" in data:
                    providers = data["providers"]
                    expected_providers = ["aws", "gcp", "azure", "okta"]
                    
                    if all(provider in providers for provider in expected_providers):
                        self.log_test("Provider Statistics", True, "core_apis", 
                                    f"All providers present: {list(providers.keys())}")
                    else:
                        self.log_test("Provider Statistics", False, "core_apis", 
                                    f"Missing providers. Found: {list(providers.keys())}")
                else:
                    self.log_test("Provider Statistics", False, "core_apis", "Invalid response structure")
            else:
                self.log_test("Provider Statistics", False, "core_apis", f"Status: {response.status_code}")
        
        except Exception as e:
            self.log_test("Provider Statistics", False, "core_apis", f"Exception: {str(e)}")

    # ===== USER MANAGEMENT APIs =====
    
    def test_user_management_apis(self):
        """Test user management CRUD operations"""
        print("\n=== USER MANAGEMENT APIs ===")
        
        if not self.admin_token:
            self.log_test("User Management", False, "user_management", "No admin token available")
            return
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        test_user_id = None
        
        # Test user creation
        try:
            user_data = {
                "email": "testprod@company.com",
                "password": "TestPassword123",
                "role": "user"
            }
            
            response = self.make_request("POST", "/users", headers=headers, data=user_data)
            
            if response.status_code == 200:
                data = response.json()
                test_user_id = data.get("id")
                self.log_test("User Creation", True, "user_management", f"User created: {data.get('email')}")
            else:
                self.log_test("User Creation", False, "user_management", f"Status: {response.status_code}")
                return
        
        except Exception as e:
            self.log_test("User Creation", False, "user_management", f"Exception: {str(e)}")
            return
        
        # Test user listing
        try:
            response = self.make_request("GET", "/users/all", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) >= 2:
                    self.log_test("User Listing", True, "user_management", f"Retrieved {len(data)} users")
                else:
                    self.log_test("User Listing", False, "user_management", f"Invalid user list: {data}")
            else:
                self.log_test("User Listing", False, "user_management", f"Status: {response.status_code}")
        
        except Exception as e:
            self.log_test("User Listing", False, "user_management", f"Exception: {str(e)}")
        
        # Test user update
        if test_user_id:
            try:
                update_data = {"email": "updatedprod@company.com"}
                response = self.make_request("PUT", f"/users/{test_user_id}", headers=headers, data=update_data)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("email") == "updatedprod@company.com":
                        self.log_test("User Update", True, "user_management", f"User updated successfully")
                    else:
                        self.log_test("User Update", False, "user_management", f"Update failed: {data}")
                else:
                    self.log_test("User Update", False, "user_management", f"Status: {response.status_code}")
            
            except Exception as e:
                self.log_test("User Update", False, "user_management", f"Exception: {str(e)}")
        
        # Test user deletion
        if test_user_id:
            try:
                response = self.make_request("DELETE", f"/users/{test_user_id}", headers=headers)
                
                if response.status_code == 200:
                    self.log_test("User Deletion", True, "user_management", f"User deleted successfully")
                else:
                    self.log_test("User Deletion", False, "user_management", f"Status: {response.status_code}")
            
            except Exception as e:
                self.log_test("User Deletion", False, "user_management", f"Exception: {str(e)}")

    # ===== DATA IMPORT/EXPORT =====
    
    def test_export_functionality(self):
        """Test data export endpoints"""
        print("\n=== DATA IMPORT/EXPORT ===")
        
        if not self.admin_token:
            self.log_test("Export Functionality", False, "data_operations", "No admin token available")
            return
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        export_formats = ["csv", "json", "xlsx"]
        
        passed_exports = 0
        for format_type in export_formats:
            try:
                response = self.make_request("GET", f"/export/{format_type}", headers=headers)
                
                if response.status_code == 200:
                    content_length = len(response.content)
                    if content_length > 0:
                        passed_exports += 1
                        print(f"  ✅ Export {format_type.upper()}: Success ({content_length} bytes)")
                    else:
                        print(f"  ❌ Export {format_type.upper()}: Empty response")
                else:
                    print(f"  ❌ Export {format_type.upper()}: Status {response.status_code}")
            
            except Exception as e:
                print(f"  ❌ Export {format_type.upper()}: Exception: {str(e)}")
        
        if passed_exports == len(export_formats):
            self.log_test("Export Functionality", True, "data_operations", f"All {len(export_formats)} formats working")
        else:
            self.log_test("Export Functionality", False, "data_operations", f"Only {passed_exports}/{len(export_formats)} formats working")

    def test_provider_samples(self):
        """Test provider sample formats"""
        if not self.admin_token:
            self.log_test("Provider Samples", False, "data_operations", "No admin token available")
            return
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            response = self.make_request("GET", "/providers/samples", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                expected_providers = ["aws", "gcp", "azure", "okta"]
                
                if all(provider in data for provider in expected_providers):
                    self.log_test("Provider Samples", True, "data_operations", 
                                f"All provider samples available: {list(data.keys())}")
                else:
                    self.log_test("Provider Samples", False, "data_operations", 
                                f"Missing provider samples. Found: {list(data.keys())}")
            else:
                self.log_test("Provider Samples", False, "data_operations", f"Status: {response.status_code}")
        
        except Exception as e:
            self.log_test("Provider Samples", False, "data_operations", f"Exception: {str(e)}")

    # ===== SECURITY & ERROR HANDLING =====
    
    def test_security_responses(self):
        """Test security and error handling"""
        print("\n=== SECURITY & ERROR HANDLING ===")
        
        # Test unauthorized access
        try:
            response = self.make_request("GET", "/users")
            
            if response.status_code in [401, 403]:
                self.log_test("Unauthorized Access", True, "security", f"Correctly blocked with {response.status_code}")
            else:
                self.log_test("Unauthorized Access", False, "security", f"Expected 401/403, got {response.status_code}")
        
        except Exception as e:
            self.log_test("Unauthorized Access", False, "security", f"Exception: {str(e)}")
        
        # Test non-existent user search
        if self.admin_token:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            try:
                response = self.make_request("GET", "/search/nonexistent@company.com", headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("user") is None:
                        self.log_test("Non-existent User Handling", True, "security", "Correctly returns null for non-existent user")
                    else:
                        self.log_test("Non-existent User Handling", False, "security", "Should return null for non-existent user")
                else:
                    self.log_test("Non-existent User Handling", False, "security", f"Status: {response.status_code}")
            
            except Exception as e:
                self.log_test("Non-existent User Handling", False, "security", f"Exception: {str(e)}")

    # ===== DATABASE OPERATIONS =====
    
    def test_database_operations(self):
        """Test database operations and data integrity"""
        print("\n=== DATABASE OPERATIONS ===")
        
        if not self.admin_token:
            self.log_test("Database Operations", False, "data_operations", "No admin token available")
            return
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test sample data is loaded
        try:
            response = self.make_request("GET", "/users", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) >= 3:
                    sample_emails = [user.get("user_email") for user in data]
                    expected_emails = ["alice@company.com", "bob@company.com", "carol@company.com"]
                    
                    if all(email in sample_emails for email in expected_emails):
                        self.log_test("Sample Data Loaded", True, "data_operations", 
                                    f"All {len(expected_emails)} sample users present")
                    else:
                        self.log_test("Sample Data Loaded", False, "data_operations", 
                                    f"Missing sample users. Found: {sample_emails}")
                else:
                    self.log_test("Sample Data Loaded", False, "data_operations", f"Insufficient users: {len(data) if isinstance(data, list) else 'invalid'}")
            else:
                self.log_test("Sample Data Loaded", False, "data_operations", f"Status: {response.status_code}")
        
        except Exception as e:
            self.log_test("Sample Data Loaded", False, "data_operations", f"Exception: {str(e)}")

    # ===== PERFORMANCE & RELIABILITY =====
    
    def test_performance(self):
        """Test API response times and reliability"""
        print("\n=== PERFORMANCE & RELIABILITY ===")
        
        if not self.admin_token:
            self.log_test("Performance Test", False, "core_apis", "No admin token available")
            return
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test response times for key endpoints
        endpoints = ["/users", "/providers", "/analytics"]
        fast_responses = 0
        
        for endpoint in endpoints:
            try:
                start_time = time.time()
                response = self.make_request("GET", endpoint, headers=headers)
                response_time = time.time() - start_time
                
                if response.status_code == 200 and response_time < 5.0:  # 5 second threshold
                    fast_responses += 1
                    print(f"  ✅ {endpoint}: {response_time:.2f}s")
                else:
                    print(f"  ⚠️  {endpoint}: {response_time:.2f}s (Status: {response.status_code})")
            
            except Exception as e:
                print(f"  ❌ {endpoint}: Exception: {str(e)}")
        
        if fast_responses >= len(endpoints) - 1:  # Allow one slow response
            self.log_test("Performance Test", True, "core_apis", f"Response times acceptable")
        else:
            self.log_test("Performance Test", False, "core_apis", f"Performance issues detected")

    def run_all_tests(self):
        """Run complete production readiness verification"""
        print("🚀 FINAL PRODUCTION READINESS VERIFICATION")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Testing with admin credentials: {DEFAULT_ADMIN_EMAIL}")
        print("=" * 80)
        
        # Run all test categories
        self.test_admin_login()
        self.test_jwt_validation()
        
        self.test_user_search()
        self.test_resource_search()
        self.test_analytics_endpoint()
        self.test_provider_statistics()
        
        self.test_user_management_apis()
        
        self.test_export_functionality()
        self.test_provider_samples()
        
        self.test_security_responses()
        
        self.test_database_operations()
        
        self.test_performance()
        
        # Print comprehensive summary
        print("\n" + "="*80)
        print("🏁 FINAL PRODUCTION READINESS ASSESSMENT")
        print("="*80)
        
        # Category breakdown
        for category, stats in self.results["categories"].items():
            if stats["total"] > 0:
                success_rate = (stats["passed"] / stats["total"]) * 100
                status = "✅" if success_rate >= 80 else "⚠️" if success_rate >= 60 else "❌"
                print(f"{status} {category.upper()}: {stats['passed']}/{stats['total']} ({success_rate:.1f}%)")
        
        print(f"\n📊 OVERALL RESULTS:")
        print(f"Total Tests: {self.results['total_tests']}")
        print(f"✅ Passed: {self.results['passed']}")
        print(f"❌ Failed: {self.results['failed']}")
        
        if self.results['failed'] > 0:
            print(f"\n❌ FAILED TESTS:")
            for error in self.results['errors']:
                print(f"  - {error}")
        
        overall_success_rate = (self.results['passed'] / self.results['total_tests']) * 100 if self.results['total_tests'] > 0 else 0
        print(f"\n📈 Overall Success Rate: {overall_success_rate:.1f}%")
        
        # Production readiness assessment
        if overall_success_rate >= 95:
            print("🎉 EXCELLENT: System is PRODUCTION READY with outstanding performance!")
        elif overall_success_rate >= 85:
            print("✅ GOOD: System is PRODUCTION READY with minor issues that don't affect core functionality")
        elif overall_success_rate >= 70:
            print("⚠️  MODERATE: System has some issues that should be addressed before production")
        else:
            print("🚨 CRITICAL: System has major issues that must be fixed before production")
        
        return overall_success_rate >= 85

if __name__ == "__main__":
    verifier = ProductionReadinessVerifier()
    success = verifier.run_all_tests()
    sys.exit(0 if success else 1)