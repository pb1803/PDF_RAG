"""
Enhanced RAG pipeline with improved formatting, table generation, and external knowledge fallback.

This project uses Gemini models for text generation and Google text-embedding-004 
for vector embeddings. PDFs placed in the /pdfs folder are automatically processed.

ENHANCED RAG ARCHITECTURE:
1. PDF Processing: Extract text from PDF files with accurate page tracking
2. Chunking: Break text into semantic chunks with metadata preservation
3. Embeddings: Generate vectors using text-embedding-004
4. Storage: Store chunks and embeddings in Qdrant vector database
5. Retrieval: Find top-K most relevant chunks with similarity scoring
6. Smart Formatting: Convert raw chunks into clean, student-friendly explanations
7. Table Generation: Auto-generate comparison tables when appropriate
8. External Fallback: Use Gemini general knowledge when PDF content is insufficient
9. Blended Responses: Combine PDF facts with external knowledge when needed
"""
import asyncio
import re
from typing import Dict, Any, List, Optional, Tuple, Literal
import google.generativeai as genai
from app.core.config import settings
from app.core.logger import rag_logger, log_operation, log_error
from app.rag.embedder import gemini_embedder
from app.rag.retriever import document_retriever, RetrievedChunk


# Enhanced system prompt for improved formatting
SYSTEM_PROMPT = """
You are an AI Academic Tutor that provides clean, well-formatted responses.

### Response Structure (ALWAYS follow this format):
## Definition
[2-3 lines maximum - clear, concise definition]

## Explanation  
[Simple language explanation - keep it short and student-friendly]

## Example
[Only include if relevant and helpful - keep it brief]

## Table
[Auto-generate ONLY when question includes: difference, compare, vs, advantages, disadvantages]

## Follow-up Question
[One engaging question to continue learning]

## Sources
[List page numbers from PDF or mention "external sources"]

### Important Rules:
- Use clean Markdown formatting
- Keep explanations concise and readable
- Generate tables for comparison questions
- Always include accurate page citations
- Use simple, student-friendly language
- Never show placeholders or ask for more context
"""

# External knowledge system prompt
EXTERNAL_KNOWLEDGE_PROMPT = """
You are providing general knowledge since the PDF doesn't contain this information.

Provide a helpful answer using your general knowledge, but keep it:
- Accurate and educational
- Formatted with the same structure (Definition, Explanation, Example if relevant)
- Clearly marked as external knowledge

Always end with: "⚠️ Note: This information was not found in the uploaded PDF. It has been answered using general knowledge sources."
"""


