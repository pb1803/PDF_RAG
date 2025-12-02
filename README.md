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

Upload your study materials and start chatting with your AI tutor instantly!

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

- **Python 3.9+**
- **Google Cloud Project** with Generative AI API enabled
- **4GB+ RAM** recommended
- **2GB+ Storage** for document processing

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/ai-tutor.git
cd ai-tutor
```

### 2. Set Up Environment
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

### 3. Configure Environment Variables
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
```

**Required Environment Variables:**
```env
# Google AI Configuration (Choose one method)

# Method 1: Service Account (Recommended)
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
PROJECT_ID=your-google-cloud-project-id

# Method 2: API Key (Alternative)
GOOGLE_API_KEY=your-google-api-key

# Other settings
QDRANT_URL=http://localhost:6333
GEMINI_MODEL=gemini-2.0-flash
```

### 4. Set Up Google Cloud Credentials

#### Option A: Service Account (Recommended)
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable the **Generative AI API**
4. Create a Service Account:
   - IAM & Admin → Service Accounts → Create
   - Download the JSON key file
   - Save as `service-account.json` in project root
   - Update `.env`: `GOOGLE_APPLICATION_CREDENTIALS=service-account.json`

#### Option B: API Key (Simpler)
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create an API key
3. Update `.env`: `GOOGLE_API_KEY=your-api-key`

### 5. Start Qdrant Vector Database
```bash
# Using Docker (Recommended)
docker run -p 6333:6333 qdrant/qdrant

# Or using Docker Compose
docker-compose up qdrant -d
```

### 6. Launch the Application
```bash
python main.py
```

### 7. Open Your Browser
Navigate to `http://localhost:8000` and start learning!

## 📚 Usage Guide

### Uploading Documents
1. Place PDF files in the `pdfs/` folder
2. The system automatically processes them
3. Wait for "✅ RAG pipeline complete" in the logs

### Chatting with AI Tutor
1. Click "**New Chat**" to start a conversation
2. Ask questions like:
   - "Summarize the main topics in my documents"
   - "What is machine learning according to my notes?"
   - "Create study questions from chapter 3"
3. Get instant answers with source citations!

### Managing Conversations
- **Rename chats** by clicking the edit icon
- **Delete conversations** you no longer need
- **Export chat history** for study reviews

## 🐳 Docker Deployment

### Quick Docker Setup
```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build manually
docker build -t ai-tutor .
docker run -p 8000:8000 ai-tutor
```

### Environment Variables for Docker
```yaml
# docker-compose.yml
environment:
  - GOOGLE_API_KEY=your-key-here
  - QDRANT_URL=http://qdrant:6333
```

## ⚙️ Configuration

### Model Settings
```env
# Performance tuning
GEMINI_MODEL=gemini-2.0-flash      # or gemini-1.5-pro
EMBEDDING_MODEL=text-embedding-004
TEMPERATURE=0.1                    # Lower = more focused
MAX_TOKENS=1000                   # Response length
TOP_K_FINAL=5                     # Number of sources per answer
```

### Document Processing
```env
MAX_CHUNK_SIZE=800                # Text chunk size
MIN_CHUNK_SIZE=200               # Minimum chunk size
CHUNK_OVERLAP=100                # Overlap between chunks
MAX_FILE_SIZE_MB=50             # Maximum PDF size
```

## 🔧 Troubleshooting

### Common Issues

**"Google API Error"**
```bash
# Check your API key/credentials
python -c "import google.generativeai as genai; genai.configure(api_key='your-key'); print('✅ API key valid')"
```

**"Qdrant Connection Failed"**
```bash
# Make sure Qdrant is running
curl http://localhost:6333/collections
```

**"PDF Processing Failed"**
- Ensure PDFs are text-based (not scanned images)
- Check file size limits in settings
- Verify PDF files are not corrupted

**"Frontend Not Loading"**
- Clear browser cache (Ctrl+F5)
- Check browser console for errors
- Ensure all static files are served correctly

### Performance Optimization

**For better response times:**
```env
TOP_K_RETRIEVAL=5          # Reduce for faster search
MAX_CHUNK_SIZE=500         # Smaller chunks = faster processing
```

**For better accuracy:**
```env
TOP_K_RETRIEVAL=10         # More sources considered
TEMPERATURE=0.0            # More deterministic responses
```

## 📖 API Documentation

Once running, visit:
- **Interactive API Docs**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`
- **Health Check**: `http://localhost:8000/health`

### Key Endpoints
```bash
POST /api/v1/chat/new              # Create new chat session
POST /api/v1/chat/{id}/ask         # Ask a question
GET  /api/v1/chat/list             # Get all chats
GET  /api/v1/chat/{id}             # Get chat details
DELETE /api/v1/chat/{id}           # Delete a chat
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Test specific module
pytest tests/test_rag_pipeline.py
```

## 📊 Project Structure

```
ai-tutor/
├── app/                   # Main application
│   ├── api/              # FastAPI routes
│   ├── core/             # Configuration & database
│   ├── models/           # Data models
│   ├── rag/              # RAG pipeline components
│   └── schemas/          # Request/response schemas
├── tests/                # Unit tests
├── pdfs/                 # PDF documents (auto-processed)
├── logs/                 # Application logs
├── static files/         # Frontend (HTML/CSS/JS)
├── main.py              # Application entry point
├── requirements.txt     # Dependencies
└── docker-compose.yml   # Docker setup
```

## 🔒 Security Notes

- **API Keys**: Never commit `.env` or `service-account.json`
- **CORS**: Configure properly for production deployment
- **Rate Limiting**: Implement for public deployments
- **Input Validation**: All user inputs are sanitized

## 🌐 Production Deployment

### Environment Setup
```env
DEBUG=false
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
```

### Reverse Proxy (nginx)
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Process Management (systemd)
```ini
# /etc/systemd/system/ai-tutor.service
[Unit]
Description=AI Tutor Application
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/ai-tutor
Environment=PATH=/path/to/ai-tutor/venv/bin
ExecStart=/path/to/ai-tutor/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋‍♂️ Support

- **Documentation**: Check the `/docs` endpoint when running
- **Issues**: Open a GitHub issue for bugs
- **Discussions**: Use GitHub Discussions for questions

## 🚀 What's Next?

- [ ] **Mobile App** - React Native implementation
- [ ] **Voice Chat** - Speech-to-text integration
- [ ] **Multi-Language** - Support for non-English documents
- [ ] **Collaborative Learning** - Multi-user chat sessions
- [ ] **Advanced Analytics** - Learning progress tracking

## 🌟 Show Your Support

If this project helped you, please ⭐ star it on GitHub!

---

**Built with ❤️ for students worldwide**

*Made possible by Google Generative AI, FastAPI, and the open-source community*