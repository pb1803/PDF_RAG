"""
Integration tests for chat session functionality.
"""
import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel
from unittest.mock import AsyncMock, patch
import tempfile
import os

# Test database setup
TEST_DB_URL = "sqlite:///test_chat_sessions.db"

@pytest.fixture
def test_db_engine():
    """Create a test database engine."""
    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)
    # Clean up test database file
    try:
        os.remove("test_chat_sessions.db")
    except FileNotFoundError:
        pass

@pytest.fixture
def test_db_session(test_db_engine):
    """Create a test database session."""
    with Session(test_db_engine) as session:
        yield session

@pytest.fixture
def test_app():
    """Create a test FastAPI application."""
    from app.core.db import engine
    from main import app
    
    # Override the database dependency for testing
    def override_get_session():
        engine_test = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
        SQLModel.metadata.create_all(engine_test)
        with Session(engine_test) as session:
            yield session
    
    from app.core.db import get_session
    app.dependency_overrides[get_session] = override_get_session
    
    yield app
    
    # Clean up
    app.dependency_overrides.clear()

@pytest.fixture
def client(test_app):
    """Create a test client."""
    return TestClient(test_app)

@pytest.fixture
def mock_rag_pipeline():
    """Mock RAG pipeline for testing."""
    with patch('app.api.chat_routes.rag_pipeline') as mock:
        mock.answer_question = AsyncMock(return_value={
            "answer": "This is a test answer about machine learning. It's a powerful technology used in AI systems.",
            "sources": ["Page 12", "Page 15"],
            "follow_up": "Would you like to know more about specific ML algorithms?",
            "citations": [
                {"page": 12, "snippet": "Machine learning is a subset of AI..."},
                {"page": 15, "snippet": "ML algorithms can learn from data..."}
            ],
            "used_chunks": [
                {"chunk_id": "test-1", "page": 12, "score": 0.9, "snippet": "Machine learning..."}
            ],
            "doc_id": "test-doc",
            "confidence_score": 0.85
        })
        yield mock