class RAGPipeline:
    """
    Enhanced RAG pipeline with smart formatting, table generation, and external knowledge fallback.
    """
    
    def __init__(self):
        self.logger = rag_logger
        self.embedder = gemini_embedder
        self.retriever = document_retriever
        self.gemini_model = settings.gemini_model
        self.temperature = settings.temperature
        self.max_tokens = settings.max_tokens
        self._initialized = False
        
        # Thresholds for smart fallback
        self.min_similarity_threshold = 0.3
        self.min_chunks_for_pdf_answer = 1
    
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
        Enhanced answer generation with smart formatting, table generation, and external fallback.
        
        Args:
            doc_id: Document ID to query
            question: User question
            top_k: Number of chunks to retrieve (optional override)
            temperature: Generation temperature (optional override)
            chat_history: Previous conversation messages for context
            
        Returns:
            Enhanced answer with improved formatting and metadata
        """
        if not self._initialized:
            await self.initialize()
        
        # Use provided values or defaults
        retrieval_k = top_k or settings.top_k_final
        gen_temperature = temperature or self.temperature
        
        log_operation(
            self.logger,
            "enhanced_rag_answer_start",
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
            
            # Step 2: Determine answer strategy based on chunk quality
            answer_type = self._determine_answer_type(question, chunks)
            
            # Step 3: Generate answer based on strategy
            if answer_type == "pdf_only":
                answer = await self._generate_pdf_answer(question, chunks, chat_history, gen_temperature)
            elif answer_type == "external_only":
                answer = await self._generate_external_answer(question, gen_temperature)
            else:  # mixed
                answer = await self._generate_blended_answer(question, chunks, chat_history, gen_temperature)
            
            # Step 4: Apply smart formatting enhancements
            formatted_answer = await self._apply_smart_formatting(answer, question, chunks)
            
            # Step 5: Extract components from formatted answer
            follow_up = self._extract_follow_up_question(formatted_answer)
            sources = self._format_enhanced_sources(chunks, answer_type)
            citations = self._extract_citations(formatted_answer, chunks)
            
            # Step 6: Calculate confidence score
            confidence = self._calculate_confidence_score(chunks, answer_type)
            
            # Step 7: Build enhanced response
            response = {
                "answer": formatted_answer,
                "sources": sources,
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
                "confidence_score": confidence,
                "answer_type": answer_type
            }
            
            log_operation(
                self.logger,
                "enhanced_rag_answer_complete",
                doc_id=doc_id,
                chunks_used=len(chunks),
                answer_length=len(formatted_answer),
                confidence=confidence,
                answer_type=answer_type
            )
            
            return response
            
        except Exception as e:
            log_error(
                self.logger,
                e,
                operation="enhanced_rag_answer",
                doc_id=doc_id,
                question=question[:100]
            )
            # Clean user-facing error message
            raise RuntimeError("Text generation failed. Please try again or rephrase your question.")
    
    # ============================================================================
    # ENHANCED HELPER METHODS FOR IMPROVED RAG PIPELINE
    # ============================================================================
    
    def _determine_answer_type(self, question: str, chunks: List[RetrievedChunk]) -> Literal["pdf_only", "external_only", "mixed"]:
        """
        Determine the best answer strategy based on chunk quality and question type.
        
        Args:
            question: User question
            chunks: Retrieved chunks
            
        Returns:
            Answer type strategy
        """
        if not chunks:
            return "external_only"
        
        # Check chunk quality
        high_quality_chunks = [c for c in chunks if c.similarity_score >= self.min_similarity_threshold]
        
        if len(high_quality_chunks) >= self.min_chunks_for_pdf_answer:
            # Check if chunks provide sufficient coverage
            total_chunk_length = sum(len(chunk.text) for chunk in high_quality_chunks)
            if total_chunk_length >= 200:  # Minimum content threshold
                return "pdf_only"
            else:
                return "mixed"  # Partial info, blend with external
        else:
            return "external_only"
    
    async def _generate_pdf_answer(
        self, 
        question: str, 
        chunks: List[RetrievedChunk], 
        chat_history: Optional[List[Dict[str, str]]], 
        temperature: float
    ) -> str:
        """Generate answer using only PDF content with enhanced formatting."""
        # Compress and rewrite chunk text for better readability
        compressed_chunks = await self._compress_pdf_chunks(chunks)
        
        # Build enhanced prompt
        system_prompt = SYSTEM_PROMPT
        
        context_text = ""
        for i, chunk in enumerate(compressed_chunks):
            context_text += f"📘 From your textbook (Page {chunk.page_number}):\n{chunk.text}\n\n"
        
        # Include chat history if available
        history_section = ""
        if chat_history:
            history_lines = []
            for msg in chat_history[-10:]:
                role = msg.get("role", "unknown")
                text = msg.get("text", "")
                history_lines.append(f"{role.title()}: {text}")
            history_text = "\n".join(history_lines)
            history_section = f"\n\nPrevious conversation:\n{history_text}\n"
        
        # Check if table generation is needed
        table_instruction = ""
        if self._detect_table_question(question):
            table_instruction = "\n\nIMPORTANT: Generate a comparison table in the ## Table section since this is a comparison question."
        
        user_prompt = f"""Textbook content: {context_text.strip()}

User question: {question}{history_section}{table_instruction}

Provide a well-formatted response following the exact structure in the system prompt."""
        
        return await self._generate_answer(system_prompt, user_prompt, temperature)
    
    async def _generate_external_answer(self, question: str, temperature: float) -> str:
        """Generate answer using external knowledge when PDF content is insufficient."""
        system_prompt = EXTERNAL_KNOWLEDGE_PROMPT
        
        # Check if table generation is needed
        table_instruction = ""
        if self._detect_table_question(question):
            table_instruction = "\n\nIMPORTANT: Generate a comparison table since this is a comparison question."
        
        user_prompt = f"""Question: {question}{table_instruction}

Provide a helpful educational answer using general knowledge. Follow the structured format and clearly mark this as external knowledge."""
        
        return await self._generate_answer(system_prompt, user_prompt, temperature)
    
    async def _generate_blended_answer(
        self, 
        question: str, 
        chunks: List[RetrievedChunk], 
        chat_history: Optional[List[Dict[str, str]]], 
        temperature: float
    ) -> str:
        """Generate blended answer combining PDF content with external knowledge."""
        # Compress PDF chunks
        compressed_chunks = await self._compress_pdf_chunks(chunks)
        
        system_prompt = """
