#!/usr/bin/env python3
"""
Test script for chat session functionality.
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_chat_sessions():
    """Test the chat session endpoints."""
    print("🚀 Testing Chat Session Functionality\n")
    
    try:
        # Test 1: Create a new chat session
        print("1. Creating a new chat session...")
        create_response = requests.post(
            f"{BASE_URL}/api/v1/chat/new",
            json={"title": "Test Physics Chat"}
        )
        
        if create_response.status_code == 200:
            session_data = create_response.json()
            session_id = session_data["session_id"]
            print(f"✅ Created session: {session_id}")
            print(f"   Title: {session_data['title']}")
        else:
            print(f"❌ Failed to create session: {create_response.text}")
            return False
        
        # Test 2: List chat sessions
        print("\n2. Listing chat sessions...")
        list_response = requests.get(f"{BASE_URL}/api/v1/chat/list")
        
        if list_response.status_code == 200:
            sessions = list_response.json()
            print(f"✅ Found {len(sessions)} session(s)")
            if sessions:
                print(f"   Latest: {sessions[0]['title']}")
        else:
            print(f"❌ Failed to list sessions: {list_response.text}")
            return False
        
        # Test 3: Ask a question in the chat
        print("\n3. Asking a question in the chat...")
        ask_response = requests.post(
            f"{BASE_URL}/api/v1/chat/{session_id}/ask",
            json={
                "question": "What is a database?",
                "doc_id": "any",
                "top_k": 3
            }
        )
        
        if ask_response.status_code == 200:
            answer_data = ask_response.json()
            print(f"✅ Got answer (length: {len(answer_data.get('answer', ''))})")
            print(f"   Follow-up: {answer_data.get('follow_up', 'None')}")
            print(f"   Sources: {answer_data.get('sources', [])}")
            print(f"   Confidence: {answer_data.get('confidence_score', 'N/A')}")
        else:
            print(f"❌ Failed to ask question: {ask_response.text}")
            return False
        
        # Test 4: Ask a follow-up question (tests memory)
        print("\n4. Asking a follow-up question...")
        followup_response = requests.post(
            f"{BASE_URL}/api/v1/chat/{session_id}/ask",
            json={
                "question": "Can you give me an example?",
                "doc_id": "any",
                "top_k": 3
            }
        )
        
        if followup_response.status_code == 200:
            followup_data = followup_response.json()
            print(f"✅ Got follow-up answer (length: {len(followup_data.get('answer', ''))})")
            print(f"   Memory should include previous context")
        else:
            print(f"❌ Failed to ask follow-up: {followup_response.text}")
            return False
        
        # Test 5: Get chat session with messages
        print("\n5. Retrieving chat session with messages...")
        get_response = requests.get(f"{BASE_URL}/api/v1/chat/{session_id}")
        
        if get_response.status_code == 200:
            chat_data = get_response.json()
            messages = chat_data.get("messages", [])
            print(f"✅ Chat has {len(messages)} messages")
            
            for i, msg in enumerate(messages[-4:]):  # Show last 4 messages
                role = msg["role"]
                text = msg["text"][:100] + "..." if len(msg["text"]) > 100 else msg["text"]
                print(f"   {i+1}. {role}: {text}")
        else:
            print(f"❌ Failed to get chat: {get_response.text}")
            return False
        
        # Test 6: Rename the chat session
        print("\n6. Renaming the chat session...")
        rename_response = requests.post(
            f"{BASE_URL}/api/v1/chat/{session_id}/rename",
            json={"title": "Database Discussion - Updated"}
        )
        
        if rename_response.status_code == 200:
            print("✅ Successfully renamed chat session")
        else:
            print(f"❌ Failed to rename: {rename_response.text}")
            return False
        
        # Test 7: Get chat statistics
        print("\n7. Getting chat statistics...")
        stats_response = requests.get(f"{BASE_URL}/api/v1/chat/{session_id}/stats")
        
        if stats_response.status_code == 200:
            stats = stats_response.json()
            print(f"✅ Chat stats:")
            print(f"   Total messages: {stats.get('total_messages')}")
            print(f"   User messages: {stats.get('user_messages')}")
            print(f"   Assistant messages: {stats.get('assistant_messages')}")
        else:
            print(f"❌ Failed to get stats: {stats_response.text}")
            return False
        
        print("\n🎉 All chat session tests passed!")
        return True
        
    except requests.ConnectionError:
        print("❌ Connection failed. Is the server running on http://localhost:8000?")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        return False

def test_health_check():
    """Test the health check endpoint."""
    print("🏥 Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            health = response.json()
            print(f"✅ Health check passed")
            print(f"   Status: {health.get('status')}")
            components = health.get('components', {})
            for comp, status in components.items():
                print(f"   {comp}: {status}")
            return True
        else:
            print(f"❌ Health check failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 AI Tutor Chat Session Test Suite")
    print("=" * 50)
    
    # Wait a moment for server to be ready
    print("⏳ Waiting for server to be ready...")
    time.sleep(2)
    
    # Test health first
    health_ok = test_health_check()
    print()
    
    if health_ok:
        # Test chat functionality
        chat_ok = test_chat_sessions()
        
        if chat_ok:
            print("\n🎯 Summary: All tests passed! Chat sessions are working correctly.")
        else:
            print("\n⚠️ Summary: Some chat tests failed. Check the logs above.")
    else:
        print("\n⚠️ Summary: Server health check failed. Check server status.")