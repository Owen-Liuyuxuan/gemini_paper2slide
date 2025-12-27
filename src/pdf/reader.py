"""
PDF text extraction and metadata parsing.

Uses PyMuPDF (fitz) for efficient PDF processing.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import fitz  # PyMuPDF

from src.utils.logger import get_logger
from src.utils.models import PDFMetadata

logger = get_logger("pdf_reader")


class PDFReader:
    """
    Extract text and metadata from PDF documents.
    
    Uses PyMuPDF for high-performance PDF processing with support
    for text extraction, metadata parsing, and document structure analysis.
    """
    
    def __init__(self) -> None:
        """Initialize PDF reader."""
        logger.info("PDFReader initialized")
    
    def extract_text(self, pdf_path: Path) -> Dict[str, any]:
        """
        Extract text content from PDF.
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            Dictionary containing:
                - full_text: Complete document text
                - pages: List of page texts
                - page_count: Number of pages
                - toc: Table of contents if available
        
        Raises:
            FileNotFoundError: If PDF file doesn't exist
            ValueError: If PDF is encrypted or corrupted
        
        Example:
            >>> reader = PDFReader()
            >>> content = reader.extract_text(Path("paper.pdf"))
            >>> print(content["full_text"][:100])
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        logger.info(f"Extracting text from {pdf_path}")
        
        try:
            doc = fitz.open(pdf_path)
            
            if doc.is_encrypted:
                raise ValueError(f"PDF is encrypted: {pdf_path}")
            
            # Extract text from all pages
            pages = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text("text")
                pages.append({
                    "page_num": page_num,
                    "text": text,
                    "word_count": len(text.split())
                })
            
            # Combine all text
            full_text = "\n\n".join(page["text"] for page in pages)
            
            # Extract table of contents
            toc = doc.get_toc()
            
            doc.close()
            
            result = {
                "full_text": full_text,
                "pages": pages,
                "page_count": len(pages),
                "toc": toc,
                "word_count": len(full_text.split())
            }
            
            logger.info(
                f"Extracted {result['page_count']} pages, "
                f"{result['word_count']} words from {pdf_path.name}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to extract text from {pdf_path}: {e}")
            raise
    
    def extract_metadata(self, pdf_path: Path) -> PDFMetadata:
        """
        Extract metadata from PDF.
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            PDFMetadata object with document information
        
        Raises:
            FileNotFoundError: If PDF file doesn't exist
            ValueError: If required metadata is missing
        
        Example:
            >>> reader = PDFReader()
            >>> metadata = reader.extract_metadata(Path("paper.pdf"))
            >>> print(metadata.title)
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        logger.info(f"Extracting metadata from {pdf_path}")
        
        try:
            doc = fitz.open(pdf_path)
            meta = doc.metadata
            
            # Extract title (fallback to filename if not in metadata)
            title = meta.get("title", "") or pdf_path.stem
            
            # Extract authors
            authors_str = meta.get("author", "")
            authors = [a.strip() for a in authors_str.split(",") if a.strip()]
            
            # Extract keywords
            keywords_str = meta.get("keywords", "")
            keywords = [k.strip() for k in keywords_str.split(",") if k.strip()]
            
            # Extract creation date
            creation_date = None
            if date_str := meta.get("creationDate"):
                try:
                    # PyMuPDF date format: D:YYYYMMDDHHmmSSOHH'mm'
                    if date_str.startswith("D:"):
                        date_str = date_str[2:16]  # Extract YYYYMMDDHHmmSS
                        creation_date = datetime.strptime(date_str, "%Y%m%d%H%M%S")
                except Exception as e:
                    logger.warning(f"Failed to parse creation date: {e}")
            
            # Extract abstract (try to find it in first page)
            abstract = self._extract_abstract(doc)
            
            page_count = len(doc)
            doc.close()
            
            metadata = PDFMetadata(
                title=title,
                authors=authors,
                abstract=abstract,
                keywords=keywords,
                page_count=page_count,
                creation_date=creation_date,
                file_path=pdf_path
            )
            
            logger.info(f"Extracted metadata: {title} by {', '.join(authors)}")
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to extract metadata from {pdf_path}: {e}")
            raise
    
    def _extract_abstract(self, doc: fitz.Document) -> Optional[str]:
        """
        Attempt to extract abstract from first few pages.
        
        Args:
            doc: Opened PyMuPDF document
        
        Returns:
            Abstract text or None if not found
        """
        # Search first 3 pages for abstract
        for page_num in range(min(3, len(doc))):
            page = doc[page_num]
            text = page.get_text("text")
            
            # Look for "Abstract" section
            lines = text.split("\n")
            for i, line in enumerate(lines):
                if "abstract" in line.lower() and len(line) < 50:
                    # Found abstract header, collect following lines
                    abstract_lines = []
                    for j in range(i + 1, min(i + 20, len(lines))):
                        if lines[j].strip():
                            # Stop at next section header
                            if any(keyword in lines[j].lower() 
                                   for keyword in ["introduction", "1.", "keywords"]):
                                break
                            abstract_lines.append(lines[j].strip())
                    
                    if abstract_lines:
                        return " ".join(abstract_lines)
        
        return None
    
    def get_page_count(self, pdf_path: Path) -> int:
        """
        Get number of pages in PDF.
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            Number of pages
        
        Example:
            >>> reader = PDFReader()
            >>> count = reader.get_page_count(Path("paper.pdf"))
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        doc = fitz.open(pdf_path)
        count = len(doc)
        doc.close()
        
        return count