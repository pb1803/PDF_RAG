#!/usr/bin/env python3
"""
Quick test for enhanced RAG pipeline functionality.
"""
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_imports():
    """Test that all imports work correctly."""
    try:
        from app.rag.rag_pipeline import rag_pipeline
        from app.schemas.responses import AskQuestionResponse
        from app.api.qa_routes import router
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import error: {str(e)}")
        return False

def test_helper_methods():
    """Test that helper methods exist."""
    try:
        from app.rag.rag_pipeline import rag_pipeline
        
        # Check if new methods exist
        methods_to_check = [
            '_determine_answer_type',
            '_generate_pdf_answer', 
            '_generate_external_answer',
            '_generate_blended_answer',
            '_compress_pdf_chunks',
            '_apply_smart_formatting',
            '_detect_table_question',
            '_format_enhanced_sources'
        ]
        
        missing_methods = []
        for method in methods_to_check:
            if not hasattr(rag_pipeline, method):
                missing_methods.append(method)
        
        if missing_methods:
            print(f"❌ Missing methods: {missing_methods}")
            return False
        else:
            print("✅ All helper methods present")
            return True
            
    except Exception as e:
        print(f"❌ Method check error: {str(e)}")
        return False

def test_table_detection():
    """Test table detection functionality."""
    try:
        from app.rag.rag_pipeline import rag_pipeline
        
        # Test questions that should trigger tables
        table_questions = [
            "What is the difference between SQL and NoSQL?",
            "Compare generalization vs specialization",
            "Advantages and disadvantages of normalization"
        ]
        
        # Test questions that should NOT trigger tables
        non_table_questions = [
            "What is a database?",
            "Explain foreign keys",
            "How does indexing work?"
        ]
        
        for question in table_questions:
            if not rag_pipeline._detect_table_question(question):
                print(f"❌ Failed to detect table need for: {question}")
                return False
        
        for question in non_table_questions:
            if rag_pipeline._detect_table_question(question):
                print(f"❌ False positive table detection for: {question}")
                return False
        
        print("✅ Table detection working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Table detection error: {str(e)}")
        return False

def test_response_schema():
    """Test that response schema has new fields."""
    try:
        from app.schemas.responses import AskQuestionResponse
        
        # Check if new fields exist in the model
        required_fields = ['answer_type', 'confidence', 'follow_up']
        
        model_fields = AskQuestionResponse.model_fields.keys()
        
        missing_fields = []
        for field in required_fields:
            if field not in model_fields:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ Missing response fields: {missing_fields}")
            return False
        else:
            print("✅ Response schema updated correctly")
            return True
            
    except Exception as e:
        print(f"❌ Response schema error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧠 Quick Enhanced RAG Test")
    print("=" * 30)
    
    tests = [
        ("Import Test", test_imports),
        ("Helper Methods Test", test_helper_methods), 
        ("Table Detection Test", test_table_detection),
        ("Response Schema Test", test_response_schema)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        if test_func():
            passed += 1
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Enhanced RAG pipeline is ready.")
    else:
        print("❌ Some tests failed. Check the implementation.")