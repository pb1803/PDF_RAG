#!/usr/bin/env python3
"""
AI Tutor Deployment Verification Script
Checks all components and dependencies for successful deployment
"""

import os
import sys
import subprocess
import json
import requests
from pathlib import Path
import sqlite3
import time

class DeploymentChecker:
    def __init__(self):
        self.checks = []
        self.errors = []
        self.warnings = []
        
    def check(self, name):
        """Decorator for test functions"""
        def decorator(func):
            self.checks.append((name, func))
            return func
        return decorator
    
    def log_error(self, message):
        self.errors.append(message)
        print(f"❌ ERROR: {message}")
    
    def log_warning(self, message):
        self.warnings.append(message)
        print(f"⚠️  WARNING: {message}")
    
    def log_success(self, message):
        print(f"✅ {message}")

checker = DeploymentChecker()

@checker.check("Python Environment")
def check_python():
    """Check Python version and virtual environment"""
    try:
        version = sys.version_info
        if version.major != 3 or version.minor < 9:
            checker.log_error(f"Python 3.9+ required, found {version.major}.{version.minor}")
            return False
        
        # Check if in virtual environment
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            checker.log_success("Python virtual environment active")
        else:
            checker.log_warning("Not in virtual environment - recommended for deployment")
        
        checker.log_success(f"Python {version.major}.{version.minor}.{version.micro}")
        return True
    except Exception as e:
        checker.log_error(f"Python check failed: {e}")
        return False

@checker.check("Required Files")
def check_files():
    """Check for essential project files"""
    required_files = [
        'main.py',
        'requirements.txt',
        '.env.example',
        'README.md',
        'Dockerfile',
        'docker-compose.yml'
    ]
    
    missing = []
    for file in required_files:
        if not os.path.exists(file):
            missing.append(file)
    
    if missing:
        checker.log_error(f"Missing required files: {', '.join(missing)}")
        return False
    
    checker.log_success("All required files present")
    return True

@checker.check("Python Dependencies")
def check_dependencies():
    """Check if all Python packages are installed"""
    try:
        with open('requirements.txt', 'r') as f:
            requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        missing = []
        for req in requirements:
            package_name = req.split('==')[0].split('>=')[0].split('~=')[0]
            try:
                __import__(package_name.replace('-', '_'))
            except ImportError:
                missing.append(package_name)
        
        if missing:
            checker.log_error(f"Missing packages: {', '.join(missing)}")
            checker.log_error("Run: pip install -r requirements.txt")
            return False
        
        checker.log_success("All Python dependencies installed")
        return True
    except Exception as e:
        checker.log_error(f"Dependency check failed: {e}")
        return False

@checker.check("Environment Configuration")
def check_environment():
    """Check environment configuration"""
    if not os.path.exists('.env'):
        checker.log_error("No .env file found. Copy .env.example to .env and configure")
        return False
    
    # Check for critical environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    critical_vars = ['GOOGLE_API_KEY']
    missing = []
    
    for var in critical_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        checker.log_warning(f"Missing environment variables: {', '.join(missing)}")
        checker.log_warning("Configure these in .env file for full functionality")
    else:
        checker.log_success("Environment variables configured")
    
    return True

@checker.check("Directory Structure")
def check_directories():
    """Check required directories exist"""
    required_dirs = ['app', 'logs', 'uploads', 'pdfs']
    
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)
            checker.log_success(f"Created directory: {dir_name}")
        else:
            checker.log_success(f"Directory exists: {dir_name}")
    
    return True

@checker.check("Database Connection")
def check_database():
    """Check SQLite database functionality"""
    try:
        # Test database connection
        conn = sqlite3.connect('aiagent.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        conn.close()
        
        checker.log_success(f"Database accessible with {len(tables)} tables")
        return True
    except Exception as e:
        checker.log_warning(f"Database check failed: {e}")
        return True  # Not critical for initial deployment

@checker.check("Docker Availability")
def check_docker():
    """Check if Docker is available for Qdrant"""
    try:
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            checker.log_success("Docker available")
            
            # Check if Qdrant container is running
            result = subprocess.run(['docker', 'ps', '--filter', 'name=qdrant'], 
                                  capture_output=True, text=True, timeout=10)
            if 'qdrant' in result.stdout:
                checker.log_success("Qdrant container running")
            else:
                checker.log_warning("Qdrant container not running - start with: docker run -d -p 6333:6333 --name qdrant qdrant/qdrant")
            
            return True
        else:
            checker.log_warning("Docker not responding")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        checker.log_warning("Docker not found - install Docker for Qdrant database")
        return False

@checker.check("Application Startup")
def check_app_startup():
    """Test application startup without running server"""
    try:
        # Import main application modules to check for syntax errors
        sys.path.insert(0, os.getcwd())
        
        from app.core.config import settings
        from app.api.pdf_routes import router as pdf_router
        from app.api.qa_routes import router as qa_router
        
        checker.log_success("Application modules import successfully")
        return True
    except Exception as e:
        checker.log_error(f"Application startup check failed: {e}")
        return False

def run_all_checks():
    """Run all deployment checks"""
    print("🤖 AI Tutor Deployment Verification")
    print("=" * 50)
    
    passed = 0
    total = len(checker.checks)
    
    for name, check_func in checker.checks:
        print(f"\n🔍 Checking: {name}")
        try:
            if check_func():
                passed += 1
        except Exception as e:
            checker.log_error(f"Check '{name}' failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Results: {passed}/{total} checks passed")
    
    if checker.errors:
        print(f"\n❌ Errors ({len(checker.errors)}):")
        for error in checker.errors:
            print(f"   • {error}")
    
    if checker.warnings:
        print(f"\n⚠️  Warnings ({len(checker.warnings)}):")
        for warning in checker.warnings:
            print(f"   • {warning}")
    
    if passed == total and not checker.errors:
        print("\n🎉 All checks passed! Ready for deployment")
        print("\n🚀 To start the application:")
        print("   python main.py")
        print("\n🌐 Then visit: http://localhost:8000")
    elif checker.errors:
        print("\n🔧 Fix the errors above before deployment")
        return False
    else:
        print("\n⚠️  Some warnings present but deployment should work")
    
    return True

if __name__ == "__main__":
    success = run_all_checks()
    sys.exit(0 if success else 1)