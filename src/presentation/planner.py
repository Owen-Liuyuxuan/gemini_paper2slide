"""
Plan presentation structure based on paper analysis.

Creates a structured plan for the presentation with content allocation
and visual recommendations for each slide.
"""

from pathlib import Path
from typing import Dict, List

from src.llm.gemini_client import GeminiClient
from src.utils.logger import get_logger
from src.utils.models import ExtractedImage, PDFMetadata, PaperAnalysis, PresentationPlan, SlideContent, SlideType

logger = get_logger("presentation_planner")


class PresentationPlanner:
    """
    Plan presentation structure based on paper analysis.
    
    Creates a structured plan for the presentation with content allocation
    and visual recommendations for each slide.
    """
    
    def __init__(self, gemini_client: GeminiClient):
        """
        Initialize presentation planner.
        
        Args:
            gemini_client: Initialized GeminiClient instance
        """
        self.gemini_client = gemini_client
        self.logger = logger
        
        logger.info("PresentationPlanner initialized")
    
    def create_plan(
        self, 
        paper_analysis: PaperAnalysis, 
        pdf_metadata: PDFMetadata, 
        pdf_images: List[ExtractedImage]
    ) -> PresentationPlan:
        """
        Create presentation plan based on paper analysis.
        
        Args:
            paper_analysis: Analysis of the paper
            pdf_metadata: Metadata extracted from PDF
            pdf_images: List of images extracted from PDF
        
        Returns:
            PresentationPlan object with complete presentation structure
        """
        logger.info("Creating presentation plan")
        
        # Build prompt for presentation planning
        prompt = self._build_presentation_plan_prompt(paper_analysis)
        
        # Generate plan using Gemini
        plan_text = self.gemini_client.generate_text(
            prompt=prompt,
            max_tokens=2048
        )
        
        # Parse the plan text into structured format
        slides = self._parse_plan_to_slides(plan_text, paper_analysis)
        
        # Create presentation plan
        presentation_plan = PresentationPlan(
            metadata=pdf_metadata,
            analysis=paper_analysis,
            slides=slides,
            style_guidelines=self._get_style_guidelines(),
            total_slides=len(slides)
        )
        
        logger.info(f"Created presentation plan with {len(slides)} slides")
        return presentation_plan
    
    def allocate_content_to_slides(self, key_points: List) -> List[SlideContent]:
        """
        Allocate content to slides based on importance and flow.
        
        Args:
            key_points: List of key points to allocate
        
        Returns:
            List of SlideContent objects
        """
        logger.debug("Allocating content to slides")
        
        slides = []
        
        # Create title slide
        title_slide = SlideContent(
            index=0,
            type=SlideType.TITLE,
            title="Presentation Title",
            main_points=[],
            visual_elements="Title, authors, affiliation",
            related_pdf_images=[],
            notes="Title slide with paper title and authors"
        )
        slides.append(title_slide)
        
        # Create agenda slide if we have enough content
        if len(key_points) > 3:
            agenda_points = [kp.title for kp in key_points[:5]]  # Up to 5 agenda items
            agenda_slide = SlideContent(
                index=1,
                type=SlideType.AGENDA,
                title="Presentation Outline",
                main_points=agenda_points,
                visual_elements="Bullet points or numbered list",
                related_pdf_images=[],
                notes="Overview of presentation structure"
            )
            slides.append(agenda_slide)
        
        # Create content slides for key points
        for i, key_point in enumerate(key_points):
            slide_index = len(slides)  # Adjust for title and agenda slides
            
            # Determine slide type based on content
            slide_type = self._determine_slide_type(key_point)
            
            slide = SlideContent(
                index=slide_index,
                type=slide_type,
                title=key_point.title,
                main_points=[key_point.content] if len(key_point.content) < 200 else 
                           self._split_content(key_point.content),
                visual_elements="Relevant visual elements for the topic",
                related_pdf_images=key_point.related_figures,
                notes=f"Key point: {key_point.section}"
            )
            slides.append(slide)
        
        # Add conclusion slide
        conclusion_slide = SlideContent(
            index=len(slides),
            type=SlideType.CONCLUSION,
            title="Conclusions & Future Work",
            main_points=["Summary of key findings", "Implications", "Future research directions"],
            visual_elements="Summary points, potential next steps",
            related_pdf_images=[],
            notes="Concluding remarks and future work"
        )
        slides.append(conclusion_slide)
        
        logger.debug(f"Allocated content to {len(slides)} slides")
        return slides
    
    def plan_visual_elements(self, slide_content: SlideContent, pdf_images: List[ExtractedImage]) -> str:
        """
        Plan visual elements for a specific slide.
        
        Args:
            slide_content: Content for the slide
            pdf_images: List of images extracted from the PDF
        
        Returns:
            Description of planned visual elements
        """
        logger.debug(f"Planning visual elements for slide: {slide_content.title}")
        
        # Determine relevant images for this slide
        relevant_images = []
        if slide_content.related_pdf_images:
            for img_idx in slide_content.related_pdf_images:
                if img_idx < len(pdf_images):
                    relevant_images.append(f"Image from page {pdf_images[img_idx].page_num}")
        
        # Create visual element description
        visual_desc = f"Suggested visual elements for '{slide_content.title}': "
        
        if relevant_images:
            visual_desc += f"Incorporate relevant figures: {', '.join(relevant_images)}. "
        
        # Add general visual suggestions based on slide type
        if slide_content.type == SlideType.TITLE:
            visual_desc += "Use consistent color scheme with institutional branding, include visual metaphor for research topic."
        elif slide_content.type == SlideType.AGENDA:
            visual_desc += "Use clean layout with numbered or bulleted items, visual indicators for each section."
        elif slide_content.type == SlideType.CONCLUSION:
            visual_desc += "Summarize key points visually, use consistent styling with previous slides."
        else:
            visual_desc += "Use clear, readable layout with appropriate spacing, consistent fonts and colors."
        
        return visual_desc
    
    def _build_presentation_plan_prompt(self, paper_analysis: PaperAnalysis) -> str:
        """
        Build prompt for creating presentation plan.
        
        Args:
            paper_analysis: Analysis of the paper
        
        Returns:
            Formatted prompt string
        """
        # Load presentation plan prompt template
        prompt_template = self._get_prompt('presentation_plan')
        
        # Format the prompt with paper analysis
        prompt = prompt_template.format(
            analysis=f"""
Summary: {paper_analysis.summary}
Research Question: {paper_analysis.research_question}
Methodology: {paper_analysis.methodology}
Key Contributions: {", ".join(paper_analysis.key_contributions)}
Recommended Slides: {paper_analysis.recommended_slide_count}
Visual Theme: {paper_analysis.visual_theme}
"""
        )
        
        return prompt
    
    def _parse_plan_to_slides(self, plan_text: str, paper_analysis: PaperAnalysis) -> List[SlideContent]:
        """
        Parse presentation plan text into structured SlideContent objects.
        
        Args:
            plan_text: Text containing the presentation plan
            paper_analysis: Analysis of the paper for reference
        
        Returns:
            List of SlideContent objects
        """
        logger.debug("Parsing presentation plan to slides")
        
        # For this implementation, we'll create a basic allocation
        # In a more advanced implementation, we could use NLP or Gemini to parse the plan
        
        # Create slides based on the key points from the analysis
        slides = []
        
        # Title slide
        title_slide = SlideContent(
            index=0,
            type=SlideType.TITLE,
            title=paper_analysis.summary[:50] + "..." if len(paper_analysis.summary) > 50 else paper_analysis.summary,
            main_points=[],
            visual_elements="Title, authors, affiliation, visual metaphor for research",
            related_pdf_images=[],
            notes="Title slide with paper information"
        )
        slides.append(title_slide)
        
        # Add slides for each key point in the analysis
        for i, key_point in enumerate(paper_analysis.key_points):
            slide_index = i + 1  # +1 because of title slide
            
            # Determine the most appropriate slide type
            if "method" in key_point.title.lower():
                slide_type = SlideType.CONTENT
            elif "result" in key_point.title.lower() or "finding" in key_point.title.lower():
                slide_type = SlideType.FIGURE if paper_analysis.important_figures else SlideType.CONTENT
            elif "conclusion" in key_point.title.lower():
                slide_type = SlideType.CONCLUSION
            else:
                slide_type = SlideType.CONTENT
            
            # Split content if it's too long
            content_parts = self._split_content(key_point.content, max_length=200)
            
            slide = SlideContent(
                index=slide_index,
                type=slide_type,
                title=key_point.title,
                main_points=content_parts,
                visual_elements=f"Visual elements relevant to {key_point.title}",
                related_pdf_images=key_point.related_figures or paper_analysis.important_figures[:2],  # Use up to 2 important figures
                notes=f"Importance: {key_point.importance}, Section: {key_point.section}"
            )
            slides.append(slide)
        
        # Add a conclusion slide if we don't already have one
        has_conclusion = any(slide.type == SlideType.CONCLUSION for slide in slides)
        if not has_conclusion:
            conclusion_slide = SlideContent(
                index=len(slides),
                type=SlideType.CONCLUSION,
                title="Conclusions & Impact",
                main_points=["Key contributions", "Significance of results", "Future directions"],
                visual_elements="Summary of key points, impact statement",
                related_pdf_images=paper_analysis.important_figures[:1],  # Use one important figure
                notes="Final summary and implications"
            )
            slides.append(conclusion_slide)
        
        logger.debug(f"Parsed plan into {len(slides)} slides")
        return slides
    
    def _get_prompt(self, prompt_name: str) -> str:
        """
        Get prompt template from file.
        
        Args:
            prompt_name: Name of the prompt file (without extension)
        
        Returns:
            Prompt text
        """
        prompt_file = Path(f"src/llm/prompts/{prompt_name}.txt")
        try:
            return prompt_file.read_text()
        except FileNotFoundError:
            logger.warning(f"Prompt file {prompt_file} not found, using default")
            # Return a default prompt
            if prompt_name == "presentation_plan":
                return (
                    "Based on the paper analysis, create a presentation plan with:\n"
                    "1. Recommended number of slides (typically 8-12)\n"
                    "2. Content allocation for each slide\n"
                    "3. Visual style recommendations\n"
                    "4. Key messages for each slide\n"
                    "\nPaper Analysis:\n{analysis}"
                )
            else:
                return "Create a presentation plan based on the provided analysis."
    
    def _determine_slide_type(self, key_point) -> SlideType:
        """
        Determine the most appropriate slide type for a key point.
        
        Args:
            key_point: Key point to evaluate
        
        Returns:
            Appropriate SlideType
        """
        title_lower = key_point.title.lower()
        
        if any(word in title_lower for word in ["title", "cover"]):
            return SlideType.TITLE
        elif any(word in title_lower for word in ["outline", "agenda", "overview"]):
            return SlideType.AGENDA
        elif any(word in title_lower for word in ["conclusion", "summary", "wrap", "end"]):
            return SlideType.CONCLUSION
        elif any(word in title_lower for word in ["figure", "diagram", "chart", "graph", "image"]):
            return SlideType.FIGURE
        else:
            return SlideType.CONTENT
    
    def _split_content(self, content: str, max_length: int = 150) -> List[str]:
        """
        Split content into smaller chunks if it's too long.
        
        Args:
            content: Content to split
            max_length: Maximum length for each chunk
        
        Returns:
            List of content chunks
        """
        if len(content) <= max_length:
            return [content]
        
        # Split by sentences
        sentences = content.split('. ')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk + ". " + sentence) <= max_length:
                if current_chunk:
                    current_chunk += ". " + sentence
                else:
                    current_chunk = sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk + ".")
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk + ("." if not current_chunk.endswith(".") else ""))
        
        # If we still have chunks that are too long, just truncate
        final_chunks = []
        for chunk in chunks:
            if len(chunk) <= max_length:
                final_chunks.append(chunk)
            else:
                # Split by words if still too long
                words = chunk.split()
                temp_chunk = ""
                for word in words:
                    if len(temp_chunk + " " + word) <= max_length:
                        temp_chunk += " " + word if temp_chunk else word
                    else:
                        if temp_chunk:
                            final_chunks.append(temp_chunk)
                        temp_chunk = word
                if temp_chunk:
                    final_chunks.append(temp_chunk)
        
        return final_chunks if final_chunks else [content[:max_length]]
    
    def _get_style_guidelines(self) -> Dict:
        """
        Get default style guidelines for the presentation.
        
        Returns:
            Dictionary of style guidelines
        """
        return {
            "color_scheme": "professional",
            "layout": "modern",
            "font_style": "clean sans-serif",
            "margins": "adequate for readability",
            "consistency": "maintain visual consistency across slides"
        }