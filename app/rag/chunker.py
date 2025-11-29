"""
Text chunking with semantic boundaries and metadata preservation.
"""
import re
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from app.core.config import settings
from app.core.logger import rag_logger, log_operation


@dataclass
class TextChunk:
    """Represents a text chunk with metadata."""
    chunk_id: str
    doc_id: str
    page_number: int
    text: str
    start_char: int
    end_char: int
    token_count: Optional[int] = None


class SemanticChunker:
    """
    Semantic text chunker that preserves sentence boundaries and maintains metadata.
    """
    
    def __init__(self):
        self.logger = rag_logger
        self.max_chunk_size = settings.max_chunk_size
        self.min_chunk_size = settings.min_chunk_size
        self.overlap_size = settings.chunk_overlap
    
    async def chunk_pages(
        self, 
        pages: List[Tuple[int, str]], 
        doc_id: str
    ) -> List[TextChunk]:
        """
        Chunk pages into semantic chunks with metadata.
        
        Args:
            pages: List of (page_number, page_text) tuples
            doc_id: Document identifier
            
        Returns:
            List of TextChunk objects
        """
        log_operation(
            self.logger,
            "chunking_start",
            doc_id=doc_id,
            total_pages=len(pages)
        )
        
        all_chunks = []
        chunk_counter = 0
        
        for page_num, page_text in pages:
            if not page_text.strip():
                continue
            
            page_chunks = self._chunk_page_text(
                page_text, 
                page_num, 
                doc_id, 
                chunk_counter
            )
            
            all_chunks.extend(page_chunks)
            chunk_counter += len(page_chunks)
        
        log_operation(
            self.logger,
            "chunking_complete",
            doc_id=doc_id,
            total_chunks=len(all_chunks),
            avg_chunk_size=sum(len(c.text) for c in all_chunks) // max(len(all_chunks), 1)
        )
        
        return all_chunks
    
    def _chunk_page_text(
        self, 
        text: str, 
        page_num: int, 
        doc_id: str, 
        start_chunk_id: int
    ) -> List[TextChunk]:
        """
        Chunk text from a single page.
        
        Args:
            text: Page text to chunk
            page_num: Page number
            doc_id: Document ID
            start_chunk_id: Starting chunk ID number
            
        Returns:
            List of TextChunk objects for the page
        """
        # Split into sentences
        sentences = self._split_into_sentences(text)
        
        chunks = []
        current_chunk = ""
        current_start_char = 0
        chunk_id = start_chunk_id
        
        for i, sentence in enumerate(sentences):
            # Test adding this sentence
            test_chunk = current_chunk + (" " if current_chunk else "") + sentence
            
            # Check if we should start a new chunk
            if (len(test_chunk) > self.max_chunk_size and 
                len(current_chunk) >= self.min_chunk_size):
                
                # Save current chunk
                if current_chunk.strip():
                    chunk_obj = TextChunk(
                        chunk_id=f"{doc_id}_chunk_{chunk_id:04d}",
                        doc_id=doc_id,
                        page_number=page_num,
                        text=current_chunk.strip(),
                        start_char=current_start_char,
                        end_char=current_start_char + len(current_chunk),
                        token_count=self._estimate_tokens(current_chunk)
                    )
                    chunks.append(chunk_obj)
                    chunk_id += 1
                
                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk)
                current_chunk = overlap_text + (" " if overlap_text else "") + sentence
                current_start_char = max(0, 
                    current_start_char + len(chunks[-1].text if chunks else "") - len(overlap_text)
                )
            else:
                # Add sentence to current chunk
                current_chunk = test_chunk
        
        # Add final chunk if it has content
        if current_chunk.strip():
            chunk_obj = TextChunk(
                chunk_id=f"{doc_id}_chunk_{chunk_id:04d}",
                doc_id=doc_id,
                page_number=page_num,
                text=current_chunk.strip(),
                start_char=current_start_char,
                end_char=current_start_char + len(current_chunk),
                token_count=self._estimate_tokens(current_chunk)
            )
            chunks.append(chunk_obj)
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences using regex patterns.
        
        Args:
            text: Text to split
            
        Returns:
            List of sentences
        """
        # Enhanced sentence splitting pattern
        # Handles common abbreviations and edge cases
        sentence_endings = r'[.!?]+(?=\s+[A-Z]|$)'
        
        # Split on sentence endings
        sentences = re.split(sentence_endings, text)
        
        # Clean and filter sentences
        clean_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 10:  # Minimum sentence length
                clean_sentences.append(sentence)
        
        # If no proper sentences found, split by length
        if not clean_sentences:
            clean_sentences = self._split_by_length(text)
        
        return clean_sentences
    
    def _split_by_length(self, text: str, max_length: int = 200) -> List[str]:
        """
        Fallback splitting by length at word boundaries.
        
        Args:
            text: Text to split
            max_length: Maximum chunk length
            
        Returns:
            List of text segments
        """
        words = text.split()
        segments = []
        current_segment = []
        current_length = 0
        
        for word in words:
            word_length = len(word) + 1  # +1 for space
            
            if current_length + word_length > max_length and current_segment:
                segments.append(" ".join(current_segment))
                current_segment = [word]
                current_length = len(word)
            else:
                current_segment.append(word)
                current_length += word_length
        
        if current_segment:
            segments.append(" ".join(current_segment))
        
        return segments
    
    def _get_overlap_text(self, text: str) -> str:
        """
        Get overlap text for chunk boundaries.
        
        Args:
            text: Source text
            
        Returns:
            Overlap text
        """
        if len(text) <= self.overlap_size:
            return text
        
        # Try to break at sentence boundary
        sentences = self._split_into_sentences(text)
        if len(sentences) > 1:
            # Take last sentence if it fits in overlap
            last_sentence = sentences[-1]
            if len(last_sentence) <= self.overlap_size:
                return last_sentence
        
        # Fallback to character-based overlap at word boundary
        overlap_text = text[-self.overlap_size:]
        
        # Find word boundary
        space_idx = overlap_text.find(' ')
        if space_idx > 0:
            overlap_text = overlap_text[space_idx + 1:]
        
        return overlap_text
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Estimated token count
        """
        # Simple heuristic: ~4 characters per token for English
        return max(1, len(text) // 4)
    
    def get_chunk_statistics(self, chunks: List[TextChunk]) -> Dict[str, Any]:
        """
        Calculate statistics for a list of chunks.
        
        Args:
            chunks: List of TextChunk objects
            
        Returns:
            Statistics dictionary
        """
        if not chunks:
            return {
                "total_chunks": 0,
                "total_characters": 0,
                "avg_chunk_size": 0,
                "min_chunk_size": 0,
                "max_chunk_size": 0,
                "pages_covered": 0
            }
        
        sizes = [len(chunk.text) for chunk in chunks]
        pages = set(chunk.page_number for chunk in chunks)
        
        return {
            "total_chunks": len(chunks),
            "total_characters": sum(sizes),
            "avg_chunk_size": sum(sizes) // len(sizes),
            "min_chunk_size": min(sizes),
            "max_chunk_size": max(sizes),
            "pages_covered": len(pages),
            "chunks_per_page": len(chunks) / len(pages) if pages else 0
        }
    
    def validate_chunks(self, chunks: List[TextChunk]) -> List[str]:
        """
        Validate chunk list and return any issues found.
        
        Args:
            chunks: List of chunks to validate
            
        Returns:
            List of validation error messages
        """
        issues = []
        
        if not chunks:
            issues.append("No chunks provided")
            return issues
        
        # Check for empty chunks
        empty_chunks = [c.chunk_id for c in chunks if not c.text.strip()]
        if empty_chunks:
            issues.append(f"Empty chunks found: {empty_chunks}")
        
        # Check for oversized chunks
        oversized = [c.chunk_id for c in chunks if len(c.text) > self.max_chunk_size * 1.2]
        if oversized:
            issues.append(f"Oversized chunks (>20% max): {oversized}")
        
        # Check for duplicate chunk IDs
        chunk_ids = [c.chunk_id for c in chunks]
        if len(chunk_ids) != len(set(chunk_ids)):
            issues.append("Duplicate chunk IDs found")
        
        return issues


# Global chunker instance
semantic_chunker = SemanticChunker()