class TestChatSessions:
    """Test cases for chat session management."""
    
    def test_create_chat_session(self, client):
        """Test creating a new chat session."""
        response = client.post("/api/v1/chat/new", json={"title": "Test Chat"})
        
        assert response.status_code == 200
        data = response.json()
        
        assert "session_id" in data
        assert data["title"] == "Test Chat"
        assert "created_at" in data
        assert len(data["session_id"]) > 0  # UUID should be non-empty
    
    def test_create_chat_session_default_title(self, client):
        """Test creating a chat session with default title."""
        response = client.post("/api/v1/chat/new", json={})
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["title"] == "New chat"
    
    def test_list_chat_sessions_empty(self, client):
        """Test listing chat sessions when none exist."""
        response = client.get("/api/v1/chat/list")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_list_chat_sessions_with_data(self, client):
        """Test listing chat sessions with existing data."""
        # Create a chat session first
        create_response = client.post("/api/v1/chat/new", json={"title": "Physics Discussion"})
        session_id = create_response.json()["session_id"]
        
        # List sessions
        response = client.get("/api/v1/chat/list")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 1
        assert data[0]["session_id"] == session_id
        assert data[0]["title"] == "Physics Discussion"
        assert "last_message_snippet" in data[0]
        assert "updated_at" in data[0]
    
    def test_get_chat_session(self, client):
        """Test retrieving a specific chat session."""
        # Create a chat session
        create_response = client.post("/api/v1/chat/new", json={"title": "Math Help"})
        session_id = create_response.json()["session_id"]
        
        # Get the session
        response = client.get(f"/api/v1/chat/{session_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "session" in data
        assert "messages" in data
        assert data["session"]["id"] == session_id
        assert data["session"]["title"] == "Math Help"
        assert isinstance(data["messages"], list)
        assert len(data["messages"]) == 0  # No messages yet
    
    def test_get_nonexistent_chat_session(self, client):
        """Test retrieving a non-existent chat session."""
        response = client.get("/api/v1/chat/fake-id")
        
        assert response.status_code == 404
        assert "Chat session not found" in response.json()["detail"]
    
    def test_ask_question_in_chat(self, client, mock_rag_pipeline):
        """Test asking a question in a chat session."""
        # Create a chat session
        create_response = client.post("/api/v1/chat/new", json={"title": "ML Discussion"})
        session_id = create_response.json()["session_id"]
        
        # Ask a question
        question_data = {
            "question": "What is machine learning?",
            "doc_id": "test-doc",
            "top_k": 5
        }
        
        response = client.post(f"/api/v1/chat/{session_id}/ask", json=question_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "answer" in data
        assert "sources" in data
        assert "follow_up" in data
        assert "session_id" in data
        assert data["session_id"] == session_id
        assert "processing_time_seconds" in data
        
        # Verify RAG pipeline was called
        mock_rag_pipeline.answer_question.assert_called_once()
    
    def test_ask_question_with_chat_history(self, client, mock_rag_pipeline):
        """Test asking questions with chat history context."""
        # Create a chat session
        create_response = client.post("/api/v1/chat/new", json={"title": "History Test"})
        session_id = create_response.json()["session_id"]
        
        # Ask first question
        response1 = client.post(f"/api/v1/chat/{session_id}/ask", json={
            "question": "What is AI?",
            "doc_id": "test-doc"
        })
        assert response1.status_code == 200
        
        # Ask follow-up question
        response2 = client.post(f"/api/v1/chat/{session_id}/ask", json={
            "question": "How does it work?",
            "doc_id": "test-doc"
        })
        assert response2.status_code == 200
        
        # Verify chat history was passed to RAG pipeline
        assert mock_rag_pipeline.answer_question.call_count == 2
        
        # Check that the second call had chat history
        second_call_args = mock_rag_pipeline.answer_question.call_args_list[1]
        assert "chat_history" in second_call_args.kwargs
        chat_history = second_call_args.kwargs["chat_history"]
        
        assert len(chat_history) >= 2  # Should have user and assistant messages
        assert any(msg["role"] == "user" and "What is AI?" in msg["text"] for msg in chat_history)
        assert any(msg["role"] == "assistant" for msg in chat_history)
    
    def test_ask_question_nonexistent_session(self, client):
        """Test asking a question in a non-existent session."""
        response = client.post("/api/v1/chat/fake-session/ask", json={
            "question": "Test question",
            "doc_id": "test-doc"
        })
        
        assert response.status_code == 404
        assert "Chat session not found" in response.json()["detail"]
    
    def test_rename_chat_session(self, client):
        """Test renaming a chat session."""
        # Create a chat session
        create_response = client.post("/api/v1/chat/new", json={"title": "Old Title"})
        session_id = create_response.json()["session_id"]
        
        # Rename it
        response = client.post(f"/api/v1/chat/{session_id}/rename", json={
            "title": "New Title"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["session_id"] == session_id
        assert data["title"] == "New Title"
        
        # Verify the rename worked
        get_response = client.get(f"/api/v1/chat/{session_id}")
        assert get_response.json()["session"]["title"] == "New Title"
    
    def test_rename_nonexistent_session(self, client):
        """Test renaming a non-existent session."""
        response = client.post("/api/v1/chat/fake-id/rename", json={
            "title": "New Title"
        })
        
        assert response.status_code == 404
        assert "Chat session not found" in response.json()["detail"]
    
    def test_delete_chat_session(self, client, mock_rag_pipeline):
        """Test deleting a chat session and its messages."""
        # Create a chat session
        create_response = client.post("/api/v1/chat/new", json={"title": "To Delete"})
        session_id = create_response.json()["session_id"]
        
        # Add some messages
        client.post(f"/api/v1/chat/{session_id}/ask", json={
            "question": "Test question 1",
            "doc_id": "test-doc"
        })
        client.post(f"/api/v1/chat/{session_id}/ask", json={
            "question": "Test question 2",
            "doc_id": "test-doc"
        })
        
        # Delete the session
        response = client.delete(f"/api/v1/chat/{session_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["session_id"] == session_id
        assert data["messages_deleted"] == 4  # 2 user + 2 assistant messages
        
        # Verify session is gone
        get_response = client.get(f"/api/v1/chat/{session_id}")
        assert get_response.status_code == 404
    
    def test_delete_nonexistent_session(self, client):
        """Test deleting a non-existent session."""
        response = client.delete("/api/v1/chat/fake-id")
        
        assert response.status_code == 404
        assert "Chat session not found" in response.json()["detail"]
    
    def test_get_chat_stats(self, client, mock_rag_pipeline):
        """Test getting chat session statistics."""
        # Create a chat session
        create_response = client.post("/api/v1/chat/new", json={"title": "Stats Test"})
        session_id = create_response.json()["session_id"]
        
        # Add some messages
        client.post(f"/api/v1/chat/{session_id}/ask", json={
            "question": "Question 1",
            "doc_id": "test-doc"
        })
        client.post(f"/api/v1/chat/{session_id}/ask", json={
            "question": "Question 2",
            "doc_id": "test-doc"
        })
        
        # Get stats
        response = client.get(f"/api/v1/chat/{session_id}/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["session_id"] == session_id
        assert data["title"] == "Stats Test"
        assert data["total_messages"] == 4  # 2 user + 2 assistant
        assert data["user_messages"] == 2
        assert data["assistant_messages"] == 2
        assert "first_message_at" in data
        assert "last_message_at" in data
        assert "created_at" in data
        assert "updated_at" in data

class TestChatMemoryTrimming:
    """Test chat memory management functionality."""
    
    def test_memory_trimming_last_n_messages(self, client, mock_rag_pipeline):
        """Test that only the last N messages are used for context."""
        # Create a chat session
        create_response = client.post("/api/v1/chat/new", json={"title": "Memory Test"})
        session_id = create_response.json()["session_id"]
        
        # Add many messages (more than the limit)
        for i in range(15):  # Add 15 questions (30 total messages)
            client.post(f"/api/v1/chat/{session_id}/ask", json={
                "question": f"Question number {i+1}",
                "doc_id": "test-doc"
            })
        
        # Ask one more question to trigger memory usage
        client.post(f"/api/v1/chat/{session_id}/ask", json={
            "question": "Final question - check memory",
            "doc_id": "test-doc"
        })
        
        # Check that the last call to RAG pipeline had limited history
        last_call_args = mock_rag_pipeline.answer_question.call_args_list[-1]
        chat_history = last_call_args.kwargs["chat_history"]
        
        # Should have at most 10 messages (the limit set in chat_routes.py)
        assert len(chat_history) <= 10
        
        # Should contain recent messages
        assert any("Final question" in msg["text"] for msg in chat_history)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])