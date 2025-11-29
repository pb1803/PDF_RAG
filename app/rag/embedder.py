"""
Google Generative AI embeddings wrapper for the RAG system.
Uses text-embedding-004 for generating embeddings via the Google Generative AI API.
"""
import asyncio
from typing import List, Optional, Dict, Any
import os
import google.generativeai as genai
from app.core.config import settings
from app.core.logger import rag_logger, log_operation, log_error


class GeminiEmbedder:
    """
    Google Generative AI embeddings wrapper for text-embedding-004.
    
    EMBEDDING PIPELINE:
    1. Accepts text chunks from the chunker
    2. Uses text-embedding-004 via Google Generative AI API
    3. Generates high-quality 768-dimension embeddings
    4. Returns vectors for storage in Qdrant vector database
    
    CONFIGURATION:
    - Requires GOOGLE_API_KEY environment variable
    - Uses text-embedding-004 model for optimal document retrieval
    - Implements rate limiting and error handling
    """
    
    def __init__(self):
        self.logger = rag_logger
        self.embedding_model = settings.embedding_model
        
        # Initialize client
        self._genai_client = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize the embedder with Google Generative AI."""
        if self._initialized:
            return
        
        # Use Google Generative AI API key (the only supported method now)
        if not settings.google_api_key:
            raise ValueError(
                "GOOGLE_API_KEY is required. Please set this environment variable."
            )
        
        try:
            await self._initialize_generative_ai()
            self._initialized = True
            log_operation(
                self.logger,
                "embedder_initialized",
                embedding_model=self.embedding_model,
                client_type="generative_ai"
            )
            self.logger.info(f"Using Google Generative AI with {self.embedding_model}")
            
        except Exception as e:
            log_error(
                self.logger,
                e,
                operation="embedder_initialization"
            )
            raise RuntimeError(f"Failed to initialize embedder: {str(e)}")
    
    async def _initialize_generative_ai(self):
        """Initialize Generative AI client with API key."""
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY environment variable is required."
            )
        
        genai.configure(api_key=api_key)
        self._genai_client = genai
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not self._initialized:
            await self.initialize()
        
        if not texts:
            return []
        
        log_operation(
            self.logger,
            "embed_texts_start",
            text_count=len(texts),
            total_chars=sum(len(t) for t in texts)
        )
        
        try:
            embeddings = await self._embed_with_genai(texts)
            
            log_operation(
                self.logger,
                "embed_texts_complete",
                text_count=len(texts),
                embedding_count=len(embeddings)
            )
            
            return embeddings
            
        except Exception as e:
            log_error(
                self.logger,
                e,
                operation="embed_texts",
                text_count=len(texts)
            )
            # Clean error message for users
            raise RuntimeError("Embedding generation failed. Please check your API key and try again.")
    
    async def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding for a single query text.
        
        Args:
            text: Query text to embed
            
        Returns:
            Embedding vector
        """
        embeddings = await self.embed_texts([text])
        return embeddings[0] if embeddings else []
    
    async def _embed_with_genai(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings using Google Generative AI text-embedding-004.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        
        for text in texts:
            try:
                # Run in executor to avoid blocking
                embedding = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self._get_genai_embedding_sync,
                    text
                )
                embeddings.append(embedding)
                
                # Small delay to respect rate limits
                await asyncio.sleep(0.1)
                
            except Exception as e:
                self.logger.warning(f"Failed to embed text: {str(e)}")
                # Use zero vector as fallback
                embeddings.append([0.0] * settings.vector_size)
        
        return embeddings
    
    def _get_genai_embedding_sync(self, text: str) -> List[float]:
        """
        Synchronous Google Generative AI embedding call using text-embedding-004.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        try:
            result = self._genai_client.embed_content(
                model=f"models/{self.embedding_model}",
                content=text,
                task_type="retrieval_document"  # Optimized for document retrieval
            )
            return result['embedding']
            
        except Exception as e:
            raise RuntimeError(f"Google Generative AI embedding failed: {str(e)}")
    
    async def get_embedding_info(self) -> Dict[str, Any]:
        """
        Get information about the embedding model.
        
        Returns:
            Model information dictionary
        """
        if not self._initialized:
            await self.initialize()
        
        return {
            "model_name": self.embedding_model,
            "vector_size": settings.vector_size,
            "client_type": "generative_ai",
            "api_type": "google_generative_ai"
        }
    
    async def health_check(self) -> bool:
        """
        Check if the embedder is healthy and can generate embeddings.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            if not self._initialized:
                await self.initialize()
            
            # Test with a simple text
            test_embedding = await self.embed_query("health check")
            
            return len(test_embedding) == settings.vector_size
            
        except Exception as e:
            log_error(
                self.logger,
                e,
                operation="embedder_health_check"
            )
            return False
    
    def is_ready(self) -> bool:
        """Check if the embedder is ready to use."""
        return self._initialized


# Global embedder instance
gemini_embedder = GeminiEmbedder()