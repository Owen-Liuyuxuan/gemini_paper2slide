"""
Image generation orchestrator with reference image workflow for style consistency.

Generates presentation slides using Gemini's image generation capabilities,
maintaining visual consistency through reference images.
"""

from pathlib import Path
from typing import Dict, List

from src.llm.gemini_client import GeminiClient
from src.utils.logger import get_logger
from src.utils.models import GeneratedSlide, SlideContent

logger = get_logger("image_generator")


class ImageGenerator:
    """
    Generate presentation slides with visual consistency.
    
    Uses reference images to maintain style consistency across slides,
    starting with the title slide as the first reference.
    """
    
    def __init__(self, gemini_client: GeminiClient):
        """
        Initialize image generator.
        
        Args:
            gemini_client: Initialized GeminiClient instance
        """
        self.gemini_client = gemini_client
        self.logger = logger
        self.reference_slides = []
        
        logger.info("ImageGenerator initialized")
    
    def generate_title_slide(self, paper_info: Dict) -> GeneratedSlide:
        """
        Generate title slide - becomes first reference for style consistency.
        
        Args:
            paper_info: Dictionary containing paper title, authors, theme, etc.
        
        Returns:
            GeneratedSlide object for the title slide
        """
        logger.info("Generating title slide")
        
        # Build prompt for title slide
        prompt = self._build_title_prompt(paper_info)
        
        # Generate the image
        start_time = __import__('time').time()
        image_bytes = self.gemini_client.generate_image(
            prompt=prompt,
            aspect_ratio="16:9",
            image_size="4K"
        )
        generation_time = __import__('time').time() - start_time
        
        # Create slide content
        slide_content = SlideContent(
            index=0,
            type="title",
            title=paper_info.get("title", "Title Slide"),
            main_points=[],
            visual_elements="Academic title slide with paper title, authors, and visual theme",
            related_pdf_images=[],
            notes="Title slide for the presentation"
        )
        
        # Create generated slide
        slide = GeneratedSlide(
            index=0,
            type="title",
            image=image_bytes,
            prompt=prompt,
            generation_time=generation_time,
            content=slide_content
        )
        
        # Add to reference slides for consistency
        self.reference_slides.append(slide)
        
        logger.info("Title slide generated successfully")
        return slide
    
    def generate_reference_slide(self, content: str, title_slide: GeneratedSlide) -> GeneratedSlide:
        """
        Generate second slide using title slide as reference for consistency.
        
        Args:
            content: Content for the slide
            title_slide: Previously generated title slide to use as reference
        
        Returns:
            GeneratedSlide object for the reference slide
        """
        logger.info("Generating reference slide with title slide as reference")
        
        # Build prompt for content slide
        prompt = f"""
        Create a professional academic presentation slide with the following content:
        {content}
        
        Style: Clean, professional, suitable for academic presentation
        Visual Theme: Consistent with the research topic
        """
        
        # Generate using title slide as reference
        start_time = __import__('time').time()
        image_bytes = self.gemini_client.generate_image(
            prompt=prompt,
            reference_images=[title_slide.image],
            aspect_ratio="16:9",
            image_size="4K"
        )
        generation_time = __import__('time').time() - start_time
        
        # Create slide content
        slide_content = SlideContent(
            index=1,
            type="content",
            title="Reference Slide",
            main_points=[content],
            visual_elements="Content slide maintaining consistency with title slide",
            related_pdf_images=[],
            notes="Reference slide for maintaining visual consistency"
        )
        
        # Create generated slide
        slide = GeneratedSlide(
            index=1,
            type="content",
            image=image_bytes,
            prompt=prompt,
            generation_time=generation_time,
            content=slide_content
        )
        
        # Add to reference slides for consistency
        self.reference_slides.append(slide)
        
        logger.info("Reference slide generated successfully")
        return slide
    
    def generate_content_slide(
        self, 
        content: SlideContent, 
        references: List[GeneratedSlide], 
        pdf_images: List[str] = None
    ) -> GeneratedSlide:
        """
        Generate content slide using reference images for consistency.
        
        Args:
            content: SlideContent object with title, points, etc.
            references: List of previously generated slides to use as references
            pdf_images: Optional list of relevant PDF images to include
        
        Returns:
            GeneratedSlide object for the content slide
        """
        logger.info(f"Generating content slide {content.index}: {content.title}")
        
        # Build prompt for content slide
        prompt = f"""
        Generate a presentation slide image with the following content:

        Slide Title: {content.title}
        Main Points: {', '.join(content.main_points)}
        Visual Elements: {content.visual_elements}

        Style: Clean, professional, suitable for academic presentation
        Layout: Organized, readable, with appropriate spacing
        """
        
        if content.notes:
            prompt += f"\nAdditional Notes: {content.notes}"
        
        # Prepare reference images
        ref_images = []
        if references:
            # Use up to 2 most recent reference slides
            for ref_slide in references[-2:]:  # Use last 2 slides as reference
                ref_images.append(ref_slide.image)
        
        # Add PDF images if provided
        figure_descriptions = ""
        if pdf_images:
            figure_descriptions = f"Relevant figures from the paper: {', '.join(pdf_images)}"
            prompt += f"\n{figure_descriptions}"
        
        # Generate the slide
        start_time = __import__('time').time()
        image_bytes = self.gemini_client.generate_image(
            prompt=prompt,
            reference_images=ref_images,
            aspect_ratio="16:9",
            image_size="4K"
        )
        generation_time = __import__('time').time() - start_time
        
        # Create generated slide
        slide = GeneratedSlide(
            index=content.index,
            type=content.type,
            image=image_bytes,
            prompt=prompt,
            generation_time=generation_time,
            content=content
        )
        
        # Add to reference slides for future consistency (but limit to 2)
        self.reference_slides.append(slide)
        if len(self.reference_slides) > 2:
            # Keep only the last 2 slides as references to avoid too many images
            self.reference_slides = self.reference_slides[-2:]
        
        logger.info(f"Content slide {content.index} generated successfully")
        return slide
    
    def _build_title_prompt(self, paper_info: Dict) -> str:
        """
        Build prompt for title slide generation.
        
        Args:
            paper_info: Dictionary containing paper information
        
        Returns:
            Formatted prompt string
        """
        title = paper_info.get("title", "Research Paper")
        authors = paper_info.get("authors", [])
        theme = paper_info.get("theme", "Academic Research")
        
        authors_str = ", ".join(authors) if isinstance(authors, list) else str(authors)
        
        # Load title slide prompt template
        prompt_template = self._get_prompt('title_slide')
        
        # Format the prompt with paper information
        prompt = prompt_template.format(
            title=title,
            authors=authors_str,
            theme=theme
        )
        
        return prompt
    
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
            if prompt_name == "title_slide":
                return (
                    "Generate a visually appealing title slide for an academic presentation.\n"
                    "\nTitle: {title}\nAuthors: {authors}\nKey Theme: {theme}\n"
                    "\nStyle: Modern, professional, academic\n"
                    "Include: Title, authors, key visual metaphor for the research"
                )
            elif prompt_name == "content_slide":
                return (
                    "Generate a presentation slide image with the following content:\n"
                    "\nSlide Title: {title}\nMain Points: {points}\nVisual Theme: {theme}\n"
                    "\nReference Images: Maintain visual consistency with the provided reference slides.\n"
                    "Extracted Figures: {figure_descriptions}\n"
                    "\nStyle: Clean, professional, suitable for academic presentation"
                )
            else:
                return "Create a professional slide with the provided content."