You are an AI Academic Tutor providing a blended response using both textbook content and general knowledge.

### Response Structure:
## Definition
[Clear, concise definition]

## Explanation  
[Combine textbook facts with additional context from general knowledge]

## Example
[Include if helpful]

## Table
[Generate for comparison questions]

## Follow-up Question
[One engaging question]

## Sources
[Clearly distinguish between textbook pages and external sources]

### Important:
- Clearly mark what comes from the textbook vs. external sources
- Use 📘 for textbook content and 🌐 for external knowledge
- Blend information seamlessly but maintain transparency
"""
        
        # Build context with clear source marking
        context_text = ""
        for chunk in compressed_chunks:
            context_text += f"📘 From textbook (Page {chunk.page_number}):\n{chunk.text}\n\n"
        
        # Include chat history
        history_section = ""
        if chat_history:
            history_lines = []
            for msg in chat_history[-10:]:
                role = msg.get("role", "unknown")
                text = msg.get("text", "")
                history_lines.append(f"{role.title()}: {text}")
            history_text = "\n".join(history_lines)
            history_section = f"\n\nPrevious conversation:\n{history_text}\n"
        
        # Check if table generation is needed
        table_instruction = ""
        if self._detect_table_question(question):
            table_instruction = "\n\nIMPORTANT: Generate a comparison table in the ## Table section."
        
        user_prompt = f"""Available textbook content: {context_text.strip()}

User question: {question}{history_section}{table_instruction}

The textbook provides partial information. Blend it with your general knowledge to provide a complete, well-formatted answer. Clearly mark sources."""
        
        return await self._generate_answer(system_prompt, user_prompt, temperature)
    
    async def _compress_pdf_chunks(self, chunks: List[RetrievedChunk]) -> List[RetrievedChunk]:
        """
        Compress and rewrite PDF chunk text for better readability.
        
        Args:
            chunks: Original chunks
            
        Returns:
            Chunks with compressed, rewritten text
        """
        compressed_chunks = []
        
        for chunk in chunks:
            # Use Gemini to compress and rewrite chunk text
            compression_prompt = f"""
Rewrite this textbook content to be more concise and student-friendly while preserving all key information:

Original text: {chunk.text}

Requirements:
- Keep all important facts and details
- Remove unnecessary words and repetition
- Use clear, simple language
- Maintain technical accuracy
- Make it more readable for students
"""
            
            try:
                # Generate compressed version
                model = genai.GenerativeModel(
                    model_name=self.gemini_model,
                    generation_config={"temperature": 0.1, "max_output_tokens": 500}
                )
                
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: model.generate_content(compression_prompt)
                )
                
                compressed_text = response.text.strip() if response.text else chunk.text
                
                # Create new chunk with compressed text
                compressed_chunk = RetrievedChunk(
                    chunk_id=chunk.chunk_id,
                    text=compressed_text,
                    page_number=chunk.page_number,
                    similarity_score=chunk.similarity_score
                )
                compressed_chunks.append(compressed_chunk)
                
            except Exception as e:
                self.logger.warning(f"Failed to compress chunk {chunk.chunk_id}: {str(e)}")
                # Use original chunk if compression fails
                compressed_chunks.append(chunk)
        
        return compressed_chunks
    
    async def _apply_smart_formatting(self, answer: str, question: str, chunks: List[RetrievedChunk]) -> str:
        """
        Apply smart formatting enhancements to the generated answer.
        
        Args:
            answer: Raw generated answer
            question: Original question
            chunks: Source chunks
            
        Returns:
            Enhanced formatted answer
        """
        # Check if answer already has good structure
        if "## Definition" in answer and "## Sources" in answer:
            return answer  # Already well-formatted
        
        # Apply formatting using Gemini
        formatting_prompt = f"""
Reformat this answer to follow the exact structure below. Keep all the content but organize it properly:

## Definition
[2-3 lines maximum - clear, concise definition]

## Explanation  
[Simple language explanation - keep it short and student-friendly]

## Example
[Only include if relevant and helpful - keep it brief]

## Table
[Only include if this is a comparison question about differences, advantages, vs, etc.]

## Follow-up Question
[One engaging question to continue learning]

## Sources
[List page numbers or mention external sources]

Original answer to reformat: {answer}

Original question: {question}

