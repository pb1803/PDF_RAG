"""
FastAPI main application for PDF RAG system.
"""
import asyncio
import threading
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.core.logger import app_logger, log_operation, log_error
from app.core.db import create_db_and_tables, check_database_connection
from app.api.pdf_routes import router as pdf_router
from app.api.qa_routes import router as qa_router
from app.api.chat_routes import router as chat_router
from app.schemas.responses import HealthCheckResponse, ErrorResponse
from app.rag.embedder import gemini_embedder
from app.rag.vectorstore import qdrant_store
from app.rag.rag_pipeline import rag_pipeline
from simple_pdf_processor import SimplePDFProcessor


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown.
    
    PDF RAG PIPELINE OVERVIEW:
    1. PDF Files → Text Extraction (PyMuPDF)
    2. Text → Semantic Chunks (adaptive chunking)
    3. Chunks → Embeddings (text-embedding-004 via Google Generative AI)
    4. Embeddings → Vector Storage (Qdrant local)
    5. Query → Similarity Search (Qdrant cosine search)
    6. Relevant Chunks → Answer Generation (text-bison-001 via Google Generative AI)
    """
    # Startup
    log_operation(app_logger, "application_startup")
    
    # Log the AI models being used
    app_logger.info(f"🤖 MODELS: Using {settings.gemini_model} for generation")
    app_logger.info(f"🤖 MODELS: Using {settings.embedding_model} for embeddings")
    app_logger.info("🗄️ DATABASE: Connected to local Qdrant server")
    
    try:
        # Initialize components in proper order: database → embedder → vectorstore → rag_pipeline
        
        # Step 1: Initialize Database
        try:
            create_db_and_tables()
            if check_database_connection():
                app_logger.info("✅ Database initialized successfully")
            else:
                app_logger.error("❌ Database connection failed")
        except Exception as e:
            log_error(app_logger, e, operation="database_startup")
            app_logger.error("❌ Database initialization failed")
        
        # Step 2: Initialize embedder (text-embedding-004)
        try:
            await gemini_embedder.initialize()
            app_logger.info("✅ Embedder (text-embedding-004) initialized successfully")
        except Exception as e:
            log_error(app_logger, e, operation="embedder_startup")
            app_logger.error("❌ Embedder initialization failed")
        
        # Step 3: Initialize vectorstore (Qdrant)
        try:
            await qdrant_store.initialize()
            app_logger.info("✅ Vector store (Qdrant) initialized successfully")
        except Exception as e:
            log_error(app_logger, e, operation="vectorstore_startup")
            app_logger.error("❌ Vector store initialization failed")
        
        # Step 4: Initialize RAG pipeline
        try:
            await rag_pipeline.initialize()
            app_logger.info(f"✅ RAG pipeline ({settings.gemini_model}) initialized successfully")
        except Exception as e:
            log_error(app_logger, e, operation="rag_pipeline_startup")
            app_logger.error("❌ RAG pipeline initialization failed")
        
        # Step 5: Start PDF processor in background
        try:
            pdf_processor = SimplePDFProcessor("d:\\aiagent\\pdfs")
            threading.Thread(target=pdf_processor.start_monitoring, daemon=True).start()
            app_logger.info("✅ PDF Auto-Processor Initialized - monitoring /pdfs folder")
        except Exception as e:
            log_error(app_logger, e, operation="pdf_processor_startup")
            app_logger.error("❌ PDF processor startup failed")
        
        app_logger.info("🚀 Application startup complete - Ready to process PDFs, answer questions, and manage chat sessions!")
        
    except Exception as e:
        log_error(app_logger, e, operation="application_startup")
        # Continue startup even if some components fail
        # They can be initialized on first use
        app_logger.warning("⚠️ Some components failed to initialize - they will retry on first use")
    
    yield
    
    # Shutdown
    log_operation(app_logger, "application_shutdown")
    app_logger.info("👋 Application shutting down")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description=f"AI-powered PDF Question-Answering system using Google {settings.gemini_model} and RAG",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(pdf_router, prefix="/api/v1", tags=["PDF Management"])
app.include_router(qa_router, prefix="/api/v1", tags=["Question Answering"])
app.include_router(chat_router, tags=["Chat Sessions"])
app.include_router(chat_router, tags=["Chat Sessions"])


# Add CORS headers for the chat interface
@app.middleware("http")
async def add_cors_header(request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response


@app.get("/", response_model=dict)
async def root():
    """Root endpoint with basic API information."""
    return {
        "message": "PDF RAG System API",
        "version": settings.version,
        "docs_url": "/docs",
        "health_check": "/health",
        "chat_ui": "/chat"
    }


@app.get("/chat")
async def chat_ui():
    """Serve the chat interface."""
    return FileResponse("chat.html")


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint to verify all components are working."""
    log_operation(app_logger, "health_check_start")
    
    try:
        # Check each component
        dependencies = {}
        
        # Check Qdrant
        try:
            qdrant_ready = qdrant_store.is_ready()
            dependencies["qdrant"] = "connected" if qdrant_ready else "disconnected"
        except Exception as e:
            dependencies["qdrant"] = f"error: {str(e)[:50]}"
        
        # Check embedder (text-embedding-004)
        try:
            embedder_ready = gemini_embedder.is_ready()
            dependencies["embedder"] = "connected" if embedder_ready else "disconnected"
        except Exception as e:
            dependencies["embedder"] = f"error: {str(e)[:50]}"
        
        # Check RAG pipeline (text-bison-001)
        try:
            pipeline_ready = rag_pipeline.is_ready()
            dependencies["generator"] = "connected" if pipeline_ready else "disconnected"
        except Exception as e:
            dependencies["generator"] = f"error: {str(e)[:50]}"
        
        # Check PDF processor
        try:
            import os
            pdf_folder_exists = os.path.exists("d:\\aiagent\\pdfs")
            dependencies["pdf_processor"] = "running" if pdf_folder_exists else "pdf_folder_missing"
        except Exception as e:
            dependencies["pdf_processor"] = f"error: {str(e)[:50]}"
        
        # Overall status
        all_connected = all(status in ["connected", "running"] for status in dependencies.values())
        overall_status = "healthy" if all_connected else "degraded"
        
        # Enhanced response with model information
        response_data = {
            "status": overall_status,
            "version": settings.version,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "models": {
                "embedder": settings.embedding_model,
                "generator": settings.gemini_model
            },
            "qdrant": dependencies.get("qdrant", "disconnected"),
            "pdf_processor": dependencies.get("pdf_processor", "error"),
            "components": dependencies
        }
        
        response = HealthCheckResponse(**response_data)
        
        log_operation(
            app_logger,
            "health_check_complete",
            status=overall_status,
            models=response_data["models"],
            components=dependencies
        )
        
        return response
        
    except Exception as e:
        log_error(app_logger, e, operation="health_check")
        
        return HealthCheckResponse(
            status="unhealthy",
            version=settings.version,
            timestamp=datetime.utcnow().isoformat() + "Z",
            models={
                "embedder": settings.embedding_model,
                "generator": settings.gemini_model
            },
            qdrant="error",
            pdf_processor="error",
            components={"error": "Health check failed"}
        )


