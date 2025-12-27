"""
Coordinate the slide generation workflow.

Orchestrates the entire slide generation process using the image generator
with a 3-stage workflow: title → content with style consistency.
"""

from typing import List

from src.llm.image_generator import ImageGenerator
from src.presentation.style_manager import StyleManager
from src.utils.logger import get_logger
from src.utils.models import ExtractedImage, GeneratedSlide, PresentationPlan

logger = get_logger("slide_generator")


class SlideGenerator:
    """
    Coordinate slide generation workflow.
    
    Implements a 3-stage workflow:
    1. Generate title slide (extract style)
    2. Generate remaining slides using extracted style for consistency
    """
    
    def __init__(self, image_generator: ImageGenerator, style_manager: StyleManager):
        """
        Initialize slide generator.
        
        Args:
            image_generator: Initialized ImageGenerator instance
            style_manager: Initialized StyleManager instance
        """
        self.image_generator = image_generator
        self.style_manager = style_manager
        self.logger = logger
        
        logger.info("SlideGenerator initialized with 3-stage workflow")
    
    def generate_slide_sequence(
        self, 
        plan: PresentationPlan, 
        pdf_images: List[ExtractedImage]
    ) -> List[GeneratedSlide]:
        """
        Generate slides in sequence maintaining visual consistency.
        
        Implements the proper 3-stage workflow:
        1. Generate title slide (special handling, extracts style)
        2. Generate all content slides using extracted style
        
        Args:
            plan: Presentation plan with slide content
            pdf_images: List of images extracted from the PDF
        
        Returns:
            List of generated slide images
        """
        logger.info(f"Starting 3-stage slide generation for {plan.total_slides} slides")
        
        generated_slides = []
        
        # STAGE 1: Generate title slide (special handling)
        if len(plan.slides) > 0 and plan.slides[0].type.value == "title":
            logger.info("STAGE 1: Generating title slide with style extraction")
            
            title_info = {
                "title": plan.metadata.title,
                "authors": plan.metadata.authors,
                "theme": plan.analysis.visual_theme
            }
            
            try:
                title_slide = self.image_generator.generate_title_slide(title_info)
                generated_slides.append(title_slide)
                logger.info("✓ Title slide generated, style extracted for consistency")
            except Exception as e:
                logger.error(f"Failed to generate title slide: {e}")
                raise
            
            # Start from second slide
            remaining_slides = plan.slides[1:]
        else:
            logger.warning("No title slide found in plan, generating all slides without style extraction")
            remaining_slides = plan.slides
        
        # STAGE 2: Generate all remaining slides using extracted style
        logger.info(f"STAGE 2: Generating {len(remaining_slides)} content slides with style consistency")
        
        for idx, slide_content in enumerate(remaining_slides, start=1):
            logger.info(f"Generating slide {slide_content.index}/{plan.total_slides}: {slide_content.title}")
            
            # Get related PDF images for this slide
            related_images_paths = []
            for img_idx in slide_content.related_pdf_images:
                if img_idx < len(pdf_images) and pdf_images[img_idx].file_path:
                    related_images_paths.append(str(pdf_images[img_idx].file_path))
            
            try:
                # Generate the slide with style consistency
                generated_slide = self.image_generator.generate_content_slide(
                    content=slide_content,
                    references=self.image_generator.reference_slides,  # Not used but kept for compatibility
                    pdf_images=related_images_paths
                )
                
                generated_slides.append(generated_slide)
                logger.info(f"✓ Slide {slide_content.index} generated successfully")
            except Exception as e:
                logger.error(f"Failed to generate slide {slide_content.index}: {e}")
                # Continue with other slides instead of failing completely
                continue
        
        logger.info(f"✓ Completed slide generation: {len(generated_slides)}/{plan.total_slides} slides successful")
        
        if len(generated_slides) < plan.total_slides:
            logger.warning(f"Only {len(generated_slides)}/{plan.total_slides} slides generated successfully")
        
        return generated_slides