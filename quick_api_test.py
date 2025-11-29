#!/usr/bin/env python3
"""
Simple API test to verify endpoints are working.
"""
import requests
import json

def test_api_endpoints():
    """Test basic API functionality."""
    base_url = "http://localhost:8000"
    
    print("🚀 Testing API Endpoints")
    print("=" * 40)
    
    # Test health endpoint
    try:
        print("1. Testing health endpoint...")
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint working")
            health_data = response.json()
            print(f"   Status: {health_data.get('status', 'unknown')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to server: {e}")
        print("   Make sure the server is running: python main.py")
        return False
    
    # Test create chat endpoint
    try:
        print("\n2. Testing create chat endpoint...")
        response = requests.post(
            f"{base_url}/api/v1/chat/new",
            json={"title": "API Test Chat"},
            timeout=10
        )
        if response.status_code == 200:
            print("✅ Chat creation endpoint working")
            chat_data = response.json()
            session_id = chat_data.get("session_id")
            print(f"   Created session: {session_id}")
            return session_id
        else:
            print(f"❌ Chat creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Chat creation error: {e}")
        return False

if __name__ == "__main__":
    session_id = test_api_endpoints()
    if session_id:
        print(f"\n🎉 API endpoints are working! Session ID: {session_id}")
        print("\n📋 Available endpoints:")
        print("   GET  /health")
        print("   POST /api/v1/chat/new")
        print("   GET  /api/v1/chat/list") 
        print("   GET  /api/v1/chat/{session_id}")
        print("   POST /api/v1/chat/{session_id}/ask")
        print("   POST /api/v1/chat/{session_id}/rename")
        print("   DELETE /api/v1/chat/{session_id}")
        print("   GET  /api/v1/chat/{session_id}/stats")
        print("\n🌐 Try the interactive docs at: http://localhost:8000/docs")
    else:
        print("\n❌ API test failed. Check server logs for details.")