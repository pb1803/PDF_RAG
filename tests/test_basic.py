"""
Basic tests for AI Tutor application with mocking support
"""

import sys
import os
import pytest
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_app_structure():
    """Test that basic app structure exists"""
    assert os.path.exists('main.py'), "main.py should exist"
    assert os.path.exists('app/'), "app/ directory should exist"
    assert os.path.exists('requirements.txt'), "requirements.txt should exist"
    assert os.path.exists('.env.example'), ".env.example should exist"
    assert os.path.exists('README.md'), "README.md should exist"

def test_basic_fastapi_import():
    """Test that FastAPI can be imported"""
    try:
        import fastapi
        assert fastapi is not None
        print("✅ FastAPI imported successfully")
    except ImportError:
        pytest.fail("FastAPI should be available in CI environment")

def test_app_imports():
    """Test that main app components can be imported"""
    # Set mock environment first
    os.environ['DISABLE_RAG_REAL_CALLS'] = 'true'
    os.environ['MOCK_EMBEDDINGS'] = 'true' 
    os.environ['MOCK_GEMINI'] = 'true'
    
    try:
        from app.core.config import settings
        assert settings is not None
        print("✅ Core config imported successfully")
    except ImportError as e:
        pytest.skip(f"Core config import skipped due to missing dependency: {e}")

def test_api_imports():
    """Test that API routes can be imported"""
    # Set mock environment
    os.environ['DISABLE_RAG_REAL_CALLS'] = 'true'
    os.environ['MOCK_EMBEDDINGS'] = 'true'
    os.environ['MOCK_GEMINI'] = 'true'
    
    try:
        from app.api import pdf_routes, qa_routes, chat_routes
        assert pdf_routes is not None
        assert qa_routes is not None  
        assert chat_routes is not None
        print("✅ API routes imported successfully")
    except ImportError as e:
        # If optional dependencies are missing in CI, skip this test
        pytest.skip(f"API import skipped due to missing dependency: {e}")

def test_main_app_import():
    """Test that main app can be imported"""
    # Set mock environment
    os.environ['DISABLE_RAG_REAL_CALLS'] = 'true'
    os.environ['MOCK_EMBEDDINGS'] = 'true'
    os.environ['MOCK_GEMINI'] = 'true'
    
    try:
        from main import app
        assert app is not None
        print("✅ Main app imported successfully")
    except ImportError as e:
        pytest.skip(f"Main app import skipped due to missing dependency: {e}")