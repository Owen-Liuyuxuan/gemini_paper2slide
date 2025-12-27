"""
Plan presentation structure based on paper analysis.

Creates a structured plan for the presentation with content allocation
and visual recommendations for each slide using structured output.
"""

from pathlib import Path
from typing import Dict, List

from src.llm.gemini_client import GeminiClient
from src.utils.logger import get_logger
from src.utils.models import (
    ExtractedImage,
    PDFMetadata,
    PaperAnalysis,
    PresentationPlan,
    PresentationPlanSchema,
    SlideContent,
    SlideSpec,
    SlideType,
)

logger = get_logger("presentation_planner")


class PresentationPlanner:
    """
    Plan presentation structure based on paper analysis.
    
    Creates a structured plan for the presentation with content allocation
    and visual recommendations for each slide using Gemini's structured output.
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
        pdf_images: List[ExtractedImage] = None,
        image_descriptions: Dict[int, str] = None
    ) -> PresentationPlan:
        """
        Create presentation plan based on paper analysis.
        
        Uses Gemini's structured output to generate a comprehensive plan.
        
        Args:
            paper_analysis: Analysis of the paper
            pdf_metadata: Metadata extracted from PDF
            pdf_images: Optional list of images extracted from PDF (can be None/empty)
            image_descriptions: Optional descriptions (from extraction or Gemini analysis)
        
        Returns:
            PresentationPlan object with complete presentation structure
        """
        logger.info("Creating presentation plan using structured output")
        
        # Ensure pdf_images is a list
        if pdf_images is None:
            pdf_images = []
        
        # Build comprehensive prompt for presentation planning
        prompt = self._build_presentation_plan_prompt(
            paper_analysis, 
            pdf_metadata, 
            pdf_images,
            image_descriptions
        )
        
        # Generate structured plan using Gemini
        try:
            plan_schema = self.gemini_client.generate_structured_output(
                prompt=prompt,
                response_schema=PresentationPlanSchema
            )
            logger.info(f"Generated structured plan with {plan_schema.slide_count} slides")
        except Exception as e:
            logger.error(f"Structured plan generation failed: {e}")
            # Fallback to basic plan
            plan_schema = self._create_fallback_plan(paper_analysis, pdf_metadata)
        
        # Convert schema to SlideContent objects
        slides = self._convert_plan_to_slides(plan_schema, paper_analysis, pdf_images)
        
        # Create presentation plan
        presentation_plan = PresentationPlan(
            metadata=pdf_metadata,
            analysis=paper_analysis,
            slides=slides,
            style_guidelines={
                "description": plan_schema.style_description,
                "flow": plan_schema.presentation_flow,
                "color_scheme": "professional",
                "layout": "modern",
                "consistency": "maintain visual consistency across slides"
            },
            total_slides=len(slides)
        )
        
        logger.info(f"Created presentation plan with {len(slides)} slides")
        return presentation_plan
    
    def _build_presentation_plan_prompt(
        self,
        paper_analysis: PaperAnalysis,
        pdf_metadata: PDFMetadata,
        pdf_images: List[ExtractedImage],
        image_descriptions: Dict[int, str] = None
    ) -> str:
        """
        Build comprehensive prompt for creating presentation plan.
        
        Loads template from file and fills in with paper details.
        
        Args:
            paper_analysis: Analysis of the paper
            pdf_metadata: PDF metadata
            pdf_images: Extracted images
            image_descriptions: Image descriptions
        
        Returns:
            Formatted prompt string
        """
        # Load template from file
        template = self._load_prompt_template("presentation_plan")
        
        # Format key points
        key_points_text = "\n".join([
            f"  - {kp.title} (importance: {kp.importance:.2f}): {kp.content[:200]}..."
            for kp in paper_analysis.key_points
        ])
        
        # Format available figures
        if pdf_images and len(pdf_images) > 0:
            figures_text = f"{len(pdf_images)} figures extracted"
            if image_descriptions:
                figures_text += "\nSome important figures:\n"
                for idx, desc in list(image_descriptions.items())[:5]:
                    if idx < len(pdf_images):
                        figures_text += f"  - Page {pdf_images[idx].page_num}: {desc[:150]}...\n"
        elif image_descriptions:
            # Gemini figure analysis (no extraction)
            figures_text = f"{len(image_descriptions)} figures analyzed by Gemini\n"
            for page, desc in list(image_descriptions.items())[:5]:
                figures_text += f"  - Page {page}: {desc[:150]}...\n"
        else:
            figures_text = "No figure information available"
        
        # Fill in template
        prompt = template.format(
            title=pdf_metadata.title,
            authors=', '.join(pdf_metadata.authors) if pdf_metadata.authors else 'Unknown',
            page_count=pdf_metadata.page_count,
            abstract=pdf_metadata.abstract[:300] if pdf_metadata.abstract else 'Not available',
            research_question=paper_analysis.research_question,
            methodology=paper_analysis.methodology[:200],
            key_contributions=', '.join(paper_analysis.key_contributions),
            visual_theme=paper_analysis.visual_theme,
            recommended_slide_count=paper_analysis.recommended_slide_count,
            key_points=key_points_text,
            figures=figures_text
        )
        
        return prompt
    
    def _load_prompt_template(self, template_name: str) -> str:
        """
        Load prompt template from file.
        
        Args:
            template_name: Name of the template file (without .txt extension)
        
        Returns:
            Template content
        """
        prompt_file = Path("src/llm/prompts") / f"{template_name}.txt"
        
        try:
            return prompt_file.read_text()
        except FileNotFoundError:
            logger.warning(f"Prompt template {prompt_file} not found, using default")
            return self._get_default_template(template_name)
    
    def _get_default_template(self, template_name: str) -> str:
        """
        Get default template if file not found.
        
        Args:
            template_name: Name of template
        
        Returns:
            Default template content
        """
        if template_name == "presentation_plan":
            return """Create a comprehensive presentation plan for the following academic paper:

