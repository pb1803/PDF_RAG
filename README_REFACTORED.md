# PDF RAG System - Production Ready

## Overview
A production-ready FastAPI RAG (Retrieval Augmented Generation) system that processes PDF documents and answers questions using Google Generative AI models.

## Architecture

### AI Models Used
- **Text Generation**: `gemini-1.5-flash` (Google Generative AI)
- **Embeddings**: `text-embedding-004` (Google Generative AI)
- **Vector Database**: Qdrant (local server)

### RAG Pipeline
```
PDF Files → Text Extraction → Semantic Chunking → Embeddings → Vector Storage → Q&A
```

1. **PDF Processing**: PyMuPDF extracts text from uploaded PDFs
2. **Chunking**: Adaptive semantic chunking creates optimal text segments
3. **Embeddings**: text-embedding-004 generates 768-dimension vectors
4. **Storage**: Qdrant stores chunks and embeddings for fast retrieval
5. **Querying**: gemini-1.5-flash generates answers from retrieved context

## Setup

### Requirements
```bash
pip install -r requirements.txt
```

### Environment Variables
Create a `.env` file:
```bash
GOOGLE_API_KEY=your_google_generative_ai_api_key_here
```

### Start Services
1. **Start Qdrant**: 
   ```bash
   docker run -p 6333:6333 qdrant/qdrant
   ```
2. **Start FastAPI**:
   ```bash
   python main.py
   ```

## Features

### Auto PDF Processing
- Place PDF files in `/pdfs` folder
- System automatically processes new files
- Existing PDFs processed on startup
- Files become immediately searchable

### API Endpoints
- `GET /health` - System status and model information
- `POST /api/v1/upload_pdf` - Manual PDF upload
- `POST /api/v1/ask` - Question answering
- `GET /chat` - Web interface

### Health Check Response
```json
{
  "status": "healthy",
  "models": {
    "embedder": "text-embedding-004",
    "generator": "gemini-1.5-flash"
  },
  "qdrant": "connected",
  "pdf_processor": "running"
}
```

## Error Handling
- Clean user-facing error messages
- No raw stack traces in API responses
- Structured logging for debugging
- Graceful component failure handling

## Production Features
- Background PDF monitoring
- Rate limiting for API calls
- Comprehensive health checks
- Clean shutdown handling
- Detailed structured logging

## Usage

### Web Interface
Visit `http://localhost:8000/chat` for the interactive chat interface.

### API Usage
```bash
# Check system health
curl http://localhost:8000/health

# Ask a question
curl -X POST "http://localhost:8000/api/v1/ask" \
  -H "Content-Type: application/json" \
  -d '{"doc_id": "any", "question": "What is this document about?"}'
```

### Adding PDFs
Simply copy PDF files to the `/pdfs` folder. They will be automatically:
1. Text extracted
2. Chunked into semantic segments
3. Embedded using text-embedding-004
4. Indexed in Qdrant vector database
5. Made available for questioning

## Monitoring
- Application logs show processing status
- Health endpoint monitors all components
- PDF processor logs auto-processing events
- Structured logs for debugging

## Technology Stack
- **FastAPI**: Modern Python web framework
- **Google Generative AI**: Gemini-1.5-flash and text-embedding-004
- **Qdrant**: Vector similarity search
- **PyMuPDF**: PDF text extraction
- **Watchdog**: File system monitoring
- **Structured Logging**: Comprehensive observability