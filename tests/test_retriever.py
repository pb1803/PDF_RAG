"""
Tests for the document retriever module.
"""
import pytest
from unittest.mock import AsyncMock, Mock
from app.rag.retriever import DocumentRetriever, RetrievedChunk


class TestDocumentRetriever:
    """Test cases for DocumentRetriever."""
    
    @pytest.fixture
    def retriever(self):
        """Create a retriever instance for testing."""
        retriever = DocumentRetriever()
        # Mock the embedder and vectorstore to avoid external dependencies
        retriever.embedder = AsyncMock()
        retriever.vectorstore = AsyncMock()
        return retriever
    
    @pytest.fixture
    def sample_chunks(self):
        """Sample retrieved chunks for testing."""
        return [
            RetrievedChunk(
                chunk_id="chunk_001",
                text="This is about machine learning algorithms and their applications.",
                page_number=1,
                similarity_score=0.95,
                start_char=0,
                end_char=65
            ),
            RetrievedChunk(
                chunk_id="chunk_002", 
                text="Deep learning is a subset of machine learning that uses neural networks.",
                page_number=2,
                similarity_score=0.87,
                start_char=100,
                end_char=173
            ),
            RetrievedChunk(
                chunk_id="chunk_003",
                text="Natural language processing involves understanding human language.",
                page_number=3,
                similarity_score=0.82,
                start_char=200,
                end_char=265
            ),
            RetrievedChunk(
                chunk_id="chunk_004",
                text="Computer vision focuses on helping computers understand visual information.",
                page_number=1,
                similarity_score=0.78,
                start_char=300,
                end_char=374
            )
        ]
    
    @pytest.mark.asyncio
    async def test_retrieve_chunks_basic(self, retriever, sample_chunks):
        """Test basic chunk retrieval functionality."""
        query = "machine learning"
        doc_id = "test-doc-123"
        
        # Mock embedder response
        retriever.embedder.embed_query.return_value = [0.1] * 768
        
        # Mock vectorstore response
        mock_search_results = [
            {
                "chunk_id": chunk.chunk_id,
                "text": chunk.text,
                "page_number": chunk.page_number,
                "score": chunk.similarity_score,
                "start_char": chunk.start_char,
                "end_char": chunk.end_char,
                "doc_id": doc_id
            }
            for chunk in sample_chunks
        ]
        retriever.vectorstore.search_similar_chunks.return_value = mock_search_results
        
        # Test retrieval
        results = await retriever.retrieve_chunks(query, doc_id, top_k=4, rerank=False)
        
        assert len(results) == 4
        assert all(isinstance(chunk, RetrievedChunk) for chunk in results)
        assert all(chunk.doc_id == doc_id for chunk in results)  # Should match doc_id
        
        # Verify embedder was called
        retriever.embedder.embed_query.assert_called_once_with(query)
        
        # Verify vectorstore was called
        retriever.vectorstore.search_similar_chunks.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_retrieve_chunks_no_results(self, retriever):
        """Test retrieval when no chunks are found."""
        query = "nonexistent topic"
        doc_id = "test-doc-empty"
        
        # Mock empty response
        retriever.embedder.embed_query.return_value = [0.1] * 768
        retriever.vectorstore.search_similar_chunks.return_value = []
        
        results = await retriever.retrieve_chunks(query, doc_id)
        
        assert len(results) == 0
    
    @pytest.mark.asyncio
    async def test_retrieve_chunks_with_reranking(self, retriever, sample_chunks):
        """Test retrieval with re-ranking enabled."""
        query = "machine learning algorithms"
        doc_id = "test-doc-123"
        
        # Mock responses
        retriever.embedder.embed_query.return_value = [0.1] * 768
        mock_search_results = [
            {
                "chunk_id": chunk.chunk_id,
                "text": chunk.text,
                "page_number": chunk.page_number,
                "score": chunk.similarity_score,
                "start_char": chunk.start_char,
                "end_char": chunk.end_char
            }
            for chunk in sample_chunks
        ]
        retriever.vectorstore.search_similar_chunks.return_value = mock_search_results
        
        results = await retriever.retrieve_chunks(
            query, doc_id, top_k=4, rerank=True, final_k=2
        )
        
        # Should limit to final_k results
        assert len(results) <= 2
        
        # Results should have rank_score set
        for chunk in results:
            assert chunk.rank_score is not None
    
    def test_calculate_keyword_overlap(self, retriever):
        """Test keyword overlap calculation."""
        query = "machine learning algorithms"
        text = "This text discusses machine learning and various algorithms used in AI."
        
        score = retriever._calculate_keyword_overlap(query, text)
        
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should have good overlap
    
    def test_calculate_keyword_overlap_no_match(self, retriever):
        """Test keyword overlap with no matches."""
        query = "quantum computing"
        text = "This text is about cooking recipes and food preparation."
        
        score = retriever._calculate_keyword_overlap(query, text)
        
        assert score == 0.0
    
    def test_extract_keywords(self, retriever):
        """Test keyword extraction."""
        text = "This is a test about machine learning and artificial intelligence."
        
        keywords = retriever._extract_keywords(text)
        
        assert isinstance(keywords, set)
        assert len(keywords) > 0
        assert "machine" in keywords
        assert "learning" in keywords
        assert "artificial" in keywords
        assert "intelligence" in keywords
        
        # Stop words should be filtered out
        assert "this" not in keywords
        assert "and" not in keywords
        assert "is" not in keywords
    
    def test_calculate_length_score(self, retriever):
        """Test text length scoring."""
        # Optimal length text
        optimal_text = "This is text of optimal length." * 5  # ~160 chars
        score_optimal = retriever._calculate_length_score(optimal_text)
        
        # Very short text
        short_text = "Short."
        score_short = retriever._calculate_length_score(short_text)
        
        # Very long text
        long_text = "This is very long text. " * 100  # ~2400 chars
        score_long = retriever._calculate_length_score(long_text)
        
        assert 0.0 <= score_optimal <= 1.0
        assert 0.0 <= score_short <= 1.0
        assert 0.0 <= score_long <= 1.0
        
        # Optimal should score higher than very short
        assert score_optimal > score_short
    
    def test_calculate_position_score(self, retriever):
        """Test page position scoring."""
        score_page_1 = retriever._calculate_position_score(1)
        score_page_10 = retriever._calculate_position_score(10)
        score_page_50 = retriever._calculate_position_score(50)
        
        assert 0.0 <= score_page_1 <= 1.0
        assert 0.0 <= score_page_10 <= 1.0
        assert 0.0 <= score_page_50 <= 1.0
        
        # Earlier pages should score higher
        assert score_page_1 >= score_page_10
        assert score_page_10 >= score_page_50
    
    def test_combine_scores(self, retriever):
        """Test score combination."""
        chunk = RetrievedChunk(
            chunk_id="test_chunk",
            text="Test text",
            page_number=1,
            similarity_score=0.8,
            rank_score=0.7
        )
        
        combined = retriever._combine_scores(chunk)
        
        assert 0.0 <= combined <= 1.0
        
        # Should be weighted combination
        expected = (0.8 * 0.6) + (0.7 * 0.4)
        assert abs(combined - expected) < 0.01
    
    def test_combine_scores_no_rank(self, retriever):
        """Test score combination without rank score."""
        chunk = RetrievedChunk(
            chunk_id="test_chunk",
            text="Test text",
            page_number=1,
            similarity_score=0.8,
            rank_score=None
        )
        
        combined = retriever._combine_scores(chunk)
        
        assert combined == 0.8  # Should return similarity score only
    
    @pytest.mark.asyncio
    async def test_calculate_rank_score(self, retriever):
        """Test rank score calculation."""
        query = "machine learning"
        chunk = RetrievedChunk(
            chunk_id="test_chunk",
            text="Machine learning is a powerful tool for data analysis and prediction.",
            page_number=2,
            similarity_score=0.85
        )
        
        rank_score = await retriever._calculate_rank_score(query, chunk)
        
        assert 0.0 <= rank_score <= 1.0
        assert rank_score > 0  # Should have some score due to keyword overlap
    
    def test_find_chunk_index(self, retriever, sample_chunks):
        """Test finding chunk index in list."""
        target_chunk = sample_chunks[1]  # Second chunk
        
        index = retriever._find_chunk_index(target_chunk, sample_chunks)
        
        assert index == 1
    
    def test_find_chunk_index_not_found(self, retriever, sample_chunks):
        """Test finding chunk index when not in list."""
        target_chunk = RetrievedChunk(
            chunk_id="nonexistent",
            text="Not found",
            page_number=999,
            similarity_score=0.0
        )
        
        index = retriever._find_chunk_index(target_chunk, sample_chunks)
        
        assert index is None