**Paper Information:**
- Title: {title}
- Authors: {authors}
- Page Count: {page_count}
- Abstract: {abstract}...

**Analysis Summary:**
- Research Question: {research_question}
- Methodology: {methodology}...
- Key Contributions: {key_contributions}
- Visual Theme: {visual_theme}
- Recommended Slides: {recommended_slide_count}

**Key Points to Cover:**
{key_points}

**Available Figures:**
{figures}

**Task:**
Create a detailed presentation plan with proper structure, slides, style, and flow.
Provide the plan in JSON format matching the PresentationPlanSchema."""
        else:
            return "Create a presentation plan based on the provided information."
    
    def _convert_plan_to_slides(
        self,
        plan_schema: PresentationPlanSchema,
        paper_analysis: PaperAnalysis,
        pdf_images: List[ExtractedImage]
    ) -> List[SlideContent]:
        """
        Convert PresentationPlanSchema to SlideContent objects.
        
        Args:
            plan_schema: Structured plan from Gemini
            paper_analysis: Paper analysis for context
            pdf_images: Extracted images for mapping
        
        Returns:
            List of SlideContent objects
        """
        logger.debug(f"Converting plan schema with {len(plan_schema.slides)} slides")
        
        slides = []
        for slide_spec in plan_schema.slides:
            # Map string type to SlideType enum
            slide_type = self._parse_slide_type(slide_spec.type)
            
            # Map figure page numbers to image indices
            related_images = []
            for page_num in slide_spec.related_figure_pages:
                for idx, img in enumerate(pdf_images):
                    if img.page_num == page_num:
                        related_images.append(idx)
                        break
            
            slide = SlideContent(
                index=slide_spec.index,
                type=slide_type,
                title=slide_spec.title,
                main_points=slide_spec.key_points,
                visual_elements=slide_spec.visual_suggestions,
                related_pdf_images=related_images,
                notes=f"From structured plan: {plan_schema.presentation_flow[:100]}..."
            )
            slides.append(slide)
        
        logger.debug(f"Converted to {len(slides)} SlideContent objects")
        return slides
    
    def _parse_slide_type(self, type_str: str) -> SlideType:
        """
        Parse string slide type to SlideType enum.
        
        Args:
            type_str: String representation of slide type
        
        Returns:
            SlideType enum value
        """
        type_mapping = {
            "title": SlideType.TITLE,
            "agenda": SlideType.AGENDA,
            "content": SlideType.CONTENT,
            "figure": SlideType.FIGURE,
            "conclusion": SlideType.CONCLUSION,
        }
        
        type_lower = type_str.lower()
        return type_mapping.get(type_lower, SlideType.CONTENT)
    
    def _create_fallback_plan(
        self,
        paper_analysis: PaperAnalysis,
        pdf_metadata: PDFMetadata
    ) -> PresentationPlanSchema:
        """
        Create a fallback plan if structured generation fails.
        
        Args:
            paper_analysis: Paper analysis
            pdf_metadata: PDF metadata
        
        Returns:
            Basic PresentationPlanSchema
        """
        logger.warning("Creating fallback presentation plan")
        
        slides = []
        
        # Title slide
        slides.append(SlideSpec(
            index=0,
            type="title",
            title=pdf_metadata.title[:100],
            key_points=[],
            visual_suggestions="Title, authors, institutional affiliation",
            related_figure_pages=[]
        ))
        
        # Content slides from key points
        for i, kp in enumerate(paper_analysis.key_points[:8]):  # Max 8 content slides
            slides.append(SlideSpec(
                index=i+1,
                type="content",
                title=kp.title,
                key_points=[kp.content] if len(kp.content) < 200 else [kp.content[:200] + "..."],
                visual_suggestions=f"Visual elements relevant to {kp.title}",
                related_figure_pages=kp.related_figures[:2] if kp.related_figures else []
            ))
        
        # Conclusion slide
        slides.append(SlideSpec(
            index=len(slides),
            type="conclusion",
            title="Conclusions & Future Work",
            key_points=[
                "Summary of key contributions",
                "Implications of the research",
                "Future directions"
            ],
            visual_suggestions="Summary points and future directions",
            related_figure_pages=[]
        ))
        
        return PresentationPlanSchema(
            slide_count=len(slides),
            slides=slides,
            style_description=f"{paper_analysis.visual_theme} style with professional academic design",
            presentation_flow="Introduction → Methodology → Results → Conclusions"
        )
