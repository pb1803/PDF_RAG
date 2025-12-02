"""
Chat session API endpoints.
"""
import time
from fastapi import APIRouter, Depends, HTTPException, Body
from uuid import uuid4
from typing import List
from sqlmodel import Session, select, delete, text
from datetime import datetime

from app.core.db import get_session
from app.core.logger import api_logger, log_operation, log_error
from app.models.chat_models import (
    Chat, Message, ChatCreate, ChatResponse, 
    ChatListItem, AskRequest, RenameRequest
)
from app.rag.rag_pipeline import rag_pipeline
from app.schemas.responses import ErrorResponse

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


@router.post(
    "/new",
    response_model=ChatResponse,
    responses={500: {"model": ErrorResponse}}
)
def create_chat(
    request: ChatCreate = Body(default_factory=ChatCreate),
    db: Session = Depends(get_session)
):
    """
    Create a new chat session.
    
    Returns:
        ChatResponse with session_id, title, and timestamps
    """
    try:
        chat_id = str(uuid4())
        chat = Chat(
            id=chat_id,
            title=request.title or "New chat",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(chat)
        db.commit()
        db.refresh(chat)
        
        log_operation(
            api_logger,
            "chat_created",
            session_id=chat_id,
            title=chat.title
        )
        
        return ChatResponse(
            session_id=chat.id,
            title=chat.title,
            created_at=chat.created_at,
            updated_at=chat.updated_at
        )
        
    except Exception as e:
        log_error(api_logger, e, operation="create_chat")
        raise HTTPException(
            status_code=500,
            detail="Failed to create chat session"
        )


@router.get(
    "/list",
    response_model=List[ChatListItem],
    responses={500: {"model": ErrorResponse}}
)
def list_chats(db: Session = Depends(get_session)):
    """
    List all chat sessions with metadata and last message snippets.
    
    Returns:
        List of chat sessions ordered by last update time
    """
    try:
        chats = db.exec(
            select(Chat).order_by(Chat.updated_at.desc())
        ).all()
        
        result = []
        for chat in chats:
            # Get last message snippet
            last_msg = db.exec(
                select(Message)
                .where(Message.chat_id == chat.id)
                .order_by(Message.created_at.desc())
                .limit(1)
            ).first()
            
            snippet = ""
            if last_msg:
                snippet = last_msg.text[:120]
                if len(last_msg.text) > 120:
                    snippet += "..."
            
            result.append(ChatListItem(
                session_id=chat.id,
                title=chat.title,
                last_message_snippet=snippet,
                updated_at=chat.updated_at
            ))
        
        log_operation(
            api_logger,
            "chat_list_retrieved",
            chat_count=len(result)
        )
        
        return result
        
    except Exception as e:
        log_error(api_logger, e, operation="list_chats")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve chat list"
        )


@router.get(
    "/{session_id}",
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
def get_chat(session_id: str, db: Session = Depends(get_session)):
    """
    Get chat session with messages.
    
    Args:
        session_id: Chat session ID
        
    Returns:
        Chat session with up to 50 most recent messages
    """
    try:
        chat = db.get(Chat, session_id)
        if not chat:
            raise HTTPException(
                status_code=404,
                detail="Chat session not found"
            )
        
        # Get last 50 messages
        messages = db.exec(
            select(Message)
            .where(Message.chat_id == session_id)
            .order_by(Message.created_at.desc())
            .limit(50)
        ).all()
        
        # Reverse to chronological order
        messages = list(reversed(messages))
        
        log_operation(
            api_logger,
            "chat_retrieved",
            session_id=session_id,
            message_count=len(messages)
        )
        
        return {
            "session": {
                "id": chat.id,
                "title": chat.title,
                "created_at": chat.created_at,
                "updated_at": chat.updated_at
            },
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "text": msg.text,
                    "created_at": msg.created_at
                }
                for msg in messages
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(api_logger, e, operation="get_chat", session_id=session_id)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve chat session"
        )


