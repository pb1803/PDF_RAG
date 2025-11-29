# 🚀 Enhanced RAG Pipeline - Academic Agent

A state-of-the-art **Retrieval-Augmented Generation (RAG)** system designed for academic content, featuring GPT-quality responses, automatic table generation, and intelligent knowledge fallback.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![Gemini](https://img.shields.io/badge/Gemini-2.0--flash-orange.svg)](https://ai.google.dev)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🎯 **Key Features**

### 🧠 **Enhanced AI Capabilities**
- **GPT-Quality Formatting**: Structured responses with Definition, Explanation, Examples, and Sources
- **Smart Table Generation**: Automatically creates comparison tables for relevant questions
- **External Knowledge Fallback**: Uses Gemini AI when PDF content is insufficient
- **Blended Responses**: Seamlessly combines PDF content with external knowledge
- **Smart Confidence Scoring**: Provides transparency about answer quality

### 📚 **Academic-Focused**
- **PDF Processing**: Automatic extraction and chunking of academic documents
- **Citation Management**: Accurate page number references and source attribution
- **Student-Friendly**: Converts complex academic text into readable explanations
- **Multi-Document Support**: Handle multiple textbooks and papers simultaneously

### 🔧 **Technical Excellence**
- **Vector Search**: Qdrant-powered semantic search with reranking
- **Chat Memory**: Persistent conversation history with context awareness
- **API-First Design**: RESTful APIs with comprehensive documentation
- **Backward Compatible**: Maintains compatibility with existing integrations

---

## 🚀 **Quick Start**

### **Prerequisites**
- Python 3.8 or higher
- Google API Key (for Gemini AI)
- 4GB+ RAM recommended
- Windows/macOS/Linux

### **🎯 Automated Setup (Recommended)**
```bash
# Clone the repository
git clone https://github.com/pb1803/Academic_agent.git
cd Academic_agent

# Run automated setup
python setup.py

# Follow the prompts to configure your environment
```

### **📋 Manual Setup**

### **1. Clone the Repository**
```bash
git clone https://github.com/pb1803/Academic_agent.git
cd Academic_agent
```

### **2. Set Up Environment**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### **3. Configure Environment Variables**
```bash
# Copy example environment file
cp .env.example .env

# Edit .env file with your settings
# Required: GOOGLE_API_KEY
```

**Example .env configuration:**
```env
# Google AI Configuration (Required)
GOOGLE_API_KEY=your_google_api_key_here

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=True

# Database Configuration
DATABASE_URL=sqlite:///./aiagent.db

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
```

### **4. Add Your Documents**
```bash
# Place PDF files in the pdfs directory
cp your_textbook.pdf pdfs/
cp your_research_paper.pdf pdfs/
```

### **5. Start the Server**
```bash
python main.py
```

The server will start on `http://localhost:8000`

### **6. Test the System**
```bash
# Run quick tests
python quick_test_enhanced.py

# Test API endpoints
python test_api_enhanced.py

# Open web demo
# Open enhanced_rag_demo.html in your browser
```

---

## 📖 **Detailed Setup Guide**

### **Getting Google API Key**

1. **Go to Google AI Studio**: https://aistudio.google.com/
2. **Create API Key**: Click "Get API Key" → "Create API Key"
3. **Copy the Key**: Save it securely
4. **Add to .env**: `GOOGLE_API_KEY=your_key_here`

### **Project Structure**
```
Academic_agent/
├── app/                          # Main application code
│   ├── api/                      # FastAPI routes
│   │   ├── chat_routes.py        # Chat session endpoints
│   │   ├── pdf_routes.py         # PDF upload/management
│   │   └── qa_routes.py          # Q&A endpoints
│   ├── core/                     # Core configuration
│   │   ├── config.py             # Settings management
│   │   ├── db.py                 # Database setup
│   │   └── logger.py             # Logging configuration
│   ├── models/                   # Data models
│   │   └── chat_models.py        # Chat/message models
│   ├── rag/                      # RAG pipeline
│   │   ├── embedder.py           # Text embedding
│   │   ├── rag_pipeline.py       # Main RAG logic
│   │   ├── retriever.py          # Document retrieval
│   │   └── vectorstore.py        # Vector database
│   └── schemas/                  # API schemas
│       ├── requests.py           # Request models
│       └── responses.py          # Response models
├── pdfs/                         # PDF documents (add your files here)
├── logs/                         # Application logs
├── uploads/                      # Temporary file uploads
├── qdrant-local/                 # Local vector database
├── tests/                        # Test files
├── enhanced_rag_demo.html        # Web demo interface
├── main.py                       # Application entry point
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

### **Adding Documents**

1. **Supported Formats**: PDF files
2. **Placement**: Copy files to `pdfs/` directory
3. **Processing**: Files are automatically processed on server start
4. **Verification**: Check logs for successful indexing

**Example:**
```bash
# Add your textbooks
cp "Database Management Systems.pdf" pdfs/
cp "Computer Networks.pdf" pdfs/

# Restart server to process new files
python main.py
```

---

## 🔧 **API Usage**

### **Basic Question Answering**
```bash
curl -X POST "http://localhost:8000/api/v1/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "any",
    "question": "What is a database?",
    "top_k": 5,
    "temperature": 0.1
  }'
