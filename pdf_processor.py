#!/usr/bin/env python3
"""
Auto-process PDFs from a folder and make them available for chatting.
"""
import asyncio
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

load_dotenv()

logger = setup_logger("pdf_processor")

class PDFProcessor:
    """Main class to handle PDF folder monitoring."""
    
    def __init__(self, pdf_folder_path: str):
        self.pdf_folder = Path(pdf_folder_path)
        self.handler = PDFHandler()
        self.observer = None
        self.loop = None
        
    def start_monitoring(self):
        """Start monitoring the PDF folder in a synchronous way for threading."""
        # Create folder if it doesn't exist
        self.pdf_folder.mkdir(exist_ok=True)
        
        logger.info(f"📁 PDF Processor monitoring: {self.pdf_folder.absolute()}")
        
        # Create new event loop for this thread
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        # Set the loop in handler for use in file events
        self.handler.event_loop = self.loop
        
        try:
            self.loop.run_until_complete(self._async_monitor())
        except Exception as e:
            logger.error(f"PDF processor error: {e}")
        finally:
            self.loop.close()
    
    async def _async_monitor(self):
        """Async monitoring implementation."""
        # Process existing files first
        await process_existing_pdfs(self.pdf_folder, self.handler)
        
        # Start watching for new files
        self.observer = Observer()
        self.observer.schedule(self.handler, str(self.pdf_folder), recursive=False)
        self.observer.start()
        
        logger.info("👀 PDF processor started - watching for new files...")
        
        try:
            while True:
                await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"PDF processor error: {e}")
        finally:
            if self.observer:
                self.observer.stop()
                self.observer.join()

class PDFHandler(FileSystemEventHandler):
    """Handle new PDF files added to the folder."""
    
    def __init__(self):
        self.processed_files = set()
        self.event_loop = None  # Will be set by PDFProcessor
        
    async def process_pdf(self, file_path: str):
        """Process a single PDF file."""
        try:
            file_path = Path(file_path)
            
            # Skip if already processed or not a PDF
            if (file_path.name in self.processed_files or 
                not file_path.suffix.lower() == '.pdf' or
                not file_path.exists()):
                return
                
            logger.info(f"🔄 Processing new PDF: {file_path.name}")
            
            # Generate doc_id from filename
            doc_id = file_path.stem.replace(' ', '_').replace('-', '_').lower()
            
            # Extract text from PDF
            pages = await pdf_extractor.extract_from_file(file_path)
            
            if not pages:
                logger.error(f"❌ No text extracted from {file_path.name}")
                return
                
            logger.info(f"📄 Extracted {len(pages)} pages from {file_path.name}")
            
            # Initialize components
            await gemini_embedder.initialize()
            await qdrant_store.initialize()
            
            # Chunk the pages
            chunks = await semantic_chunker.chunk_pages(pages, doc_id)
            
            if not chunks:
                logger.error(f"❌ No chunks created from {file_path.name}")
                return
                
            logger.info(f"🧩 Created {len(chunks)} chunks from {file_path.name}")
            
            # Generate embeddings
            chunk_texts = [chunk.text for chunk in chunks]
            embeddings = await gemini_embedder.embed_texts(chunk_texts)
            
            # Store in vector database
            chunks_indexed = await qdrant_store.upsert_chunks(chunks, embeddings)
            
            # Mark as processed
            self.processed_files.add(file_path.name)
            
            logger.info(f"✅ Successfully processed {file_path.name} - {chunks_indexed} chunks indexed")
            print(f"✅ {file_path.name} is ready for questions!")
            
        except Exception as e:
            logger.error(f"❌ Error processing {file_path}: {e}")
            print(f"❌ Failed to process {file_path.name}: {e}")
    
    def on_created(self, event):
        """Handle file creation."""
        if not event.is_directory and event.src_path.endswith('.pdf'):
            # Use the event loop from the processor
            if self.event_loop and self.event_loop.is_running():
                future = asyncio.run_coroutine_threadsafe(self.process_pdf(event.src_path), self.event_loop)
                # Don't wait for result to avoid blocking
    
    def on_moved(self, event):
        """Handle file moves (like drag & drop)."""
        if not event.is_directory and event.dest_path.endswith('.pdf'):
            if self.event_loop and self.event_loop.is_running():
                future = asyncio.run_coroutine_threadsafe(self.process_pdf(event.dest_path), self.event_loop)

async def process_existing_pdfs(pdf_folder: Path, handler: PDFHandler):
    """Process any existing PDFs in the folder."""
    print(f"🔍 Checking for existing PDFs in {pdf_folder}...")
    
    pdf_files = list(pdf_folder.glob("*.pdf"))
    
    if not pdf_files:
        print("📁 No existing PDFs found.")
        return
        
    print(f"📚 Found {len(pdf_files)} existing PDF(s). Processing...")
    
    for pdf_file in pdf_files:
        await handler.process_pdf(str(pdf_file))

async def start_pdf_watcher():
    """Start watching the PDF folder."""
    
    # Create PDF folder if it doesn't exist
    pdf_folder = Path("pdfs")
    pdf_folder.mkdir(exist_ok=True)
    
    print("=" * 60)
    print("🤖 PDF Auto-Processor Started")
    print("=" * 60)
    print(f"📁 PDF Folder: {pdf_folder.absolute()}")
    print("📋 Instructions:")
    print("   1. Drop any PDF files into the 'pdfs' folder")
    print("   2. Files will be automatically processed")
    print("   3. Once processed, ask questions in the chat!")
    print("=" * 60)
    
    # Create event handler
    handler = PDFHandler()
    
    # Process existing files
    await process_existing_pdfs(pdf_folder, handler)
    
    # Start watching for new files
    observer = Observer()
    observer.schedule(handler, str(pdf_folder), recursive=False)
    observer.start()
    
    print("👀 Watching for new PDF files...")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("🛑 Stopping PDF watcher...")
        observer.stop()
    
    observer.join()

if __name__ == "__main__":
    asyncio.run(start_pdf_watcher())