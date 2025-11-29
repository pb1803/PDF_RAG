#!/usr/bin/env python3
"""
Enhanced RAG Pipeline - Academic Agent Setup Script
Automated setup and configuration for the Academic Agent system.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_banner():
    """Print setup banner."""
    print("🚀" + "=" * 60 + "🚀")
    print("    Enhanced RAG Pipeline - Academic Agent Setup")
    print("    Automated Installation and Configuration")
    print("🚀" + "=" * 60 + "🚀")
    print()

def check_python_version():
    """Check if Python version is compatible."""
    print("📋 Checking Python version...")
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required!")
        print(f"   Current version: {sys.version}")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")

def check_git():
    """Check if git is available."""
    print("📋 Checking Git installation...")
    try:
        subprocess.run(["git", "--version"], check=True, capture_output=True)
        print("✅ Git is available")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  Git not found - some features may be limited")
        return False

def create_virtual_environment():
    """Create and activate virtual environment."""
    print("🔧 Setting up virtual environment...")
    
    venv_path = Path("venv")
    if venv_path.exists():
        print("✅ Virtual environment already exists")
        return
    
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✅ Virtual environment created")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create virtual environment: {e}")
        sys.exit(1)

def get_pip_command():
    """Get the appropriate pip command for the platform."""
    if os.name == 'nt':  # Windows
        return os.path.join("venv", "Scripts", "pip")
    else:  # Unix/Linux/macOS
        return os.path.join("venv", "bin", "pip")

def install_dependencies():
    """Install Python dependencies."""
    print("📦 Installing dependencies...")
    
    pip_cmd = get_pip_command()
    
    try:
        # Upgrade pip first
        subprocess.run([pip_cmd, "install", "--upgrade", "pip"], check=True)
        
        # Install requirements
        subprocess.run([pip_cmd, "install", "-r", "requirements.txt"], check=True)
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        sys.exit(1)

def create_directories():
    """Create necessary directories."""
    print("📁 Creating necessary directories...")
    
    directories = [
        "logs",
        "uploads", 
        "pdfs",
        "qdrant-local",
        "data"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")

def setup_environment_file():
    """Set up environment configuration."""
    print("⚙️  Setting up environment configuration...")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return
    
    if env_example.exists():
        shutil.copy(env_example, env_file)
        print("✅ Created .env from .env.example")
    else:
        # Create basic .env file
        env_content = """# Enhanced RAG Pipeline - Academic Agent Configuration
# Copy this file to .env and fill in your values

# Google AI Configuration (Required)
GOOGLE_API_KEY=your_google_api_key_here

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=True

# Database Configuration
DATABASE_URL=sqlite:///./data/aiagent.db

# Qdrant Configuration
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION_NAME=pdf_documents

# RAG Configuration
GEMINI_MODEL=gemini-2.0-flash
EMBEDDING_MODEL=text-embedding-004
TEMPERATURE=0.1
MAX_TOKENS=2000
TOP_K_RETRIEVAL=8
TOP_K_FINAL=5

# File Upload Configuration
MAX_FILE_SIZE_MB=50
UPLOAD_DIR=uploads

# Logging Configuration
LOG_LEVEL=INFO
"""
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("✅ Created basic .env file")
    
    print("⚠️  Please edit .env file and add your Google API key!")

def check_api_key():
    """Check if API key is configured."""
    print("🔑 Checking API key configuration...")
    
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  .env file not found")
        return False
    
    with open(env_file, 'r') as f:
        content = f.read()
        if "your_google_api_key_here" in content:
            print("⚠️  Please update GOOGLE_API_KEY in .env file")
            return False
        elif "GOOGLE_API_KEY=" in content:
            print("✅ API key appears to be configured")
            return True
    
    return False

def run_tests():
    """Run basic tests to verify installation."""
    print("🧪 Running basic tests...")
    
    python_cmd = sys.executable
    if os.name == 'nt':  # Windows
        python_cmd = os.path.join("venv", "Scripts", "python")
    else:  # Unix/Linux/macOS
        python_cmd = os.path.join("venv", "bin", "python")
    
    try:
        # Test imports
        subprocess.run([
            python_cmd, "-c", 
            "import fastapi, google.generativeai, qdrant_client; print('✅ Core imports successful')"
        ], check=True)
        
        # Run quick test if available
        if Path("quick_test_enhanced.py").exists():
            print("🔍 Running enhanced tests...")
            subprocess.run([python_cmd, "quick_test_enhanced.py"], check=True)
        
        print("✅ All tests passed!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Tests failed: {e}")
        return False

def print_next_steps():
    """Print next steps for the user."""
    print("\n🎉 Setup Complete!")
    print("=" * 50)
    print("Next steps:")
    print()
    print("1. 📝 Edit .env file and add your Google API key:")
    print("   GOOGLE_API_KEY=your_actual_api_key_here")
    print()
    print("2. 📚 Add PDF files to the pdfs/ directory:")
    print("   cp your_textbook.pdf pdfs/")
    print()
    print("3. 🚀 Start the server:")
    if os.name == 'nt':  # Windows
        print("   venv\\Scripts\\python main.py")
    else:  # Unix/Linux/macOS
        print("   venv/bin/python main.py")
    print()
    print("4. 🌐 Open your browser:")
    print("   http://localhost:8000")
    print("   http://localhost:8000/docs (API documentation)")
    print()
    print("5. 🧪 Test the system:")
    print("   Open enhanced_rag_demo.html in your browser")
    print()
    print("📖 For detailed instructions, see README.md")
    print("🐛 For issues, check: https://github.com/pb1803/Academic_agent/issues")

def main():
    """Main setup function."""
    print_banner()
    
    # Check prerequisites
    check_python_version()
    has_git = check_git()
    
    # Setup steps
    create_virtual_environment()
    install_dependencies()
    create_directories()
    setup_environment_file()
    
    # Check configuration
    api_key_configured = check_api_key()
    
    # Run tests
    if api_key_configured:
        tests_passed = run_tests()
    else:
        print("⚠️  Skipping tests - API key not configured")
        tests_passed = False
    
    # Print next steps
    print_next_steps()
    
    if not api_key_configured:
        print("\n⚠️  IMPORTANT: Configure your Google API key before starting!")
    
    if tests_passed:
        print("\n🎉 System is ready to use!")
    else:
        print("\n⚠️  Please complete configuration and run tests manually")

if __name__ == "__main__":
    main()