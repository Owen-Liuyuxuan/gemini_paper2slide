"""
Analyze academic papers using Gemini's document understanding capabilities.

Extracts key information, contributions, methodology, and identifies important figures.
"""

from pathlib import Path
from typing import List

from src.llm.gemini_client import GeminiClient
from src.utils.logger import get_logger
from src.utils.models import ExtractedImage, KeyPoint, PaperAnalysis

logger = get_logger("document_analyzer")


class DocumentAnalyzer:
    """
    Analyze PDF documents using Gemini's document understanding capabilities.
    
    Extracts key information from academic papers including research question,
    methodology, contributions, and identifies important figures for presentation.
    """
    
    def __init__(self, gemini_client: GeminiClient):
        """
        Initialize document analyzer.
        
        Args:
            gemini_client: Initialized GeminiClient instance
        """
        self.gemini_client = gemini_client
        self.logger = logger
        logger.info("DocumentAnalyzer initialized")
    
    def analyze_paper(self, pdf_path: Path) -> PaperAnalysis:
        """
        Analyze entire PDF with Gemini's document understanding.
        
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
        
        # Get paper analysis prompt
        prompt = self._get_prompt('paper_analysis')
        
        # Analyze the document
        analysis_text = self.gemini_client.analyze_document(
            pdf_path=pdf_path,
            prompt=prompt
        )
        
        logger.debug(f"Raw analysis text length: {len(analysis_text)}")
        
        # Parse the analysis into structured format
        return self._parse_analysis(analysis_text)
    
    def extract_key_points(self, analysis: PaperAnalysis) -> List[KeyPoint]:
        """
        Extract key points from paper analysis.
        
        Args:
            analysis: PaperAnalysis object from analyze_paper
        
        Returns:
            List of KeyPoint objects with important information
        """
        logger.info("Extracting key points from analysis")
        return analysis.key_points
    
    def identify_important_figures(self, pdf_images: List[ExtractedImage]) -> List[int]:
        """
        Identify which extracted figures are most important for presentation.
        
        Args:
            pdf_images: List of extracted images from PDF
        
        Returns:
            List of indices of important figures
        """
        logger.info(f"Identifying important figures from {len(pdf_images)} extracted images")
        
        # For now, return the indices of all high-quality images
        # In a more advanced implementation, we could use Gemini to analyze
        # each image and determine its importance for the presentation
        important_indices = [
            idx for idx, img in enumerate(pdf_images)
            if img.quality_score >= 0.6  # threshold for important figures
        ]
        
        logger.info(f"Identified {len(important_indices)} important figures")
        return important_indices
    
    def _get_prompt(self, prompt_name: str) -> str:
        """
        Get prompt template from file.
        
        Args:
            prompt_name: Name of the prompt file (without extension)
        
        Returns:
            Prompt text
        """
        # In a complete implementation, this would load from a prompt manager
        # For now, we'll use a simple implementation
        prompt_file = Path(f"src/llm/prompts/{prompt_name}.txt")
        try:
            return prompt_file.read_text()
        except FileNotFoundError:
            logger.warning(f"Prompt file {prompt_file} not found, using default")
            # Return a default prompt
            if prompt_name == "paper_analysis":
                return (
                    "Analyze this academic paper comprehensively. Focus on:\n"
                    "1. Main research question and motivation\n"
                    "2. Key methodology and approach\n"
                    "3. Main results and contributions\n"
                    "4. Important figures and their significance\n"
                    "5. Potential visual representations for a presentation\n"
                    "\nProvide a structured analysis suitable for creating a presentation."
                )
            else:
                return "Analyze this document and provide a comprehensive summary."
    
    def _parse_analysis(self, analysis_text: str) -> PaperAnalysis:
        """
        Parse raw analysis text into structured PaperAnalysis object.
        
        Args:
            analysis_text: Raw analysis text from Gemini
        
        Returns:
            PaperAnalysis object with structured information
        """
        logger.debug("Parsing analysis text into structured format")
        
        # For now, we'll create a basic implementation
        # In a more advanced version, we could use NLP techniques or 
        # structured output from Gemini to parse the analysis
        
        # This is a simplified implementation - in practice, you'd want to 
        # use more sophisticated parsing or Gemini's structured output capabilities
        lines = analysis_text.split('\n')
        
        # Find key sections in the analysis
        summary = self._extract_section(analysis_text, ['summary', 'overview'])
        research_question = self._extract_section(analysis_text, ['research question', 'main question', 'objective'])
        methodology = self._extract_section(analysis_text, ['methodology', 'approach', 'method'])
        contributions = self._extract_section_list(analysis_text, ['contributions', 'key contributions', 'main contributions'])
        
        # Create key points from important parts of the analysis
        key_points = self._create_key_points(analysis_text)
        
        # Create a basic paper analysis
        paper_analysis = PaperAnalysis(
            summary=summary or "No summary found in analysis",
            research_question=research_question or "Research question not identified",
            methodology=methodology or "Methodology not clearly described",
            key_contributions=contributions or ["Contributions not clearly identified"],
            key_points=key_points,
            important_figures=[],  # Will be populated by identify_important_figures
            recommended_slide_count=min(max(8, len(key_points)), 15),  # Between 8-15 slides
            visual_theme="professional academic"  # Default theme
        )
        
        logger.info("Successfully parsed analysis into structured format")
        return paper_analysis
    
    def _extract_section(self, text: str, keywords: List[str]) -> str:
        """
        Extract a section from text based on keywords.
        
        Args:
            text: Text to search in
            keywords: List of keywords that identify the section
        
        Returns:
            Extracted section text
        """
        text_lower = text.lower()
        
        for keyword in keywords:
            pos = text_lower.find(keyword)
            if pos != -1:
                # Find the start of the section (after the keyword)
                start = pos + len(keyword)
                # Find the end of the section (next major heading or end of text)
                end = len(text)
                
                # Look for common section separators
                for separator in ['\n\n', '\n1.', '\n2.', '\n##', '\nResearch question', '\nMethodology']:
                    next_section = text.find(separator, start)
                    if 0 < next_section < end:
                        end = next_section
                
                # Extract the section content
                section = text[start:end].strip()
                
                # Remove leading colons, dashes, etc.
                if section.startswith(':'):
                    section = section[1:].strip()
                
                return section
        
        return ""
    
    def _extract_section_list(self, text: str, keywords: List[str]) -> List[str]:
        """
        Extract a list of items from a section based on keywords.
        
        Args:
            text: Text to search in
            keywords: List of keywords that identify the section
        
        Returns:
            List of extracted items
        """
        section_text = self._extract_section(text, keywords)
        
        if not section_text:
            return []
        
        # Try to identify list items
        items = []
        
        # Look for numbered lists
        import re
        number_pattern = r'(?:^|\n)\s*\d+\.\s*(.*?)(?=\n\s*\d+\.|\n\s*##|\n\s*Abstract|$)'
        matches = re.findall(number_pattern, section_text, re.DOTALL)
        
        if matches:
            items = [item.strip() for item in matches if item.strip()]
        else:
            # Look for bullet points or other separators
            lines = section_text.split('\n')
            for line in lines:
                # Check if line looks like a list item
                if line.strip().startswith(('-', '*', '•', '◦', '▪')):
                    items.append(line.strip()[1:].strip())
                elif line.strip().startswith(('1.', '2.', '3.', '4.', '5.')):
                    items.append(line.strip()[3:].strip())
        
        return items if items else [section_text]
    
    def _create_key_points(self, analysis_text: str) -> List[KeyPoint]:
        """
        Create KeyPoint objects from analysis text.
        
        Args:
            analysis_text: Raw analysis text
        
        Returns:
            List of KeyPoint objects
        """
        # This is a simplified implementation
        # In a more advanced version, we could use Gemini to create structured key points
        
        # Extract potential key points based on common academic paper sections
        sections = [
            ("Research Question", self._extract_section(analysis_text, ["research question", "main question"])),
            ("Methodology", self._extract_section(analysis_text, ["methodology", "approach"])),
            ("Key Contributions", self._extract_section(analysis_text, ["contributions", "contributions"])),
            ("Main Results", self._extract_section(analysis_text, ["results", "findings"])),
            ("Conclusions", self._extract_section(analysis_text, ["conclusion", "conclusions"])),
        ]
        
        key_points = []
        for title, content in sections:
            if content.strip():
                key_points.append(KeyPoint(
                    title=title,
                    content=content,
                    importance=0.8,  # Default importance
                    section="analysis",
                    related_figures=[]
                ))
        
        # If we couldn't extract specific sections, just take the first few paragraphs
        if not key_points:
            paragraphs = [p.strip() for p in analysis_text.split('\n\n') if p.strip() and len(p) > 50]
            for i, para in enumerate(paragraphs[:5]):  # Take up to 5 paragraphs
                key_points.append(KeyPoint(
                    title=f"Key Point {i+1}",
                    content=para,
                    importance=0.7 - (i * 0.1),  # Decreasing importance
                    section="general",
                    related_figures=[]
                ))
        
        return key_points