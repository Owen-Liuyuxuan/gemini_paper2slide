"""
Analyze academic papers using Gemini's document understanding capabilities.

Extracts key information, contributions, methodology, and identifies important figures
using structured output for reliable parsing.
"""

from pathlib import Path
from typing import Dict, List, Optional

from src.llm.gemini_client import GeminiClient
from src.utils.logger import get_logger
from src.utils.models import (
    PaperAnalysisSchema,
)
from src.utils.progress import ProgressStage, ProgressCallback

logger = get_logger("document_analyzer")


class DocumentAnalyzer:
    """
    Analyze PDF documents using Gemini's document understanding capabilities.
    
    Extracts key information from academic papers including research question,
    methodology, contributions, and identifies important figures for presentation.
    Uses structured output for reliable and consistent parsing.
    """
    
    def __init__(self, gemini_client: GeminiClient):
        """
        Initialize document analyzer.
        
        Args:
            gemini_client: Initialized GeminiClient instance
        """
        self.gemini_client = gemini_client
        self.logger = logger
        logger.info("DocumentAnalyzer initialized with structured output support")
    
    def analyze_paper(
        self, 
        pdf_path: Path,
        progress_callback: Optional[ProgressCallback] = None
    ) -> PaperAnalysisSchema:
        """
        Analyze entire PDF with Gemini's document understanding.
        
        Uses structured output to ensure reliable parsing of the analysis.
        
        Args:
            pdf_path: Path to PDF file to analyze
            progress_callback: Optional callback for progress reporting
        
        Returns:
            PaperAnalysis object with comprehensive analysis
        
        Example:
            >>> from src.llm.gemini_client import GeminiClient
            >>> client = GeminiClient()
            >>> analyzer = DocumentAnalyzer(client)
            >>> analysis = analyzer.analyze_paper(Path("paper.pdf"))
        """
        logger.info(f"Analyzing paper: {pdf_path}")
        
        if progress_callback:
            progress_callback(
                ProgressStage.ANALYZING,
                10,
                "Starting paper analysis..."
            )
        
        # Step 1: Get initial analysis from PDF
        prompt = self._get_analysis_prompt()

        if progress_callback:
            progress_callback(
                ProgressStage.ANALYZING,
                30,
                "Analyzing document structure and content..."
            )

        # This can take a long time, so we'll update progress periodically
        import threading
        import time
        
        progress_update_thread = None
        if progress_callback:
            stop_progress_updates = threading.Event()
            
            def update_progress_periodically():
                """Update progress message periodically to show system is still working"""
                messages = [
                    "Analyzing document structure and content...",
                    "Extracting key information from paper...",
                    "Processing paper content...",
                    "Still analyzing paper..."
                ]
                message_index = 0
                while not stop_progress_updates.wait(10):  # Update every 10 seconds
                    message_index = (message_index + 1) % len(messages)
                    progress_callback(
                        ProgressStage.ANALYZING,
                        30 + (message_index * 15),  # 30-75% range
                        messages[message_index]
                    )
            
            progress_update_thread = threading.Thread(
                target=update_progress_periodically,
                daemon=True
            )
            progress_update_thread.start()
        
        try:
            paper_analysis = self.gemini_client.generate_structured_output(
                prompt=prompt,
                response_schema=PaperAnalysisSchema,
                pdf_path=pdf_path
            )
            
            # Stop progress update thread
            if progress_update_thread:
                stop_progress_updates.set()
                progress_update_thread.join(timeout=1)
        except Exception as e:
            # Stop progress update thread on error
            if progress_update_thread:
                stop_progress_updates.set()
                progress_update_thread.join(timeout=1)
            raise
        
        if progress_callback:
            progress_callback(
                ProgressStage.ANALYZING,
                100,
                f"Paper analysis complete. Recommended {paper_analysis.recommended_slide_count} slides."
            )
        
        return paper_analysis
    
    def _get_analysis_prompt(self) -> str:
        """
        Get prompt template for paper analysis.
        
        Returns:
            Prompt text
        """
        return self.gemini_client._load_prompt_template("paper_analysis")
