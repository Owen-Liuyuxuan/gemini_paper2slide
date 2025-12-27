"""
Coordinate the slide generation workflow.

Orchestrates the entire slide generation process using the image generator
and maintains reference images for visual consistency.
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
    
    Manages the entire slide generation process, using reference images
    to maintain visual consistency across all slides in the presentation.
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
        
        logger.info("SlideGenerator initialized")
    
    def generate_presentation(self, presentation_plan: PresentationPlan) -> List[GeneratedSlide]:
        """
        Generate complete presentation from plan.
        
        Args:
            presentation_plan: Complete presentation plan
        
        Returns:
            List of GeneratedSlide objects
        """
        logger.info(f"Generating presentation with {presentation_plan.total_slides} slides")
        
        slides = []
        
        # Generate slides one by one
        for i, slide_content in enumerate(presentation_plan.slides):
            logger.info(f"Generating slide {i+1}/{len(presentation_plan.slides)}: {slide_content.title}")
            
            # Generate the slide
            generated_slide = self.image_generator.generate_content_slide(
                content=slide_content,
                references=self.image_generator.reference_slides,
                pdf_images=[]  # Will be filled in generate_slide_sequence
            )
            
            slides.append(generated_slide)
        
        logger.info(f"Successfully generated {len(slides)} slides")
        return slides
    
    def generate_slide_sequence(self, plan: PresentationPlan, pdf_images: List[ExtractedImage]) -> List[GeneratedSlide]:
        """
        Generate slides in sequence maintaining visual consistency.
        
        Args:
            plan: Presentation plan with slide content
            pdf_images: List of images extracted from the PDF
        
        Returns:
            List of generated slide images
        """
        logger.info("Starting sequential slide generation")
        
        generated_slides = []
        
        # Process each slide in the plan
        for idx, slide_content in enumerate(plan.slides):
            logger.debug(f"Processing slide {slide_content.index}: {slide_content.title}")
            
            # Get related PDF images for this slide
            related_images_paths = []
            for img_idx in slide_content.related_pdf_images:
                if img_idx < len(pdf_images) and pdf_images[img_idx].file_path:
                    related_images_paths.append(str(pdf_images[img_idx].file_path))
            
            # Generate the slide with reference to previous slides for consistency
            generated_slide = self.image_generator.generate_content_slide(
                content=slide_content,
                references=self.image_generator.reference_slides,  # Use existing references
                pdf_images=related_images_paths
            )
            
            generated_slides.append(generated_slide)
            
            logger.debug(f"Generated slide {slide_content.index}")
        
        logger.info(f"Completed sequential generation of {len(generated_slides)} slides")
        return generated_slides