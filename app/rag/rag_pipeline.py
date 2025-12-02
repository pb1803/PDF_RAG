"""
Main RAG pipeline for question answering with Gemini-2.0-flash.

This project uses Gemini models for text generation and Google text-embedding-004 
for vector embeddings. PDFs placed in the /pdfs folder are automatically processed.

RAG ARCHITECTURE:
1. PDF Processing: Extract text from PDF files using PyMuPDF
2. Chunking: Break text into semantic chunks for better retrieval
3. Embeddings: Generate vectors using text-embedding-004
4. Storage: Store chunks and embeddings in Qdrant vector database
5. Retrieval: Find top-K most relevant chunks for user questions
6. Generation: Use Gemini-2.0-flash to generate natural, detailed, ChatGPT-like answers from retrieved context
"""
import asyncio
import re
from typing import Dict, Any, List, Optional, Tuple
import google.generativeai as genai
from app.core.config import settings
from app.core.logger import rag_logger, log_operation, log_error
from app.rag.embedder import gemini_embedder
from app.rag.retriever import document_retriever, RetrievedChunk


# Natural conversational tutor system prompt
SYSTEM_PROMPT = """
You are an AI Academic Tutor. You answer based ONLY on:
1. retrieved_chunks (the relevant textbook snippets)
2. chat_history (last 10 messages) 
3. the user's question

### How to answer:
- Start with a **2–3 line definition**
- Then add a **short explanation in simple words**
- If helpful, add a **small example**
- Add a **follow-up question** such as:
  "Do you want to know where this is used?" OR
  "Would you like the syntax or an example?"

### If chunks are empty:
Say: "I couldn't find this in the textbook. Want a general answer?"

### Important:
- NEVER ask the user for chunks or context manually.
- NEVER show placeholders like {question}.
- Use clean, student-friendly language.
- Include page references when chunks contain them.
"""


