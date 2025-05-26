#!/usr/bin/env python3
"""
Quick verification of current database state and user search functionality
"""

import requests
import json

# Configuration
BACKEND_URL = "https://d602465a-6f1d-46f0-8a14-ab8451e05734.preview.emergentagent.com/api"
DEFAULT_ADMIN_EMAIL = "adminn@iamsharan.com"
DEFAULT_ADMIN_PASSWORD = "Testing@123"

def get_admin_token():
    """Get admin token"""
    login_data = {
        "email": DEFAULT_ADMIN_EMAIL,
        "password": DEFAULT_ADMIN_PASSWORD
    }
    
    response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

def main():
    print("🔍 Verifying Current Database State")
    print("=" * 50)
    
    token = get_admin_token()
    if not token:
        print("❌ Failed to get admin token")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get all users
    print("\n📋 Current Users in Database:")
    response = requests.get(f"{BACKEND_URL}/users", headers=headers)
    if response.status_code == 200:
        users = response.json()
        for i, user in enumerate(users, 1):
            print(f"  {i}. {user['user_email']} ({user['user_name']})")
            print(f"     Resources: {len(user['resources'])}")
    
    # Test search with actual users
    print("\n🔍 Testing Search with Current Users:")
    if response.status_code == 200:
        users = response.json()
        for user in users[:3]:  # Test first 3 users
            email = user['user_email']
            search_response = requests.get(f"{BACKEND_URL}/search/{email}", headers=headers)
            
            if search_response.status_code == 200:
                search_data = search_response.json()
                if search_data.get("user"):
                    print(f"  ✅ {email}: Found with {len(search_data['user']['resources'])} resources")
                    print(f"     Graph nodes: {len(search_data['graph_data']['nodes'])}")
                    print(f"     Graph edges: {len(search_data['graph_data']['edges'])}")
                else:
                    print(f"  ❌ {email}: No user data returned")
            else:
                print(f"  ❌ {email}: Search failed with status {search_response.status_code}")
    
    # Test analytics
    print("\n📊 Analytics Summary:")
    analytics_response = requests.get(f"{BACKEND_URL}/analytics", headers=headers)
    if analytics_response.status_code == 200:
        analytics = analytics_response.json()
        print(f"  Total Users: {analytics['total_users']}")
        print(f"  Total Resources: {analytics['total_resources']}")
        print(f"  Risk Distribution: {analytics['risk_distribution']}")
        print(f"  Cross-provider Admins: {analytics['cross_provider_admins']}")
    
    print("\n✅ Database verification complete!")

if __name__ == "__main__":
    main()