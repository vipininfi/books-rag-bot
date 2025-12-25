#!/usr/bin/env python3
"""
Test search performance with the actual user account vipin@gmail.com
This simulates the real frontend search flow.
"""

import asyncio
import time
import requests
import json

# Test configuration
BASE_URL = "http://localhost:8001"
USER_EMAIL = "vipin@gmail.com"
USER_PASSWORD = "vipin123"

async def test_real_user_search():
    """Test search with the actual user account and subscriptions."""
    
    print("🔐 Testing with Real User Account")
    print("=" * 50)
    print(f"Email: {USER_EMAIL}")
    print(f"Testing search performance from frontend perspective")
    print("=" * 50)
    
    # Step 1: Login to get token
    print("🔑 Step 1: Logging in...")
    
    login_data = {
        "username": USER_EMAIL,
        "password": USER_PASSWORD
    }
    
    try:
        login_response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            return
        
        login_result = login_response.json()
        token = login_result["access_token"]
        user_id = login_result["user_id"]
        user_role = login_result["user_role"]
        
        print(f"✅ Login successful!")
        print(f"   User ID: {user_id}")
        print(f"   Role: {user_role}")
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        return
    
    # Step 2: Check subscriptions
    print(f"\n📚 Step 2: Checking subscriptions...")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        subs_response = requests.get(
            f"{BASE_URL}/api/v1/subscriptions/authors",
            headers=headers
        )
        
        if subs_response.status_code == 200:
            subscriptions = subs_response.json()
            print(f"✅ Found {len(subscriptions)} subscriptions:")
            
            for sub in subscriptions:
                print(f"   - Author: {sub['name']} (ID: {sub['id']}) - Books: {sub['book_count']}")
        else:
            print(f"⚠️ Could not get subscriptions: {subs_response.status_code}")
            
    except Exception as e:
        print(f"❌ Subscription check error: {e}")
    
    # Step 3: Test search queries
    print(f"\n🔍 Step 3: Testing search queries...")
    
    test_queries = [
        "who is doctor dolittle",
        "how to forgive someone", 
        "what is the main character",
        "forgiveness steps"
    ]
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🧪 TEST {i}: '{query}'")
        print("-" * 30)
        
        search_data = {
            "query": query,
            "limit": 10
        }
        
        # Time the search (simulating frontend)
        start_time = time.time()
        
        try:
            search_response = requests.post(
                f"{BASE_URL}/api/v1/search/semantic",
                headers=headers,
                json=search_data
            )
            
            search_time = time.time() - start_time
            
            if search_response.status_code == 200:
                results = search_response.json()
                
                print(f"⏱️  TOTAL TIME: {search_time:.3f}s")
                print(f"📊 Results: {results['total_results']}")
                
                # Performance assessment
                if search_time < 0.5:
                    print(f"🎉 EXCELLENT! (< 0.5s)")
                elif search_time < 1.0:
                    print(f"✅ GOOD! (< 1.0s)")
                elif search_time < 2.0:
                    print(f"⚠️  ACCEPTABLE (< 2.0s)")
                else:
                    print(f"❌ STILL SLOW (> 2.0s)")
                
                # Show sample results
                if results['results']:
                    result = results['results'][0]
                    print(f"📋 Top result:")
                    print(f"   Score: {result['score']:.3f}")
                    print(f"   Book: {result['book_title']} by {result['author_name']}")
                    print(f"   Section: {result['section_title']}")
                    print(f"   Page: {result['page_number']}")
                    print(f"   Text: {result['text'][:100]}...")
                else:
                    print(f"📋 No results found")
            
            else:
                print(f"❌ Search failed: {search_response.status_code}")
                print(f"Response: {search_response.text}")
                
        except Exception as e:
            search_time = time.time() - start_time
            print(f"❌ Search error after {search_time:.3f}s: {e}")
    
    # Step 4: Test RAG queries
    print(f"\n🤖 Step 4: Testing RAG queries...")
    
    rag_query = "who is doctor dolittle"
    
    print(f"\n🧪 RAG TEST: '{rag_query}'")
    print("-" * 30)
    
    rag_data = {
        "query": rag_query,
        "max_chunks": 8
    }
    
    start_time = time.time()
    
    try:
        rag_response = requests.post(
            f"{BASE_URL}/api/v1/search/rag",
            headers=headers,
            json=rag_data
        )
        
        rag_time = time.time() - start_time
        
        if rag_response.status_code == 200:
            rag_result = rag_response.json()
            
            print(f"⏱️  RAG TIME: {rag_time:.3f}s")
            print(f"📊 Sources: {rag_result['total_chunks']}")
            print(f"🤖 Model: {rag_result.get('llm_model', 'Unknown')}")
            
            # Show answer preview
            answer = rag_result['answer']
            print(f"📝 Answer preview: {answer[:200]}...")
            
            # Performance assessment
            if rag_time < 2.0:
                print(f"🎉 EXCELLENT RAG! (< 2.0s)")
            elif rag_time < 5.0:
                print(f"✅ GOOD RAG! (< 5.0s)")
            else:
                print(f"⚠️  SLOW RAG (> 5.0s)")
        
        else:
            print(f"❌ RAG failed: {rag_response.status_code}")
            print(f"Response: {rag_response.text}")
            
    except Exception as e:
        rag_time = time.time() - start_time
        print(f"❌ RAG error after {rag_time:.3f}s: {e}")

def check_server_status():
    """Check if the server is running."""
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        return response.status_code == 200
    except:
        return False

async def main():
    """Run the real user test."""
    
    print("🎯 REAL USER SEARCH PERFORMANCE TEST")
    print("This tests the actual user experience from frontend to backend")
    print()
    
    # Check server status
    if not check_server_status():
        print(f"❌ Server not running at {BASE_URL}")
        print(f"💡 Start the server with: python start_server.py")
        return
    
    print(f"✅ Server is running at {BASE_URL}")
    
    await test_real_user_search()
    
    print(f"\n🎉 REAL USER TEST COMPLETE!")
    print(f"💡 This shows the actual performance users experience")

if __name__ == "__main__":
    asyncio.run(main())