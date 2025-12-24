#!/usr/bin/env python3
"""
Check web interface functionality
"""

import requests
import time

def check_web_interface():
    """Check if the web interface is working."""
    base_url = "http://localhost:8001"
    
    print("🌐 Checking web interface...")
    
    try:
        # Check if server is running
        print("1. Checking server health...")
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Server is running")
        else:
            print(f"   ❌ Server health check failed: {response.status_code}")
            return
        
        # Check if main page loads
        print("2. Checking main page...")
        response = requests.get(base_url, timeout=5)
        if response.status_code == 200:
            print("   ✅ Main page loads")
            if "Book RAG System" in response.text:
                print("   ✅ Page content looks correct")
            else:
                print("   ⚠️  Page content might be incorrect")
        else:
            print(f"   ❌ Main page failed: {response.status_code}")
        
        # Check static files
        print("3. Checking static files...")
        response = requests.get(f"{base_url}/static/js/app.js", timeout=5)
        if response.status_code == 200:
            print("   ✅ JavaScript file loads")
        else:
            print(f"   ❌ JavaScript file failed: {response.status_code}")
        
        response = requests.get(f"{base_url}/static/css/style.css", timeout=5)
        if response.status_code == 200:
            print("   ✅ CSS file loads")
        else:
            print(f"   ❌ CSS file failed: {response.status_code}")
        
        # Test login endpoint
        print("4. Testing login endpoint...")
        login_data = {
            "username": "demo@user.com",
            "password": "demo123"
        }
        
        response = requests.post(f"{base_url}/api/v1/auth/login", data=login_data, timeout=10)
        if response.status_code == 200:
            print("   ✅ Login endpoint working")
            data = response.json()
            if "access_token" in data:
                print("   ✅ Access token received")
            else:
                print("   ⚠️  No access token in response")
        else:
            print(f"   ❌ Login failed: {response.status_code}")
            print(f"   Response: {response.text}")
        
        print("\n🎉 Web interface check complete!")
        print(f"\n🌐 Open your browser and go to: {base_url}")
        print("📧 Demo login: demo@user.com / demo123")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure it's running on port 8001")
        print("💡 To start the server, run: python3 start_server.py")
    except Exception as e:
        print(f"❌ Check failed: {str(e)}")

if __name__ == "__main__":
    check_web_interface()