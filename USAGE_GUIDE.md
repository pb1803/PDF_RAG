# 🚀 AI PDF RAG System - Usage Guide

## Quick Start

Your AI agent is now running! Here's how to use it for PDF question-answering:

## 📋 Prerequisites
- ✅ Server running on `http://localhost:8000`
- ✅ Qdrant vector database active
- ✅ Google API key configured
- ✅ All components connected

## 🔗 API Endpoints

### 1. Health Check
```bash
curl -Method GET -Uri "http://localhost:8000/health"
```

### 2. Upload PDF
```bash
# Upload a PDF file
curl -X POST "http://localhost:8000/api/v1/upload_pdf" \
  -F "file=@your-document.pdf" \
  -F "doc_id=my-document-1"

# Or upload from URL
curl -X POST "http://localhost:8000/api/v1/upload_pdf" \
  -F "file_url=https://example.com/document.pdf" \
  -F "doc_id=my-document-2"
```

### 3. Ask Questions
```bash
# Ask a question about your uploaded document
curl -X POST "http://localhost:8000/api/v1/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "my-document-1",
    "question": "What is the main topic of this document?",
    "top_k": 5
  }'
```

### 4. Get Document Info
```bash
curl -X GET "http://localhost:8000/api/v1/document/my-document-1/info"
```

### 5. Delete Document
```bash
curl -X DELETE "http://localhost:8000/api/v1/delete_document" \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "my-document-1"
  }'
```

## 💻 PowerShell Examples

### Upload PDF
```powershell
# Upload local file
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/upload_pdf" -Method POST -Form @{
    file = Get-Item "C:\path\to\your\document.pdf"
    doc_id = "my-document"
}
Write-Output $response
```

### Ask Question
```powershell
$body = @{
    doc_id = "my-document"
    question = "What are the key findings?"
    top_k = 5
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/ask" -Method POST -Body $body -ContentType "application/json"
Write-Output $response
```

## 🐍 Python Examples

### Upload and Query PDF
```python
import requests
import json

# 1. Upload PDF
with open("document.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/v1/upload_pdf",
        files={"file": f},
        data={"doc_id": "my-document"}
    )
print("Upload:", response.json())

# 2. Ask question
question_data = {
    "doc_id": "my-document",
    "question": "What is this document about?",
    "top_k": 5
}

response = requests.post(
    "http://localhost:8000/api/v1/ask",
    json=question_data
)
answer = response.json()
print("Answer:", answer["answer"])
print("Sources:", answer["citations"])
```

## 🌐 Web Interface

Visit these URLs in your browser:
- **API Docs**: `http://localhost:8000/docs` (Interactive Swagger UI)
- **Alternative Docs**: `http://localhost:8000/redoc`
- **Health Check**: `http://localhost:8000/health`

## 📊 Response Examples

### Successful Upload Response
```json
{
  "message": "PDF uploaded and processed successfully",
  "doc_id": "my-document",
  "chunks_created": 15,
  "pages_processed": 8,
  "processing_time": 2.34
}
```

### Question Answer Response
```json
{
  "answer": "The document discusses artificial intelligence and machine learning techniques...",
  "citations": [
    {
      "page_number": 1,
      "text": "AI and ML are transformative technologies...",
      "relevance_score": 0.92
    }
  ],
  "doc_id": "my-document",
  "confidence_score": 0.89,
  "processing_time": 1.2
}
```

## 🎯 Best Practices

### Document Upload
- **Supported formats**: PDF files only
- **File size limit**: 50MB maximum
- **Use descriptive doc_ids**: `financial-report-2024` instead of `doc1`

### Question Asking
- **Be specific**: "What are the Q3 revenue figures?" vs "Tell me about revenue"
- **Use context**: Reference specific sections if known
- **Adjust top_k**: Use 3-5 for focused answers, 8-10 for comprehensive analysis

### Performance Tips
- **Batch questions**: Use the batch endpoint for multiple questions
- **Cache responses**: Store frequently asked questions
- **Monitor processing time**: Large documents take longer to process

## 🔧 Troubleshooting

### Common Issues
1. **"Document not found"**: Check if upload was successful
2. **Empty responses**: Try rephrasing the question
3. **Slow responses**: Reduce top_k or check server resources

### Health Monitoring
```bash
# Check system status
curl http://localhost:8000/health

# Expected response:
# {
#   "status": "healthy",
#   "dependencies": {
#     "qdrant": "connected",
#     "gemini_embedder": "connected", 
#     "rag_pipeline": "connected"
#   }
# }
```

## 🎪 Demo Workflow

### Complete Example
```bash
# 1. Check health
curl http://localhost:8000/health

# 2. Upload sample PDF
curl -X POST "http://localhost:8000/api/v1/upload_pdf" \
  -F "file=@sample.pdf" \
  -F "doc_id=demo-doc"

# 3. Ask questions
curl -X POST "http://localhost:8000/api/v1/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "demo-doc",
    "question": "What is the main purpose of this document?",
    "top_k": 5
  }'

# 4. Get document info
curl http://localhost:8000/api/v1/document/demo-doc/info

# 5. Clean up
curl -X DELETE "http://localhost:8000/api/v1/delete_document" \
  -H "Content-Type: application/json" \
  -d '{"doc_id": "demo-doc"}'
```

## 🌟 Advanced Features

- **Batch Questions**: Ask multiple questions in one request
- **Custom Parameters**: Adjust temperature and top_k for different response styles
- **Document Management**: List, inspect, and delete documents
- **Citation Tracking**: Get page numbers and source text for all answers
- **Confidence Scoring**: Evaluate answer reliability

Your AI PDF RAG system is ready to help you extract insights from any PDF document!