# 🤖 AI Tutor - Smart Study Assistant

A production-ready AI-powered study assistant that helps students learn from their PDF documents using advanced RAG (Retrieval-Augmented Generation) technology.

![AI Tutor Interface](https://img.shields.io/badge/Interface-ChatGPT--like-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green) ![Python](https://img.shields.io/badge/Python-3.9+-blue) ![Gemini](https://img.shields.io/badge/Gemini-2.0--Flash-orange)

## ✨ Features

- **🎯 Smart Q&A**: Ask questions about your uploaded PDFs and get instant, accurate answers
- **🧠 Memory & Context**: Maintains conversation history for deeper learning discussions
- **📚 Multi-Document Search**: Search across all your documents simultaneously
- **🎨 Modern UI**: ChatGPT-like dark theme interface with real-time chat
- **📄 Source Citations**: Every answer includes page references from your study materials
- **🔄 Real-time Processing**: Auto-processes PDFs as you upload them
- **💾 Persistent Storage**: All conversations and documents are saved locally

## 🚀 Live Demo

Upload your study materials and start chatting with your AI tutor instantly at `http://localhost:8000` after setup!

## 🛠️ Tech Stack

### Backend
- **FastAPI** - High-performance web framework
- **Google Gemini 2.0 Flash** - Advanced language model for generation
- **text-embedding-004** - State-of-the-art embeddings for semantic search
- **Qdrant** - Vector database for document storage
- **SQLite** - Chat history and session management

### Frontend
- **Vanilla JavaScript** - Lightweight, responsive interface
- **Modern CSS3** - Dark theme with smooth animations
- **Real-time API** - WebSocket-like experience with REST

## 📋 Prerequisites

- **Python 3.9+** installed on your system
- **Docker Desktop** (recommended for Qdrant database)
- **Google AI API Key** (free from Google AI Studio)
- **4GB+ RAM** recommended
- **2GB+ Storage** for document processing

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

**For Windows:**
```bash
# Clone the repository
git clone https://github.com/pb1803/PDF_RAG.git
cd PDF_RAG

# Run automated setup
setup.bat
```

**For Linux/macOS:**
```bash
# Clone the repository
git clone https://github.com/pb1803/PDF_RAG.git
cd PDF_RAG

# Make setup script executable and run
chmod +x setup.sh
./setup.sh
```

### Option 2: Manual Setup

#### Step 1: Clone the Repository
```bash
git clone https://github.com/pb1803/PDF_RAG.git
cd PDF_RAG
```

#### Step 2: Set Up Python Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### Step 3: Get Google AI API Key
1. Go to **[Google AI Studio](https://aistudio.google.com/app/apikey)**
2. Click **"Create API Key"**
3. Copy the generated API key
4. Keep it safe - you'll need it in the next step

#### Step 4: Configure Environment
```bash
# Copy environment template
cp .env.example .env
```

Edit the `.env` file with your API key:
```env
# Google AI Configuration
GOOGLE_API_KEY=your_actual_api_key_here

# Other settings (can leave as default)
DEBUG=true
HOST=0.0.0.0
PORT=8000
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION_NAME=pdf_documents
GEMINI_MODEL=gemini-2.0-flash
EMBEDDING_MODEL=text-embedding-004
```

#### Step 5: Start Qdrant Vector Database
```bash
# Using Docker (Recommended)
docker run -d -p 6333:6333 --name qdrant qdrant/qdrant

# Verify it's running
docker ps
```

**Don't have Docker?** Install Docker Desktop:
- **Windows/Mac**: Download from [docker.com](https://www.docker.com/products/docker-desktop/)
- **Linux**: `sudo apt install docker.io` (Ubuntu) or equivalent

#### Step 6: Launch the Application
```bash
python main.py
```

You should see:
```
✅ Database initialized successfully
✅ Embedder (text-embedding-004) initialized successfully  
✅ Vector store (Qdrant) initialized successfully
✅ RAG pipeline (gemini-2.0-flash) initialized successfully
🚀 Application startup complete - Ready to process PDFs!
```

#### Step 7: Open Your Browser
Navigate to **`http://localhost:8000`** and start learning!

## 📚 How to Use

### 1. Add Your Study Materials
- Place PDF files in the `pdfs/` folder
- The system will automatically process them
- Wait for "✅ RAG pipeline complete" message in the terminal

### 2. Start Chatting
1. Open **`http://localhost:8000`** in your browser
2. Click **"New Chat"** 
3. Ask questions like:
   - "What are the main concepts in my documents?"
   - "Explain machine learning from my notes"
   - "Create practice questions from chapter 5"
   - "Summarize the key points about blockchain"

### 3. Get Intelligent Answers
- Receive detailed answers with source citations
- See confidence scores for answer accuracy
- Navigate between different chat sessions
- Export conversations for later review

## ⚡ Quick Verification

Run this command to verify everything is working:
```bash
python verify_deployment.py
```

This will check:
- ✅ Python environment
- ✅ Dependencies installed  
- ✅ Environment configuration
- ✅ Database connectivity
- ✅ Docker/Qdrant status
- ✅ Application startup

## 🐳 Docker Deployment (Advanced)

### Quick Docker Setup
```bash
# Build and run with Docker Compose
docker-compose up --build -d

# Access at http://localhost:8000
```

### Manual Docker Build
```bash
# Build the image
docker build -t ai-tutor .

# Run the container
docker run -p 8000:8000 --env GOOGLE_API_KEY=your-key-here ai-tutor
```

## 🔧 Troubleshooting

### Common Issues & Solutions

**❌ "Google API Error" or "Authentication failed"**
```bash
# Check your API key is correct
# Go to https://aistudio.google.com/app/apikey
# Generate a new key if needed
# Make sure it's properly set in .env file
```

**❌ "Qdrant Connection Failed"**
```bash
# Check if Qdrant is running
docker ps

# If not running, start it:
docker run -d -p 6333:6333 --name qdrant qdrant/qdrant

# Test connection:
curl http://localhost:6333/collections
```

**❌ "Module not found" errors**
```bash
# Make sure virtual environment is activated
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

**❌ "PDF Processing Failed"**
- Ensure PDFs contain text (not just images)
- Check file size is under 50MB
- Verify PDF is not corrupted or password-protected

**❌ "Port 8000 already in use"**
```bash
# Change port in .env file:
PORT=8001

# Or kill process using port 8000:
# Windows: netstat -ano | findstr 8000
# Linux/Mac: lsof -ti:8000 | xargs kill
```

**❌ "Frontend not loading"**
- Clear browser cache (Ctrl+F5 or Cmd+Shift+R)
- Try in incognito/private browsing mode
- Check browser console for JavaScript errors

### Performance Tips

**For faster responses:**
```env
TOP_K_RETRIEVAL=5          # Reduce sources searched
MAX_CHUNK_SIZE=500         # Smaller chunks process faster
```

**For better accuracy:**
```env
TOP_K_RETRIEVAL=10         # More comprehensive search
TEMPERATURE=0.0            # More focused responses
TOP_K_FINAL=8             # More sources in final answer
```

## 📖 API Documentation

Once running, explore the interactive API:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **Health Check**: `http://localhost:8000/health`

### Key API Endpoints
```bash
POST /api/v1/chat/new              # Create new chat session
POST /api/v1/chat/{id}/ask         # Ask a question
GET  /api/v1/chat/list             # Get all chats
GET  /api/v1/chat/{id}             # Get chat details
DELETE /api/v1/chat/{id}           # Delete a chat
GET  /api/v1/pdfs/list            # List processed PDFs
```

## 📊 Project Structure

```
PDF_RAG/
├── 📁 app/                   # Main application code
│   ├── 📁 api/              # FastAPI route handlers
│   │   ├── chat_routes.py   # Chat session management
│   │   ├── pdf_routes.py    # PDF processing endpoints
│   │   └── qa_routes.py     # Question-answering API
│   ├── 📁 core/             # Core configuration
│   │   ├── config.py        # Application settings
│   │   └── logger.py        # Logging configuration
│   ├── 📁 rag/              # RAG pipeline components
│   │   ├── chunker.py       # Text chunking logic
│   │   ├── embedder.py      # Embedding generation
│   │   ├── extractor.py     # PDF text extraction
│   │   ├── rag_pipeline.py  # Main RAG orchestrator
│   │   ├── retriever.py     # Document retrieval
│   │   └── vectorstore.py   # Qdrant vector operations
│   └── 📁 schemas/          # Pydantic data models
│       ├── requests.py      # API request schemas
│       └── responses.py     # API response schemas
├── 📁 pdfs/                 # 📄 Place your PDF files here
├── 📁 logs/                 # 📝 Application logs
├── 📁 uploads/              # 📤 Temporary file uploads
├── 📁 tests/                # 🧪 Unit tests
├── 🌐 index.html           # Frontend interface
├── 🎨 style.css            # UI styling  
├── ⚡ app.js              # Frontend JavaScript
├── 🚀 main.py             # Application entry point
├── 📋 requirements.txt     # Python dependencies
├── 🐳 docker-compose.yml  # Docker configuration
├── 🔧 setup.sh           # Linux/Mac setup script
├── 🔧 setup.bat          # Windows setup script
├── ✅ verify_deployment.py # Deployment checker
└── 📖 README.md           # This documentation
```

## 🔐 Security & Privacy

- **Local Storage**: All data stays on your machine
- **API Security**: Google AI API calls are encrypted
- **No Data Collection**: No analytics or tracking
- **Privacy First**: Your documents never leave your computer
- **Open Source**: Full transparency in code

## ⚙️ Advanced Configuration

### Custom Model Settings
```env
# In .env file
GEMINI_MODEL=gemini-2.0-flash      # Latest model (recommended)
EMBEDDING_MODEL=text-embedding-004  # Best embedding model
TEMPERATURE=0.1                     # Response creativity (0.0-1.0)
MAX_TOKENS=1000                    # Maximum response length
TOP_K_RETRIEVAL=8                  # Sources to consider
TOP_K_FINAL=5                      # Sources in final answer
```

### Document Processing Tuning
```env
MAX_CHUNK_SIZE=800                 # Optimal for most documents
MIN_CHUNK_SIZE=200                # Minimum meaningful chunk
CHUNK_OVERLAP=100                 # Context preservation
MAX_FILE_SIZE_MB=50              # Upload limit
```

### Database Configuration
```env
QDRANT_URL=http://localhost:6333   # Vector database URL
QDRANT_COLLECTION_NAME=pdf_documents
DATABASE_URL=sqlite:///aiagent.db  # Chat history database
```

## 🌐 Production Deployment

### Environment Setup
```env
DEBUG=false
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
```

### Using systemd (Linux)
```ini
# /etc/systemd/system/ai-tutor.service
[Unit]
Description=AI Tutor Application
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/PDF_RAG
Environment=PATH=/path/to/PDF_RAG/venv/bin
ExecStart=/path/to/PDF_RAG/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### With nginx Reverse Proxy
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🧪 Testing & Validation

### Run Deployment Verification
```bash
python verify_deployment.py
```

### Run Unit Tests
```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest tests/

# Run with coverage report
pytest --cov=app tests/
```

### Manual Testing
```bash
# Test API endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/chat/list

# Test document processing
# 1. Place a PDF in pdfs/ folder
# 2. Watch logs for processing completion
# 3. Test questions in the web interface
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch:
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. Make your changes and test them
4. Commit with a clear message:
   ```bash
   git commit -m 'Add amazing feature that does X'
   ```
5. Push to your fork:
   ```bash
   git push origin feature/amazing-feature
   ```
6. Open a Pull Request with description of changes

## 🆘 Support & Help

### Getting Help
- **📚 Documentation**: Check `/docs` endpoint when running locally
- **🐛 Bug Reports**: Open a [GitHub Issue](https://github.com/pb1803/PDF_RAG/issues)
- **💬 Questions**: Use [GitHub Discussions](https://github.com/pb1803/PDF_RAG/discussions)
- **🔧 Troubleshooting**: See troubleshooting section above

### Frequently Asked Questions

**Q: Can I use documents in languages other than English?**
A: Yes! Gemini supports multiple languages. The system works with most major languages.

**Q: How many PDFs can I upload?**
A: No hard limit, but performance depends on your system resources. Start with 5-10 documents.

**Q: Can I use this offline?**
A: The app runs locally, but requires internet for Google AI API calls. Consider using local models for full offline use.

**Q: Is my data private?**
A: Yes! All documents stay on your machine. Only anonymized text chunks are sent to Google AI for processing.

**Q: Can I customize the AI responses?**
A: Yes! Adjust `TEMPERATURE`, `TOP_K_FINAL`, and other settings in the `.env` file.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Google AI** for Gemini and embedding models
- **Qdrant** for vector database technology  
- **FastAPI** for the web framework
- **The Open Source Community** for amazing libraries

## 🚀 What's Next?

Planned features and improvements:

- [ ] **📱 Mobile App** - React Native implementation
- [ ] **🎤 Voice Chat** - Speech-to-text integration  
- [ ] **🌍 Multi-Language** - Support for non-English documents
- [ ] **👥 Collaboration** - Multi-user chat sessions
- [ ] **📊 Analytics** - Learning progress tracking
- [ ] **🔌 Plugins** - Custom integrations and extensions
- [ ] **☁️ Cloud Deployment** - One-click cloud hosting

## 🌟 Show Your Support

If this AI Tutor helped your learning journey:

⭐ **Star the repository** on GitHub  
🍴 **Fork it** to contribute  
📢 **Share it** with fellow students  
💖 **Sponsor the project** for continued development

---

## 📞 Quick Support

**Need immediate help?**

1. **Check logs**: `tail -f logs/aiagent.log`
2. **Run verification**: `python verify_deployment.py`
3. **Test API**: Visit `http://localhost:8000/docs`
4. **Reset everything**: 
   ```bash
   docker stop qdrant && docker rm qdrant
   rm -rf qdrant-local/ aiagent.db
   docker run -d -p 6333:6333 --name qdrant qdrant/qdrant
   python main.py
   ```

**Built with ❤️ for students worldwide**

*Empowering education through AI • Making learning more accessible • Open source for everyone*