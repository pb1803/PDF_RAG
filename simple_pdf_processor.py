#!/usr/bin/env python3
"""
Simple synchronous PDF processor.

PDF AUTO-PROCESSING SYSTEM:
- Automatically monitors the /pdfs folder for new PDF files
- On startup: processes any existing PDFs in the folder
- On file add: immediately processes new PDF files (drag & drop, copy, etc.)
- Processing pipeline: PDF → Extract Text → Create Chunks → Generate Embeddings → Store in Qdrant
- Uses text-embedding-004 for embeddings and Gemini-1.5-flash for Q&A
- Each processed PDF becomes searchable via the Q&A endpoints
- Continues monitoring even if individual PDF processing fails
"""
import os
import time
from pathlib import Path
import uuid
from typing import List
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Add the app directory to path
import sys
sys.path.insert(0, os.path.dirname(__file__))

from app.rag.extractor import pdf_extractor
from app.rag.chunker import semantic_chunker  
from app.rag.embedder import gemini_embedder
from app.rag.vectorstore import qdrant_store
from app.core.logger import setup_logger
from dotenv import load_dotenv
import asyncio

load_dotenv()

logger = setup_logger("simple_pdf_processor")

class SimplePDFHandler(FileSystemEventHandler):
    """
    Handle new PDF files added to the folder.
    
    PROCESSING STEPS:
    1. Detect new PDF file (via file system events)
    2. Extract text from PDF pages using PyMuPDF
    3. Create semantic chunks from extracted text
    4. Generate embeddings using text-embedding-004
    5. Store chunks and embeddings in Qdrant vector database
    6. PDF becomes immediately searchable via Q&A endpoints
    """
    
    def __init__(self):
        self.processed_files = set()
        
    def process_pdf_sync(self, file_path: str):
        """
        Process a PDF file synchronously through the complete RAG pipeline.
        
        PIPELINE STEPS:
        1. Extract text from PDF pages (PyMuPDF)
        2. Create semantic chunks from text (adaptive chunking)
        3. Generate embeddings using text-embedding-004 (Google Generative AI)
        4. Store chunks + embeddings in Qdrant vector database
        5. PDF becomes immediately searchable via Q&A endpoints
        """
        try:
            file_path = Path(file_path)
            
            if file_path.name in self.processed_files:
                logger.info(f"Skipping already processed file: {file_path.name}")
                return
                
            logger.info(f"🔄 Starting RAG pipeline for: {file_path.name}")
            
            # Generate document ID
            doc_id = str(uuid.uuid4())
            
            # Run async operations in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Initialize components that need it
                loop.run_until_complete(gemini_embedder.initialize())
                loop.run_until_complete(qdrant_store.initialize())
                
                # Extract text (no initialization needed)
                pages = loop.run_until_complete(pdf_extractor.extract_from_file(str(file_path)))
                logger.info(f"📄 Text extraction: {len(pages)} pages extracted")
                
                # Create chunks (no initialization needed) 
                chunks = loop.run_until_complete(semantic_chunker.chunk_pages(pages, doc_id))
                logger.info(f"🔗 Semantic chunking: {len(chunks)} chunks created")
                
                # Store in vector database (embeddings generated automatically)
                chunks_indexed = loop.run_until_complete(qdrant_store.store_chunks(chunks))
                logger.info(f"💾 Vector storage: {chunks_indexed} chunks indexed with text-embedding-004")
                
            finally:
                loop.close()
            
            # Mark as processed
            self.processed_files.add(file_path.name)
            
            logger.info(f"✅ RAG pipeline complete: {file_path.name} ready for questions")
            
        except Exception as e:
            logger.error(f"❌ RAG pipeline failed for {file_path.name}: {e}")
            # Don't add to processed_files so it can be retried
            # But continue monitoring other files
    
    def on_created(self, event):
        """Handle file creation."""
        try:
            if not event.is_directory and event.src_path.endswith('.pdf'):
                self.process_pdf_sync(event.src_path)
        except Exception as e:
            logger.error(f"Error handling file creation event: {e}")
            # Continue monitoring despite errors
    
    def on_moved(self, event):
        """Handle file moves (like drag & drop)."""
        try:
            if not event.is_directory and event.dest_path.endswith('.pdf'):
                self.process_pdf_sync(event.dest_path)
        except Exception as e:
            logger.error(f"Error handling file move event: {e}")
            # Continue monitoring despite errors

class SimplePDFProcessor:
    """Main class to handle PDF folder monitoring."""
    
    def __init__(self, pdf_folder_path: str):
        self.pdf_folder = Path(pdf_folder_path)
        self.handler = SimplePDFHandler()
        self.observer = None
        
    def start_monitoring(self):
        """
        Start monitoring the PDF folder.
        
        AUTO-PROCESSING BEHAVIOR:
        1. Creates /pdfs folder if it doesn't exist
        2. Processes any existing PDF files found in the folder
        3. Starts watching for new files (drag & drop, copy, move operations)
        4. Each new PDF is automatically processed and becomes searchable
        """
        # Create folder if it doesn't exist
        self.pdf_folder.mkdir(exist_ok=True)
        
        logger.info(f"📁 PDF Auto-Processor monitoring: {self.pdf_folder.absolute()}")
        
        # Process existing files first
        self.process_existing_pdfs()
        
        # Start watching for new files
        self.observer = Observer()
        self.observer.schedule(self.handler, str(self.pdf_folder), recursive=False)
        self.observer.start()
        
        logger.info("👀 PDF Auto-Processor active - watching for new files...")
    
    def process_existing_pdfs(self):
        """
        Process any existing PDFs in the folder on startup.
        
        This ensures that PDFs added while the server was offline
        are automatically processed and become searchable.
        """
        logger.info(f"🔍 Scanning for existing PDFs in {self.pdf_folder}...")
        
        pdf_files = list(self.pdf_folder.glob("*.pdf"))
        
        if not pdf_files:
            logger.info("📁 No existing PDFs found - folder is empty")
            return
            
        logger.info(f"📚 Found {len(pdf_files)} existing PDF(s) - processing through RAG pipeline...")
        
        for pdf_file in pdf_files:
            try:
                self.handler.process_pdf_sync(str(pdf_file))
            except Exception as e:
                logger.error(f"Failed to process existing PDF {pdf_file.name}: {e}")
                # Continue processing other files
    
    def stop_monitoring(self):
        """Stop monitoring and cleanup resources."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            logger.info("📁 PDF Auto-Processor stopped")