Reformat the answer to match this structure exactly. If it's a comparison question, add a proper markdown table."""
        
        try:
            model = genai.GenerativeModel(
                model_name=self.gemini_model,
                generation_config={"temperature": 0.1, "max_output_tokens": 1500}
            )
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: model.generate_content(formatting_prompt)
            )
            
            formatted_answer = response.text.strip() if response.text else answer
            
            # Ensure sources section is accurate
            formatted_answer = self._fix_sources_section(formatted_answer, chunks)
            
            return formatted_answer
            
        except Exception as e:
            self.logger.warning(f"Failed to apply smart formatting: {str(e)}")
            return answer  # Return original if formatting fails
    
    def _detect_table_question(self, question: str) -> bool:
        """
        Detect if the question requires a comparison table.
        
        Args:
            question: User question
            
        Returns:
            True if table should be generated
        """
        table_keywords = [
            "difference", "differences", "compare", "comparison", "vs", "versus",
            "advantages", "disadvantages", "pros", "cons", "contrast",
            "similarities", "distinguish", "differentiate"
        ]
        
        question_lower = question.lower()
        return any(keyword in question_lower for keyword in table_keywords)
    
    def _fix_sources_section(self, answer: str, chunks: List[RetrievedChunk]) -> str:
        """
        Fix the sources section to show accurate page numbers.
        
        Args:
            answer: Formatted answer
            chunks: Source chunks
            
        Returns:
            Answer with corrected sources
        """
        if not chunks:
            # Replace sources section with external note
            sources_pattern = r"## Sources\n.*?(?=\n##|\n$|$)"
            replacement = "## Sources\n📄 External sources (not found in uploaded PDF)"
            return re.sub(sources_pattern, replacement, answer, flags=re.DOTALL)
        
        # Build accurate sources list
        page_numbers = sorted(list(set(chunk.page_number for chunk in chunks)))
        if len(page_numbers) == 1:
            sources_text = f"📄 Page {page_numbers[0]}"
        elif len(page_numbers) <= 3:
            sources_text = f"📄 Pages {', '.join(map(str, page_numbers))}"
        else:
            sources_text = f"📄 Pages {page_numbers[0]}-{page_numbers[-1]} (and others)"
        
        # Replace sources section
        sources_pattern = r"## Sources\n.*?(?=\n##|\n$|$)"
        replacement = f"## Sources\n{sources_text}"
        
        if "## Sources" in answer:
            return re.sub(sources_pattern, replacement, answer, flags=re.DOTALL)
        else:
            # Add sources section if missing
            return f"{answer}\n\n## Sources\n{sources_text}"
    
    def _extract_main_answer(self, formatted_answer: str) -> str:
        """
        Extract the main answer content, removing the follow-up question.
        
        Args:
            formatted_answer: Full formatted answer
            
        Returns:
            Main answer without follow-up
        """
        # Remove follow-up question section
        main_answer = re.sub(r"\n## Follow-up Question\n.*?(?=\n##|\n$|$)", "", formatted_answer, flags=re.DOTALL)
        return main_answer.strip()
    
    def _format_enhanced_sources(self, chunks: List[RetrievedChunk], answer_type: str) -> List[str]:
        """
        Enhanced source formatting with answer type awareness.
        
        Args:
            chunks: Retrieved chunks
            answer_type: Type of answer generated
            
        Returns:
            List of formatted source citations
        """
        if answer_type == "external_only":
            return ["External sources"]
        
        if not chunks:
            return []
        
        # Get unique page numbers
        page_numbers = sorted(list(set(chunk.page_number for chunk in chunks)))
        sources = [f"Page {page}" for page in page_numbers]
        
        if answer_type == "mixed":
            sources.append("External sources")
        
        return sources
    
    def _calculate_confidence_score(self, chunks: List[RetrievedChunk], answer_type: str) -> float:
        """
        Calculate confidence score based on chunks and answer type.
        
        Args:
            chunks: Retrieved chunks
            answer_type: Type of answer generated
            
        Returns:
            Confidence score (0-1)
        """
        if answer_type == "external_only":
            return 0.0
        
        if not chunks:
            return 0.0
        
        # Calculate average similarity score
        avg_similarity = sum(chunk.similarity_score for chunk in chunks) / len(chunks)
        
        # Adjust based on answer type
        if answer_type == "pdf_only":
            return min(avg_similarity, 1.0)
        else:  # mixed
            return min(avg_similarity * 0.7, 1.0)  # Lower confidence for mixed answers
    
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
        Format source citations in clean format (legacy method).
        
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