```

**Enhanced Response Format:**
```json
{
  "answer": "## Definition\nA database is a structured collection...\n## Sources\n📄 Page 12, 15",
  "follow_up": "Would you like to see examples of database types?",
  "sources": ["Page 12", "Page 15"],
  "answer_type": "pdf_only",
  "confidence": 0.87,
  "used_chunks": [...]
}
```

### **Chat Sessions**
```bash
# Create new chat session
curl -X POST "http://localhost:8000/api/v1/chat/new"

# Ask question in session
curl -X POST "http://localhost:8000/api/v1/chat/{session_id}/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "any",
    "question": "Explain normalization with examples"
  }'
```

### **Table Generation Example**
```bash
# Questions with comparison keywords automatically generate tables
curl -X POST "http://localhost:8000/api/v1/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "any",
    "question": "What is the difference between SQL and NoSQL databases?"
  }'
```

**Response includes auto-generated table:**
```markdown
## Table
| Feature | SQL | NoSQL |
|---------|-----|-------|
| Schema | Fixed | Flexible |
| ACID | Full support | Eventual consistency |
| Scalability | Vertical | Horizontal |
```

---

## 🧪 **Testing**

### **Quick Status Check**
```bash
# Check project status and health
python project_status.py
```

### **Run All Tests**
```bash
# Using Makefile (recommended)
make test           # Run all tests
make test-cov       # Run with coverage
make test-quick     # Quick unit tests
make test-api       # API endpoint tests

# Or run individual test scripts
python quick_test_enhanced.py      # Unit tests
python test_enhanced_rag.py        # Integration tests  
python test_api_enhanced.py        # API tests
python comprehensive_demo.py       # Full demo
```

### **Performance Benchmarking**
```bash
# Run performance benchmarks
python benchmark_rag.py

# Or using Makefile
make benchmark
```

### **Test Different Question Types**

1. **Simple Definition**: "What is a database?"
2. **Comparison Table**: "What is the difference between SQL and NoSQL?"
3. **External Knowledge**: "What is quantum computing?"
4. **Pros/Cons**: "What are the advantages and disadvantages of normalization?"

---

## 🌐 **Web Interface**

Open `enhanced_rag_demo.html` in your browser for an interactive demo featuring:

- **Real-time Testing**: Ask questions and see enhanced responses
- **Feature Showcase**: Demonstrates all enhanced capabilities
- **Response Analysis**: Shows answer type, confidence, and sources
- **Example Questions**: Pre-built examples for different features

---

## 📊 **Enhanced Features Deep Dive**

### **1. Answer Types**
- **`pdf_only`**: High-quality PDF content available
- **`mixed`**: Combines PDF + external knowledge
- **`external_only`**: Falls back to Gemini general knowledge

### **2. Smart Table Generation**
Automatically detects questions containing:
- "difference", "compare", "vs", "versus"
- "advantages", "disadvantages", "pros", "cons"
- "similarities", "contrast"

### **3. Confidence Scoring**
- **0.8-1.0**: High confidence (strong PDF support)
- **0.5-0.8**: Medium confidence (partial PDF support)
- **0.0-0.5**: Low confidence (external knowledge used)

### **4. Source Attribution**
- **📘 From your textbook (Page X)**: PDF content
- **🌐 From external sources**: Gemini knowledge
- **⚠️ Note**: Clear indicators when external knowledge is used

---

## 🔧 **Configuration**

### **Environment Variables**

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GOOGLE_API_KEY` | Google AI API key | - | ✅ |
| `HOST` | Server host | 0.0.0.0 | ❌ |
| `PORT` | Server port | 8000 | ❌ |
| `DEBUG` | Debug mode | True | ❌ |
| `GEMINI_MODEL` | Gemini model | gemini-2.0-flash | ❌ |
| `EMBEDDING_MODEL` | Embedding model | text-embedding-004 | ❌ |
| `TEMPERATURE` | Generation temperature | 0.1 | ❌ |
| `TOP_K_RETRIEVAL` | Chunks to retrieve | 8 | ❌ |
| `TOP_K_FINAL` | Final chunks to use | 5 | ❌ |

