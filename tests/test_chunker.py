"""
Tests for the text chunker module.
"""
import pytest
from app.rag.chunker import SemanticChunker, TextChunk


class TestSemanticChunker:
    """Test cases for SemanticChunker."""
    
    @pytest.fixture
    def chunker(self):
        """Create a chunker instance for testing."""
        return SemanticChunker()
    
    @pytest.fixture
    def sample_pages(self):
        """Sample pages for testing."""
        return [
            (1, "This is the first page. It contains some sample text. The text has multiple sentences."),
            (2, "This is the second page with more content. It also has several sentences for testing. The chunker should handle this properly."),
            (3, "Short page."),
            (4, "This is a longer page with much more content that should be split into multiple chunks. " * 10)
        ]
    
    @pytest.mark.asyncio
    async def test_chunk_pages_basic(self, chunker, sample_pages):
        """Test basic page chunking functionality."""
        doc_id = "test-doc-123"
        
        chunks = await chunker.chunk_pages(sample_pages, doc_id)
        
        # Should produce some chunks
        assert len(chunks) > 0
        
        # All chunks should have the correct doc_id
        assert all(chunk.doc_id == doc_id for chunk in chunks)
        
        # All chunks should have valid page numbers
        assert all(chunk.page_number in [1, 2, 3, 4] for chunk in chunks)
        
        # All chunks should have non-empty text
        assert all(len(chunk.text.strip()) > 0 for chunk in chunks)
    
    @pytest.mark.asyncio
    async def test_chunk_empty_pages(self, chunker):
        """Test chunking with empty pages."""
        doc_id = "test-doc-empty"
        empty_pages = []
        
        chunks = await chunker.chunk_pages(empty_pages, doc_id)
        
        assert len(chunks) == 0
    
    @pytest.mark.asyncio
    async def test_chunk_whitespace_pages(self, chunker):
        """Test chunking with whitespace-only pages."""
        doc_id = "test-doc-whitespace"
        whitespace_pages = [
            (1, "   "),
            (2, "\n\t\n"),
            (3, "")
        ]
        
        chunks = await chunker.chunk_pages(whitespace_pages, doc_id)
        
        assert len(chunks) == 0
    
    def test_split_into_sentences(self, chunker):
        """Test sentence splitting functionality."""
        text = "First sentence. Second sentence! Third sentence? Fourth sentence."
        
        sentences = chunker._split_into_sentences(text)
        
        assert len(sentences) == 4
        assert all(len(s.strip()) > 0 for s in sentences)
    
    def test_split_into_sentences_complex(self, chunker):
        """Test sentence splitting with complex punctuation."""
        text = "Dr. Smith went to the U.S.A. He visited New York City. What did he find? Amazing!"
        
        sentences = chunker._split_into_sentences(text)
        
        # Should handle abbreviations properly
        assert len(sentences) >= 2
    
    def test_get_overlap_text(self, chunker):
        """Test overlap text extraction."""
        text = "This is a test sentence. This is another sentence. Final sentence here."
        
        overlap = chunker._get_overlap_text(text)
        
        assert len(overlap) > 0
        assert len(overlap) <= chunker.overlap_size
    
    def test_estimate_tokens(self, chunker):
        """Test token estimation."""
        text = "This is a test sentence with some words."
        
        token_count = chunker._estimate_tokens(text)
        
        assert token_count > 0
        assert isinstance(token_count, int)
        # Should be roughly text length / 4
        assert token_count <= len(text) // 3
    
    @pytest.mark.asyncio
    async def test_get_chunk_statistics(self, chunker, sample_pages):
        """Test chunk statistics calculation."""
        doc_id = "test-doc-stats"
        
        chunks = await chunker.chunk_pages(sample_pages, doc_id)
        stats = chunker.get_chunk_statistics(chunks)
        
        assert "total_chunks" in stats
        assert "total_characters" in stats
        assert "avg_chunk_size" in stats
        assert "min_chunk_size" in stats
        assert "max_chunk_size" in stats
        assert "pages_covered" in stats
        
        assert stats["total_chunks"] == len(chunks)
        assert stats["total_characters"] > 0
        assert stats["pages_covered"] <= 4
    
    def test_validate_chunks(self, chunker):
        """Test chunk validation."""
        # Create test chunks
        good_chunks = [
            TextChunk(
                chunk_id="chunk_001",
                doc_id="test-doc",
                page_number=1,
                text="This is a valid chunk.",
                start_char=0,
                end_char=23
            ),
            TextChunk(
                chunk_id="chunk_002",
                doc_id="test-doc",
                page_number=1,
                text="Another valid chunk.",
                start_char=24,
                end_char=44
            )
        ]
        
        issues = chunker.validate_chunks(good_chunks)
        assert len(issues) == 0
        
        # Test with empty chunk
        bad_chunks = good_chunks + [
            TextChunk(
                chunk_id="chunk_003",
                doc_id="test-doc",
                page_number=2,
                text="",  # Empty text
                start_char=0,
                end_char=0
            )
        ]
        
        issues = chunker.validate_chunks(bad_chunks)
        assert len(issues) > 0
        assert "empty chunks" in issues[0].lower()
    
    @pytest.mark.asyncio
    async def test_chunk_large_text(self, chunker):
        """Test chunking of very large text."""
        doc_id = "test-doc-large"
        
        # Create a very long page
        long_text = "This is a sentence that will be repeated many times. " * 100
        large_pages = [(1, long_text)]
        
        chunks = await chunker.chunk_pages(large_pages, doc_id)
        
        # Should split into multiple chunks
        assert len(chunks) > 1
        
        # No chunk should exceed max size by too much
        for chunk in chunks:
            assert len(chunk.text) <= chunker.max_chunk_size * 1.2  # 20% tolerance