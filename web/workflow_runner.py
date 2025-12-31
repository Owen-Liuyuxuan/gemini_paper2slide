"""
Workflow runner that connects the generation workflow to the status manager.

Runs the slide generation workflow and reports progress through the
JobStatusManager for web API consumption.
"""

import sys
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.llm.document_analyzer import DocumentAnalyzer
from src.llm.gemini_client import GeminiClient
from src.output.image_saver import ImageSaver
from src.presentation.planner import PresentationPlanner
from src.presentation.slide_generator import SlideGenerator
from src.utils.cache_manager import CacheManager
from src.utils.logger import get_logger
from src.utils.progress import ProgressStage, ProgressCallback

from web.status_manager import JobStatusManager

logger = get_logger("workflow_runner")


def run_generation_workflow(
    job_id: str,
    pdf_path: Path,
    output_dir: Path,
    status_manager: JobStatusManager,
    use_cache: bool = True,
    api_key: Optional[str] = None
) -> None:
    """
    Run the complete slide generation workflow with progress reporting.
    
    This function orchestrates the entire workflow and reports progress
    through the status manager for web API consumption.
    
    Args:
        job_id: Unique job identifier
        pdf_path: Path to uploaded PDF file
        output_dir: Directory for output slides
        status_manager: JobStatusManager instance for progress reporting
        use_cache: Whether to use cached intermediate results
        api_key: Google Gemini API key (optional, falls back to config/env)
    """
    def progress_callback(
        stage: ProgressStage,
        progress: int,
        message: str,
        details: dict = None
    ) -> None:
        """Callback to update job status"""
        status_manager.update_status(job_id, stage, progress, message, details)
        logger.info(f"[{job_id}] {stage.value}: {progress}% - {message}")
    
    try:
        # Initialize output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components with provided API key
        gemini_client = GeminiClient(api_key=api_key) if api_key else GeminiClient()
        cache = CacheManager() if use_cache else None
        
        # STEP 1: Analyze paper
        progress_callback(ProgressStage.ANALYZING, 5, "Initializing...")
        doc_analyzer = DocumentAnalyzer(gemini_client)
        
        cache_key = f"analysis_{pdf_path.stem}"
        
        if cache and cache.exists(cache_key):
            paper_analysis = cache.get(cache_key)
            logger.info(f"[{job_id}] Retrieved analysis from cache")
            progress_callback(ProgressStage.ANALYZING, 100, "Retrieved analysis from cache")
        else:
            paper_analysis = doc_analyzer.analyze_paper(
                pdf_path,
                progress_callback=progress_callback
            )
            if cache:
                cache.set(cache_key, paper_analysis)
            logger.info(f"[{job_id}] Paper analysis complete")
        
        # STEP 2: Create presentation plan
        progress_callback(ProgressStage.PLANNING, 30, "Creating presentation plan...")
        planner = PresentationPlanner(gemini_client)
        plan = planner.create_plan(
            paper_analysis,
            pdf_path,
            progress_callback=lambda stage, p, m, details=None: progress_callback(
                ProgressStage.PLANNING, 30 + int(p * 0.1), m, details
            )
        )
        logger.info(f"[{job_id}] Created plan with {plan.total_slides} slides")
        
        # STEP 3: Generate slides (with per-slide progress)
        progress_callback(
            ProgressStage.GENERATING_SLIDES,
            40,
            f"Starting slide generation ({plan.total_slides} slides)..."
        )
        slide_generator = SlideGenerator(gemini_client)
        slides = slide_generator.generate_slide_sequence(
            plan,
            pdf_path,
            progress_callback=lambda stage, p, m, details=None: progress_callback(
                ProgressStage.GENERATING_SLIDES, 40 + int(p * 0.5), m, details
            )
        )
        logger.info(f"[{job_id}] Generated {len(slides)} slides")
        
        # STEP 4: Save outputs
        progress_callback(ProgressStage.SAVING, 90, "Saving slides to disk...")
        image_saver = ImageSaver(str(output_dir))
        slide_paths = image_saver.save_slides(slides)
        logger.info(f"[{job_id}] Saved {len(slides)} slide images")
        
        progress_callback(ProgressStage.SAVING, 95, "Merging slides into PDF...")
        pdf_path_output = image_saver.merge_slides_to_pdf(slide_paths=slide_paths)
        logger.info(f"[{job_id}] Merged slides into PDF: {pdf_path_output.name}")
        
        progress_callback(
            ProgressStage.COMPLETE,
            100,
            f"Successfully generated {len(slides)} slides!"
        )
        logger.info(f"[{job_id}] Generation complete!")
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"[{job_id}] Generation failed: {error_msg}", exc_info=True)
        status_manager.set_error(job_id, error_msg)
        raise