### **Advanced Configuration**

Edit `app/core/config.py` for advanced settings:
- Chunk size and overlap
- Similarity thresholds
- Model parameters
- Database settings

---

## 🚀 **Deployment**

### **Docker Deployment**
```bash
# Build image
docker build -t academic-agent .

# Run container
docker run -p 8000:8000 -e GOOGLE_API_KEY=your_key academic-agent
```

### **Production Deployment**
```bash
# Install production server
pip install gunicorn

# Run with gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

---

## 🔍 **Troubleshooting**

### **Common Issues**

**1. "No module named 'sqlmodel'"**
```bash
pip install sqlmodel
```

**2. "GOOGLE_API_KEY is required"**
- Ensure `.env` file exists with valid API key
- Check API key has proper permissions

**3. "No documents found"**
- Add PDF files to `pdfs/` directory
- Restart server to process new files
- Check logs for processing errors

**4. "Connection refused"**
- Ensure server is running on correct port
- Check firewall settings
- Verify host/port configuration

### **Debug Mode**
```bash
# Enable detailed logging
export DEBUG=True
python main.py
```

### **Check System Health**
```bash
curl http://localhost:8000/health
```

---

## 📚 **API Documentation**

### **Interactive Documentation**
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### **Key Endpoints**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | System health check |
| `/api/v1/ask` | POST | Ask questions about documents |
| `/api/v1/chat/new` | POST | Create new chat session |
| `/api/v1/chat/{id}/ask` | POST | Ask in chat session |
| `/api/v1/documents` | GET | List available documents |

---

## 🛠️ **Development Tools**

### **Using Makefile (Recommended)**
```bash
# Setup and installation
make setup          # Run automated setup
make install        # Install production dependencies
make install-dev    # Install development dependencies

# Development workflow
make run            # Start development server
make test           # Run all tests
make lint           # Run linting checks
make format         # Format code
make clean          # Clean temporary files

# Docker operations
make docker-build   # Build Docker image
make docker-run     # Run with Docker Compose
make docker-stop    # Stop containers

# Documentation and demos
make demo           # Run comprehensive demo
make demo-web       # Open web demo
make docs           # Generate documentation
```

### **Project Status Monitoring**
```bash
# Check overall project health
python project_status.py

# Performance benchmarking
python benchmark_rag.py
```

## 🤝 **Contributing**

### **Development Setup**
```bash
# Clone repository
git clone https://github.com/pb1803/Academic_agent.git
cd Academic_agent

# Install development dependencies
make install-dev

# Run tests
make test

# Format and lint code
make format lint
```

### **Contribution Guidelines**
See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines including:
- Code style and standards
- Testing requirements
- Pull request process
- Development workflow

**Quick contribution steps:**
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Make changes and test (`make test lint`)
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open Pull Request

---

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 **Acknowledgments**

- **Google AI**: For Gemini 2.0 Flash and text-embedding-004 models
- **Qdrant**: For high-performance vector search
- **FastAPI**: For the excellent web framework
- **Academic Community**: For inspiration and feedback

---

## 📞 **Support**

### **Getting Help**
- **Issues**: [GitHub Issues](https://github.com/pb1803/Academic_agent/issues)
- **Discussions**: [GitHub Discussions](https://github.com/pb1803/Academic_agent/discussions)
- **Documentation**: Check this README and API docs

### **Reporting Bugs**
Please include:
1. System information (OS, Python version)
2. Error messages and logs
3. Steps to reproduce
4. Expected vs actual behavior

---

## 🔮 **Roadmap**

### **Upcoming Features**
- [ ] Multi-language support
- [ ] Advanced document formats (Word, PowerPoint)
- [ ] Real-time collaboration
- [ ] Custom model fine-tuning
- [ ] Advanced analytics dashboard

### **Performance Improvements**
- [ ] Caching layer for faster responses
- [ ] Batch processing for multiple documents
- [ ] Optimized embedding storage
- [ ] Response streaming

---

**🚀 Ready to revolutionize your academic research with AI? Get started now!**

```bash
git clone https://github.com/pb1803/Academic_agent.git
cd Academic_agent
pip install -r requirements.txt
python main.py
```

**Visit http://localhost:8000 and experience the future of academic AI assistance!**