"""
Analyze academic papers using Gemini's document understanding capabilities.

Extracts key information, contributions, methodology, and identifies important figures
using structured output for reliable parsing.
"""

from pathlib import Path
from typing import Dict, List

from src.llm.gemini_client import GeminiClient
from src.utils.logger import get_logger
from src.utils.models import (
    PaperAnalysisSchema,
)

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
    
    def analyze_paper(self, pdf_path: Path) -> PaperAnalysisSchema:
        """
        Analyze entire PDF with Gemini's document understanding.
        
        Uses structured output to ensure reliable parsing of the analysis.
        
        Args:
            pdf_path: Path to PDF file to analyze
        
        Returns:
            PaperAnalysis object with comprehensive analysis
        
        Example:
            >>> from src.llm.gemini_client import GeminiClient
            >>> client = GeminiClient()
            >>> analyzer = DocumentAnalyzer(client)
            >>> analysis = analyzer.analyze_paper(Path("paper.pdf"))
        """
        logger.info(f"Analyzing paper: {pdf_path}")
        
        # Step 1: Get initial analysis from PDF
        prompt = self._get_analysis_prompt()

        paper_analysis = self.gemini_client.generate_structured_output(
            prompt=prompt,
            response_schema=PaperAnalysisSchema,
            pdf_path=pdf_path
        )        
        return paper_analysis
    
    def _get_analysis_prompt(self) -> str:
        """
        Get prompt template for paper analysis.
        
        Returns:
            Prompt text
        """
        return self.gemini_client._load_prompt_template("paper_analysis")
