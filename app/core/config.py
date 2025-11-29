"""
Configuration settings for the RAG system.
"""
import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    app_name: str = "PDF RAG System"
    version: str = "1.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Qdrant Configuration
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection_name: str = "pdf_documents"
    vector_size: int = 768  # Gemini embedding size
    
    # Google AI Configuration  
    google_application_credentials: Optional[str] = None
    google_api_key: Optional[str] = None
    gemini_model: str = "gemini-2.0-flash"  # Updated from 1.5-flash (deprecated)
    embedding_model: str = "text-embedding-004"  # Continue using text-embedding-004 for embeddings
    project_id: Optional[str] = None
    location: str = "us-central1"
    
    # RAG Configuration
    max_chunk_size: int = 800
    min_chunk_size: int = 200
    chunk_overlap: int = 100
    top_k_retrieval: int = 8
    top_k_final: int = 5
    temperature: float = 0.1
    max_tokens: int = 1000
    
    # File Upload Configuration
    max_file_size_mb: int = 50
    allowed_file_types: List[str] = ["application/pdf"]
    upload_dir: str = "uploads"
    
    # Logging Configuration
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Database Configuration
    database_url: str = "sqlite:///./aiagent.db"
    database_echo: bool = False
    
    # Chat Session Configuration
    max_message_length: int = 5000
    max_chat_history_messages: int = 20
    max_prompt_history_messages: int = 10
    chat_session_cleanup_days: int = 30  # Auto-cleanup old sessions after 30 days
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Set Google credentials if provided
        if self.google_application_credentials:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.google_application_credentials
        
        # Create upload directory if it doesn't exist
        os.makedirs(self.upload_dir, exist_ok=True)


# Global settings instance
settings = Settings()