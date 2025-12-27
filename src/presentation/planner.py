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
        
        logger.info("PresentationPlanner initialized with structured output support")
    
    def create_plan(
        self, 
        paper_analysis: PaperAnalysis, 
        pdf_metadata: PDFMetadata, 
        pdf_images: List[ExtractedImage],
        image_descriptions: Dict[int, str] = None
    ) -> PresentationPlan:
        """
        Create presentation plan based on paper analysis.
        
        Uses Gemini's structured output to generate a comprehensive plan.
        
        Args:
            paper_analysis: Analysis of the paper
            pdf_metadata: Metadata extracted from PDF
            pdf_images: List of images extracted from PDF
            image_descriptions: Optional descriptions of extracted images
        
        Returns:
            PresentationPlan object with complete presentation structure
        """
        logger.info("Creating presentation plan using structured output")
        
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
        
        Args:
            paper_analysis: Analysis of the paper
            pdf_metadata: PDF metadata
            pdf_images: Extracted images
            image_descriptions: Image descriptions
        
        Returns:
            Formatted prompt string
        """
        # Format key points
        key_points_text = "\n".join([
            f"  - {kp.title} (importance: {kp.importance:.2f}): {kp.content[:200]}..."
            for kp in paper_analysis.key_points
        ])
        
        # Format available figures
        figures_text = f"{len(pdf_images)} figures extracted"
        if image_descriptions:
            figures_text += "\nSome important figures:\n"
            for idx, desc in list(image_descriptions.items())[:5]:
                figures_text += f"  - Page {pdf_images[idx].page_num}: {desc[:150]}...\n"
        
        prompt = f"""
Create a comprehensive presentation plan for the following academic paper:

**Paper Information:**
- Title: {pdf_metadata.title}
- Authors: {', '.join(pdf_metadata.authors) if pdf_metadata.authors else 'Unknown'}
- Page Count: {pdf_metadata.page_count}
- Abstract: {pdf_metadata.abstract[:300] if pdf_metadata.abstract else 'Not available'}...

**Analysis Summary:**
- Research Question: {paper_analysis.research_question}
- Methodology: {paper_analysis.methodology[:200]}...
- Key Contributions: {', '.join(paper_analysis.key_contributions)}
- Visual Theme: {paper_analysis.visual_theme}
- Recommended Slides: {paper_analysis.recommended_slide_count}

**Key Points to Cover:**
{key_points_text}

**Available Figures:**
{figures_text}

**Task:**
Create a detailed presentation plan that:

1. **Structure**: Design a logical flow from introduction to conclusion
2. **Slides**: For each slide, specify:
   - Slide type: "title", "agenda", "content", "figure", or "conclusion"
   - Title: Clear, descriptive title
   - Key points: 3-5 bullet points or main messages
   - Visual suggestions: What visual elements to include
   - Related figures: Which PDF figures (by page number) to incorporate

3. **Style**: Define a cohesive visual style that:
   - Matches the research topic ({paper_analysis.visual_theme})
   - Is professional and academic
   - Maintains consistency across all slides

4. **Flow**: Ensure the presentation tells a compelling story

**Requirements:**
- Total slides: {paper_analysis.recommended_slide_count} (±2 is acceptable)
- Include: 1 title slide, content slides, 1 conclusion slide
- Optional: 1 agenda/outline slide if beneficial
- Distribute content evenly across slides
- Match important figures to relevant content

Provide the plan in JSON format.
"""
        
        return prompt
    
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