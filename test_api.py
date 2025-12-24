#!/usr/bin/env python3
"""
Test the API endpoints
"""

import requests
import json

def test_api():
    """Test the API endpoints."""
    base_url = "http://localhost:8001"
    
    print("🧪 Testing API endpoints...")
    
    try:
        # Test health endpoint
        print("1. Testing health endpoint...")
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("   ✅ Health endpoint working")
        else:
            print(f"   ❌ Health endpoint failed: {response.status_code}")
        
        # Test login endpoint
        print("2. Testing login endpoint...")
        login_data = {
            "username": "demo@user.com",
            "password": "demo123"
        }
        
        response = requests.post(f"{base_url}/api/v1/auth/login", data=login_data)
        if response.status_code == 200:
            print("   ✅ Login endpoint working")
            token_data = response.json()
            token = token_data.get("access_token")
            print(f"   Token received: {token[:20]}...")
            
            # Test protected endpoint
            print("3. Testing protected endpoint...")
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(f"{base_url}/api/v1/subscriptions/authors", headers=headers)
            if response.status_code == 200:
                print("   ✅ Protected endpoint working")
                authors = response.json()
                print(f"   Found {len(authors)} authors")
            else:
                print(f"   ❌ Protected endpoint failed: {response.status_code}")
                print(f"   Response: {response.text}")
        else:
            print(f"   ❌ Login failed: {response.status_code}")
            print(f"   Response: {response.text}")
        
        print("\n🎉 API testing complete!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure it's running on port 8001")
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")

if __name__ == "__main__":
    test_api()