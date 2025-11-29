"""
PDF upload and document management routes.
"""
import asyncio
import time
import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse
import aiofiles
from pathlib import Path
from app.core.config import settings
from app.core.logger import api_logger, log_operation, log_error
from app.schemas.requests import UploadPDFRequest, DeleteDocumentRequest
from app.schemas.responses import (
    UploadPDFResponse, DeleteDocumentResponse, ErrorResponse
)
from app.rag.extractor import pdf_extractor
from app.rag.chunker import semantic_chunker
from app.rag.embedder import gemini_embedder
from app.rag.vectorstore import qdrant_store


router = APIRouter()


@router.post(
    "/upload_pdf", 
    response_model=UploadPDFResponse,
    responses={
        400: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def upload_pdf(
    file: Optional[UploadFile] = File(None),
    file_url: Optional[str] = Form(None),
    doc_id: Optional[str] = Form(None)
):
    """
    Upload and process a PDF document.
    
    Accepts either a file upload or a file URL (including file:// URLs).
    Extracts text, chunks it, generates embeddings, and stores in vector database.
    """
    start_time = time.time()
    
    # Validate input
    if not file and not file_url:
        raise HTTPException(
            status_code=400,
            detail="Either 'file' or 'file_url' must be provided"
        )
    
    if file and file_url:
        raise HTTPException(
            status_code=400,
            detail="Provide either 'file' or 'file_url', not both"
        )
    
    # Generate doc_id if not provided
    if not doc_id:
        doc_id = str(uuid.uuid4())
    
    log_operation(
        api_logger,
        "upload_pdf_start",
        doc_id=doc_id,
        has_file=file is not None,
        has_url=file_url is not None
    )
    
    try:
        # Process file or URL
        if file:
            filename, pages = await _process_uploaded_file(file, doc_id)
        else:
            filename, pages = await _process_file_url(file_url, doc_id)
        
        if not pages:
            raise HTTPException(
                status_code=400,
                detail="No text content extracted from PDF"
            )
        
        # Initialize components
        await _initialize_components()
        
        # Chunk the pages
        chunks = await semantic_chunker.chunk_pages(pages, doc_id)
        
        if not chunks:
            raise HTTPException(
                status_code=400,
                detail="Failed to create chunks from document"
            )
        
        # Generate embeddings
        chunk_texts = [chunk.text for chunk in chunks]
        embeddings = await gemini_embedder.embed_texts(chunk_texts)
        
        if len(embeddings) != len(chunks):
            raise HTTPException(
                status_code=500,
                detail="Mismatch between chunks and embeddings"
            )
        
        # Store in vector database
        chunks_indexed = await qdrant_store.upsert_chunks(chunks, embeddings)
        
        processing_time = time.time() - start_time
        
        response = UploadPDFResponse(
            doc_id=doc_id,
            status="indexed",
            chunks_indexed=chunks_indexed,
            filename=filename,
            total_pages=len(pages),
            processing_time_seconds=round(processing_time, 2)
        )
        
        log_operation(
            api_logger,
            "upload_pdf_complete",
            doc_id=doc_id,
            chunks_indexed=chunks_indexed,
            processing_time=processing_time
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(
            api_logger,
            e,
            operation="upload_pdf",
            doc_id=doc_id
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process PDF: {str(e)}"
        )


@router.delete(
    "/delete_document",
    response_model=DeleteDocumentResponse,
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def delete_document(request: DeleteDocumentRequest):
    """
    Delete a document and all its chunks from the vector database.
    """
    log_operation(
        api_logger,
        "delete_document_start",
        doc_id=request.doc_id
    )
    
    try:
        await _initialize_components()
        
        # Check if document exists
        doc_info = await qdrant_store.get_document_info(request.doc_id)
        if not doc_info:
            raise HTTPException(
                status_code=404,
                detail=f"Document not found: {request.doc_id}"
            )
        
        # Delete from vector store
        chunks_deleted = await qdrant_store.delete_document(request.doc_id)
        
        # Clean up any uploaded files (optional - implement if storing files)
        await _cleanup_document_files(request.doc_id)
        
        response = DeleteDocumentResponse(
            doc_id=request.doc_id,
            status="deleted",
            chunks_deleted=chunks_deleted
        )
        
        log_operation(
            api_logger,
            "delete_document_complete",
            doc_id=request.doc_id,
            chunks_deleted=chunks_deleted
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(
            api_logger,
            e,
            operation="delete_document",
            doc_id=request.doc_id
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document: {str(e)}"
        )


@router.get(
    "/document/{doc_id}/info",
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def get_document_info(doc_id: str):
    """
    Get information about a document.
    """
    try:
        await _initialize_components()
        
        doc_info = await qdrant_store.get_document_info(doc_id)
        if not doc_info:
            raise HTTPException(
                status_code=404,
                detail=f"Document not found: {doc_id}"
            )
        
        return doc_info
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(
            api_logger,
            e,
            operation="get_document_info",
            doc_id=doc_id
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get document info: {str(e)}"
        )


async def _process_uploaded_file(file: UploadFile, doc_id: str):
    """Process an uploaded file."""
    # Validate file type
    if file.content_type not in settings.allowed_file_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}"
        )
    
    # Check file size
    if file.size and file.size > settings.max_file_size_mb * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {settings.max_file_size_mb}MB"
        )
    
    # Save file temporarily
    temp_path = Path(settings.upload_dir) / f"{doc_id}_{file.filename}"
    temp_path.parent.mkdir(parents=True, exist_ok=True)
    
    async with aiofiles.open(temp_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    try:
        # Extract text
        pages = await pdf_extractor.extract_from_file(temp_path)
        return file.filename, pages
        
    finally:
        # Clean up temp file
        if temp_path.exists():
            temp_path.unlink()


async def _process_file_url(file_url: str, doc_id: str):
    """Process a file URL."""
    try:
        pages = await pdf_extractor.extract_from_url(file_url)
        
        # Extract filename from URL
        from urllib.parse import urlparse
        parsed = urlparse(file_url)
        filename = Path(parsed.path).name or f"document_{doc_id}.pdf"
        
        return filename, pages
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to process file URL: {str(e)}"
        )


async def _initialize_components():
    """Initialize RAG components if needed."""
    tasks = [
        gemini_embedder.initialize(),
        qdrant_store.initialize()
    ]
    
    await asyncio.gather(*tasks)


async def _cleanup_document_files(doc_id: str):
    """Clean up any stored files for a document."""
    try:
        # Look for files with doc_id pattern
        upload_dir = Path(settings.upload_dir)
        if upload_dir.exists():
            for file_path in upload_dir.glob(f"{doc_id}_*"):
                if file_path.is_file():
                    file_path.unlink()
                    
    except Exception as e:
        # Log but don't fail the delete operation
        log_error(
            api_logger,
            e,
            operation="cleanup_document_files",
            doc_id=doc_id
        )