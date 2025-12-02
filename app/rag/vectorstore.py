"""
Qdrant vector store wrapper for the RAG system.
"""
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from qdrant_client import QdrantClient
from qdrant_client import models

from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter, FieldCondition, 
    MatchValue, SearchParams, CollectionInfo
)
from qdrant_client.http import models as rest
from app.core.config import settings
from app.core.logger import rag_logger, log_operation, log_error
from app.rag.chunker import TextChunk


class QdrantVectorStore:
    """
    Qdrant vector store wrapper for document chunks and embeddings.
    """
    
    def __init__(self):
        self.logger = rag_logger
        self.client = None
        self.collection_name = settings.qdrant_collection_name
        self.vector_size = settings.vector_size
        self._initialized = False
    
    async def initialize(self):
        """Initialize Qdrant client and collection."""
        if self._initialized:
            return
        
        try:
            # Create client - use local storage if URL indicates local mode
            if settings.qdrant_url.startswith("http"):
                # Try remote connection first
                try:
                    self.client = QdrantClient(url=settings.qdrant_url)
                except Exception:
                    # Fall back to local storage if remote connection fails
                    self.logger.warning("Remote Qdrant connection failed, using local storage")
                    self.client = QdrantClient(path="./qdrant-local")
            else:
                # Use local storage directly
                self.client = QdrantClient(path="./qdrant-local")
            
            # Run collection setup in executor to avoid blocking
            await asyncio.get_event_loop().run_in_executor(
                None,
                self._setup_collection
            )
            
            self._initialized = True
            log_operation(
                self.logger,
                "vectorstore_initialized",
                collection_name=self.collection_name,
                vector_size=self.vector_size
            )
            
        except Exception as e:
            log_error(
                self.logger,
                e,
                operation="vectorstore_initialization"
            )
            raise RuntimeError(f"Failed to initialize Qdrant: {str(e)}")
    
    def _setup_collection(self):
        """Set up Qdrant collection (runs in thread pool)."""
        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                # Create collection
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
                self.logger.info(f"Created collection: {self.collection_name}")
            else:
                self.logger.info(f"Collection exists: {self.collection_name}")
                
        except Exception as e:
            raise RuntimeError(f"Failed to setup collection: {str(e)}")
    
    async def upsert_chunks(
        self, 
        chunks: List[TextChunk], 
        embeddings: List[List[float]]
    ) -> int:
        """
        Upsert document chunks with embeddings.
        
        Args:
            chunks: List of TextChunk objects
            embeddings: List of embedding vectors
            
        Returns:
            Number of chunks upserted
        """
        if not self._initialized:
            await self.initialize()
        
        if len(chunks) != len(embeddings):
            raise ValueError("Chunks and embeddings lists must have same length")
        
        log_operation(
            self.logger,
            "upsert_chunks_start",
            chunk_count=len(chunks),
            doc_id=chunks[0].doc_id if chunks else None
        )
        
        try:
            # Prepare points for upsert
            points = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                point = PointStruct(
                    id=hash(chunk.chunk_id) & 0x7FFFFFFF,  # Ensure positive int
                    vector=embedding,
                    payload={
                        "chunk_id": chunk.chunk_id,
                        "doc_id": chunk.doc_id,
                        "page_number": chunk.page_number,
                        "text": chunk.text,
                        "start_char": chunk.start_char,
                        "end_char": chunk.end_char,
                        "token_count": chunk.token_count or 0,
                        "chunk_index": i
                    }
                )
                points.append(point)
            
            # Upsert in batches
            batch_size = 100
            total_upserted = 0
            
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.client.upsert(
                        collection_name=self.collection_name,
                        points=batch
                    )
                )
                
                total_upserted += len(batch)
            
            log_operation(
                self.logger,
                "upsert_chunks_complete",
                chunks_upserted=total_upserted,
                doc_id=chunks[0].doc_id if chunks else None
            )
            
            return total_upserted
            
        except Exception as e:
            log_error(
                self.logger,
                e,
                operation="upsert_chunks",
                chunk_count=len(chunks)
            )
            raise
    
    async def search_similar_chunks(
        self,
        query_embedding: List[float],
        doc_id: str,
        top_k: int = None,
        score_threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Search for similar chunks in a specific document.
        
        Args:
            query_embedding: Query embedding vector
            doc_id: Document ID to search within
            top_k: Number of results to return
            score_threshold: Minimum similarity score
            
        Returns:
            List of search results with scores and metadata
        """
        if not self._initialized:
            await self.initialize()
        
        top_k = top_k or settings.top_k_retrieval
        
        log_operation(
            self.logger,
            "search_chunks_start",
            doc_id=doc_id,
            top_k=top_k,
            score_threshold=score_threshold
        )
        
        try:
            # Create filter for document ID
            doc_filter = Filter(
                must=[
                    FieldCondition(
                        key="doc_id",
                        match=MatchValue(value=doc_id)
                    )
                ]
            )
            
            # Perform search using the correct Qdrant client method
            search_result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_embedding,
                    query_filter=doc_filter,
                    limit=top_k,
                    score_threshold=score_threshold,
                    search_params=SearchParams(hnsw_ef=128, exact=False)
                )
            )
            
            # Format results
            results = []
            for scored_point in search_result:
                result = {
                    "chunk_id": scored_point.payload["chunk_id"],
                    "score": scored_point.score,
                    "page_number": scored_point.payload["page_number"],
                    "text": scored_point.payload["text"],
                    "start_char": scored_point.payload["start_char"],
                    "end_char": scored_point.payload["end_char"],
                    "token_count": scored_point.payload.get("token_count", 0)
                }
                results.append(result)
            
            log_operation(
                self.logger,
                "search_chunks_complete",
                doc_id=doc_id,
                results_found=len(results),
                top_score=results[0]["score"] if results else 0.0
            )
            
            return results
            
        except Exception as e:
            log_error(
                self.logger,
                e,
                operation="search_chunks",
                doc_id=doc_id,
                top_k=top_k
            )
            return []

    async def search_all_documents(
        self,
        query_embedding: List[float],
        top_k: int = None,
        score_threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Search for similar chunks across ALL documents.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            score_threshold: Minimum similarity score
            
        Returns:
            List of search results with scores and metadata
        """
        if not self._initialized:
            await self.initialize()
        
        top_k = top_k or settings.top_k_retrieval
        
        log_operation(
            self.logger,
            "search_chunks_start",
            doc_id="all_documents",
            top_k=top_k,
            score_threshold=score_threshold
        )
        
        try:
            # Search across ALL documents (no doc_id filter)
            search_result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_embedding,
                    limit=top_k,
                    score_threshold=score_threshold,
                    search_params=SearchParams(hnsw_ef=128, exact=False)
                )
            )
            
            # Format results
            results = []
            for scored_point in search_result:
                result = {
                    "chunk_id": scored_point.payload["chunk_id"],
                    "score": scored_point.score,
                    "page_number": scored_point.payload["page_number"],
                    "text": scored_point.payload["text"],
                    "start_char": scored_point.payload["start_char"],
                    "end_char": scored_point.payload["end_char"],
                    "doc_id": scored_point.payload["doc_id"],
                    "token_count": scored_point.payload.get("token_count", 0)
                }
                results.append(result)
            
            log_operation(
                self.logger,
                "search_chunks_complete",
                doc_id="all_documents",
                results_found=len(results),
                top_score=results[0]["score"] if results else 0.0
            )
            
            return results
            
        except Exception as e:
            log_error(
                self.logger,
                e,
                operation="search_all_documents",
                top_k=top_k
            )
            return []
    
    async def delete_document(self, doc_id: str) -> int:
        """
        Delete all chunks for a document.
        
        Args:
            doc_id: Document ID to delete
            
        Returns:
            Number of chunks deleted
        """
        if not self._initialized:
            await self.initialize()
        
        log_operation(
            self.logger,
            "delete_document_start",
            doc_id=doc_id
        )
        
        try:
            # First, count chunks to be deleted
            count_filter = Filter(
                must=[
                    FieldCondition(
                        key="doc_id",
                        match=MatchValue(value=doc_id)
                    )
                ]
            )
            
            # Get count via scroll (since count API may not be available)
            scroll_result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.scroll(
                    collection_name=self.collection_name,
                    scroll_filter=count_filter,
                    limit=10000,
                    with_payload=False,
                    with_vectors=False
                )[0]  # Get points only, not next_page_offset
            )
            
            chunks_count = len(scroll_result)
            
            # Delete points
            if chunks_count > 0:
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.client.delete(
                        collection_name=self.collection_name,
                        points_selector=rest.FilterSelector(
                            filter=count_filter
                        )
                    )
                )
            
            log_operation(
                self.logger,
                "delete_document_complete",
                doc_id=doc_id,
                chunks_deleted=chunks_count
            )
            
            return chunks_count
            
        except Exception as e:
            log_error(
                self.logger,
                e,
                operation="delete_document",
                doc_id=doc_id
            )
            raise
    
    async def get_document_info(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a document's chunks.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Document information or None if not found
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            doc_filter = Filter(
                must=[
                    FieldCondition(
                        key="doc_id",
                        match=MatchValue(value=doc_id)
                    )
                ]
            )
            
            # Scroll through chunks to gather info
            scroll_result, _ = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.scroll(
                    collection_name=self.collection_name,
                    scroll_filter=doc_filter,
                    limit=10000,
                    with_payload=True,
                    with_vectors=False
                )
            )
            
            if not scroll_result:
                return None
            
            # Analyze chunks
            pages = set()
            total_chars = 0
            for point in scroll_result:
                payload = point.payload
                pages.add(payload["page_number"])
                total_chars += len(payload["text"])
            
            return {
                "doc_id": doc_id,
                "chunk_count": len(scroll_result),
                "page_count": len(pages),
                "total_characters": total_chars,
                "pages_covered": sorted(list(pages))
            }
            
        except Exception as e:
            log_error(
                self.logger,
                e,
                operation="get_document_info",
                doc_id=doc_id
            )
            return None
    
    async def health_check(self) -> bool:
        """
        Check if Qdrant is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            if not self._initialized:
                await self.initialize()
            
            # Test collection access
            collection_info = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.get_collection(self.collection_name)
            )
            
            return collection_info is not None
            
        except Exception as e:
            log_error(
                self.logger,
                e,
                operation="vectorstore_health_check"
            )
            return False
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get collection statistics.
        
        Returns:
            Collection statistics
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            collection_info = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.get_collection(self.collection_name)
            )
            
            return {
                "collection_name": self.collection_name,
                "points_count": collection_info.points_count,
                "segments_count": collection_info.segments_count,
                "vector_size": collection_info.config.params.vectors.size,
                "distance": str(collection_info.config.params.vectors.distance),
                "status": str(collection_info.status)
            }
            
        except Exception as e:
            log_error(
                self.logger,
                e,
                operation="get_collection_stats"
            )
            return False
    
    async def list_documents(self) -> List[Dict[str, Any]]:
        """
        List all documents in the collection.
        
        Returns:
            List of document information
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Get all points with payloads to find unique documents
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.scroll(
                    collection_name=self.collection_name,
                    limit=1000,  # Adjust as needed
                    with_payload=True,
                    with_vectors=False
                )
            )
            
            points = response[0]
            documents = {}
            
            # Extract unique documents
            for point in points:
                if point.payload and 'doc_id' in point.payload:
                    doc_id = point.payload['doc_id']
                    if doc_id not in documents:
                        documents[doc_id] = {
                            'doc_id': doc_id,
                            'filename': point.payload.get('filename', ''),
                            'title': point.payload.get('title', ''),
                            'page_count': point.payload.get('page_count', 0)
                        }
            
            return list(documents.values())
            
        except Exception as e:
            log_error(
                self.logger,
                e,
                operation="list_documents"
            )
            return []
    
    async def get_document_info(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific document.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Document information or None if not found
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Search for points with this doc_id
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.scroll(
                    collection_name=self.collection_name,
                    scroll_filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="doc_id",
                                match=models.MatchValue(value=doc_id)
                            )
                        ]
                    ),
                    limit=1,
                    with_payload=True,
                    with_vectors=False
                )
            )
            
            points = response[0]
            if points:
                point = points[0]
                return {
                    'doc_id': doc_id,
                    'filename': point.payload.get('filename', ''),
                    'title': point.payload.get('title', ''),
                    'page_count': point.payload.get('page_count', 0),
                    'creation_date': point.payload.get('creation_date', '')
                }
            
            return None
            
        except Exception as e:
            log_error(
                self.logger,
                e,
                operation="get_document_info",
                doc_id=doc_id
            )
            return None
    
    async def list_documents(self) -> List[dict]:
        """List all documents in the collection."""
        try:
            if not self._initialized:
                await self.initialize()
            
            # Get all points with their payloads
            result = await asyncio.to_thread(
                self.client.scroll,
                collection_name=self.collection_name,
                limit=1000,
                with_payload=True,
                with_vectors=False
            )
            
            points, next_page_offset = result
            
            # Extract unique documents
            documents = {}
            for point in points:
                if hasattr(point, 'payload') and point.payload:
                    doc_id = point.payload.get('doc_id')
                    if doc_id and doc_id not in documents:
                        documents[doc_id] = {
                            'doc_id': doc_id,
                            'filename': point.payload.get('filename', 'Unknown'),
                            'total_pages': point.payload.get('total_pages', 0),
                            'created_at': point.payload.get('created_at', '')
                        }
            
            return list(documents.values())
            
        except Exception as e:
            self.logger.error(f"Error listing documents: {e}")
            return []
    
    async def store_chunks(self, chunks: List[TextChunk]) -> int:
        """
        Store chunks by generating embeddings and upserting to vector store.
        
        Args:
            chunks: List of TextChunk objects
            
        Returns:
            Number of chunks stored
        """
        if not chunks:
            return 0
            
        # Import here to avoid circular imports
        from app.rag.embedder import gemini_embedder
        
        try:
            # Generate embeddings for all chunks
            texts = [chunk.text for chunk in chunks]
            embeddings = await gemini_embedder.embed_texts(texts)
            
            # Store in vector database
            return await self.upsert_chunks(chunks, embeddings)
            
        except Exception as e:
            self.logger.error(f"Error storing chunks: {e}")
            raise
    
    def is_ready(self) -> bool:
        """Check if the vector store is ready to use."""
        return self._initialized


# Global vector store instance
qdrant_store = QdrantVectorStore()