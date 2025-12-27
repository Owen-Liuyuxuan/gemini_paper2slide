"""
Save generated slide images to disk.

Handles saving slide images and organizing them in the output directory.
"""

import json
from pathlib import Path
from typing import List

from src.utils.logger import get_logger
from src.utils.models import GeneratedSlide, PresentationPlan

logger = get_logger("image_saver")


class ImageSaver:
    """
    Save generated slide images to disk.
    
    Handles saving slide images and organizing them in the output directory.
    """
    
    def __init__(self, output_dir: str):
        """
        Initialize image saver.
        
        Args:
            output_dir: Directory to save images to
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"ImageSaver initialized with output directory: {self.output_dir}")
    
    def save_slides(self, slides: List[GeneratedSlide]) -> None:
        """
        Save all generated slides to disk.
        
        Args:
            slides: List of GeneratedSlide objects to save
        
        Example:
            >>> saver = ImageSaver("output/")
            >>> saver.save_slides(generated_slides)
        """
        logger.info(f"Saving {len(slides)} slides to {self.output_dir}")
        
        for slide in slides:
            # Create filename based on slide index
            filename = f"slide_{slide.index:02d}.{slide.content.type.value}.png"
            filepath = self.output_dir / filename
            
            # Save the image
            with open(filepath, 'wb') as f:
                f.write(slide.image)
            
            # Update slide with file path
            slide.file_path = filepath
            logger.debug(f"Saved slide {slide.index} to {filepath}")
        
        logger.info(f"Successfully saved {len(slides)} slides")
    
    def save_metadata(self, presentation_plan: PresentationPlan, slides: List[GeneratedSlide]) -> None:
        """
        Save presentation metadata to disk.
        
        Args:
            presentation_plan: The presentation plan
            slides: List of generated slides
        """
        logger.info(f"Saving presentation metadata to {self.output_dir}")
        
        # Create metadata dictionary
        metadata = {
            "presentation_info": {
                "title": presentation_plan.metadata.title,
                "authors": presentation_plan.metadata.authors,
                "abstract": presentation_plan.metadata.abstract,
                "page_count": presentation_plan.metadata.page_count,
                "file_path": str(presentation_plan.metadata.file_path)
            },
            "analysis_info": {
                "summary": presentation_plan.analysis.summary,
                "research_question": presentation_plan.analysis.research_question,
                "methodology": presentation_plan.analysis.methodology,
                "key_contributions": presentation_plan.analysis.key_contributions,
                "recommended_slide_count": presentation_plan.analysis.recommended_slide_count,
                "visual_theme": presentation_plan.analysis.visual_theme
            },
            "slide_info": [
                {
                    "index": slide.index,
                    "type": slide.type.value,
                    "title": slide.content.title,
                    "main_points": slide.content.main_points,
                    "visual_elements": slide.content.visual_elements,
                    "related_pdf_images": slide.content.related_pdf_images,
                    "notes": slide.content.notes,
                    "file_path": str(slide.file_path) if slide.file_path else None,
                    "generation_time": slide.generation_time,
                    "size_mb": slide.size_mb
                }
                for slide in slides
            ],
            "generation_stats": {
                "total_slides": len(slides),
                "total_generation_time": sum(slide.generation_time for slide in slides),
                "average_generation_time": sum(slide.generation_time for slide in slides) / len(slides) if slides else 0
            }
        }
        
        # Save metadata to JSON file
        metadata_path = self.output_dir / "presentation_metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Metadata saved to {metadata_path}")