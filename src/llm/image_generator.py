"""
Image generation orchestrator with style consistency workflow.

Generates presentation slides using Gemini's image generation capabilities,
maintaining visual consistency through style descriptions extracted from reference slides.
"""

import time
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional

from PIL import Image

from src.llm.gemini_client import GeminiClient
from src.utils.logger import get_logger
from src.utils.models import GeneratedSlide, SlideContent

logger = get_logger("image_generator")


class ImageGenerator:
    """
    Generate presentation slides with visual consistency.
    
    Uses style descriptions extracted from initial slides to maintain
    consistency across the entire presentation.
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
        self.style_description = None
        
        logger.info("ImageGenerator initialized with style consistency support")
    
    def generate_title_slide(self, paper_info: Dict) -> GeneratedSlide:
        """
        Generate title slide - becomes the style reference for consistency.
        
        Args:
            paper_info: Dictionary containing paper title, authors, theme, etc.
        
        Returns:
            GeneratedSlide object for the title slide
        """
        logger.info("Generating title slide (will be used for style extraction)")
        
        # Build prompt for title slide
        prompt = self._build_title_prompt(paper_info)
        
        # Generate the image (now returns PIL Image)
        start_time = time.time()
        image = self.gemini_client.generate_image(
            prompt=prompt,
            aspect_ratio="16:9",
            image_size="4K"
        )
        generation_time = time.time() - start_time
        
        # Convert PIL Image to bytes
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        image_bytes = buffer.getvalue()
        
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
        
        # Add to reference slides and extract style
        self.reference_slides.append(slide)
        self._extract_and_store_style(image_bytes)
        
        logger.info("Title slide generated successfully with style extracted")
        return slide
    
    def generate_content_slide(
        self, 
        content: SlideContent, 
        references: Optional[List[GeneratedSlide]] = None,
        pdf_images: List[str] = None
    ) -> GeneratedSlide:
        """
        Generate content slide using style description for consistency.
        
        Args:
            content: SlideContent object with title, points, etc.
            references: Optional list of reference slides (unused, kept for compatibility)
            pdf_images: Optional list of relevant PDF images to include
        
        Returns:
            GeneratedSlide object for the content slide
        """
        logger.info(f"Generating content slide {content.index}: {content.title}")
        
        # Format main points
        formatted_points = self._format_points(content.main_points)
        
        # Build additional context
        additional_context = ""
        if content.notes:
            additional_context += f"**Additional Context**: {content.notes}\n"
        
        if pdf_images:
            additional_context += f"**Relevant Figures**: Consider incorporating elements from {len(pdf_images)} related figures from the paper\n"
        
        # Load content slide prompt from file and format it
        base_prompt = self.gemini_client.load_prompt(
            "content_slide",
            title=content.title,
            main_points=formatted_points,
            visual_elements=content.visual_elements,
            additional_context=additional_context if additional_context else ""
        )
        
        # Generate with style consistency (returns PIL Image)
        start_time = time.time()
        image = self.gemini_client.generate_image(
            prompt=base_prompt,
            style_description=self.style_description,  # Use extracted style
            aspect_ratio="16:9",
            image_size="4K"
        )
        generation_time = time.time() - start_time
        
        # Convert PIL Image to bytes
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        image_bytes = buffer.getvalue()
        
        # Create generated slide
        slide = GeneratedSlide(
            index=content.index,
            type=content.type,
            image=image_bytes,
            prompt=base_prompt,
            generation_time=generation_time,
            content=content
        )
        
        logger.info(f"Content slide {content.index} generated successfully")
        return slide
    
    def _extract_and_store_style(self, image_bytes: bytes) -> None:
        """
        Extract and store style description from an image.
        
        Args:
            image_bytes: Image data to analyze
        """
        logger.debug("Extracting style description from title slide")
        
        try:
            # Save image temporarily for analysis
            temp_image = BytesIO(image_bytes)
            pil_image = Image.open(temp_image)
            
            # Convert back to bytes for style extraction
            style_bytes = BytesIO()
            pil_image.save(style_bytes, format='PNG')
            
            # Extract style description
            self.style_description = self.gemini_client.extract_style_from_image(
                image_data=style_bytes.getvalue()
            )
            
            logger.info(f"Style extracted: {self.style_description[:100]}...")
        except Exception as e:
            logger.error(f"Style extraction failed: {e}")
            # Use a default style description
            self.style_description = """
Professional academic presentation style with:
- Clean, modern layout
- Readable sans-serif typography
- Professional color scheme (blues/grays)
- Adequate white space
- Clear hierarchy and organization
"""
    
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
        
        # Load title slide prompt from file and format it
        prompt = self.gemini_client.load_prompt(
            "title_slide",
            title=title,
            authors=authors_str,
            theme=theme
        )
        
        return prompt
    
    def _format_points(self, points: List[str]) -> str:
        """
        Format main points for inclusion in prompt.
        
        Args:
            points: List of main points
        
        Returns:
            Formatted string
        """
        if not points:
            return "  (No specific points provided)"
        
        formatted = "\n".join([f"  • {point}" for point in points])
        return formatted