"""
Write additional metadata for the presentation.

Handles saving additional metadata files such as slide notes, presentation outline, etc.
"""

import json
from pathlib import Path

from src.utils.logger import get_logger
from src.utils.models import GeneratedSlide, PresentationPlan

logger = get_logger("metadata_writer")


class MetadataWriter:
    """
    Write additional metadata for the presentation.

    Handles saving additional metadata files such as slide notes, presentation outline, etc.
    """

    def __init__(self, output_dir: str):
        """
        Initialize metadata writer.

        Args:
            output_dir: Directory to save metadata to
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"MetadataWriter initialized with output directory: {self.output_dir}")

    def save_slide_notes(self, slides: list[GeneratedSlide]) -> None:
        """
        Save speaker notes for each slide.

        Args:
            slides: List of GeneratedSlide objects
        """
        logger.info(f"Saving slide notes to {self.output_dir}")

        notes_data = []
        for slide in slides:
            notes_data.append(
                {
                    "slide_index": slide.index,
                    "slide_type": slide.type.value,
                    "title": slide.content.title,
                    "notes": slide.content.notes,
                    "main_points": slide.content.main_points,
                }
            )

        notes_path = self.output_dir / "slide_notes.json"
        with open(notes_path, "w", encoding="utf-8") as f:
            json.dump(notes_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Slide notes saved to {notes_path}")

    def save_presentation_outline(self, presentation_plan: PresentationPlan) -> None:
        """
        Save presentation outline based on the plan.

        Args:
            presentation_plan: The presentation plan
        """
        logger.info(f"Saving presentation outline to {self.output_dir}")

        outline_data = {
            "title": presentation_plan.metadata.title,
            "authors": presentation_plan.metadata.authors,
            "outline": [
                {
                    "slide_index": slide.index,
                    "slide_type": slide.type.value,
                    "title": slide.title,
                    "main_points": slide.main_points[:2],  # First 2 main points
                    "related_figures": slide.related_pdf_images,
                }
                for slide in presentation_plan.slides
            ],
            "total_slides": presentation_plan.total_slides,
            "key_themes": presentation_plan.analysis.key_contributions,
        }

        outline_path = self.output_dir / "presentation_outline.json"
        with open(outline_path, "w", encoding="utf-8") as f:
            json.dump(outline_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Presentation outline saved to {outline_path}")

    def save_generation_log(self, slides: list[GeneratedSlide]) -> None:
        """
        Save a log of generation statistics.

        Args:
            slides: List of GeneratedSlide objects
        """
        logger.info(f"Saving generation log to {self.output_dir}")

        total_time = sum(slide.generation_time for slide in slides)
        avg_time = total_time / len(slides) if slides else 0

        log_data = {
            "total_slides_generated": len(slides),
            "total_generation_time": total_time,
            "average_generation_time_per_slide": avg_time,
            "generation_times_per_slide": [
                {
                    "slide_index": slide.index,
                    "slide_type": slide.type.value,
                    "generation_time": slide.generation_time,
                    "size_mb": slide.size_mb,
                }
                for slide in slides
            ],
        }

        log_path = self.output_dir / "generation_log.json"
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Generation log saved to {log_path}")
