#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Cloud Access Visualization Platform
Tests all API endpoints and validates data structure and functionality.
"""

import requests
import json
import sys
import os
from typing import Dict, List, Any

# Get backend URL from environment
BACKEND_URL = "https://d602465a-6f1d-46f0-8a14-ab8451e05734.preview.emergentagent.com/api"

class BackendTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.test_results = []
        self.sample_users = ["alice@company.com", "bob@company.com", "carol@company.com"]
        
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
            
            # Check if we have exactly 3 users
            if len(users) != 3:
                self.log_test("Sample Data Initialization", False, f"Expected 3 users, found {len(users)}")
                return False
            
            # Check if all expected users exist
            user_emails = [user["user_email"] for user in users]
            missing_users = [email for email in self.sample_users if email not in user_emails]
            
            if missing_users:
                self.log_test("Sample Data Initialization", False, f"Missing users: {missing_users}")
                return False
            
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
            
            self.log_test("Sample Data Initialization", True, f"All 3 users loaded with realistic cloud access across multiple providers")
            return True
            
        except Exception as e:
            self.log_test("Sample Data Initialization", False, f"Error: {str(e)}")
            return False

    def test_search_functionality(self):
        """Test 3: Core Search Functionality - GET /api/search/{email}"""
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
                
                # Validate node types
                node_types = set(node.get("type") for node in nodes)
                expected_types = {"user", "provider", "service", "resource"}
                
                if not node_types.intersection(expected_types):
                    self.log_test(f"Search User: {email}", False, f"Missing expected node types. Found: {node_types}")
                    all_passed = False
                    continue
                
                # Validate edges connect nodes properly
                node_ids = set(node["id"] for node in nodes)
                invalid_edges = []
                for edge in edges:
                    if edge["source"] not in node_ids or edge["target"] not in node_ids:
                        invalid_edges.append(edge["id"])
                
                if invalid_edges:
                    self.log_test(f"Search User: {email}", False, f"Invalid edges found: {invalid_edges}")
                    all_passed = False
                    continue
                
                self.log_test(f"Search User: {email}", True, f"Found {len(nodes)} nodes, {len(edges)} edges with proper structure")
                
            except Exception as e:
                self.log_test(f"Search User: {email}", False, f"Error: {str(e)}")
                all_passed = False
        
        # Test with non-existent user
        try:
            response = requests.get(f"{self.base_url}/search/nonexistent@company.com", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data["user"] is None and len(data["graph_data"]["nodes"]) == 0:
                    self.log_test("Search Non-existent User", True, "Properly handled non-existent user")
                else:
                    self.log_test("Search Non-existent User", False, "Should return null user and empty graph")
                    all_passed = False
            else:
                self.log_test("Search Non-existent User", False, f"HTTP {response.status_code}: {response.text}")
                all_passed = False
                
        except Exception as e:
            self.log_test("Search Non-existent User", False, f"Error: {str(e)}")
            all_passed = False
        
        return all_passed

    def test_users_endpoint(self):
        """Test 4: GET /api/users endpoint"""
        try:
            response = requests.get(f"{self.base_url}/users", timeout=10)
            
            if response.status_code != 200:
                self.log_test("Users Endpoint", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            users = response.json()
            
            if not isinstance(users, list):
                self.log_test("Users Endpoint", False, "Response is not a list")
                return False
            
            if len(users) == 0:
                self.log_test("Users Endpoint", False, "No users returned")
                return False
            
            # Validate user structure
            for user in users:
                required_fields = ["user_email", "user_name", "resources"]
                missing_fields = [field for field in required_fields if field not in user]
                
                if missing_fields:
                    self.log_test("Users Endpoint", False, f"User missing fields: {missing_fields}")
                    return False
            
            self.log_test("Users Endpoint", True, f"Retrieved {len(users)} users with proper structure")
            return True
            
        except Exception as e:
            self.log_test("Users Endpoint", False, f"Error: {str(e)}")
            return False

    def test_providers_endpoint(self):
        """Test 5: GET /api/providers for statistics"""
        try:
            response = requests.get(f"{self.base_url}/providers", timeout=10)
            
            if response.status_code != 200:
                self.log_test("Providers Endpoint", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            stats = response.json()
            
            # Validate structure
            if "total_users" not in stats or "providers" not in stats:
                self.log_test("Providers Endpoint", False, "Missing 'total_users' or 'providers' in response")
                return False
            
            providers = stats["providers"]
            expected_providers = ["aws", "gcp", "azure", "okta"]
            
            for provider in expected_providers:
                if provider not in providers:
                    self.log_test("Providers Endpoint", False, f"Missing provider: {provider}")
                    return False
                
                provider_stats = providers[provider]
                if "users" not in provider_stats or "resources" not in provider_stats:
                    self.log_test("Providers Endpoint", False, f"Provider {provider} missing 'users' or 'resources' stats")
                    return False
            
            self.log_test("Providers Endpoint", True, f"Statistics for {len(providers)} providers with total {stats['total_users']} users")
            return True
            
        except Exception as e:
            self.log_test("Providers Endpoint", False, f"Error: {str(e)}")
            return False

    def test_user_resources_endpoint(self):
        """Test 6: GET /api/users/{email}/resources for specific user resources"""
        all_passed = True
        
        # Test with existing users
        for email in self.sample_users:
            try:
                response = requests.get(f"{self.base_url}/users/{email}/resources", timeout=10)
                
                if response.status_code != 200:
                    self.log_test(f"User Resources: {email}", False, f"HTTP {response.status_code}: {response.text}")
                    all_passed = False
                    continue
                
                resources = response.json()
                
                if not isinstance(resources, list):
                    self.log_test(f"User Resources: {email}", False, "Response is not a list")
                    all_passed = False
                    continue
                
                if len(resources) == 0:
                    self.log_test(f"User Resources: {email}", False, "No resources returned")
                    all_passed = False
                    continue
                
                # Validate resource structure
                for resource in resources:
                    required_fields = ["provider", "service", "resource_name", "access_type"]
                    missing_fields = [field for field in required_fields if field not in resource]
                    
                    if missing_fields:
                        self.log_test(f"User Resources: {email}", False, f"Resource missing fields: {missing_fields}")
                        all_passed = False
                        break
                
                if all_passed:
                    self.log_test(f"User Resources: {email}", True, f"Retrieved {len(resources)} resources with proper structure")
                
            except Exception as e:
                self.log_test(f"User Resources: {email}", False, f"Error: {str(e)}")
                all_passed = False
        
        # Test with non-existent user
        try:
            response = requests.get(f"{self.base_url}/users/nonexistent@company.com/resources", timeout=10)
            
            if response.status_code == 404:
                self.log_test("User Resources: Non-existent User", True, "Properly returned 404 for non-existent user")
            else:
                self.log_test("User Resources: Non-existent User", False, f"Expected 404, got {response.status_code}")
                all_passed = False
                
        except Exception as e:
            self.log_test("User Resources: Non-existent User", False, f"Error: {str(e)}")
            all_passed = False
        
        return all_passed

    def test_graph_data_validation(self):
        """Test 7: Detailed validation of graph data structure"""
        try:
            # Get graph data for alice@company.com
            response = requests.get(f"{self.base_url}/search/alice@company.com", timeout=10)
            
            if response.status_code != 200:
                self.log_test("Graph Data Validation", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            data = response.json()
            graph_data = data["graph_data"]
            nodes = graph_data["nodes"]
            edges = graph_data["edges"]
            
            # Validate node color coding
            provider_colors = {"aws": "#FF9900", "gcp": "#4285F4", "azure": "#0078D4", "okta": "#007DC1"}
            access_colors = {"read": "#28A745", "write": "#FFC107", "admin": "#DC3545", "owner": "#6F42C1", "user": "#17A2B8", "execute": "#FD7E14", "delete": "#E83E8C"}
            
            color_validation_passed = True
            
            for node in nodes:
                if node["type"] == "provider" and node.get("provider"):
                    expected_color = provider_colors.get(node["provider"])
                    if node.get("color") != expected_color:
                        color_validation_passed = False
                        break
                elif node["type"] == "resource" and node.get("access_type"):
                    expected_color = access_colors.get(node["access_type"])
                    if node.get("color") != expected_color:
                        color_validation_passed = False
                        break
            
            if not color_validation_passed:
                self.log_test("Graph Data Validation", False, "Color coding for providers/access types is incorrect")
                return False
            
            # Validate node hierarchy (user -> provider -> service -> resource)
            user_nodes = [n for n in nodes if n["type"] == "user"]
            provider_nodes = [n for n in nodes if n["type"] == "provider"]
            service_nodes = [n for n in nodes if n["type"] == "service"]
            resource_nodes = [n for n in nodes if n["type"] == "resource"]
            
            if len(user_nodes) != 1:
                self.log_test("Graph Data Validation", False, f"Expected 1 user node, found {len(user_nodes)}")
                return False
            
            if len(provider_nodes) == 0:
                self.log_test("Graph Data Validation", False, "No provider nodes found")
                return False
            
            if len(service_nodes) == 0:
                self.log_test("Graph Data Validation", False, "No service nodes found")
                return False
            
            if len(resource_nodes) == 0:
                self.log_test("Graph Data Validation", False, "No resource nodes found")
                return False
            
            self.log_test("Graph Data Validation", True, f"Graph structure validated: {len(user_nodes)} user, {len(provider_nodes)} providers, {len(service_nodes)} services, {len(resource_nodes)} resources with proper color coding")
            return True
            
        except Exception as e:
            self.log_test("Graph Data Validation", False, f"Error: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all backend tests"""
        print("=" * 80)
        print("CLOUD ACCESS VISUALIZATION BACKEND API TESTING")
        print("=" * 80)
        print(f"Testing backend at: {self.base_url}")
        print()
        
        # Run all tests
        tests = [
            self.test_api_health_check,
            self.test_sample_data_initialization,
            self.test_search_functionality,
            self.test_users_endpoint,
            self.test_providers_endpoint,
            self.test_user_resources_endpoint,
            self.test_graph_data_validation
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
            print("🎉 ALL TESTS PASSED! Backend API is working correctly.")
            return True
        else:
            print("⚠️  SOME TESTS FAILED! Check the details above.")
            return False

if __name__ == "__main__":
    tester = BackendTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)