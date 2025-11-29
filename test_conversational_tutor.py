#!/usr/bin/env python3
"""
Test script for the new conversational tutor system.
"""
import asyncio
import sys
import os

# Add the app directory to path
sys.path.insert(0, os.path.dirname(__file__))

from app.rag.rag_pipeline import rag_pipeline

async def test_conversational_tutor():
    """Test the new conversational tutor functionality."""
    try:
        # Initialize the pipeline
        await rag_pipeline.initialize()
        print("✅ RAG Pipeline initialized successfully")
        
        # Test with a sample question
        test_question = "What is machine learning?"
        print(f"\n🤔 Test Question: {test_question}")
        
        # This will test the new conversational format
        result = await rag_pipeline.answer_question(
            doc_id="any",  # Will use first available document
            question=test_question,
            top_k=3,
            temperature=0.7
        )
        
        print("\n📋 Response Structure:")
        print(f"Answer: {result.get('answer', 'N/A')}")
        print(f"Sources: {result.get('sources', [])}")
        print(f"Follow-up: {result.get('follow_up', 'N/A')}")
        print(f"Confidence: {result.get('confidence_score', 'N/A')}")
        print(f"Citations count: {len(result.get('citations', []))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing conversational tutor: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Testing Conversational Tutor System")
    success = asyncio.run(test_conversational_tutor())
    
    if success:
        print("\n✅ Conversational tutor test completed successfully!")
    else:
        print("\n❌ Conversational tutor test failed!")