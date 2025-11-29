#!/usr/bin/env python3
"""
Test the actual response format from the enhanced RAG API.
"""
import requests
import json

def test_response_format():
    """Test the enhanced response format."""
    print("🧪 Testing Enhanced Response Format")
    print("=" * 40)
    
    # Test simple question
    print("\n1. Testing Simple Question:")
    print("-" * 25)
    
    response = requests.post(
        "http://localhost:8000/api/v1/ask",
        json={
            "doc_id": "any",
            "question": "What is a database?",
            "top_k": 3
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"✅ Status: {response.status_code}")
        print(f"📊 Answer Type: {data.get('answer_type', 'missing')}")
        print(f"🎯 Confidence: {data.get('confidence', 'missing')}")
        print(f"📚 Sources: {data.get('sources', [])}")
        print(f"❓ Follow-up: {data.get('follow_up', 'missing')}")
        
        # Show formatted answer structure
        answer = data.get('answer', '')
        print(f"\n📝 Answer Structure Check:")
        print(f"   - Has Definition: {'✅' if '## Definition' in answer else '❌'}")
        print(f"   - Has Explanation: {'✅' if '## Explanation' in answer else '❌'}")
        print(f"   - Has Sources: {'✅' if '## Sources' in answer else '❌'}")
        
        # Show first 200 chars of answer
        print(f"\n📄 Answer Preview:")
        print(f"   {answer[:200]}...")
        
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
    
    # Test comparison question for table generation
    print("\n\n2. Testing Comparison Question (Table Generation):")
    print("-" * 50)
    
    response = requests.post(
        "http://localhost:8000/api/v1/ask",
        json={
            "doc_id": "any",
            "question": "What are the differences between normalization and denormalization?",
            "top_k": 3
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"✅ Status: {response.status_code}")
        print(f"📊 Answer Type: {data.get('answer_type', 'missing')}")
        print(f"🎯 Confidence: {data.get('confidence', 'missing')}")
        
        # Check for table generation
        answer = data.get('answer', '')
        has_table = '|' in answer and ('---' in answer or '━' in answer)
        print(f"📊 Table Generated: {'✅' if has_table else '❌'}")
        
        # Show table if present
        if has_table:
            lines = answer.split('\n')
            table_lines = []
            in_table = False
            for line in lines:
                if '|' in line:
                    table_lines.append(line)
                    in_table = True
                elif in_table and line.strip() == '':
                    break
            
            if table_lines:
                print(f"\n📊 Generated Table:")
                for line in table_lines[:5]:  # Show first 5 lines
                    print(f"   {line}")
                if len(table_lines) > 5:
                    print(f"   ... ({len(table_lines) - 5} more lines)")
        
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    test_response_format()