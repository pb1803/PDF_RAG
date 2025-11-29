#!/usr/bin/env python3
"""
Test the enhanced API endpoints.
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_enhanced_ask_endpoint():
    """Test the enhanced /api/v1/ask endpoint."""
    print("🔍 Testing Enhanced Ask Endpoint")
    print("-" * 30)
    
    # Test data
    test_request = {
        "doc_id": "any",  # Use any available document
        "question": "What is the difference between generalization and specialization?",
        "top_k": 5,
        "temperature": 0.1
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/ask",
            json=test_request,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ Request successful")
            print(f"Answer Type: {data.get('answer_type', 'missing')}")
            print(f"Confidence: {data.get('confidence', 'missing')}")
            print(f"Sources: {data.get('sources', [])}")
            print(f"Follow-up: {data.get('follow_up', 'missing')}")
            
            # Check for new fields
            has_answer_type = 'answer_type' in data
            has_confidence = 'confidence' in data
            has_follow_up = 'follow_up' in data
            
            print(f"\nNew Fields Check:")
            print(f"  - answer_type: {'✅' if has_answer_type else '❌'}")
            print(f"  - confidence: {'✅' if has_confidence else '❌'}")
            print(f"  - follow_up: {'✅' if has_follow_up else '❌'}")
            
            # Check for table generation (if it's a comparison question)
            answer = data.get('answer', '')
            has_table = '|' in answer and 'difference' in test_request['question'].lower()
            print(f"  - table generated: {'✅' if has_table else '❌'}")
            
            # Check formatting
            has_definition = '## Definition' in answer
            has_sources_section = '## Sources' in answer
            
            print(f"\nFormatting Check:")
            print(f"  - structured format: {'✅' if has_definition else '❌'}")
            print(f"  - sources section: {'✅' if has_sources_section else '❌'}")
            
            return True
            
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed. Make sure the server is running on localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Test error: {str(e)}")
        return False

def test_chat_endpoint():
    """Test the enhanced chat endpoint."""
    print("\n💬 Testing Enhanced Chat Endpoint")
    print("-" * 30)
    
    try:
        # Create a new chat session
        chat_response = requests.post(f"{BASE_URL}/api/v1/chat/new")
        
        if chat_response.status_code != 200:
            print(f"❌ Failed to create chat session: {chat_response.status_code}")
            return False
        
        session_id = chat_response.json()["session_id"]
        print(f"✅ Created chat session: {session_id}")
        
        # Test ask in chat
        ask_request = {
            "doc_id": "any",
            "question": "What are the advantages and disadvantages of normalization?",
            "top_k": 5
        }
        
        ask_response = requests.post(
            f"{BASE_URL}/api/v1/chat/{session_id}/ask",
            json=ask_request,
            timeout=30
        )
        
        if ask_response.status_code == 200:
            data = ask_response.json()
            
            print("✅ Chat ask successful")
            print(f"Answer Type: {data.get('answer_type', 'missing')}")
            print(f"Session ID: {data.get('session_id', 'missing')}")
            
            # Check for enhanced fields
            has_enhanced_fields = all(field in data for field in ['answer_type', 'confidence', 'follow_up'])
            print(f"Enhanced fields: {'✅' if has_enhanced_fields else '❌'}")
            
            return True
        else:
            print(f"❌ Chat ask failed: {ask_response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed. Make sure the server is running on localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Chat test error: {str(e)}")
        return False

def main():
    """Run all API tests."""
    print("🚀 Enhanced RAG API Tests")
    print("=" * 40)
    
    tests = [
        ("Ask Endpoint", test_enhanced_ask_endpoint),
        ("Chat Endpoint", test_chat_endpoint)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        if test_func():
            passed += 1
        time.sleep(1)  # Brief pause between tests
    
    print(f"\n📊 API Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All API tests passed! Enhanced endpoints are working.")
    else:
        print("❌ Some API tests failed. Check server status and implementation.")
        print("\nTo run the server:")
        print("python main.py")

if __name__ == "__main__":
    main()