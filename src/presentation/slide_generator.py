"""
Coordinate the slide generation workflow.

Orchestrates the entire slide generation process using the image generator
with a 3-stage workflow: title → content with style consistency.
"""

from typing import List

from pathlib import Path
from src.utils.config_loader import get_config
from src.llm.gemini_client import GeminiClient
from src.utils.logger import get_logger
from src.utils.models import GeneratedSlide, PresentationPlan

logger = get_logger("slide_generator")


class SlideGenerator:
    """
    Coordinate slide generation workflow.
    
    Implements a 3-stage workflow:
    1. Generate title slide (extract style)
    2. Generate remaining slides using extracted style for consistency
    """
    
    def __init__(self, gemini_client: GeminiClient):
        """
        Initialize slide generator.
        
        Args:
            gemini_client: Initialized Gemini Client instance
        """
        self.gemini_client = gemini_client
        self.logger = logger
        
        logger.info("SlideGenerator initialized with 3-stage workflow")
    
    def generate_slide_sequence(
        self, 
        plan: PresentationPlan, 
        pdf_path: Path,
    ) -> List[GeneratedSlide]:
        """
        Generate slides in sequence maintaining visual consistency.
        
        Implements the proper 3-stage workflow:
        1. Generate title slide (special handling, extracts style)
        2. Generate all content slides using extracted style
        
        Args:
            plan: Presentation plan with slide content
        
        Returns:
            List of generated slide images
        """
        logger.info(f"Starting 3-stage slide generation for {plan.total_slides} slides")
        
        generated_slides = []

        output_configuration = get_config("presentation")
        image_size = output_configuration.get("image_size")
        aspect_ratio = output_configuration.get("aspect_ratio")


        for i, slide in enumerate(plan.slides):
            if slide.type.value == "title":
                prompt = self.gemini_client._load_prompt_template("title_slide")
                prompt = prompt.format(
                    paper_analysis=plan.analysis,
                    content=slide,
                    main_points="\n".join(slide.main_points)
                )
                image = self.gemini_client.generate_image(prompt, pdf_path=pdf_path, aspect_ratio=aspect_ratio, image_size=image_size)
                generated_slides.append(image)
                logger.info(f"✓ Title slide {slide.index} generated successfully")
            else:
                prompt = self.gemini_client._load_prompt_template("content_slide")
                prompt = prompt.format(
                    paper_analysis=plan.analysis,
                    content=slide,
                    main_points="\n".join(slide.main_points)
                )
                image = self.gemini_client.generate_image(prompt, pdf_path=pdf_path, aspect_ratio=aspect_ratio, image_size=image_size, base_image=generated_slides[i-1] if i > 0 else None)
                generated_slides.append(image)
                logger.info(f"✓ Content slide {slide.index} generated successfully")

        return generated_slides