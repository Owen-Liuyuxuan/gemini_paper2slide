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
    ExtractedImage,
    KeyPoint,
    PaperAnalysis,
    PaperAnalysisSchema,
    KeyPointSchema
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
    
    def analyze_paper(self, pdf_path: Path) -> PaperAnalysis:
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
        
        # Analyze the document
        analysis_text = self.gemini_client.analyze_document(
            pdf_path=pdf_path,
            prompt=prompt
        )
        
        logger.debug(f"Raw analysis text length: {len(analysis_text)}")
        
        # Step 2: Parse into structured format using Gemini's structured output
        structured_analysis = self._parse_to_structured_format(analysis_text)
        
        # Step 3: Convert schema to PaperAnalysis model
        paper_analysis = self._convert_to_paper_analysis(structured_analysis)
        
        logger.info(f"Analysis complete: {len(paper_analysis.key_points)} key points identified")
        
        return paper_analysis
    
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
    
    def analyze_figures_from_pdf(self, pdf_path: Path) -> Dict[int, str]:
        """
        Analyze all figures/tables directly from PDF using Gemini's vision.
        
        This method uses Gemini's multimodal capabilities to "see" the entire PDF
        and describe figures as they appear visually, avoiding the fragile PDF
        image extraction process that often splits vector graphics into sub-elements.
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            Dictionary mapping page numbers to figure descriptions
            
        Example:
            >>> analyzer = DocumentAnalyzer(gemini_client)
            >>> figures = analyzer.analyze_figures_from_pdf(Path("paper.pdf"))
            >>> print(figures[3])  # Description of figure on page 3
        """
        logger.info(f"Analyzing figures directly from PDF: {pdf_path}")
        
        # Get the prompt for figure analysis
        prompt = self._get_figure_analysis_prompt()
        
        # Analyze the document with Gemini
        try:
            from src.utils.models import PaperFiguresSchema
            
            # Use structured output to get reliable figure descriptions
            figures_schema = self.gemini_client.generate_structured_output(
                prompt=prompt,
                response_schema=PaperFiguresSchema,
                pdf_path=pdf_path
            )
            
            logger.info(f"Identified {figures_schema.total_figures} figures/tables in PDF")
            
            # Convert to dictionary mapping page -> description
            figure_descriptions = {}
            for fig in figures_schema.figures:
                page_key = fig.page_number
                description = f"""**{fig.figure_number or 'Figure'}** ({fig.figure_type})

Visual Description:
{fig.visual_description}

Content:
{fig.content_description}

Presentation Usage:
{fig.presentation_usage}

Importance: {fig.importance:.2f}"""
                
                figure_descriptions[page_key] = description
                logger.debug(f"Page {page_key}: {fig.figure_number or 'Figure'} (importance: {fig.importance:.2f})")
            
            return figure_descriptions
            
        except Exception as e:
            logger.error(f"Figure analysis failed: {e}")
            logger.warning("Falling back to empty figure descriptions")
            return {}
    
    def identify_important_figures(
        self, 
        pdf_images: List[ExtractedImage],
        paper_analysis: PaperAnalysis
    ) -> List[int]:
        """
        Identify which extracted figures are most important for presentation.
        
        Uses quality scores and optionally Gemini to analyze image relevance.
        
        Args:
            pdf_images: List of extracted images from PDF
            paper_analysis: Paper analysis for context
        
        Returns:
            List of indices of important figures
        """
        logger.info(f"Identifying important figures from {len(pdf_images)} extracted images")
        
        # Filter by quality score first
        high_quality_images = [
            (idx, img) for idx, img in enumerate(pdf_images)
            if img.quality_score >= 0.6
        ]
        
        logger.info(f"Found {len(high_quality_images)} high-quality images")
        
        # If we have too many, prioritize by quality and size
        if len(high_quality_images) > 10:
            # Sort by quality score descending
            high_quality_images.sort(key=lambda x: x[1].quality_score, reverse=True)
            high_quality_images = high_quality_images[:10]
        
        important_indices = [idx for idx, _ in high_quality_images]
        
        logger.info(f"Identified {len(important_indices)} important figures")
        return important_indices
    
    def describe_pdf_images(
        self, 
        pdf_images: List[ExtractedImage],
        limit: int = 10
    ) -> Dict[int, str]:
        """
        Generate descriptions for important PDF images.
        
        Args:
            pdf_images: List of extracted images
            limit: Maximum number of images to describe
        
        Returns:
            Dictionary mapping image index to description
        """
        logger.info(f"Generating descriptions for up to {limit} images")
        
        descriptions = {}
        important_images = [
            (idx, img) for idx, img in enumerate(pdf_images)
            if img.quality_score >= 0.6 and img.file_path
        ]
        
        # Sort by quality and limit
        important_images.sort(key=lambda x: x[1].quality_score, reverse=True)
        important_images = important_images[:limit]
        
        for idx, img in important_images:
            try:
                description = self.gemini_client.describe_image(
                    image_path=img.file_path,
                    prompt="""
Describe this figure from an academic paper comprehensively:

1. **Type**: What kind of visualization is this? (graph, diagram, photo, chart, equation, table, etc.)
2. **Content**: What are the main elements, data, or information shown?
3. **Purpose**: What does it illustrate or demonstrate?
4. **Key Insights**: What are the key findings or messages conveyed?
5. **Presentation Value**: How important would this be in a presentation? (High/Medium/Low)

Provide a clear, concise description suitable for determining slide placement.
"""
                )
                descriptions[idx] = description
                logger.debug(f"Described image {idx} from page {img.page_num}")
            except Exception as e:
                logger.warning(f"Failed to describe image {idx}: {e}")
                continue
        
        logger.info(f"Successfully described {len(descriptions)} images")
        return descriptions
    
    def _get_analysis_prompt(self) -> str:
        """
        Get prompt template for paper analysis.
        
        Returns:
            Prompt text
        """
        prompt_file = Path("src/llm/prompts/paper_analysis.txt")
        try:
            base_prompt = prompt_file.read_text()
        except FileNotFoundError:
            logger.warning(f"Prompt file {prompt_file} not found, using default")
            base_prompt = """Analyze this academic paper comprehensively."""
        
        # Enhance with structured output instructions
        enhanced_prompt = f"""{base_prompt}

Please provide a comprehensive analysis focusing on:

1. **Summary**: A clear, concise overview of the paper (2-3 sentences)
2. **Research Question**: The main research question or objective
3. **Methodology**: The approach and methods used
4. **Key Contributions**: The main contributions (3-5 items)
5. **Key Points**: Detailed points for presentation (5-10 items), each with:
   - Title (brief, descriptive)
   - Content (detailed explanation)
   - Importance (how important for presentation, 0.0-1.0)
   - Section (which part of paper)
   - Related figures (page numbers if applicable)
6. **Recommended Slides**: Suggested number of slides (5-20)
7. **Visual Theme**: Suggested visual theme for the presentation

Provide detailed analysis suitable for creating an effective academic presentation.
"""
        
        return enhanced_prompt
    
    def _get_figure_analysis_prompt(self) -> str:
        """
        Get prompt template for figure analysis from PDF.
        
        Returns:
            Prompt text for analyzing figures/tables directly from PDF
        """
        prompt_file = Path("src/llm/prompts/figure_analysis.txt")
        try:
            return prompt_file.read_text()
        except FileNotFoundError:
            logger.warning(f"Prompt file {prompt_file} not found, using default")
            return """
Analyze all figures, tables, and diagrams in this academic paper.

For each visual element (figure, table, diagram, chart, etc.), provide:
1. Page number where it appears
2. Figure/table number or caption  
3. Detailed visual description (what is shown, colors, layout, components)
4. What data or concept it illustrates
5. Its importance to the research (rate 0-1)
6. How it could be used in a presentation slide

Focus on visual elements that would be valuable for presentation slides.
Describe each figure as if explaining to someone who cannot see it.
"""
    
    def _parse_to_structured_format(self, analysis_text: str) -> PaperAnalysisSchema:
        """
        Parse raw analysis text into structured format using Gemini.
        
        Args:
            analysis_text: Raw analysis text from Gemini
        
        Returns:
            PaperAnalysisSchema object with structured information
        """
        logger.debug("Parsing analysis into structured format")
        
        structure_prompt = f"""
Based on the following paper analysis, extract structured information in JSON format.

ANALYSIS:
{analysis_text}

Extract and structure the following information:
1. summary: Overall summary (string)
2. research_question: Main research question (string)
3. methodology: Research methodology description (string)
4. key_contributions: List of key contributions (list of strings, 3-5 items)
5. key_points: List of key points for presentation (list of objects), each with:
   - title: Brief title (string)
   - content: Detailed content (string)
   - importance: Importance score 0.0-1.0 (float)
   - section: Source section (string)
   - related_figure_pages: Page numbers of related figures (list of integers)
6. recommended_slide_count: Recommended number of slides 5-20 (integer)
7. visual_theme: Suggested visual theme (string)

Ensure the output is valid JSON matching the schema.
"""
        
        try:
            structured_analysis = self.gemini_client.generate_structured_output(
                prompt=structure_prompt,
                response_schema=PaperAnalysisSchema
            )
            logger.info("Successfully parsed analysis into structured format")
            return structured_analysis
        except Exception as e:
            logger.error(f"Structured parsing failed: {e}")
            # Fallback to creating a basic structure
            return self._create_fallback_analysis(analysis_text)
    
    def _create_fallback_analysis(self, analysis_text: str) -> PaperAnalysisSchema:
        """
        Create a fallback analysis if structured parsing fails.
        
        Args:
            analysis_text: Raw analysis text
        
        Returns:
            Basic PaperAnalysisSchema
        """
        logger.warning("Using fallback analysis structure")
        
        # Create basic key points from text paragraphs
        paragraphs = [p.strip() for p in analysis_text.split('\n\n') if len(p.strip()) > 50]
        
        key_points = []
        for i, para in enumerate(paragraphs[:7]):  # Max 7 key points
            key_points.append(KeyPointSchema(
                title=f"Key Point {i+1}",
                content=para[:500],  # Limit content length
                importance=0.7 - (i * 0.05),  # Decreasing importance
                section="general",
                related_figure_pages=[]
            ))
        
        return PaperAnalysisSchema(
            summary=analysis_text[:500] if len(analysis_text) > 500 else analysis_text,
            research_question="Research question extracted from paper",
            methodology="Methodology extracted from paper",
            key_contributions=["Contribution analysis needed"],
            key_points=key_points,
            recommended_slide_count=min(len(key_points) + 3, 12),
            visual_theme="professional academic"
        )
    
    def _convert_to_paper_analysis(self, schema: PaperAnalysisSchema) -> PaperAnalysis:
        """
        Convert PaperAnalysisSchema to PaperAnalysis model.
        
        Args:
            schema: PaperAnalysisSchema from structured output
        
        Returns:
            PaperAnalysis model
        """
        logger.debug("Converting schema to PaperAnalysis model")
        
        # Convert key points
        key_points = [
            KeyPoint(
                title=kp.title,
                content=kp.content,
                importance=kp.importance,
                section=kp.section,
                related_figures=kp.related_figure_pages
            )
            for kp in schema.key_points
        ]
        
        return PaperAnalysis(
            summary=schema.summary,
            research_question=schema.research_question,
            methodology=schema.methodology,
            key_contributions=schema.key_contributions,
            key_points=key_points,
            important_figures=[],  # Will be filled by identify_important_figures
            recommended_slide_count=schema.recommended_slide_count,
            visual_theme=schema.visual_theme
        )