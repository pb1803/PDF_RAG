"""
PDF text extraction with page-aware processing.
"""
import asyncio
from typing import List, Tuple, Optional, Union
from pathlib import Path
import fitz  # PyMuPDF
import aiofiles
from urllib.parse import urlparse
import tempfile
import os
from app.core.logger import rag_logger, log_operation, log_error


class PDFExtractor:
    """
    PDF text extractor that preserves page information.
    """
    
    def __init__(self):
        self.logger = rag_logger
    
    async def extract_from_file(self, file_path: Union[str, Path]) -> List[Tuple[int, str]]:
        """
        Extract text from a PDF file with page information.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            List of tuples (page_number, page_text)
            
        Raises:
            ValueError: If file is not a valid PDF
            FileNotFoundError: If file doesn't exist
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not file_path.suffix.lower() == '.pdf':
            raise ValueError(f"File is not a PDF: {file_path}")
        
        log_operation(
            self.logger, 
            "pdf_extraction_start", 
            file_path=str(file_path)
        )
        
        try:
            # Run PDF processing in thread pool to avoid blocking
            pages = await asyncio.get_event_loop().run_in_executor(
                None, 
                self._extract_pdf_sync,
                str(file_path)
            )
            
            log_operation(
                self.logger,
                "pdf_extraction_complete",
                file_path=str(file_path),
                pages_extracted=len(pages)
            )
            
            return pages
            
        except Exception as e:
            log_error(
                self.logger,
                e,
                operation="pdf_extraction",
                file_path=str(file_path)
            )
            raise
    
    async def extract_from_url(self, file_url: str) -> List[Tuple[int, str]]:
        """
        Extract text from a PDF URL (including file:// URLs).
        
        Args:
            file_url: URL to PDF file
            
        Returns:
            List of tuples (page_number, page_text)
        """
        parsed_url = urlparse(file_url)
        
        log_operation(
            self.logger,
            "pdf_url_extraction_start",
            url=file_url,
            scheme=parsed_url.scheme
        )
        
        try:
            if parsed_url.scheme == 'file':
                # Handle local file URLs
                file_path = parsed_url.path
                return await self.extract_from_file(file_path)
            
            elif parsed_url.scheme in ['http', 'https']:
                # Download file temporarily
                temp_path = await self._download_file(file_url)
                try:
                    return await self.extract_from_file(temp_path)
                finally:
                    # Clean up temp file
                    if temp_path.exists():
                        temp_path.unlink()
            
            else:
                raise ValueError(f"Unsupported URL scheme: {parsed_url.scheme}")
                
        except Exception as e:
            log_error(
                self.logger,
                e,
                operation="pdf_url_extraction",
                url=file_url
            )
            raise
    
    def _extract_pdf_sync(self, file_path: str) -> List[Tuple[int, str]]:
        """
        Synchronous PDF extraction (runs in thread pool).
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            List of tuples (page_number, page_text)
        """
        pages = []
        
        try:
            doc = fitz.open(file_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                
                # Clean up text
                text = self._clean_text(text)
                
                # Only include pages with meaningful content
                if text.strip():
                    pages.append((page_num + 1, text))  # 1-indexed page numbers
            
            doc.close()
            
        except Exception as e:
            raise ValueError(f"Failed to process PDF: {str(e)}")
        
        return pages
    
    async def _download_file(self, url: str) -> Path:
        """
        Download a file from URL to temporary location.
        
        Args:
            url: File URL
            
        Returns:
            Path to downloaded temporary file
        """
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                
                # Create temporary file
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix='.pdf'
                )
                temp_path = Path(temp_file.name)
                
                # Write content to temp file
                async with aiofiles.open(temp_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        await f.write(chunk)
                
                temp_file.close()
                return temp_path
    
    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        lines = []
        for line in text.split('\n'):
            line = line.strip()
            if line:
                lines.append(line)
        
        # Join lines with single spaces
        text = ' '.join(lines)
        
        # Remove multiple consecutive spaces
        import re
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    async def get_document_info(self, file_path: Union[str, Path]) -> dict:
        """
        Get metadata about a PDF document.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Document metadata
        """
        file_path = Path(file_path)
        
        try:
            doc_info = await asyncio.get_event_loop().run_in_executor(
                None,
                self._get_doc_info_sync,
                str(file_path)
            )
            return doc_info
            
        except Exception as e:
            log_error(
                self.logger,
                e,
                operation="get_document_info",
                file_path=str(file_path)
            )
            raise
    
    def _get_doc_info_sync(self, file_path: str) -> dict:
        """
        Synchronous document info extraction.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Document metadata
        """
        try:
            doc = fitz.open(file_path)
            
            info = {
                "filename": Path(file_path).name,
                "page_count": len(doc),
                "title": doc.metadata.get("title", ""),
                "author": doc.metadata.get("author", ""),
                "subject": doc.metadata.get("subject", ""),
                "creator": doc.metadata.get("creator", ""),
                "producer": doc.metadata.get("producer", ""),
                "creation_date": doc.metadata.get("creationDate", ""),
                "modification_date": doc.metadata.get("modDate", "")
            }
            
            doc.close()
            return info
            
        except Exception as e:
            raise ValueError(f"Failed to get document info: {str(e)}")


# Global extractor instance
pdf_extractor = PDFExtractor()