class RAGPipeline:
    """
    Main RAG pipeline that coordinates retrieval and generation.
    """
    
    def __init__(self):
        self.logger = rag_logger
        self.embedder = gemini_embedder
        self.retriever = document_retriever
        self.gemini_model = settings.gemini_model
        self.temperature = settings.temperature
        self.max_tokens = settings.max_tokens
        self._initialized = False
    
    async def initialize(self):
        """Initialize the pipeline components."""
        if self._initialized:
            return
        
        try:
            # Initialize embedder (which handles auth)
            await self.embedder.initialize()
            
            # Use Google Generative AI API key for text generation
            if not settings.google_api_key:
                self._initialized = False
                raise ValueError("GOOGLE_API_KEY is required for the RAG pipeline")
            
            genai.configure(api_key=settings.google_api_key)
            
            # Verify the model is available (gemini-1.5-flash)
            try:
                available_models = genai.list_models()
                model_names = [model.name for model in available_models]
                if f"models/{self.gemini_model}" not in model_names:
                    self.logger.warning(f"Model {self.gemini_model} not found in available models")
                    # Continue anyway as the model might still work
            except Exception as e:
                self.logger.warning(f"Could not verify model availability: {str(e)}")
            
            # Only set initialized to True after ALL steps succeed
            self._initialized = True
            log_operation(
                self.logger,
                "rag_pipeline_initialized",
                model=self.gemini_model,
                temperature=self.temperature,
                api_type="google_generative_ai"
            )
            self.logger.info(f"RAG pipeline initialized with {self.gemini_model} using Google Generative AI API")
            
        except Exception as e:
            self._initialized = False
            log_error(
                self.logger,
                e,
                operation="rag_pipeline_initialization"
            )
            self.logger.error(f"RAG pipeline initialization failed: {str(e)}")
            raise RuntimeError(f"Failed to initialize RAG pipeline: {str(e)}")
    
    async def answer_question(
        self,
        doc_id: str,
        question: str,
        top_k: Optional[int] = None,
        temperature: Optional[float] = None,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Answer a question about a document using RAG with chat history.
        
        Args:
            doc_id: Document ID to query
            question: User question
            top_k: Number of chunks to retrieve (optional override)
            temperature: Generation temperature (optional override)
            chat_history: Previous conversation messages for context
            
        Returns:
            Answer with citations and metadata
        """
        if not self._initialized:
            await self.initialize()
        
        # Use provided values or defaults
        retrieval_k = top_k or settings.top_k_final
        gen_temperature = temperature or self.temperature
        
        log_operation(
            self.logger,
            "rag_answer_start",
            doc_id=doc_id,
            question_length=len(question),
            top_k=retrieval_k,
            history_length=len(chat_history) if chat_history else 0
        )
        
        try:
            # Step 1: Retrieve relevant chunks
            chunks = await self.retriever.retrieve_chunks(
                query=question,
                doc_id=doc_id,
                final_k=retrieval_k
            )
            
            # Step 2: Build RAG prompt (handles empty chunks gracefully)
            system_prompt, user_prompt = self._build_rag_prompts(
                question, chunks, chat_history
            )
            
            # Step 3: Generate answer (even with empty chunks)
            answer = await self._generate_answer(
                system_prompt,
                user_prompt,
                gen_temperature
            )
            
            # Step 4: Verify and post-process answer
            verified_answer, confidence = await self._verify_answer(answer, chunks)
            
            # Step 5: Extract citations
            citations = self._extract_citations(verified_answer, chunks)
            
            # Step 6: Extract follow-up question from answer
            follow_up = self._extract_follow_up_question(verified_answer)
            
            # Step 7: Build clean response
            response = {
                "answer": self._clean_answer_text(verified_answer),
                "sources": self._format_sources(chunks),
                "follow_up": follow_up,
                "citations": citations,
                "used_chunks": [
                    {
                        "chunk_id": chunk.chunk_id,
                        "page": chunk.page_number,
                        "score": chunk.similarity_score,
                        "snippet": chunk.text[:200] + "..." if len(chunk.text) > 200 else chunk.text
                    }
                    for chunk in chunks
                ],
                "doc_id": doc_id,
                "confidence_score": confidence
            }
            
            log_operation(
                self.logger,
                "rag_answer_complete",
                doc_id=doc_id,
                chunks_used=len(chunks),
                answer_length=len(verified_answer),
                confidence=confidence
            )
            
            return response
            
        except Exception as e:
            log_error(
                self.logger,
                e,
                operation="rag_answer",
                doc_id=doc_id,
                question=question[:100]
            )
            # Clean user-facing error message
            raise RuntimeError("Text generation failed. Please try again or rephrase your question.")
    
    def _build_rag_prompts(
        self, 
        question: str, 
        chunks: List[RetrievedChunk],
        chat_history: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Build system and user prompts for natural conversational tutoring.
        
        Args:
            question: User question
            chunks: Retrieved chunks
            chat_history: Previous conversation context
            
        Returns:
            Tuple of (system_prompt, user_prompt) formatted for natural conversation
        """
        system_prompt = SYSTEM_PROMPT
        
        # Build context from chunks in natural format
        if chunks:
            context_text = ""
            for chunk in chunks:
                context_text += f"[Page {chunk.page_number}] {chunk.text}\n\n"
        else:
            context_text = "No relevant textbook content found."
        
        # Include chat history if available
        history_section = ""
        if chat_history:
            history_lines = []
            for msg in chat_history[-10:]:  # Last 10 messages
                role = msg.get("role", "unknown")
                text = msg.get("text", "")
                history_lines.append(f"{role.title()}: {text}")
            history_text = "\n".join(history_lines)
            history_section = f"\n\nPrevious conversation:\n{history_text}\n"
        
        user_prompt = f"""Here are the textbook references: {context_text.strip()}

User question: {question}{history_section}

Provide a clear, student-friendly explanation with a follow-up question:"""
        
        return system_prompt, user_prompt
    
    async def _generate_answer(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float
    ) -> str:
        """
        Generate natural, detailed answer using Google Generative AI Gemini model.
        
        Args:
            system_prompt: System prompt for natural responses
            user_prompt: User prompt with context
            temperature: Generation temperature
            
        Returns:
            Generated answer in ChatGPT-like style
        """
        try:
            # Configure generation parameters for natural, detailed responses
            generation_config = {
                "temperature": temperature,
                "top_p": 0.9,  # Slightly higher for more natural language
                "top_k": 40,
                "max_output_tokens": max(self.max_tokens, 2000),  # Allow longer responses
            }
            
            # Create model for current Gemini version
            model = genai.GenerativeModel(
                model_name=self.gemini_model,  # This is now "gemini-1.5-flash"
                generation_config=generation_config
            )
            
            # For Gemini models, combine system and user prompts for natural responses
            full_prompt = f"""{system_prompt}

{user_prompt}"""
            
            # Generate response using Gemini-1.5-flash
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: model.generate_content(full_prompt)
            )
            
            if not response.text:
                raise RuntimeError("Empty response from Gemini-1.5-flash")
            
            return response.text.strip()
            
        except Exception as e:
            # Friendly error message for users
            self.logger.error(f"Gemini generation failed: {str(e)}")
            raise RuntimeError("Text generation failed. Please try rephrasing your question or try again later.")
    
    async def _verify_answer(
        self, 
        answer: str, 
        chunks: List[RetrievedChunk]
    ) -> Tuple[str, float]:
        """
        Verify answer against retrieved chunks and calculate confidence.
        
        Args:
            answer: Generated answer
            chunks: Source chunks
            
        Returns:
            Tuple of (verified_answer, confidence_score)
        """
        # Check for the "not found" response
        not_found_phrases = [
            "could not find",
            "not found",
            "no information",
            "unable to locate",
            "not mentioned",
            "not provided",
            "insufficient information"
        ]
        
        answer_lower = answer.lower()
        if any(phrase in answer_lower for phrase in not_found_phrases):
            return answer, 0.0
        
        # Extract factual claims from answer (simplified approach)
        answer_sentences = re.split(r'[.!?]+', answer)
        answer_sentences = [s.strip() for s in answer_sentences if s.strip()]
        
        verified_sentences = []
        total_confidence = 0.0
        
        for sentence in answer_sentences:
            # Skip citations and very short sentences
            if len(sentence) < 10 or sentence.startswith('[p.'):
                verified_sentences.append(sentence)
                continue
            
            # Check if sentence content appears in chunks
            confidence = self._calculate_sentence_confidence(sentence, chunks)
            
            if confidence > 0.3:  # Threshold for factual support
                verified_sentences.append(sentence)
                total_confidence += confidence
            else:
                # Replace unsupported claims
                self.logger.warning(f"Unsupported claim filtered: {sentence[:50]}...")
        
        # If too many sentences were filtered, return fallback
        if len(verified_sentences) < len(answer_sentences) * 0.5:
            return "I could not find reliable information to answer this question in the provided document.", 0.0
        
        verified_answer = '. '.join(verified_sentences)
        if verified_answer and not verified_answer.endswith('.'):
            verified_answer += '.'
        
        avg_confidence = total_confidence / max(len(answer_sentences), 1)
        
        return verified_answer, min(avg_confidence, 1.0)
    
    def _calculate_sentence_confidence(
        self, 
        sentence: str, 
        chunks: List[RetrievedChunk]
    ) -> float:
        """
        Calculate confidence that a sentence is supported by chunks.
        
        Args:
            sentence: Sentence to verify
            chunks: Source chunks
            
        Returns:
            Confidence score (0-1)
        """
        # Extract key phrases from sentence
        sentence_words = set(re.findall(r'\b\w+\b', sentence.lower()))
        
        # Remove common words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been'
        }
        key_words = sentence_words - stop_words
        
        if not key_words:
            return 0.0
        
        best_overlap = 0.0
        
        for chunk in chunks:
            chunk_words = set(re.findall(r'\b\w+\b', chunk.text.lower()))
            overlap = len(key_words.intersection(chunk_words))
            overlap_ratio = overlap / len(key_words)
            
            # Boost for phrase matches
            sentence_clean = re.sub(r'[^\w\s]', '', sentence.lower())
            chunk_clean = re.sub(r'[^\w\s]', '', chunk.text.lower())
            
            if any(phrase in chunk_clean for phrase in sentence_clean.split() 
                   if len(phrase) > 4):
                overlap_ratio += 0.2
            
            best_overlap = max(best_overlap, overlap_ratio)
        
        return min(best_overlap, 1.0)
    
    def _extract_citations(
        self, 
        answer: str, 
        chunks: List[RetrievedChunk]
    ) -> List[Dict[str, Any]]:
        """
        Extract citation information from answer and chunks.
        
        Args:
            answer: Generated answer with citations
            chunks: Source chunks
            
        Returns:
            List of citation dictionaries
        """
        citations = []
        
        # Find page references in answer
        page_refs = re.findall(r'\[p\.(\d+)\]', answer)
        page_numbers = [int(p) for p in page_refs]
        
        # Group chunks by page
        chunks_by_page = {}
        for chunk in chunks:
            page = chunk.page_number
            if page not in chunks_by_page:
                chunks_by_page[page] = []
            chunks_by_page[page].append(chunk)
        
        # Create citations for referenced pages
        for page_num in set(page_numbers):
            if page_num in chunks_by_page:
                # Use the chunk with highest score from this page
                best_chunk = max(chunks_by_page[page_num], 
                               key=lambda c: c.similarity_score)
                
                citation = {
                    "page": page_num,
                    "snippet": self._get_citation_snippet(best_chunk.text)
                }
                citations.append(citation)
        
        # If no explicit citations found, create from top chunks
        if not citations:
            for chunk in chunks[:3]:  # Top 3 chunks
                citation = {
                    "page": chunk.page_number,
                    "snippet": self._get_citation_snippet(chunk.text)
                }
                if citation not in citations:
                    citations.append(citation)
        
        return citations
    
    def _get_citation_snippet(self, text: str, max_length: int = 150) -> str:
        """
        Extract a good snippet for citation.
        
        Args:
            text: Full chunk text
            max_length: Maximum snippet length
            
        Returns:
            Citation snippet
        """
        if len(text) <= max_length:
            return text
        
        # Try to break at sentence boundary
        sentences = re.split(r'[.!?]+', text)
        if sentences and len(sentences[0]) <= max_length:
            return sentences[0] + ('.' if not sentences[0].endswith(('.', '!', '?')) else '')
        
        # Fallback to character limit at word boundary
        snippet = text[:max_length]
        last_space = snippet.rfind(' ')
        if last_space > max_length * 0.8:  # If word break is reasonable
            snippet = snippet[:last_space]
        
        return snippet + "..."
    
    def _extract_follow_up_question(self, answer: str) -> str:
        """
        Extract or generate a follow-up question from the answer.
        
        Args:
            answer: Generated answer text
            
        Returns:
            Follow-up question string
        """
        # Look for follow-up questions in the answer
        import re
        follow_up_patterns = [
            r"(Do you want to [^?]+\?)",
            r"(Would you like [^?]+\?)", 
            r"(Should I [^?]+\?)",
            r"(Want to [^?]+\?)"
        ]
        
        for pattern in follow_up_patterns:
            match = re.search(pattern, answer, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # Generate default follow-up based on answer content
        if "example" in answer.lower():
            return "Would you like more examples?"
        elif "definition" in answer.lower() or "means" in answer.lower():
            return "Do you want to see where this is used?"
        else:
            return "Would you like me to explain this further?"
    
    def _clean_answer_text(self, answer: str) -> str:
        """
        Clean the answer text by removing follow-up questions for the main answer.
        
        Args:
            answer: Raw answer text
            
        Returns:
            Cleaned answer text
        """
        # Remove follow-up questions from main answer
        import re
        follow_up_patterns = [
            r"Do you want to [^?]+\?",
            r"Would you like [^?]+\?", 
            r"Should I [^?]+\?",
            r"Want to [^?]+\?"
        ]
        
        cleaned = answer
        for pattern in follow_up_patterns:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
        
        return cleaned.strip()
    
    def _format_sources(self, chunks: List[RetrievedChunk]) -> List[str]:
        """
        Format source citations in clean format.
        
        Args:
            chunks: Retrieved chunks
            
        Returns:
            List of formatted source citations
        """
        if not chunks:
            return []
            
        sources = []
        for chunk in chunks:
            sources.append(f"Page {chunk.page_number}")
        
        # Remove duplicates while preserving order
        unique_sources = []
        for source in sources:
            if source not in unique_sources:
                unique_sources.append(source)
                
        return unique_sources
    
    def _create_no_answer_response(self, doc_id: str, question: str) -> Dict[str, Any]:
        """
        Create response when no relevant chunks are found.
        
        Args:
            doc_id: Document ID
            question: Original question
            
        Returns:
            No-answer response
        """
        return {
            "answer": "I couldn't find this in the textbook. Want a general answer?",
            "sources": [],
            "follow_up": "Should I try a broader search?",
            "citations": [],
            "used_chunks": [],
            "doc_id": doc_id,
            "confidence_score": 0.0
        }
    
    async def health_check(self) -> bool:
        """
        Check if the RAG pipeline is healthy and can generate text with Gemini-1.5-flash.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Check if we have the required configuration
            if not settings.google_api_key:
                return False
            
            # If already initialized, do a simple generation test
            if self._initialized:
                try:
                    # Simple generation test with Gemini-1.5-flash
                    test_answer = await self._generate_answer(
                        "You are a helpful assistant.",
                        "Please respond with the word 'healthy' to confirm the system is working.",
                        0.0
                    )
                    return "healthy" in test_answer.lower()
                except Exception as e:
                    self.logger.warning(f"Health check generation test failed: {str(e)}")
                    return False
            
            # If not initialized, just check if we have the required config
            return bool(settings.google_api_key)
            
        except Exception as e:
            log_error(
                self.logger,
                e,
                operation="rag_pipeline_health_check"
            )
            return False
    
    def is_ready(self) -> bool:
        """Check if the RAG pipeline is ready to use."""
        return self._initialized


# Global pipeline instance
rag_pipeline = RAGPipeline()