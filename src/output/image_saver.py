"""
Save generated slide images to disk.

Handles saving slide images and organizing them in the output directory.
Also provides functionality to merge slides into a single PDF file.
"""

import json
from pathlib import Path
from typing import List, Optional
from PIL import Image
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
    
    def save_slides(self, slides: List[Image.Image]) -> List[Path]:
        """
        Save all generated slides to disk as PNG files.
        
        Args:
            slides: List of PIL Image objects to save
        
        Returns:
            List of file paths where slides were saved
        
        Example:
            >>> saver = ImageSaver("output/")
            >>> paths = saver.save_slides(generated_slides)
        """
        logger.info(f"Saving {len(slides)} slides to {self.output_dir}")
        
        saved_paths = []
        for index, slide in enumerate(slides):
            # Create filename based on slide index
            filename = f"slide_{index:02d}.png"
            filepath = self.output_dir / filename
            
            # Save the image (PNG supports all modes)
            slide.save(filepath, 'PNG')
            saved_paths.append(filepath)
        
        logger.info(f"Successfully saved {len(slides)} slides as PNG files")
        return saved_paths
    
    def merge_slides_to_pdf(
        self, 
        slide_paths: Optional[List[Path]] = None,
        output_filename: str = "presentation.pdf"
    ) -> Path:
        """
        Merge sequence of slide images into a single PDF file.
        
        If slide_paths is not provided, will look for slide_*.png files
        in the output directory in numerical order.
        
        Args:
            slide_paths: Optional list of image file paths to merge.
                        If None, automatically finds slide_*.png files.
            output_filename: Name of the output PDF file (default: presentation.pdf)
        
        Returns:
            Path to the created PDF file
        
        Example:
            >>> saver = ImageSaver("output/")
            >>> saver.save_slides(slides)
            >>> pdf_path = saver.merge_slides_to_pdf()
            >>> # Or with explicit paths
            >>> pdf_path = saver.merge_slides_to_pdf(slide_paths=paths)
        """
        if slide_paths is None:
            # Find all slide PNG files in numerical order
            slide_files = sorted(self.output_dir.glob("slide_*.png"))
            if not slide_files:
                raise FileNotFoundError(
                    f"No slide images found in {self.output_dir}. "
                    "Please save slides first using save_slides()."
                )
            slide_paths = slide_files
            logger.info(f"Found {len(slide_paths)} slide images to merge")
        else:
            logger.info(f"Merging {len(slide_paths)} specified slide images")
        
        # Ensure all images are in RGB mode for PDF
        images = []
        for slide_path in slide_paths:
            if not slide_path.exists():
                logger.warning(f"Slide image not found: {slide_path}, skipping")
                continue
            
            img = Image.open(slide_path)
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            images.append(img)
        
        if not images:
            raise ValueError("No valid slide images found to merge into PDF")
        
        # Create PDF output path
        pdf_path = self.output_dir / output_filename
        
        # Save all images as a single PDF
        # PIL's save() method can save multiple images to a PDF
        # by appending them sequentially
        logger.info(f"Creating PDF with {len(images)} slides...")
        images[0].save(
            pdf_path,
            'PDF',
            resolution=100.0,
            save_all=True,
            append_images=images[1:] if len(images) > 1 else []
        )
        
        logger.info(f"✓ Successfully created PDF: {pdf_path}")
        logger.info(f"  PDF contains {len(images)} slides")
        logger.info(f"  File size: {pdf_path.stat().st_size / (1024*1024):.2f} MB")
        
        return pdf_path
    
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
        }
        
        # Save metadata to JSON file
        metadata_path = self.output_dir / "presentation_metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Metadata saved to {metadata_path}")