@app.get("/config", response_model=dict)
async def get_config():
    """Get non-sensitive configuration information."""
    return {
        "app_name": settings.app_name,
        "version": settings.version,
        "qdrant_collection": settings.qdrant_collection_name,
        "vector_size": settings.vector_size,
        "embedding_model": settings.embedding_model,  # text-embedding-004
        "generation_model": settings.gemini_model,     # gemini-1.5-flash
        "max_chunk_size": settings.max_chunk_size,
        "top_k_retrieval": settings.top_k_retrieval,
        "top_k_final": settings.top_k_final,
        "temperature": settings.temperature,
        "max_file_size_mb": settings.max_file_size_mb,
        "api_provider": "google_generative_ai"
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler."""
    log_error(
        app_logger,
        exc,
        operation="http_request",
        path=str(request.url.path),
        method=request.method
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url.path)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler for unhandled exceptions."""
    log_error(
        app_logger,
        exc,
        operation="unhandled_exception",
        path=str(request.url.path),
        method=request.method
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else "An error occurred",
            "status_code": 500,
            "path": str(request.url.path)
        }
    )


# Middleware for request logging
@app.middleware("http")
async def log_requests(request, call_next):
    """Log all requests."""
    start_time = datetime.utcnow()
    
    log_operation(
        app_logger,
        "request_start",
        method=request.method,
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown"
    )
    
    response = await call_next(request)
    
    process_time = (datetime.utcnow() - start_time).total_seconds()
    
    log_operation(
        app_logger,
        "request_complete",
        method=request.method,
        path=str(request.url.path),
        status_code=response.status_code,
        process_time=process_time
    )
    
    return response


if __name__ == "__main__":
    import uvicorn
    
    log_operation(
        app_logger,
        "starting_server",
        host=settings.host,
        port=settings.port,
        debug=settings.debug
    )
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )