#!/usr/bin/env python3
"""
Test JWT Token Validation Issue
"""

import requests
import json

BACKEND_URL = "https://d602465a-6f1d-46f0-8a14-ab8451e05734.preview.emergentagent.com/api"

def test_jwt_validation():
    """Test JWT validation with different malformed tokens"""
    print("=== Testing JWT Token Validation ===")
    
    test_cases = [
        ("Valid format but wrong signature", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0QGV4YW1wbGUuY29tIiwiZXhwIjoxNjQwOTk1MjAwfQ.wrong_signature"),
        ("Malformed JWT", "not.a.jwt"),
        ("Empty token", ""),
        ("Just Bearer", "Bearer"),
        ("No Bearer prefix", "some_random_token"),
    ]
    
    for description, token in test_cases:
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(f"{BACKEND_URL}/auth/me", headers=headers, timeout=10)
            print(f"{description}: Status {response.status_code}")
            
            if response.status_code == 500:
                # Try to get more details
                try:
                    error_detail = response.json()
                    print(f"  Error detail: {error_detail}")
                except:
                    print(f"  Raw response: {response.text[:100]}")
        except Exception as e:
            print(f"{description}: Exception - {e}")

def test_analytics_endpoint_auth():
    """Test if analytics endpoint requires authentication"""
    print("\n=== Testing Analytics Endpoint Authentication ===")
    
    # Test without auth
    try:
        response = requests.get(f"{BACKEND_URL}/analytics", timeout=10)
        print(f"Analytics without auth: Status {response.status_code}")
    except Exception as e:
        print(f"Analytics without auth: Error - {e}")
    
    # Test with auth
    try:
        # Login first
        login_data = {"email": "adminn@iamsharan.com", "password": "Testing@123"}
        login_response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data, timeout=10)
        
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            response = requests.get(f"{BACKEND_URL}/analytics", headers=headers, timeout=10)
            print(f"Analytics with auth: Status {response.status_code}")
        else:
            print(f"Login failed: {login_response.status_code}")
    except Exception as e:
        print(f"Analytics with auth: Error - {e}")

if __name__ == "__main__":
    test_jwt_validation()
    test_analytics_endpoint_auth()