@router.post(
    "/{session_id}/ask",
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def ask_in_chat(
    session_id: str,
    request: AskRequest,
    db: Session = Depends(get_session)
):
    """
    Ask a question in a chat session with memory.
    
    Args:
        session_id: Chat session ID
        request: Question and optional parameters
        
    Returns:
        Answer with sources, follow-up, and session context
    """
    start_time = time.time()
    
    try:
        # Verify chat exists
        chat = db.get(Chat, session_id)
        if not chat:
            raise HTTPException(
                status_code=404,
                detail="Chat session not found"
            )
        
        # Store user message
        user_message = Message(
            chat_id=session_id,
            role="user",
            text=request.question[:5000],  # Truncate if too long
            created_at=datetime.utcnow()
        )
        db.add(user_message)
        db.commit()
        db.refresh(user_message)
        
        # Get chat history (last 20 messages for context)
        history_messages = db.exec(
            select(Message)
            .where(Message.chat_id == session_id)
            .order_by(Message.created_at.desc())
            .limit(20)
        ).all()
        
        # Format chat history (chronological order, last 10 for prompt)
        history_messages = list(reversed(history_messages))
        chat_history = [
            {"role": msg.role, "text": msg.text}
            for msg in history_messages[-10:]  # Last 10 messages
        ]
        
        log_operation(
            api_logger,
            "chat_ask_start",
            session_id=session_id,
            question_length=len(request.question),
            history_length=len(chat_history),
            doc_id=request.doc_id,
            top_k=request.top_k
        )
        
        # Call RAG pipeline with chat history
        rag_result = await rag_pipeline.answer_question(
            doc_id=request.doc_id,
            question=request.question,
            top_k=request.top_k,
            chat_history=chat_history
        )
        
        # Store assistant reply
        assistant_message = Message(
            chat_id=session_id,
            role="assistant",
            text=rag_result["answer"][:5000],  # Truncate if too long
            created_at=datetime.utcnow()
        )
        db.add(assistant_message)
        
        # Update chat timestamp
        chat.updated_at = datetime.utcnow()
        db.add(chat)
        db.commit()
        
        processing_time = time.time() - start_time
        
        log_operation(
            api_logger,
            "chat_ask_complete",
            session_id=session_id,
            processing_time=processing_time,
            answer_length=len(rag_result["answer"]),
            confidence=rag_result.get("confidence_score", 0)
        )
        
        # Return result with session context
        return {
            **rag_result,
            "session_id": session_id,
            "processing_time_seconds": round(processing_time, 2)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(
            api_logger,
            e,
            operation="chat_ask",
            session_id=session_id,
            question=request.question[:100]
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to process question. Please try again."
        )


@router.post(
    "/{session_id}/rename",
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
def rename_chat(
    session_id: str,
    request: RenameRequest,
    db: Session = Depends(get_session)
):
    """
    Rename a chat session.
    
    Args:
        session_id: Chat session ID
        request: New title
        
    Returns:
        Success confirmation
    """
    try:
        chat = db.get(Chat, session_id)
        if not chat:
            raise HTTPException(
                status_code=404,
                detail="Chat session not found"
            )
        
        old_title = chat.title
        chat.title = request.title
        chat.updated_at = datetime.utcnow()
        
        db.add(chat)
        db.commit()
        db.refresh(chat)
        
        log_operation(
            api_logger,
            "chat_renamed",
            session_id=session_id,
            old_title=old_title,
            new_title=chat.title
        )
        
        return {
            "success": True,
            "session_id": session_id,
            "title": chat.title
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(api_logger, e, operation="rename_chat", session_id=session_id)
        raise HTTPException(
            status_code=500,
            detail="Failed to rename chat session"
        )


@router.delete(
    "/{session_id}",
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
def delete_chat(session_id: str, db: Session = Depends(get_session)):
    """
    Delete a chat session and all its messages.
    
    Args:
        session_id: Chat session ID
        
    Returns:
        Success confirmation with deletion stats
    """
    try:
        chat = db.get(Chat, session_id)
        if not chat:
            raise HTTPException(
                status_code=404,
                detail="Chat session not found"
            )
        
        # Count messages before deletion
        message_count = db.exec(
            select(Message).where(Message.chat_id == session_id)
        ).count()
        
        # Delete messages first
        db.exec(delete(Message).where(Message.chat_id == session_id))
        
        # Delete chat
        db.delete(chat)
        db.commit()
        
        log_operation(
            api_logger,
            "chat_deleted",
            session_id=session_id,
            title=chat.title,
            messages_deleted=message_count
        )
        
        return {
            "success": True,
            "session_id": session_id,
            "messages_deleted": message_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(api_logger, e, operation="delete_chat", session_id=session_id)
        raise HTTPException(
            status_code=500,
            detail="Failed to delete chat session"
        )


@router.get(
    "/{session_id}/stats",
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
def get_chat_stats(session_id: str, db: Session = Depends(get_session)):
    """
    Get statistics for a chat session.
    
    Args:
        session_id: Chat session ID
        
    Returns:
        Chat statistics including message counts and timestamps
    """
    try:
        chat = db.get(Chat, session_id)
        if not chat:
            raise HTTPException(
                status_code=404,
                detail="Chat session not found"
            )
        
        # Get message statistics
        total_messages = db.exec(
            select(Message).where(Message.chat_id == session_id)
        ).count()
        
        user_messages = db.exec(
            select(Message)
            .where(Message.chat_id == session_id)
            .where(Message.role == "user")
        ).count()
        
        assistant_messages = db.exec(
            select(Message)
            .where(Message.chat_id == session_id)
            .where(Message.role == "assistant")
        ).count()
        
        # Get first and last message timestamps
        first_message = db.exec(
            select(Message)
            .where(Message.chat_id == session_id)
            .order_by(Message.created_at.asc())
            .limit(1)
        ).first()
        
        last_message = db.exec(
            select(Message)
            .where(Message.chat_id == session_id)
            .order_by(Message.created_at.desc())
            .limit(1)
        ).first()
        
        return {
            "session_id": session_id,
            "title": chat.title,
            "created_at": chat.created_at,
            "updated_at": chat.updated_at,
            "total_messages": total_messages,
            "user_messages": user_messages,
            "assistant_messages": assistant_messages,
            "first_message_at": first_message.created_at if first_message else None,
            "last_message_at": last_message.created_at if last_message else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(api_logger, e, operation="get_chat_stats", session_id=session_id)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve chat statistics"
        )