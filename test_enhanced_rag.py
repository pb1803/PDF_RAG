#!/usr/bin/env python3
"""
Test script for the enhanced RAG pipeline with improved formatting and external knowledge fallback.
"""
import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.rag.rag_pipeline import rag_pipeline
from app.rag.vectorstore import qdrant_store


async def test_enhanced_rag():
    """Test the enhanced RAG pipeline functionality."""
    print("🧠 Testing Enhanced RAG Pipeline")
    print("=" * 50)
    
    try:
        # Initialize components
        print("1. Initializing RAG pipeline...")
        await rag_pipeline.initialize()
        await qdrant_store.initialize()
        
        # Get available documents
        print("2. Checking available documents...")
        docs = await qdrant_store.list_documents()
        
        if not docs:
            print("❌ No documents found. Please add PDF files to the pdfs folder.")
            return
        
        doc_id = docs[0]["doc_id"]
        print(f"✅ Using document: {doc_id}")
        
        # Test different question types
        test_questions = [
            # Table generation test
            "What is the difference between generalization and specialization in DBMS?",
            
            # PDF-only test
            "What is a database?",
            
            # External knowledge test (likely not in PDF)
            "What is quantum computing?",
            
            # Mixed content test
            "Explain foreign keys and their importance in modern applications"
        ]
        
        print("\n3. Testing enhanced answer generation...")
        print("-" * 40)
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n🔍 Test {i}: {question}")
            print("-" * 30)
            
            try:
                result = await rag_pipeline.answer_question(
                    doc_id=doc_id,
                    question=question,
                    top_k=5
                )
                
                print(f"Answer Type: {result.get('answer_type', 'unknown')}")
                print(f"Confidence: {result.get('confidence', 0.0):.2f}")
                print(f"Sources: {result.get('sources', [])}")
                print(f"Follow-up: {result.get('follow_up', 'None')}")
                print(f"Chunks Used: {len(result.get('used_chunks', []))}")
                
                # Show formatted answer (first 300 chars)
                answer = result.get('answer', '')
                if len(answer) > 300:
                    print(f"Answer Preview: {answer[:300]}...")
                else:
                    print(f"Answer: {answer}")
                
                # Check for proper formatting
                has_definition = "## Definition" in answer
                has_sources = "## Sources" in answer
                has_table = "## Table" in answer and "difference" in question.lower()
                
                print(f"Formatting Check:")
                print(f"  - Has Definition: {'✅' if has_definition else '❌'}")
                print(f"  - Has Sources: {'✅' if has_sources else '❌'}")
                print(f"  - Has Table (if needed): {'✅' if has_table or 'difference' not in question.lower() else '❌'}")
                
            except Exception as e:
                print(f"❌ Error: {str(e)}")
        
        print("\n4. Testing health check...")
        health = await rag_pipeline.health_check()
        print(f"Health Status: {'✅ Healthy' if health else '❌ Unhealthy'}")
        
        print("\n🎉 Enhanced RAG Pipeline Test Complete!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_enhanced_rag())