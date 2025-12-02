@echo off
REM Quick setup script for AI Tutor - Windows Batch Version

echo 🤖 AI Tutor - Quick Setup Script (Windows)
echo ==========================================

REM Check Python version
echo 📋 Checking Python version...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found. Please install Python 3.9+ first.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set python_version=%%i
echo ✅ Found: %python_version%

REM Create virtual environment
echo 🔧 Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo ✅ Virtual environment created
) else (
    echo ⚠️ Virtual environment already exists
)

REM Activate virtual environment
echo 🔄 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo 📦 Installing dependencies...
pip install -r requirements.txt

REM Copy environment file
if not exist ".env" (
    echo ⚙️ Setting up environment file...
    copy .env.example .env >nul
    echo ✅ .env file created from template
    echo 📝 Please edit .env with your Google AI credentials
) else (
    echo ⚠️ .env file already exists
)

REM Create necessary directories
echo 📁 Creating necessary directories...
if not exist "pdfs" mkdir pdfs
if not exist "logs" mkdir logs
if not exist "uploads" mkdir uploads
echo. > pdfs\.gitkeep
echo. > logs\.gitkeep
echo. > uploads\.gitkeep

REM Check for Docker
echo 🐳 Checking for Docker...
docker --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Docker found
    echo 🚀 Starting Qdrant vector database...
    docker run -d -p 6333:6333 --name qdrant qdrant/qdrant 2>nul || docker start qdrant 2>nul || echo ⚠️ Qdrant container may already exist
) else (
    echo ⚠️ Docker not found. Please install Docker Desktop for Qdrant database.
)

echo.
echo 🎉 Setup complete!
echo.
echo 📋 Next steps:
echo 1. Edit .env file with your Google AI credentials
echo 2. Place PDF files in the pdfs/ folder
echo 3. Run: python main.py
echo 4. Open: http://localhost:8000
echo.
echo 📖 For detailed setup instructions, see README.md
pause