"""
High-level document retrieval with re-ranking and filtering.
"""
import asyncio
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from app.core.config import settings
from app.core.logger import rag_logger, log_operation, log_error
from app.rag.embedder import gemini_embedder
from app.rag.vectorstore import qdrant_store


@dataclass
class RetrievedChunk:
    """Represents a retrieved chunk with metadata and scores."""
    chunk_id: str
    text: str
    page_number: int
    similarity_score: float
    rank_score: Optional[float] = None
    start_char: int = 0
    end_char: int = 0
    doc_id: Optional[str] = None


class DocumentRetriever:
    """
    High-level document retriever with similarity search and re-ranking.
    """
    
    def __init__(self):
        self.logger = rag_logger
        self.embedder = gemini_embedder
        self.vectorstore = qdrant_store
    
    async def retrieve_chunks(
        self,
        query: str,
        doc_id: str,
        top_k: Optional[int] = None,
        rerank: bool = True,
        final_k: Optional[int] = None
    ) -> List[RetrievedChunk]:
        """
        Retrieve and rank relevant chunks for a query.
        
        Args:
            query: User query
            doc_id: Document ID to search
            top_k: Number of initial chunks to retrieve
            rerank: Whether to apply re-ranking
            final_k: Final number of chunks to return after re-ranking
            
        Returns:
            List of retrieved and ranked chunks
        """
        top_k = top_k or settings.top_k_retrieval
        final_k = final_k or settings.top_k_final
        
        log_operation(
            self.logger,
            "retrieval_start",
            doc_id=doc_id,
            query_length=len(query),
            top_k=top_k,
            final_k=final_k
        )
        
        try:
            # Generate query embedding
            query_embedding = await self.embedder.embed_query(query)
            
            # Search similar chunks
            search_results = await self.vectorstore.search_similar_chunks(
                query_embedding=query_embedding,
                doc_id=doc_id,
                top_k=top_k,
                score_threshold=0.0  # Let re-ranking handle filtering
            )
            
            if not search_results:
                log_operation(
                    self.logger,
                    "retrieval_no_results",
                    doc_id=doc_id,
                    query=query
                )
                return []
            
            # Convert to RetrievedChunk objects
            chunks = [
                RetrievedChunk(
                    chunk_id=result["chunk_id"],
                    text=result["text"],
                    page_number=result["page_number"],
                    similarity_score=result["score"],
                    start_char=result["start_char"],
                    end_char=result["end_char"],
                    doc_id=result.get("doc_id", doc_id)
                )
                for result in search_results
            ]
            
            # Apply re-ranking if requested
            if rerank:
                chunks = await self._rerank_chunks(query, chunks)
            
            # Limit final results
            final_chunks = chunks[:final_k]
            
            log_operation(
                self.logger,
                "retrieval_complete",
                doc_id=doc_id,
                initial_results=len(search_results),
                final_results=len(final_chunks),
                top_score=final_chunks[0].similarity_score if final_chunks else 0.0
            )
            
            return final_chunks
            
        except Exception as e:
            log_error(
                self.logger,
                e,
                operation="retrieve_chunks",
                doc_id=doc_id,
                query=query[:100]  # Log first 100 chars of query
            )
            raise
    
    async def _rerank_chunks(
        self, 
        query: str, 
        chunks: List[RetrievedChunk]
    ) -> List[RetrievedChunk]:
        """
        Re-rank chunks using multiple signals.
        
        Args:
            query: User query
            chunks: Initial chunks to re-rank
            
        Returns:
            Re-ranked chunks
        """
        if not chunks:
            return chunks
        
        log_operation(
            self.logger,
            "reranking_start",
            chunk_count=len(chunks)
        )
        
        try:
            # Calculate re-ranking scores
            for chunk in chunks:
                rank_score = await self._calculate_rank_score(query, chunk)
                chunk.rank_score = rank_score
            
            # Sort by combined score
            ranked_chunks = sorted(
                chunks,
                key=lambda c: self._combine_scores(c),
                reverse=True
            )
            
            log_operation(
                self.logger,
                "reranking_complete",
                chunk_count=len(ranked_chunks)
            )
            
            return ranked_chunks
            
        except Exception as e:
            log_error(
                self.logger,
                e,
                operation="rerank_chunks"
            )
            # Return original order on error
            return chunks
    
    async def _calculate_rank_score(
        self, 
        query: str, 
        chunk: RetrievedChunk
    ) -> float:
        """
        Calculate re-ranking score for a chunk.
        
        Args:
            query: User query
            chunk: Chunk to score
            
        Returns:
            Re-ranking score (0-1)
        """
        scores = []
        
        # 1. Keyword overlap score
        keyword_score = self._calculate_keyword_overlap(query, chunk.text)
        scores.append(keyword_score * 0.4)  # 40% weight
        
        # 2. Text length preference (moderate length preferred)
        length_score = self._calculate_length_score(chunk.text)
        scores.append(length_score * 0.2)  # 20% weight
        
        # 3. Position score (earlier pages slightly preferred)
        position_score = self._calculate_position_score(chunk.page_number)
        scores.append(position_score * 0.1)  # 10% weight
        
        # 4. Similarity score (normalized)
        sim_score = min(chunk.similarity_score, 1.0)  # Cap at 1.0
        scores.append(sim_score * 0.3)  # 30% weight
        
        return sum(scores)
    
    def _calculate_keyword_overlap(self, query: str, text: str) -> float:
        """
        Calculate keyword overlap score between query and text.
        
        Args:
            query: User query
            text: Chunk text
            
        Returns:
            Keyword overlap score (0-1)
        """
        # Normalize and extract keywords
        query_keywords = self._extract_keywords(query.lower())
        text_keywords = self._extract_keywords(text.lower())
        
        if not query_keywords:
            return 0.0
        
        # Calculate overlap
        overlapping = query_keywords.intersection(text_keywords)
        overlap_ratio = len(overlapping) / len(query_keywords)
        
        # Boost for exact phrase matches
        query_clean = re.sub(r'[^\w\s]', '', query.lower())
        text_clean = re.sub(r'[^\w\s]', '', text.lower())
        
        if query_clean in text_clean:
            overlap_ratio += 0.3
        
        return min(overlap_ratio, 1.0)
    
    def _extract_keywords(self, text: str) -> set:
        """
        Extract meaningful keywords from text.
        
        Args:
            text: Input text
            
        Returns:
            Set of keywords
        """
        # Simple keyword extraction
        # Remove punctuation and split
        words = re.findall(r'\b[a-z]+\b', text.lower())
        
        # Filter out common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we',
            'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'its',
            'our', 'their'
        }
        
        # Keep words that are at least 3 characters and not stop words
        keywords = {w for w in words if len(w) >= 3 and w not in stop_words}
        
        return keywords
    
    def _calculate_length_score(self, text: str) -> float:
        """
        Calculate score based on text length (moderate length preferred).
        
        Args:
            text: Chunk text
            
        Returns:
            Length score (0-1)
        """
        length = len(text)
        optimal_length = 400  # Characters
        
        if length <= optimal_length:
            return length / optimal_length
        else:
            # Penalize very long chunks
            excess = length - optimal_length
            penalty = min(excess / optimal_length, 0.5)  # Max 50% penalty
            return 1.0 - penalty
    
    def _calculate_position_score(self, page_number: int) -> float:
        """
        Calculate score based on page position (earlier pages slightly preferred).
        
        Args:
            page_number: Page number (1-indexed)
            
        Returns:
            Position score (0-1)
        """
        # Slight preference for earlier pages
        if page_number <= 5:
            return 1.0
        elif page_number <= 20:
            return 0.9
        else:
            return 0.8
    
    def _combine_scores(self, chunk: RetrievedChunk) -> float:
        """
        Combine similarity and rank scores.
        
        Args:
            chunk: Chunk with scores
            
        Returns:
            Combined score
        """
        if chunk.rank_score is None:
            return chunk.similarity_score
        
        # Weighted combination
        return (chunk.similarity_score * 0.6) + (chunk.rank_score * 0.4)
    
    async def get_chunk_context(
        self,
        chunks: List[RetrievedChunk],
        doc_id: str,
        context_window: int = 1
    ) -> List[RetrievedChunk]:
        """
        Expand chunks with surrounding context.
        
        Args:
            chunks: Original chunks
            doc_id: Document ID
            context_window: Number of chunks before/after to include
            
        Returns:
            Chunks with expanded context
        """
        if not chunks or context_window <= 0:
            return chunks
        
        try:
            # Get all chunks for the document sorted by page and position
            all_chunks = await self._get_all_document_chunks(doc_id)
            
            if not all_chunks:
                return chunks
            
            # Find context for each chunk
            expanded_chunks = []
            
            for chunk in chunks:
                # Find chunk in full list
                chunk_idx = self._find_chunk_index(chunk, all_chunks)
                
                if chunk_idx is not None:
                    # Get surrounding chunks
                    start_idx = max(0, chunk_idx - context_window)
                    end_idx = min(len(all_chunks), chunk_idx + context_window + 1)
                    
                    context_chunks = all_chunks[start_idx:end_idx]
                    
                    # Combine context
                    combined_text = " ".join(c.text for c in context_chunks)
                    
                    # Create expanded chunk
                    expanded_chunk = RetrievedChunk(
                        chunk_id=chunk.chunk_id,
                        text=combined_text,
                        page_number=chunk.page_number,
                        similarity_score=chunk.similarity_score,
                        rank_score=chunk.rank_score,
                        start_char=context_chunks[0].start_char,
                        end_char=context_chunks[-1].end_char
                    )
                    expanded_chunks.append(expanded_chunk)
                else:
                    # Keep original if not found
                    expanded_chunks.append(chunk)
            
            return expanded_chunks
            
        except Exception as e:
            log_error(
                self.logger,
                e,
                operation="get_chunk_context",
                doc_id=doc_id
            )
            # Return original chunks on error
            return chunks
    
    async def _get_all_document_chunks(self, doc_id: str) -> List[RetrievedChunk]:
        """
        Get all chunks for a document.
        
        Args:
            doc_id: Document ID
            
        Returns:
            All document chunks sorted by position
        """
        # This would require a more complex implementation to retrieve all chunks
        # For now, return empty list to avoid errors
        return []
    
    def _find_chunk_index(
        self, 
        target_chunk: RetrievedChunk, 
        all_chunks: List[RetrievedChunk]
    ) -> Optional[int]:
        """
        Find the index of a chunk in a list.
        
        Args:
            target_chunk: Chunk to find
            all_chunks: List to search in
            
        Returns:
            Index if found, None otherwise
        """
        for i, chunk in enumerate(all_chunks):
            if chunk.chunk_id == target_chunk.chunk_id:
                return i
        return None


# Global retriever instance
document_retriever = DocumentRetriever()