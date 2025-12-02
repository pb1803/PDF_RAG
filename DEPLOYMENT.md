# 🚀 AI Tutor - Deployment Guide

## Quick Start for Clients

### Option 1: Automated Setup (Recommended)

**For Windows:**
```bash
# Clone the repository
git clone <your-repository-url>
cd ai-tutor

# Run automated setup
setup.bat
```

**For Linux/macOS:**
```bash
# Clone the repository
git clone <your-repository-url>
cd ai-tutor

# Make setup script executable and run
chmod +x setup.sh
./setup.sh
```

### Option 2: Manual Setup

1. **Prerequisites**
   - Python 3.9+ installed
   - Docker Desktop installed
   - Google AI API key (get from Google AI Studio)

2. **Setup Steps**
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate virtual environment
   # Windows:
   venv\Scripts\activate
   # Linux/macOS:
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Setup environment
   cp .env.example .env
   # Edit .env with your Google AI API key
   
   # Start Qdrant database
   docker run -d -p 6333:6333 --name qdrant qdrant/qdrant
   
   # Create directories
   mkdir pdfs logs uploads
   ```

3. **Configuration**
   
   Edit `.env` file with your credentials:
   ```env
   GOOGLE_API_KEY=your_actual_api_key_here
   ```

4. **Run Application**
   ```bash
   python main.py
   ```

5. **Access Application**
   - Open browser: http://localhost:8000
   - Upload PDFs in the `pdfs/` folder
   - Start chatting with your documents!

## 🔧 Verification

Run the deployment checker:
```bash
python verify_deployment.py
```

## 🐳 Docker Deployment

For production deployment:
```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build manually
docker build -t ai-tutor .
docker run -p 8000:8000 ai-tutor
```

## 📁 File Structure

```
ai-tutor/
├── app/                    # Main application code
│   ├── api/               # FastAPI routes
│   ├── core/              # Configuration and logging
│   ├── rag/               # RAG pipeline implementation
│   └── schemas/           # Pydantic models
├── pdfs/                  # Place PDF files here
├── logs/                  # Application logs
├── uploads/               # Temporary file uploads
├── static/                # Frontend files (HTML, CSS, JS)
├── main.py               # Application entry point
├── requirements.txt      # Python dependencies
├── .env.example         # Environment template
├── docker-compose.yml   # Docker configuration
└── README.md           # This file
```

## 🔑 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_API_KEY` | Google AI Studio API key | ✅ Yes |
| `QDRANT_HOST` | Qdrant database host | No (default: localhost) |
| `QDRANT_PORT` | Qdrant database port | No (default: 6333) |
| `PORT` | Application port | No (default: 8000) |
| `DEBUG` | Debug mode | No (default: false) |

## 🛠️ Troubleshooting

### Common Issues

**1. "Google API Key not found"**
- Solution: Add your API key to `.env` file
- Get key from: https://aistudio.google.com/app/apikey

**2. "Qdrant connection failed"**
- Solution: Start Qdrant with Docker:
  ```bash
  docker run -d -p 6333:6333 --name qdrant qdrant/qdrant
  ```

**3. "Port 8000 already in use"**
- Solution: Change port in `.env`:
  ```env
  PORT=8001
  ```

**4. "PDF not processing"**
- Check PDF is in `pdfs/` folder
- Verify PDF is not corrupted
- Check logs in `logs/` directory

**5. "Frontend not loading"**
- Clear browser cache
- Check if static files exist in `static/` folder
- Verify FastAPI is serving static files correctly

### Logs

Check application logs:
```bash
# View latest logs
tail -f logs/aiagent.log

# Check all logs
cat logs/aiagent.log
```

### Reset Application

To reset everything:
```bash
# Stop containers
docker stop qdrant
docker rm qdrant

# Remove data
rm -rf qdrant-local/
rm aiagent.db
rm -rf uploads/*

# Restart
docker run -d -p 6333:6333 --name qdrant qdrant/qdrant
python main.py
```

## 🌐 Production Deployment

### Using Docker Compose (Recommended)

1. **Update environment variables in `docker-compose.yml`**
2. **Deploy:**
   ```bash
   docker-compose up -d
   ```

### Manual Production Setup

1. **Use production WSGI server:**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000
   ```

2. **Set up reverse proxy (Nginx):**
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

3. **Environment variables for production:**
   ```env
   DEBUG=false
   SECRET_KEY=your-secure-secret-key
   ALLOWED_ORIGINS=https://yourdomain.com
   ```

## 📞 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review logs in `logs/aiagent.log`
3. Run `python verify_deployment.py` for diagnostics
4. Check GitHub issues for similar problems

## 🔄 Updates

To update the application:
```bash
git pull origin main
pip install -r requirements.txt
python verify_deployment.py
```

## 📊 Monitoring

The application provides:
- Request logging in `logs/aiagent.log`
- Chat history in SQLite database
- Vector embeddings in Qdrant
- Real-time status via web interface

Access health check: http://localhost:8000/health