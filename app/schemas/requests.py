"""
Request schemas for the PDF RAG API.
"""
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl


class UploadPDFRequest(BaseModel):
    """Request model for PDF upload via URL."""
    file_url: HttpUrl = Field(..., description="URL to the PDF file to process")
    doc_id: Optional[str] = Field(None, description="Optional custom document ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "file_url": "file:///mnt/data/Requirement.docx",
                "doc_id": "custom-doc-123"
            }
        }


class AskQuestionRequest(BaseModel):
    """Request model for asking questions about a document."""
    doc_id: str = Field(..., description="Document ID to query against")
    question: str = Field(
        ..., 
        min_length=5,
        max_length=500,
        description="Question to ask about the document"
    )
    top_k: Optional[int] = Field(
        None, 
        ge=1, 
        le=20, 
        description="Number of top chunks to retrieve (overrides default)"
    )
    temperature: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Generation temperature (overrides default)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "doc_id": "550e8400-e29b-41d4-a716-446655440000",
                "question": "What are the main requirements for the system?",
                "top_k": 5,
                "temperature": 0.1
            }
        }


class DeleteDocumentRequest(BaseModel):
    """Request model for deleting a document."""
    doc_id: str = Field(..., description="Document ID to delete")
    
    class Config:
        json_schema_extra = {
            "example": {
                "doc_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }