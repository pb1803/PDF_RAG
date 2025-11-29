#!/usr/bin/env python3
"""
Demo of the Enhanced RAG Pipeline functionality.
"""
import requests
import json
import time

def demo_enhanced_rag():
    """Demonstrate the enhanced RAG pipeline features."""
    print("🚀 Enhanced RAG Pipeline Demo")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # Test 1: Simple question (PDF-only answer)
    print("\n📚 Test 1: Simple Database Question")
    print("-" * 35)
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/ask",
            json={"doc_id": "any", "question": "What is a database?"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success!")
            print(f"📊 Answer Type: {data.get('answer_type')}")
            print(f"🎯 Confidence: {data.get('confidence', 0):.2f}")
            print(f"📚 Sources: {', '.join(data.get('sources', []))}")
            print(f"❓ Follow-up: {data.get('follow_up', 'None')}")
            
            # Check formatting
            answer = data.get('answer', '')
            has_structure = '## Definition' in answer
            print(f"📝 Structured Format: {'✅' if has_structure else '❌'}")
            
        else:
            print(f"❌ Failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    # Test 2: Comparison question (should generate table)
    print("\n📊 Test 2: Comparison Question (Table Generation)")
    print("-" * 50)
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/ask",
            json={
                "doc_id": "any", 
                "question": "What is the difference between SQL and NoSQL databases?",
                "top_k": 3
            },
            timeout=45
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success!")
            print(f"📊 Answer Type: {data.get('answer_type')}")
            print(f"🎯 Confidence: {data.get('confidence', 0):.2f}")
            
            # Check for table
            answer = data.get('answer', '')
            has_table = '|' in answer and 'SQL' in answer
            print(f"📊 Table Generated: {'✅' if has_table else '❌'}")
            
            if has_table:
                print("\n📋 Table Preview:")
                lines = answer.split('\n')
                for line in lines:
                    if '|' in line and len(line.strip()) > 5:
                        print(f"   {line.strip()}")
                        
        else:
            print(f"❌ Failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    # Test 3: External knowledge question
    print("\n🌐 Test 3: External Knowledge Question")
    print("-" * 40)
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/ask",
            json={
                "doc_id": "any", 
                "question": "What is quantum computing and how does it work?",
                "top_k": 3
            },
            timeout=45
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success!")
            print(f"📊 Answer Type: {data.get('answer_type')}")
            print(f"🎯 Confidence: {data.get('confidence', 0):.2f}")
            print(f"📚 Sources: {', '.join(data.get('sources', []))}")
            
            # Check for external knowledge indicator
            answer = data.get('answer', '')
            has_external_note = 'external' in answer.lower() or 'not found in' in answer.lower()
            print(f"🌐 External Knowledge Used: {'✅' if has_external_note else '❌'}")
            
        else:
            print(f"❌ Failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    print(f"\n🎉 Enhanced RAG Pipeline Demo Complete!")
    print(f"🔗 Server running at: {base_url}")
    print(f"📖 API Documentation: {base_url}/docs")

if __name__ == "__main__":
    demo_enhanced_rag()