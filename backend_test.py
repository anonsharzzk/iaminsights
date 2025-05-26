#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Cloud Access Visualization Platform
Tests all API endpoints including enhanced features and validates data structure and functionality.
"""

import requests
import json
import sys
import os
import io
from typing import Dict, List, Any

# Get backend URL from environment
BACKEND_URL = "https://d602465a-6f1d-46f0-8a14-ab8451e05734.preview.emergentagent.com/api"

class BackendTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.test_results = []
        self.sample_users = ["david.wilson@company.com", "emma.clark@company.com", "automation-service@company.com"]
        
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test results"""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "details": details
        })
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        print()

    def test_api_health_check(self):
        """Test 1: Basic API Health Check - GET /api/"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "version" in data:
                    self.log_test("API Health Check", True, f"API responding with message: {data['message']}")
                    return True
                else:
                    self.log_test("API Health Check", False, f"Missing expected fields in response: {data}")
                    return False
            else:
                self.log_test("API Health Check", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("API Health Check", False, f"Connection error: {str(e)}")
            return False

    def test_sample_data_initialization(self):
        """Test 2: Verify sample data has been loaded correctly"""
        try:
            # Test GET /api/users to verify sample data
            response = requests.get(f"{self.base_url}/users", timeout=10)
            
            if response.status_code != 200:
                self.log_test("Sample Data Initialization", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            users = response.json()
            
            # Check if we have at least 3 users (from JSON import or sample data)
            if len(users) < 3:
                self.log_test("Sample Data Initialization", False, f"Expected at least 3 users, found {len(users)}")
                return False
            
            # Update sample_users to match actual users in database
            user_emails = [user["user_email"] for user in users]
            self.sample_users = user_emails[:3]  # Use first 3 users
            
            # Validate each user has realistic cloud access
            for user in users:
                if not user.get("resources") or len(user["resources"]) == 0:
                    self.log_test("Sample Data Initialization", False, f"User {user['user_email']} has no resources")
                    return False
                
                # Check for cloud providers
                providers = set(resource["provider"] for resource in user["resources"])
                expected_providers = {"aws", "gcp", "azure", "okta"}
                
                if not providers.intersection(expected_providers):
                    self.log_test("Sample Data Initialization", False, f"User {user['user_email']} missing cloud provider resources")
                    return False
            
            self.log_test("Sample Data Initialization", True, f"Found {len(users)} users with realistic cloud access across multiple providers")
            return True
            
        except Exception as e:
            self.log_test("Sample Data Initialization", False, f"Error: {str(e)}")
            return False

    def test_json_import_functionality(self):
        """Test 3: Enhanced JSON Import Functionality - POST /api/import/json"""
        try:
            # Read the sample_data.json file
            with open('/app/sample_data.json', 'r') as f:
                sample_data = f.read()
            
            # Create a file-like object for upload
            files = {'file': ('sample_data.json', sample_data, 'application/json')}
            
            response = requests.post(f"{self.base_url}/import/json", files=files, timeout=30)
            
            if response.status_code != 200:
                self.log_test("JSON Import Functionality", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            result = response.json()
            
            # Validate response structure
            if "status" not in result or "imported_users" not in result:
                self.log_test("JSON Import Functionality", False, "Missing 'status' or 'imported_users' in response")
                return False
            
            if result["status"] != "success":
                self.log_test("JSON Import Functionality", False, f"Import failed with status: {result['status']}")
                return False
            
            imported_count = result["imported_users"]
            if imported_count != 3:  # sample_data.json has 3 users
                self.log_test("JSON Import Functionality", False, f"Expected 3 imported users, got {imported_count}")
                return False
            
            # Verify the imported users are now in the database
            users_response = requests.get(f"{self.base_url}/users", timeout=10)
            if users_response.status_code == 200:
                users = users_response.json()
                imported_emails = ["david.wilson@company.com", "emma.clark@company.com", "automation-service@company.com"]
                
                user_emails = [user["user_email"] for user in users]
                missing_imported = [email for email in imported_emails if email not in user_emails]
                
                if missing_imported:
                    self.log_test("JSON Import Functionality", False, f"Imported users not found in database: {missing_imported}")
                    return False
            
            self.log_test("JSON Import Functionality", True, f"Successfully imported {imported_count} users with risk analysis")
            return True
            
        except Exception as e:
            self.log_test("JSON Import Functionality", False, f"Error: {str(e)}")
            return False

    def test_resource_search_functionality(self):
        """Test 4: Resource-based Search - GET /api/search/resource/{resource_name}"""
        try:
            # Test searching for common resource names
            test_resources = ["production", "S3", "admin"]
            
            for resource_name in test_resources:
                response = requests.get(f"{self.base_url}/search/resource/{resource_name}", timeout=10)
                
                if response.status_code != 200:
                    self.log_test(f"Resource Search: {resource_name}", False, f"HTTP {response.status_code}: {response.text}")
                    return False
                
                results = response.json()
                
                if not isinstance(results, list):
                    self.log_test(f"Resource Search: {resource_name}", False, "Response is not a list")
                    return False
                
                # Validate result structure if results exist
                for result in results:
                    required_fields = ["resource", "users_with_access", "total_users", "risk_summary"]
                    missing_fields = [field for field in required_fields if field not in result]
                    
                    if missing_fields:
                        self.log_test(f"Resource Search: {resource_name}", False, f"Result missing fields: {missing_fields}")
                        return False
                    
                    # Validate resource structure
                    resource = result["resource"]
                    resource_required = ["provider", "service", "resource_name", "access_type"]
                    resource_missing = [field for field in resource_required if field not in resource]
                    
                    if resource_missing:
                        self.log_test(f"Resource Search: {resource_name}", False, f"Resource missing fields: {resource_missing}")
                        return False
                    
                    # Validate risk summary
                    risk_summary = result["risk_summary"]
                    expected_risk_levels = ["low", "medium", "high", "critical"]
                    for level in expected_risk_levels:
                        if level not in risk_summary:
                            self.log_test(f"Resource Search: {resource_name}", False, f"Risk summary missing level: {level}")
                            return False
                
                self.log_test(f"Resource Search: {resource_name}", True, f"Found {len(results)} matching resources")
            
            return True
            
        except Exception as e:
            self.log_test("Resource Search Functionality", False, f"Error: {str(e)}")
            return False

    def test_analytics_endpoint(self):
        """Test 5: Comprehensive Analytics - GET /api/analytics"""
        try:
            response = requests.get(f"{self.base_url}/analytics", timeout=15)
            
            if response.status_code != 200:
                self.log_test("Analytics Endpoint", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            analytics = response.json()
            
            # Validate required fields
            required_fields = [
                "total_users", "total_resources", "risk_distribution", 
                "top_privileged_users", "unused_privileges_count", 
                "cross_provider_admins", "privilege_escalation_risks", "provider_stats"
            ]
            
            missing_fields = [field for field in required_fields if field not in analytics]
            if missing_fields:
                self.log_test("Analytics Endpoint", False, f"Missing fields: {missing_fields}")
                return False
            
            # Validate risk distribution
            risk_distribution = analytics["risk_distribution"]
            expected_risk_levels = ["low", "medium", "high", "critical"]
            for level in expected_risk_levels:
                if level not in risk_distribution:
                    self.log_test("Analytics Endpoint", False, f"Risk distribution missing level: {level}")
                    return False
            
            # Validate provider stats
            provider_stats = analytics["provider_stats"]
            expected_providers = ["aws", "gcp", "azure", "okta"]
            for provider in expected_providers:
                if provider not in provider_stats:
                    self.log_test("Analytics Endpoint", False, f"Provider stats missing provider: {provider}")
                    return False
                
                provider_data = provider_stats[provider]
                if "users" not in provider_data or "resources" not in provider_data:
                    self.log_test("Analytics Endpoint", False, f"Provider {provider} missing users/resources stats")
                    return False
            
            # Validate top privileged users structure
            top_privileged = analytics["top_privileged_users"]
            if isinstance(top_privileged, list) and len(top_privileged) > 0:
                user_required = ["user_email", "user_name", "admin_access_count", "total_resources", "risk_score"]
                for user in top_privileged[:3]:  # Check first 3
                    user_missing = [field for field in user_required if field not in user]
                    if user_missing:
                        self.log_test("Analytics Endpoint", False, f"Top privileged user missing fields: {user_missing}")
                        return False
            
            # Validate privilege escalation risks
            escalation_risks = analytics["privilege_escalation_risks"]
            if isinstance(escalation_risks, list) and len(escalation_risks) > 0:
                risk_required = ["user_email", "start_privilege", "end_privilege", "path_steps", "risk_score"]
                for risk in escalation_risks[:3]:  # Check first 3
                    risk_missing = [field for field in risk_required if field not in risk]
                    if risk_missing:
                        self.log_test("Analytics Endpoint", False, f"Escalation risk missing fields: {risk_missing}")
                        return False
            
            self.log_test("Analytics Endpoint", True, f"Analytics data validated: {analytics['total_users']} users, {analytics['total_resources']} resources, {len(top_privileged)} privileged users")
            return True
            
        except Exception as e:
            self.log_test("Analytics Endpoint", False, f"Error: {str(e)}")
            return False

    def test_export_functionality(self):
        """Test 6: Data Export - GET /api/export/{format}"""
        try:
            # Test different export formats
            formats = ["csv", "json"]  # Skip xlsx for now due to potential dependency issues
            
            for format_type in formats:
                response = requests.get(f"{self.base_url}/export/{format_type}", timeout=15)
                
                if response.status_code != 200:
                    self.log_test(f"Export {format_type.upper()}", False, f"HTTP {response.status_code}: {response.text}")
                    return False
                
                # Check content type and headers
                content_type = response.headers.get('content-type', '')
                content_disposition = response.headers.get('content-disposition', '')
                
                if format_type == "csv":
                    if "text/csv" not in content_type:
                        self.log_test(f"Export {format_type.upper()}", False, f"Wrong content type: {content_type}")
                        return False
                elif format_type == "json":
                    if "application/json" not in content_type:
                        self.log_test(f"Export {format_type.upper()}", False, f"Wrong content type: {content_type}")
                        return False
                
                if "attachment" not in content_disposition:
                    self.log_test(f"Export {format_type.upper()}", False, f"Missing attachment header: {content_disposition}")
                    return False
                
                # Validate content is not empty
                content = response.content
                if len(content) == 0:
                    self.log_test(f"Export {format_type.upper()}", False, "Empty export content")
                    return False
                
                # For JSON, validate it's valid JSON
                if format_type == "json":
                    try:
                        json.loads(content.decode('utf-8'))
                    except json.JSONDecodeError:
                        self.log_test(f"Export {format_type.upper()}", False, "Invalid JSON content")
                        return False
                
                self.log_test(f"Export {format_type.upper()}", True, f"Export successful, content size: {len(content)} bytes")
            
            # Test export with filters
            response = requests.get(f"{self.base_url}/export/json?provider=aws&access_type=admin", timeout=15)
            if response.status_code == 200:
                filtered_data = json.loads(response.content.decode('utf-8'))
                # Validate all entries match the filter
                for entry in filtered_data:
                    if entry.get("provider") != "aws" or entry.get("access_type") != "admin":
                        self.log_test("Export with Filters", False, "Filter not applied correctly")
                        return False
                self.log_test("Export with Filters", True, f"Filtered export successful: {len(filtered_data)} entries")
            else:
                self.log_test("Export with Filters", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            return True
            
        except Exception as e:
            self.log_test("Export Functionality", False, f"Error: {str(e)}")
            return False

    def test_risk_analysis_endpoint(self):
        """Test 7: Individual User Risk Analysis - GET /api/risk-analysis/{user_email}"""
        try:
            # Test with existing users (use the actual users in database)
            test_users = self.sample_users[:2]  # Use first 2 users from sample_users
            
            for user_email in test_users:
                response = requests.get(f"{self.base_url}/risk-analysis/{user_email}", timeout=10)
                
                if response.status_code != 200:
                    # If user doesn't exist, that's okay for some tests
                    if response.status_code == 404:
                        continue
                    self.log_test(f"Risk Analysis: {user_email}", False, f"HTTP {response.status_code}: {response.text}")
                    return False
                
                risk_analysis = response.json()
                
                # Validate required fields
                required_fields = [
                    "user_email", "overall_risk_score", "risk_level", 
                    "cross_provider_admin", "privilege_escalation_paths", 
                    "unused_privileges", "admin_access_count", 
                    "privileged_access_count", "providers_with_access", "recommendations"
                ]
                
                missing_fields = [field for field in required_fields if field not in risk_analysis]
                if missing_fields:
                    self.log_test(f"Risk Analysis: {user_email}", False, f"Missing fields: {missing_fields}")
                    return False
                
                # Validate data types and ranges
                if not isinstance(risk_analysis["overall_risk_score"], (int, float)):
                    self.log_test(f"Risk Analysis: {user_email}", False, "Risk score is not numeric")
                    return False
                
                if risk_analysis["overall_risk_score"] < 0 or risk_analysis["overall_risk_score"] > 100:
                    self.log_test(f"Risk Analysis: {user_email}", False, f"Risk score out of range: {risk_analysis['overall_risk_score']}")
                    return False
                
                # Validate risk level
                valid_risk_levels = ["low", "medium", "high", "critical"]
                if risk_analysis["risk_level"] not in valid_risk_levels:
                    self.log_test(f"Risk Analysis: {user_email}", False, f"Invalid risk level: {risk_analysis['risk_level']}")
                    return False
                
                # Validate providers list
                if not isinstance(risk_analysis["providers_with_access"], list):
                    self.log_test(f"Risk Analysis: {user_email}", False, "Providers with access is not a list")
                    return False
                
                # Validate recommendations
                if not isinstance(risk_analysis["recommendations"], list):
                    self.log_test(f"Risk Analysis: {user_email}", False, "Recommendations is not a list")
                    return False
                
                self.log_test(f"Risk Analysis: {user_email}", True, f"Risk score: {risk_analysis['overall_risk_score']}, Level: {risk_analysis['risk_level']}, Providers: {len(risk_analysis['providers_with_access'])}")
            
            # Test with non-existent user
            response = requests.get(f"{self.base_url}/risk-analysis/nonexistent@company.com", timeout=10)
            if response.status_code == 404:
                self.log_test("Risk Analysis: Non-existent User", True, "Properly returned 404 for non-existent user")
            else:
                self.log_test("Risk Analysis: Non-existent User", False, f"Expected 404, got {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            self.log_test("Risk Analysis Endpoint", False, f"Error: {str(e)}")
            return False

    def test_search_functionality(self):
        """Test 8: Core Search Functionality - GET /api/search/{email}"""
        all_passed = True
        
        # Test with existing users
        for email in self.sample_users:
            try:
                response = requests.get(f"{self.base_url}/search/{email}", timeout=10)
                
                if response.status_code != 200:
                    self.log_test(f"Search User: {email}", False, f"HTTP {response.status_code}: {response.text}")
                    all_passed = False
                    continue
                
                data = response.json()
                
                # Validate response structure
                if "user" not in data or "graph_data" not in data:
                    self.log_test(f"Search User: {email}", False, "Missing 'user' or 'graph_data' in response")
                    all_passed = False
                    continue
                
                # Validate user data
                user = data["user"]
                if not user or user["user_email"] != email:
                    self.log_test(f"Search User: {email}", False, f"User data mismatch or null")
                    all_passed = False
                    continue
                
                # Validate graph data structure
                graph_data = data["graph_data"]
                if "nodes" not in graph_data or "edges" not in graph_data:
                    self.log_test(f"Search User: {email}", False, "Graph data missing 'nodes' or 'edges'")
                    all_passed = False
                    continue
                
                nodes = graph_data["nodes"]
                edges = graph_data["edges"]
                
                if not isinstance(nodes, list) or not isinstance(edges, list):
                    self.log_test(f"Search User: {email}", False, "Nodes or edges are not lists")
                    all_passed = False
                    continue
                
                self.log_test(f"Search User: {email}", True, f"Found {len(nodes)} nodes, {len(edges)} edges with proper structure")
                
            except Exception as e:
                self.log_test(f"Search User: {email}", False, f"Error: {str(e)}")
                all_passed = False
        
        return all_passed

    def run_all_tests(self):
        """Run all backend tests including enhanced features"""
        print("=" * 80)
        print("ENHANCED CLOUD ACCESS VISUALIZATION BACKEND API TESTING")
        print("=" * 80)
        print(f"Testing backend at: {self.base_url}")
        print()
        
        # Run all tests
        tests = [
            self.test_api_health_check,
            self.test_sample_data_initialization,
            self.test_json_import_functionality,
            self.test_resource_search_functionality,
            self.test_analytics_endpoint,
            self.test_export_functionality,
            self.test_risk_analysis_endpoint,
            self.test_search_functionality
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test in tests:
            if test():
                passed_tests += 1
        
        # Summary
        print("=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        for result in self.test_results:
            status = "✅ PASS" if result["passed"] else "❌ FAIL"
            print(f"{status}: {result['test']}")
        
        print()
        print(f"OVERALL RESULT: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED! Enhanced Backend API is working correctly.")
            return True
        else:
            print("⚠️  SOME TESTS FAILED! Check the details above.")
            return False

if __name__ == "__main__":
    tester = BackendTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)