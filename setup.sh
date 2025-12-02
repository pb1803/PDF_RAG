#!/bin/bash
# Quick setup script for AI Tutor
# Supports both Linux/macOS and Windows (via Git Bash)

echo "🤖 AI Tutor - Quick Setup Script"
echo "================================="

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python --version 2>&1)
if [[ $? -ne 0 ]]; then
    echo "❌ Python not found. Please install Python 3.9+ first."
    exit 1
fi

echo "✅ Found: $python_version"

# Create virtual environment
echo "🔧 Creating virtual environment..."
if [ ! -d "venv" ]; then
    python -m venv venv
    echo "✅ Virtual environment created"
else
    echo "⚠️ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Copy environment file
if [ ! -f ".env" ]; then
    echo "⚙️ Setting up environment file..."
    cp .env.example .env
    echo "✅ .env file created from template"
    echo "📝 Please edit .env with your Google AI credentials"
else
    echo "⚠️ .env file already exists"
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p pdfs logs uploads
touch pdfs/.gitkeep logs/.gitkeep uploads/.gitkeep

# Check for Docker
echo "🐳 Checking for Docker..."
if command -v docker &> /dev/null; then
    echo "✅ Docker found"
    echo "🚀 Starting Qdrant vector database..."
    docker run -d -p 6333:6333 --name qdrant qdrant/qdrant 2>/dev/null || \
    docker start qdrant 2>/dev/null || echo "⚠️ Qdrant container may already exist"
else
    echo "⚠️ Docker not found. Please install Docker for Qdrant database."
    echo "   Alternative: Use Docker Desktop or install Qdrant manually"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file with your Google AI credentials"
echo "2. Place PDF files in the pdfs/ folder"
echo "3. Run: python main.py"
echo "4. Open: http://localhost:8000"
echo ""
echo "📖 For detailed setup instructions, see README.md"