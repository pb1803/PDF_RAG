"""
Question answering routes for the RAG system.
"""
import time
from fastapi import APIRouter, HTTPException
from app.core.logger import api_logger, log_operation, log_error
from app.schemas.requests import AskQuestionRequest
from app.schemas.responses import AskQuestionResponse, ErrorResponse
from app.rag.rag_pipeline import rag_pipeline
from app.rag.vectorstore import qdrant_store


router = APIRouter()


@router.post(
    "/ask",
    response_model=AskQuestionResponse,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def ask_question(request: AskQuestionRequest):
    """
    Ask a question about a document using RAG.
    
    Retrieves relevant chunks from the document, generates an answer using Gemini-1.5-flash,
    and returns the answer with citations and source information.
    """
    start_time = time.time()
    
    log_operation(
        api_logger,
        "ask_question_start",
        doc_id=request.doc_id,
        question_length=len(request.question),
        top_k=request.top_k,
        temperature=request.temperature
    )
    
    try:
        # Initialize pipeline
        await rag_pipeline.initialize()
        await qdrant_store.initialize()
        
        # If doc_id is "any", get the first available document
        if request.doc_id == "any":
            all_docs = await qdrant_store.list_documents()
            if not all_docs:
                log_operation(api_logger, "ask_question_no_documents")
                raise HTTPException(status_code=404, detail="No documents found. Please add PDF files to the pdfs folder.")
            
            # Use the first available document
            request.doc_id = all_docs[0]["doc_id"]
            api_logger.info(f"Using document: {request.doc_id}")
        
        # Check if document exists
        doc_info = await qdrant_store.get_document_info(request.doc_id)
        if not doc_info:
            raise HTTPException(
                status_code=404,
                detail=f"Document not found: {request.doc_id}"
            )
        
        # Validate question
        if len(request.question.strip()) < 5:
            raise HTTPException(
                status_code=400,
                detail="Question must be at least 5 characters long"
            )
        
        # Generate answer using RAG pipeline
        rag_result = await rag_pipeline.answer_question(
            doc_id=request.doc_id,
            question=request.question.strip(),
            top_k=request.top_k,
            temperature=request.temperature
        )
        
        processing_time = time.time() - start_time
        
        # Build response
        response = AskQuestionResponse(
            answer=rag_result["answer"],
            sources=rag_result.get("sources", []),
            follow_up=rag_result.get("follow_up"),
            citations=rag_result["citations"],
            used_chunks=rag_result["used_chunks"],
            doc_id=rag_result["doc_id"],
            confidence_score=rag_result.get("confidence_score"),
            processing_time_seconds=round(processing_time, 2)
        )
        
        log_operation(
            api_logger,
            "ask_question_complete",
            doc_id=request.doc_id,
            answer_length=len(response.answer),
            citations_count=len(response.citations),
            chunks_used=len(response.used_chunks),
            confidence=response.confidence_score,
            processing_time=processing_time
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(
            api_logger,
            e,
            operation="ask_question",
            doc_id=request.doc_id,
            question=request.question[:100]  # Log first 100 chars
        )
        # Clean error message for users - no stack traces
        raise HTTPException(
            status_code=500,
            detail="Text generation failed. Please try again or check your question."
        )


@router.post(
    "/ask_batch",
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def ask_batch_questions(
    doc_id: str,
    questions: list[str],
    top_k: int = None,
    temperature: float = None
):
    """
    Ask multiple questions about a document in batch.
    
    This endpoint allows asking multiple questions about the same document
    in a single request, which can be more efficient than individual requests.
    """
    if not questions:
        raise HTTPException(
            status_code=400,
            detail="At least one question must be provided"
        )
    
    if len(questions) > 10:  # Limit batch size
        raise HTTPException(
            status_code=400,
            detail="Maximum 10 questions per batch"
        )
    
    log_operation(
        api_logger,
        "ask_batch_start",
        doc_id=doc_id,
        question_count=len(questions)
    )
    
    try:
        # Initialize pipeline
        await rag_pipeline.initialize()
        await qdrant_store.initialize()
        
        # Check if document exists
        doc_info = await qdrant_store.get_document_info(doc_id)
        if not doc_info:
            raise HTTPException(
                status_code=404,
                detail=f"Document not found: {doc_id}"
            )
        
        # Process each question
        results = []
        for i, question in enumerate(questions):
            if len(question.strip()) < 5:
                results.append({
                    "question": question,
                    "error": "Question must be at least 5 characters long"
                })
                continue
            
            try:
                start_time = time.time()
                
                rag_result = await rag_pipeline.answer_question(
                    doc_id=doc_id,
                    question=question.strip(),
                    top_k=top_k,
                    temperature=temperature
                )
                
                processing_time = time.time() - start_time
                
                result = {
                    "question": question,
                    "answer": rag_result["answer"],
                    "sources": rag_result.get("sources", []),
                    "follow_up": rag_result.get("follow_up"),
                    "citations": rag_result["citations"],
                    "used_chunks": rag_result["used_chunks"],
                    "confidence_score": rag_result.get("confidence_score"),
                    "processing_time_seconds": round(processing_time, 2)
                }
                results.append(result)
                
            except Exception as e:
                log_error(
                    api_logger,
                    e,
                    operation="ask_batch_question",
                    doc_id=doc_id,
                    question_index=i
                )
                results.append({
                    "question": question,
                    "error": "Text generation failed for this question"
                })
        
        log_operation(
            api_logger,
            "ask_batch_complete",
            doc_id=doc_id,
            question_count=len(questions),
            successful_answers=len([r for r in results if "answer" in r])
        )
        
        return {
            "doc_id": doc_id,
            "results": results,
            "total_questions": len(questions),
            "successful_answers": len([r for r in results if "answer" in r])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(
            api_logger,
            e,
            operation="ask_batch",
            doc_id=doc_id,
            question_count=len(questions)
        )
        raise HTTPException(
            status_code=500,
            detail="Batch text generation failed. Please try again."
        )


@router.get(
    "/document/{doc_id}/chunks",
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def get_document_chunks(
    doc_id: str,
    page: int = None,
    limit: int = 20,
    offset: int = 0
):
    """
    Get chunks from a document for inspection.
    
    This endpoint allows retrieving the chunks that were created from a document,
    which can be useful for debugging or understanding how the document was processed.
    """
    if limit > 100:  # Limit response size
        raise HTTPException(
            status_code=400,
            detail="Maximum limit is 100 chunks"
        )
    
    try:
        await qdrant_store.initialize()
        
        # Check if document exists
        doc_info = await qdrant_store.get_document_info(doc_id)
        if not doc_info:
            raise HTTPException(
                status_code=404,
                detail=f"Document not found: {doc_id}"
            )
        
        # This would require implementing a method to retrieve chunks
        # For now, return document info
        return {
            "doc_id": doc_id,
            "document_info": doc_info,
            "message": "Chunk retrieval endpoint not fully implemented yet. Use document info for now."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(
            api_logger,
            e,
            operation="get_document_chunks",
            doc_id=doc_id
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve chunks: {str(e)}"
        )