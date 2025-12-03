# 🤖 AI Tutor - Smart Study Assistant

A production-ready AI-powered study assistant that helps students learn from their PDF documents using advanced RAG (Retrieval-Augmented Generation) technology.

![CI/CD Pipeline](https://github.com/pb1803/PDF_RAG/actions/workflows/ci.yml/badge.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green)
![Python](https://img.shields.io/badge/Python-3.9+-blue)
![Gemini](https://img.shields.io/badge/Gemini-2.0--Flash-orange)

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [API Reference](#-api-reference)
- [Chat Memory Design](#-chat-memory-design)
- [RAG Pipeline](#-rag-pipeline)
- [Environment Setup](#-environment-setup)
- [Flutter Integration](#-flutter-integration)
- [Deployment Guide](#-deployment-guide)
- [Troubleshooting](#-troubleshooting)

## ✨ Features

- **🎯 Smart Q&A**: Ask questions about your uploaded PDFs and get instant, accurate answers
- **🧠 Memory & Context**: Maintains conversation history for deeper learning discussions
- **📚 Multi-Document Search**: Search across all your documents simultaneously
- **🎨 Modern UI**: ChatGPT-like dark theme interface with real-time chat
- **📄 Source Citations**: Every answer includes page references from your study materials
- **🔄 Real-time Processing**: Auto-processes PDFs as you upload them
- **💾 Persistent Storage**: All conversations and documents are saved locally
- **🔍 Confidence Scoring**: AI responses include accuracy confidence levels
- **📱 Mobile Ready**: Responsive design works on all devices

## 🏗️ Architecture

```mermaid
graph TB
    A[Frontend - HTML/CSS/JS] --> B[FastAPI Backend]
    B --> C[Chat Router]
    B --> D[PDF Router] 
    B --> E[QA Router]
    
    C --> F[SQLite Database]
    F --> G[Chat Sessions]
    F --> H[Messages]
    
    D --> I[PDF Processor]
    I --> J[Text Extractor]
    I --> K[Semantic Chunker]
    
    E --> L[RAG Pipeline]
    L --> M[Embedder - text-embedding-004]
    L --> N[Vector Store - Qdrant]
    L --> O[Retriever]
    L --> P[Generator - Gemini 2.0 Flash]
    
    N --> Q[(Vector Database)]
    Q --> R[Document Chunks]
    Q --> S[Embeddings]
```

### Core Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Frontend** | Vanilla JS, HTML5, CSS3 | Modern chat interface |
| **API Layer** | FastAPI, Pydantic | RESTful API with validation |
| **RAG Pipeline** | Custom Python | Document processing & Q&A |
| **Embeddings** | Google text-embedding-004 | Semantic text representation |
| **Vector DB** | Qdrant | Efficient similarity search |
| **LLM** | Google Gemini 2.0 Flash | Answer generation |
| **Chat Storage** | SQLite | Conversation persistence |
| **File Processing** | PyMuPDF | PDF text extraction |

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

**Windows:**
```bash
git clone https://github.com/pb1803/PDF_RAG.git
cd PDF_RAG
setup.bat
```

**Linux/macOS:**
```bash
git clone https://github.com/pb1803/PDF_RAG.git
cd PDF_RAG
chmod +x setup.sh
./setup.sh
```

### Option 2: Manual Setup

1. **Clone Repository**
   ```bash
   git clone https://github.com/pb1803/PDF_RAG.git
   cd PDF_RAG
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   # Windows: venv\\Scripts\\activate
   # Linux/Mac: source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Get Google AI API Key**
   - Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Click "Create API Key"
   - Copy the generated key

5. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env and add: GOOGLE_API_KEY=your_actual_api_key_here
   ```

6. **Start Qdrant Database**
   ```bash
   docker run -d -p 6333:6333 --name qdrant qdrant/qdrant
   ```

7. **Launch Application**
   ```bash
   python main.py
   ```

8. **Open Browser**
   Navigate to `http://localhost:8000`

## 📖 API Reference

### Base URL
```
http://localhost:8000
```

### Authentication
No authentication required for local deployment. API key is configured server-side.

### Endpoints

#### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-03T10:00:00Z",
  "version": "1.0.0",
  "services": {
    "database": "connected",
    "vector_store": "connected",
    "embedder": "ready",
    "generator": "ready"
  }
}
```

#### Chat Management

**Create New Chat Session**
```http
POST /api/v1/chat/new
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "New Chat",
  "created_at": "2025-12-03T10:00:00Z"
}
```

**List All Chats**
```http
GET /api/v1/chat/list
```

**Response:**
```json
{
  "chats": [
    {
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Machine Learning Discussion",
      "created_at": "2025-12-03T10:00:00Z",
      "updated_at": "2025-12-03T11:30:00Z",
      "message_count": 15
    }
  ]
}
```

**Get Chat Details**
```http
GET /api/v1/chat/{session_id}
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Machine Learning Discussion", 
  "messages": [
    {
      "role": "user",
      "content": "What is machine learning?",
      "timestamp": "2025-12-03T10:00:00Z"
    },
    {
      "role": "assistant",
      "content": "Machine learning is...",
      "timestamp": "2025-12-03T10:00:30Z",
      "sources": ["document1.pdf:page_5", "document2.pdf:page_12"],
      "confidence": 0.85
    }
  ]
}
```

**Ask Question**
```http
POST /api/v1/chat/{session_id}/ask
```

**Request Body:**
```json
{
  "question": "What is the main topic of this document?",
  "doc_id": "any",
  "top_k": 5
}
```

**Response:**
```json
{
  "answer": "The main topic of this document is artificial intelligence and its applications in modern technology...",
  "sources": [
    {
      "document": "ai_overview.pdf",
      "page": 1,
      "content": "Artificial intelligence (AI) refers to...",
      "score": 0.92
    }
  ],
  "confidence": 0.87,
  "processing_time": 2.3,
  "timestamp": "2025-12-03T10:00:30Z"
}
```

**Delete Chat**
```http
DELETE /api/v1/chat/{session_id}
```

#### PDF Management

**List Processed PDFs**
```http
GET /api/v1/pdfs/list
```

**Response:**
```json
{
  "pdfs": [
    {
      "doc_id": "550e8400-e29b-41d4-a716-446655440001",
      "filename": "machine_learning_basics.pdf",
      "upload_time": "2025-12-03T09:00:00Z",
      "pages": 25,
      "chunks": 67,
      "status": "processed"
    }
  ]
}
```

#### Question Answering

**Direct Q&A (without chat context)**
```http
POST /api/v1/qa/ask
```

**Request Body:**
```json
{
  "question": "Explain neural networks",
  "doc_id": "any",
  "top_k": 5
}
```

## 🧠 Chat Memory Design

### Architecture Overview

The chat system maintains conversation context using a hybrid approach:

1. **Session Storage**: Each chat session has a unique UUID
2. **Message History**: Complete conversation history stored in SQLite
3. **Context Windows**: Last N messages sent to LLM for context
4. **Document Memory**: Vector embeddings persist across sessions

### Database Schema

```sql
-- Chat Sessions Table
CREATE TABLE chats (
    id TEXT PRIMARY KEY,           -- UUID session ID
    title TEXT NOT NULL,           -- User-defined or auto-generated title
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Messages Table  
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id TEXT NOT NULL,         -- Foreign key to chats.id
    role TEXT NOT NULL,            -- 'user' or 'assistant'  
    content TEXT NOT NULL,         -- Message content
    sources TEXT,                  -- JSON array of sources (for assistant)
    confidence REAL,               -- AI confidence score (for assistant)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chat_id) REFERENCES chats (id)
);
```

### Context Management

```python
# Context window configuration
CONTEXT_WINDOW_SIZE = 10  # Last 10 messages
MAX_CONTEXT_TOKENS = 4000  # Token limit for context

def get_conversation_context(session_id: str) -> List[Message]:
    \"\"\"Retrieve recent conversation history for context\"\"\"
    messages = get_recent_messages(session_id, CONTEXT_WINDOW_SIZE)
    
    # Truncate if token limit exceeded
    context_tokens = sum(estimate_tokens(msg.content) for msg in messages)
    if context_tokens > MAX_CONTEXT_TOKENS:
        messages = truncate_to_token_limit(messages, MAX_CONTEXT_TOKENS)
    
    return messages
```

## 🔍 RAG Pipeline

### Pipeline Overview

```mermaid
graph LR
    A[User Question] --> B[Query Processing]
    B --> C[Embedding Generation] 
    C --> D[Vector Similarity Search]
    D --> E[Document Retrieval]
    E --> F[Context Ranking]
    F --> G[Prompt Construction]
    G --> H[LLM Generation]
    H --> I[Response Post-processing]
    I --> J[Answer + Sources]
```

### Step-by-Step Process

1. **Document Ingestion**
   ```python
   def process_pdf(pdf_path: str) -> str:
       # Extract text from PDF
       text = extract_text_from_pdf(pdf_path)
       
       # Semantic chunking  
       chunks = create_semantic_chunks(text, chunk_size=800, overlap=100)
       
       # Generate embeddings
       embeddings = embed_text_chunks(chunks)
       
       # Store in vector database
       store_embeddings(chunks, embeddings, doc_id)
       
       return doc_id
   ```

2. **Query Processing**
   ```python
   def process_query(question: str, doc_id: str) -> Dict:
       # Generate question embedding
       query_embedding = embedder.embed_texts([question])[0]
       
       # Retrieve similar chunks  
       similar_chunks = vector_store.search_similar_chunks(
           query_embedding=query_embedding,
           doc_id=doc_id,
           top_k=8
       )
       
       # Re-rank by relevance
       ranked_chunks = rerank_chunks(similar_chunks, question)
       
       return ranked_chunks[:5]  # Top 5 chunks
   ```

3. **Answer Generation**
   ```python
   def generate_answer(question: str, context_chunks: List, history: List) -> Dict:
       # Construct prompt with context
       prompt = build_rag_prompt(
           question=question,
           context_chunks=context_chunks,
           conversation_history=history
       )
       
       # Generate response
       response = gemini_client.generate_content(prompt)
       
       # Calculate confidence
       confidence = calculate_confidence(response, context_chunks)
       
       return {
           "answer": response.text,
           "confidence": confidence,
           "sources": extract_sources(context_chunks)
       }
   ```

### RAG Configuration

```env
# RAG Pipeline Settings
MAX_CHUNK_SIZE=800                # Optimal chunk size for embeddings
MIN_CHUNK_SIZE=200               # Minimum meaningful chunk
CHUNK_OVERLAP=100                # Context preservation between chunks
TOP_K_RETRIEVAL=8                # Initial retrieval candidates  
TOP_K_FINAL=5                    # Final chunks for generation
RERANK_THRESHOLD=0.7             # Minimum similarity score
CONFIDENCE_THRESHOLD=0.6         # Minimum confidence for answers

# Model Settings
GEMINI_MODEL=gemini-2.0-flash    # Latest Gemini model
EMBEDDING_MODEL=text-embedding-004
TEMPERATURE=0.1                  # Response creativity (0.0-1.0)
MAX_TOKENS=1000                 # Maximum response length
```

## ⚙️ Environment Setup

### Development Environment

```env
# API Configuration
DEBUG=true
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=DEBUG

# Google AI Configuration  
GOOGLE_API_KEY=your_google_ai_api_key_here

# Qdrant Configuration
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION_NAME=pdf_documents

# Model Configuration
GEMINI_MODEL=gemini-2.0-flash
EMBEDDING_MODEL=text-embedding-004
TEMPERATURE=0.1
MAX_TOKENS=1000

# RAG Configuration  
MAX_CHUNK_SIZE=800
MIN_CHUNK_SIZE=200
CHUNK_OVERLAP=100
TOP_K_RETRIEVAL=8
TOP_K_FINAL=5

# File Upload Configuration
MAX_FILE_SIZE_MB=50
UPLOAD_DIR=uploads

# Database Configuration  
DATABASE_URL=sqlite:///aiagent.db
```

### Production Environment

```env
# Production Settings
DEBUG=false
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO

# Security
SECRET_KEY=your-secure-secret-key-change-in-production
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Database (Production)
DATABASE_URL=postgresql://user:password@localhost/aiagent

# Monitoring
SENTRY_DSN=your_sentry_dsn_here
```

## 📱 Flutter Integration

### Setup Flutter Client

1. **Add Dependencies**
   ```yaml
   # pubspec.yaml
   dependencies:
     flutter:
       sdk: flutter
     http: ^1.1.0
     web_socket_channel: ^2.4.0
     provider: ^6.1.1
     cached_network_image: ^3.3.0
   ```

2. **API Service Class**
   ```dart
   class AITutorService {
     static const String baseUrl = 'http://localhost:8000';
     
     static Future<Map<String, dynamic>> createChat() async {
       final response = await http.post(
         Uri.parse('$baseUrl/api/v1/chat/new'),
         headers: {'Content-Type': 'application/json'},
       );
       return json.decode(response.body);
     }
     
     static Future<Map<String, dynamic>> askQuestion({
       required String sessionId,
       required String question,
       String docId = 'any',
     }) async {
       final response = await http.post(
         Uri.parse('$baseUrl/api/v1/chat/$sessionId/ask'),
         headers: {'Content-Type': 'application/json'},
         body: json.encode({
           'question': question,
           'doc_id': docId,
         }),
       );
       return json.decode(response.body);
     }
     
     static Future<List<dynamic>> getChatList() async {
       final response = await http.get(
         Uri.parse('$baseUrl/api/v1/chat/list'),
       );
       final data = json.decode(response.body);
       return data['chats'] ?? [];
     }
   }
   ```

3. **Chat UI Widget**
   ```dart
   class ChatScreen extends StatefulWidget {
     final String sessionId;
     
     const ChatScreen({Key? key, required this.sessionId}) : super(key: key);
     
     @override
     _ChatScreenState createState() => _ChatScreenState();
   }
   
   class _ChatScreenState extends State<ChatScreen> {
     final TextEditingController _controller = TextEditingController();
     final List<Message> _messages = [];
     bool _isLoading = false;
     
     Future<void> _sendMessage(String text) async {
       setState(() {
         _messages.add(Message(role: 'user', content: text));
         _isLoading = true;
       });
       
       try {
         final response = await AITutorService.askQuestion(
           sessionId: widget.sessionId,
           question: text,
         );
         
         setState(() {
           _messages.add(Message(
             role: 'assistant',
             content: response['answer'],
             confidence: response['confidence'],
             sources: response['sources'],
           ));
         });
       } catch (e) {
         // Handle error
         setState(() {
           _messages.add(Message(
             role: 'assistant', 
             content: 'Sorry, I encountered an error: $e',
           ));
         });
       } finally {
         setState(() {
           _isLoading = false;
         });
       }
     }
     
     @override
     Widget build(BuildContext context) {
       return Scaffold(
         appBar: AppBar(title: Text('AI Tutor')),
         body: Column(
           children: [
             Expanded(
               child: ListView.builder(
                 itemCount: _messages.length,
                 itemBuilder: (context, index) => MessageBubble(
                   message: _messages[index],
                 ),
               ),
             ),
             if (_isLoading) CircularProgressIndicator(),
             MessageInput(
               controller: _controller,
               onSend: _sendMessage,
             ),
           ],
         ),
       );
     }
   }
   ```

### Mobile-Specific Features

1. **File Upload from Device**
   ```dart
   import 'package:file_picker/file_picker.dart';
   
   Future<void> uploadPDF() async {
     FilePickerResult? result = await FilePicker.platform.pickFiles(
       type: FileType.custom,
       allowedExtensions: ['pdf'],
     );
     
     if (result != null) {
       File file = File(result.files.single.path!);
       // Upload file to server
       await uploadFileToServer(file);
     }
   }
   ```

2. **Offline Chat History**
   ```dart
   import 'package:sqflite/sqflite.dart';
   
   class LocalDatabase {
     static Future<Database> _database() async {
       return openDatabase(
         'aiagent.db',
         version: 1,
         onCreate: (db, version) {
           return db.execute('''
             CREATE TABLE messages(
               id INTEGER PRIMARY KEY,
               session_id TEXT,
               role TEXT,
               content TEXT,
               timestamp TEXT
             )
           ''');
         },
       );
     }
     
     static Future<void> saveMessage(Message message) async {
       final db = await _database();
       await db.insert('messages', message.toMap());
     }
   }
   ```

## 🚀 Deployment Guide

### Local Development

```bash
# Start development server
python main.py

# Or with uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Docker Deployment

```yaml
# docker-compose.yml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - QDRANT_URL=http://qdrant:6333
    depends_on:
      - qdrant
    volumes:
      - ./pdfs:/app/pdfs
      - ./logs:/app/logs

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - ./qdrant_data:/qdrant/storage
```

**Deploy with Docker:**
```bash
# Set environment variables
export GOOGLE_API_KEY=your_api_key_here

# Build and run
docker-compose up -d

# Check logs
docker-compose logs -f app
```

### Cloud Deployment (AWS/GCP/Azure)

1. **Containerize Application**
   ```dockerfile
   FROM python:3.11-slim
   
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   
   COPY . .
   
   EXPOSE 8000
   CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

2. **Environment Configuration**
   ```bash
   # Production environment variables
   GOOGLE_API_KEY=your_production_api_key
   DATABASE_URL=postgresql://user:pass@host:5432/dbname
   QDRANT_URL=https://your-qdrant-cluster-url
   SECRET_KEY=your-secret-key
   ALLOWED_ORIGINS=https://yourdomain.com
   ```

3. **Health Checks**
   ```bash
   # Kubernetes health check
   livenessProbe:
     httpGet:
       path: /health
       port: 8000
     initialDelaySeconds: 30
     periodSeconds: 10
   ```

### Production Checklist

- [ ] **Security**: API keys in environment variables
- [ ] **Database**: Production database (PostgreSQL)
- [ ] **Monitoring**: Logging and error tracking
- [ ] **Backup**: Regular database and vector store backups
- [ ] **SSL/TLS**: HTTPS encryption
- [ ] **Rate Limiting**: Prevent API abuse
- [ ] **CORS**: Proper origin configuration
- [ ] **Health Checks**: Monitoring endpoints
- [ ] **Scaling**: Load balancing and auto-scaling

## 🔧 Troubleshooting

### Common Issues

**API Connection Errors**
```bash
# Check if API key is set
echo $GOOGLE_API_KEY

# Test API connectivity
curl -H "Authorization: Bearer $GOOGLE_API_KEY" \
  https://generativelanguage.googleapis.com/v1/models

# Verify .env file
cat .env | grep GOOGLE_API_KEY
```

**Qdrant Connection Issues**
```bash
# Check if Qdrant is running
docker ps | grep qdrant

# Test Qdrant connectivity
curl http://localhost:6333/collections

# Restart Qdrant
docker restart qdrant
```

**PDF Processing Failures**
- Ensure PDFs contain text (not just images)
- Check file size limits (default: 50MB)
- Verify PDF is not password-protected
- Check available disk space

**Memory Issues**
```bash
# Monitor memory usage
docker stats

# Increase Docker memory limits
# Or reduce chunk sizes in .env:
MAX_CHUNK_SIZE=500
TOP_K_RETRIEVAL=5
```

### Performance Optimization

**For Better Response Times:**
```env
TOP_K_RETRIEVAL=5          # Fewer documents to search
MAX_CHUNK_SIZE=500         # Smaller chunks process faster
TEMPERATURE=0.0            # More deterministic responses
```

**For Better Accuracy:**
```env
TOP_K_RETRIEVAL=10         # More comprehensive search
TOP_K_FINAL=8             # More context for generation
CHUNK_OVERLAP=200         # Better context preservation
```

### Debugging Tools

**Enable Debug Logging**
```env
LOG_LEVEL=DEBUG
DEBUG=true
```

**API Testing**
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test chat creation
curl -X POST http://localhost:8000/api/v1/chat/new

# Test question asking
curl -X POST http://localhost:8000/api/v1/chat/SESSION_ID/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello", "doc_id": "any"}'
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Make changes and test thoroughly
4. Run tests: `pytest tests/`
5. Update documentation if needed
6. Commit: `git commit -m 'Add amazing feature'`
7. Push: `git push origin feature/amazing-feature`
8. Open Pull Request with detailed description

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v --cov=app

# Run linting
flake8 app/
black app/

# Type checking
mypy app/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Google AI** for Gemini and embedding models
- **Qdrant** for vector database technology
- **FastAPI** for the excellent web framework
- **The Open Source Community** for invaluable libraries and tools

## 📞 Support

- **📚 Documentation**: Check `/docs` when running locally
- **🐛 Bug Reports**: [GitHub Issues](https://github.com/pb1803/PDF_RAG/issues)
- **💬 Discussions**: [GitHub Discussions](https://github.com/pb1803/PDF_RAG/discussions)
- **📧 Email**: Support available for enterprise users

---

**Built with ❤️ for students and educators worldwide**

*Empowering education through AI • Making learning more accessible • Open source for everyone*