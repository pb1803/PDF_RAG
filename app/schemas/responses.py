"""
Response schemas for the PDF RAG API.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    """Document metadata."""
    doc_id: str
    filename: str
    total_pages: int
    total_chunks: int
    upload_timestamp: str


class ChunkMetadata(BaseModel):
    """Chunk metadata for citations."""
    chunk_id: str = Field(..., description="Unique chunk identifier")
    page: int = Field(..., description="Page number where chunk appears")
    score: float = Field(..., description="Similarity score")
    snippet: str = Field(..., description="Text snippet from the chunk")


class Citation(BaseModel):
    """Citation information."""
    page: int = Field(..., description="Page number")
    snippet: str = Field(..., description="Relevant text snippet")


class UploadPDFResponse(BaseModel):
    """Response model for successful PDF upload and indexing."""
    doc_id: str = Field(..., description="Generated document ID")
    status: str = Field(..., description="Processing status")
    chunks_indexed: int = Field(..., description="Number of chunks indexed")
    filename: str = Field(..., description="Original filename")
    total_pages: int = Field(..., description="Total pages processed")
    processing_time_seconds: float = Field(..., description="Processing time")
    
    class Config:
        json_schema_extra = {
            "example": {
                "doc_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "indexed",
                "chunks_indexed": 42,
                "filename": "Requirement.docx",
                "total_pages": 15,
                "processing_time_seconds": 12.5
            }
        }


class AskQuestionResponse(BaseModel):
    """Response model for question answering."""
    answer: str = Field(..., description="Generated answer")
    sources: List[str] = Field(default_factory=list, description="Page sources used")
    follow_up: Optional[str] = Field(None, description="Follow-up question suggestion")
    citations: List[Citation] = Field(..., description="Source citations")
    used_chunks: List[ChunkMetadata] = Field(..., description="Chunks used for answer")
    doc_id: str = Field(..., description="Document ID queried")
    confidence_score: Optional[float] = Field(None, description="Answer confidence score")
    processing_time_seconds: float = Field(..., description="Processing time")
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": "A database is a structured collection of data that is organized and stored electronically. It allows for efficient data storage, retrieval, and management through specialized software called a Database Management System (DBMS).",
                "sources": ["Page 12", "Page 15"],
                "follow_up": "Would you like to see examples of different database types?",
                "citations": [
                    {
                        "page": 12,
                        "snippet": "A database is a structured collection of data..."
                    },
                    {
                        "page": 15,
                        "snippet": "Database Management Systems provide tools for..."
                    }
                ],
                "used_chunks": [
                    {
                        "chunk_id": "chunk-001",
                        "page": 12,
                        "score": 0.92,
                        "snippet": "A database is a structured collection of data..."
                    }
                ],
                "doc_id": "550e8400-e29b-41d4-a716-446655440000",
                "confidence_score": 0.85,
                "processing_time_seconds": 1.2
            }
        }


class DeleteDocumentResponse(BaseModel):
    """Response model for document deletion."""
    doc_id: str = Field(..., description="Deleted document ID")
    status: str = Field(..., description="Deletion status")
    chunks_deleted: int = Field(..., description="Number of chunks deleted")
    
    class Config:
        json_schema_extra = {
            "example": {
                "doc_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "deleted",
                "chunks_deleted": 42
            }
        }


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    error_code: Optional[str] = Field(None, description="Error code")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "Document not found",
                "detail": "No document found with ID: 550e8400-e29b-41d4-a716-446655440000",
                "error_code": "DOC_NOT_FOUND"
            }
        }


class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: str = Field(..., description="Current timestamp")
    models: Optional[Dict[str, str]] = Field(None, description="AI models in use")
    components: Optional[Dict[str, str]] = Field(None, description="Component status")
    dependencies: Optional[Dict[str, str]] = Field(None, description="Legacy dependency status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": "2024-01-15T10:30:00Z",
                "models": {
                    "embedder": "text-embedding-004",
                    "generator": "text-bison-001"
                },
                "components": {
                    "qdrant": "connected",
                    "embedder": "connected",
                    "generator": "connected",
                    "pdf_processor": "running"
                }
            }
        }