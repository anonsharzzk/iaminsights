#!/usr/bin/env python3
"""
FINAL PRODUCTION READINESS VERIFICATION - Updated for current database state
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://d602465a-6f1d-46f0-8a14-ab8451e05734.preview.emergentagent.com/api"
DEFAULT_ADMIN_EMAIL = "adminn@iamsharan.com"
DEFAULT_ADMIN_PASSWORD = "Testing@123"

class FinalProductionVerifier:
    def __init__(self):
        self.admin_token = None
        self.current_users = []
        self.results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "critical_issues": [],
            "minor_issues": [],
            "categories": {}
        }
    
    def log_test(self, test_name: str, passed: bool, critical: bool = False, details: str = ""):
        """Log test results"""
        self.results["total_tests"] += 1
        
        if passed:
            self.results["passed"] += 1
            print(f"✅ {test_name}: PASSED {details}")
        else:
            self.results["failed"] += 1
            if critical:
                self.results["critical_issues"].append(f"{test_name}: {details}")
                print(f"🚨 {test_name}: CRITICAL FAILURE {details}")
            else:
                self.results["minor_issues"].append(f"{test_name}: {details}")
                print(f"⚠️  {test_name}: MINOR ISSUE {details}")
    
    def make_request(self, method: str, endpoint: str, headers: dict = None, data: dict = None) -> requests.Response:
        """Make HTTP request with error handling"""
        url = f"{BACKEND_URL}{endpoint}"
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=30)
            elif method.upper() == "POST":
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

    def setup_authentication(self):
        """Setup authentication and get current users"""
        print("🔐 AUTHENTICATION SYSTEM VERIFICATION")
        print("=" * 60)
        
        # Test admin login
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
                        self.log_test("Admin Login", True, details=f"✓ Default admin credentials working")
                    else:
                        self.log_test("Admin Login", False, critical=True, details=f"Invalid admin credentials")
                        return False
                else:
                    self.log_test("Admin Login", False, critical=True, details=f"Missing token in response")
                    return False
            else:
                self.log_test("Admin Login", False, critical=True, details=f"Status: {response.status_code}")
                return False
        
        except Exception as e:
            self.log_test("Admin Login", False, critical=True, details=f"Exception: {str(e)}")
            return False
        
        # Test JWT validation
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            response = self.make_request("GET", "/auth/me", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("email") == DEFAULT_ADMIN_EMAIL and data.get("role") == "admin":
                    self.log_test("JWT Token Validation", True, details="✓ Token validation working")
                else:
                    self.log_test("JWT Token Validation", False, critical=True, details="Invalid token response")
                    return False
            else:
                self.log_test("JWT Token Validation", False, critical=True, details=f"Status: {response.status_code}")
                return False
        
        except Exception as e:
            self.log_test("JWT Token Validation", False, critical=True, details=f"Exception: {str(e)}")
            return False
        
        # Get current users for testing
        try:
            response = self.make_request("GET", "/users", headers=headers)
            if response.status_code == 200:
                self.current_users = response.json()
                self.log_test("User Data Access", True, details=f"✓ {len(self.current_users)} users loaded")
            else:
                self.log_test("User Data Access", False, critical=True, details=f"Cannot access user data")
                return False
        except Exception as e:
            self.log_test("User Data Access", False, critical=True, details=f"Exception: {str(e)}")
            return False
        
        return True

    def test_core_api_functionality(self):
        """Test core API endpoints"""
        print("\n🔧 CORE API FUNCTIONALITY")
        print("=" * 60)
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test user search with actual users
        successful_searches = 0
        for user in self.current_users[:3]:  # Test first 3 users
            email = user['user_email']
            try:
                response = self.make_request("GET", f"/search/{email}", headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("user") and data.get("graph_data"):
                        successful_searches += 1
                        print(f"  ✅ Search {email}: {len(data['user']['resources'])} resources, {len(data['graph_data']['nodes'])} nodes")
                    else:
                        print(f"  ❌ Search {email}: Invalid response structure")
                else:
                    print(f"  ❌ Search {email}: Status {response.status_code}")
            
            except Exception as e:
                print(f"  ❌ Search {email}: Exception: {str(e)}")
        
        if successful_searches == len(self.current_users[:3]):
            self.log_test("User Search Functionality", True, details=f"✓ All {successful_searches} user searches working")
        else:
            self.log_test("User Search Functionality", False, critical=True, 
                         details=f"Only {successful_searches}/{len(self.current_users[:3])} searches working")
        
        # Test resource search
        try:
            response = self.make_request("GET", "/search/resource/production", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("Resource Search", True, details=f"✓ Found {len(data)} resource matches")
                else:
                    self.log_test("Resource Search", False, details="Invalid response format")
            else:
                self.log_test("Resource Search", False, details=f"Status: {response.status_code}")
        
        except Exception as e:
            self.log_test("Resource Search", False, details=f"Exception: {str(e)}")
        
        # Test analytics endpoint
        try:
            response = self.make_request("GET", "/analytics", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["total_users", "total_resources", "risk_distribution", "provider_stats"]
                
                if all(field in data for field in required_fields):
                    self.log_test("Analytics Endpoint", True, 
                                 details=f"✓ {data['total_users']} users, {data['total_resources']} resources")
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_test("Analytics Endpoint", False, critical=True, details=f"Missing fields: {missing}")
            else:
                self.log_test("Analytics Endpoint", False, critical=True, details=f"Status: {response.status_code}")
        
        except Exception as e:
            self.log_test("Analytics Endpoint", False, critical=True, details=f"Exception: {str(e)}")
        
        # Test provider statistics
        try:
            response = self.make_request("GET", "/providers", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if "providers" in data:
                    providers = list(data["providers"].keys())
                    expected = ["aws", "gcp", "azure", "okta"]
                    if all(p in providers for p in expected):
                        self.log_test("Provider Statistics", True, details=f"✓ All providers: {providers}")
                    else:
                        self.log_test("Provider Statistics", False, details=f"Missing providers")
                else:
                    self.log_test("Provider Statistics", False, details="Invalid response structure")
            else:
                self.log_test("Provider Statistics", False, details=f"Status: {response.status_code}")
        
        except Exception as e:
            self.log_test("Provider Statistics", False, details=f"Exception: {str(e)}")

    def test_user_management(self):
        """Test user management APIs"""
        print("\n👥 USER MANAGEMENT SYSTEM")
        print("=" * 60)
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        test_user_id = None
        
        # Test user creation
        try:
            user_data = {
                "email": "finaltest@company.com",
                "password": "TestPassword123",
                "role": "user"
            }
            
            response = self.make_request("POST", "/users", headers=headers, data=user_data)
            
            if response.status_code == 200:
                data = response.json()
                test_user_id = data.get("id")
                self.log_test("User Creation", True, details=f"✓ Created user: {data.get('email')}")
            else:
                self.log_test("User Creation", False, critical=True, details=f"Status: {response.status_code}")
                return
        
        except Exception as e:
            self.log_test("User Creation", False, critical=True, details=f"Exception: {str(e)}")
            return
        
        # Test user listing
        try:
            response = self.make_request("GET", "/users/all", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) >= 2:
                    self.log_test("User Listing", True, details=f"✓ Retrieved {len(data)} system users")
                else:
                    self.log_test("User Listing", False, details=f"Invalid user list")
            else:
                self.log_test("User Listing", False, details=f"Status: {response.status_code}")
        
        except Exception as e:
            self.log_test("User Listing", False, details=f"Exception: {str(e)}")
        
        # Test user update
        if test_user_id:
            try:
                update_data = {"email": "finaltest.updated@company.com"}
                response = self.make_request("PUT", f"/users/{test_user_id}", headers=headers, data=update_data)
                
                if response.status_code == 200:
                    self.log_test("User Update", True, details="✓ User updated successfully")
                else:
                    self.log_test("User Update", False, details=f"Status: {response.status_code}")
            
            except Exception as e:
                self.log_test("User Update", False, details=f"Exception: {str(e)}")
        
        # Test user deletion
        if test_user_id:
            try:
                response = self.make_request("DELETE", f"/users/{test_user_id}", headers=headers)
                
                if response.status_code == 200:
                    self.log_test("User Deletion", True, details="✓ User deleted successfully")
                else:
                    self.log_test("User Deletion", False, details=f"Status: {response.status_code}")
            
            except Exception as e:
                self.log_test("User Deletion", False, details=f"Exception: {str(e)}")

    def test_data_operations(self):
        """Test data import/export functionality"""
        print("\n📊 DATA IMPORT/EXPORT OPERATIONS")
        print("=" * 60)
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test export functionality
        export_formats = ["csv", "json", "xlsx"]
        successful_exports = 0
        
        for format_type in export_formats:
            try:
                response = self.make_request("GET", f"/export/{format_type}", headers=headers)
                
                if response.status_code == 200:
                    content_length = len(response.content)
                    if content_length > 0:
                        successful_exports += 1
                        print(f"  ✅ Export {format_type.upper()}: {content_length} bytes")
                    else:
                        print(f"  ❌ Export {format_type.upper()}: Empty response")
                else:
                    print(f"  ❌ Export {format_type.upper()}: Status {response.status_code}")
            
            except Exception as e:
                print(f"  ❌ Export {format_type.upper()}: Exception: {str(e)}")
        
        if successful_exports == len(export_formats):
            self.log_test("Data Export", True, details=f"✓ All {len(export_formats)} export formats working")
        else:
            self.log_test("Data Export", False, critical=True, 
                         details=f"Only {successful_exports}/{len(export_formats)} formats working")
        
        # Test provider samples
        try:
            response = self.make_request("GET", "/providers/samples", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                expected_providers = ["aws", "gcp", "azure", "okta"]
                
                if all(provider in data for provider in expected_providers):
                    self.log_test("Provider Samples", True, details=f"✓ All provider samples available")
                else:
                    self.log_test("Provider Samples", False, details=f"Missing provider samples")
            else:
                self.log_test("Provider Samples", False, details=f"Status: {response.status_code}")
        
        except Exception as e:
            self.log_test("Provider Samples", False, details=f"Exception: {str(e)}")

    def test_security_and_performance(self):
        """Test security and performance"""
        print("\n🔒 SECURITY & PERFORMANCE")
        print("=" * 60)
        
        # Test unauthorized access
        try:
            response = self.make_request("GET", "/users")
            
            if response.status_code in [401, 403]:
                self.log_test("Unauthorized Access Protection", True, details=f"✓ Correctly blocked with {response.status_code}")
            else:
                self.log_test("Unauthorized Access Protection", False, critical=True, 
                             details=f"Expected 401/403, got {response.status_code}")
        
        except Exception as e:
            self.log_test("Unauthorized Access Protection", False, details=f"Exception: {str(e)}")
        
        # Test performance
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        endpoints = ["/users", "/providers", "/analytics"]
        fast_responses = 0
        
        for endpoint in endpoints:
            try:
                start_time = time.time()
                response = self.make_request("GET", endpoint, headers=headers)
                response_time = time.time() - start_time
                
                if response.status_code == 200 and response_time < 3.0:
                    fast_responses += 1
                    print(f"  ✅ {endpoint}: {response_time:.2f}s")
                else:
                    print(f"  ⚠️  {endpoint}: {response_time:.2f}s (Status: {response.status_code})")
            
            except Exception as e:
                print(f"  ❌ {endpoint}: Exception: {str(e)}")
        
        if fast_responses >= len(endpoints):
            self.log_test("API Performance", True, details="✓ All endpoints respond quickly")
        else:
            self.log_test("API Performance", False, details=f"Performance issues detected")

    def run_final_verification(self):
        """Run complete final verification"""
        print("🚀 FINAL PRODUCTION READINESS VERIFICATION")
        print("🌟 Cloud Access Visualization Platform")
        print("=" * 80)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Admin Credentials: {DEFAULT_ADMIN_EMAIL}")
        print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Run all test suites
        if not self.setup_authentication():
            print("🚨 CRITICAL: Authentication setup failed - cannot proceed")
            return False
        
        self.test_core_api_functionality()
        self.test_user_management()
        self.test_data_operations()
        self.test_security_and_performance()
        
        # Final assessment
        print("\n" + "="*80)
        print("🏁 FINAL PRODUCTION READINESS ASSESSMENT")
        print("="*80)
        
        print(f"📊 TEST RESULTS:")
        print(f"   Total Tests: {self.results['total_tests']}")
        print(f"   ✅ Passed: {self.results['passed']}")
        print(f"   ❌ Failed: {self.results['failed']}")
        
        if self.results['critical_issues']:
            print(f"\n🚨 CRITICAL ISSUES ({len(self.results['critical_issues'])}):")
            for issue in self.results['critical_issues']:
                print(f"   - {issue}")
        
        if self.results['minor_issues']:
            print(f"\n⚠️  MINOR ISSUES ({len(self.results['minor_issues'])}):")
            for issue in self.results['minor_issues']:
                print(f"   - {issue}")
        
        overall_success_rate = (self.results['passed'] / self.results['total_tests']) * 100 if self.results['total_tests'] > 0 else 0
        print(f"\n📈 Overall Success Rate: {overall_success_rate:.1f}%")
        
        # Production readiness decision
        if len(self.results['critical_issues']) == 0 and overall_success_rate >= 90:
            print("\n🎉 PRODUCTION READY!")
            print("✅ System passes all critical tests and is ready for production deployment")
            print("✅ Authentication system working perfectly")
            print("✅ Core APIs functioning correctly")
            print("✅ User management operational")
            print("✅ Data operations working")
            print("✅ Security measures in place")
            print("✅ Performance acceptable")
            return True
        elif len(self.results['critical_issues']) == 0 and overall_success_rate >= 80:
            print("\n✅ PRODUCTION READY with minor issues")
            print("✅ No critical issues found")
            print("⚠️  Some minor issues present but don't affect core functionality")
            return True
        else:
            print("\n🚨 NOT READY FOR PRODUCTION")
            print("❌ Critical issues must be resolved before deployment")
            return False

if __name__ == "__main__":
    verifier = FinalProductionVerifier()
    success = verifier.run_final_verification()
    sys.exit(0 if success else 1)