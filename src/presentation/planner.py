"""
Plan presentation structure based on paper analysis.

Creates a structured plan for the presentation with content allocation
and visual recommendations for each slide using structured output.
"""

from pathlib import Path

from src.llm.gemini_client import GeminiClient
from src.utils.logger import get_logger
from src.utils.models import (
    PaperAnalysisSchema,
    PresentationPlan,
    PresentationPlanSchema,
)
from src.utils.progress import ProgressCallback, ProgressStage

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

        logger.info("PresentationPlanner initialized")

    def create_plan(
        self,
        paper_analysis: PaperAnalysisSchema,
        pdf_path: Path,
        progress_callback: ProgressCallback | None = None,
    ) -> PresentationPlan:
        """
        Create presentation plan based on paper analysis.

        Uses Gemini's structured output to generate a comprehensive plan.

        Args:
            paper_analysis: Analysis of the paper
            pdf_path: Path to PDF file
            progress_callback: Optional callback for progress reporting

        Returns:
            PresentationPlan object with complete presentation structure
        """
        logger.info("Creating presentation plan using structured output")

        if progress_callback:
            progress_callback(ProgressStage.PLANNING, 10, "Starting presentation planning...")

        # Build comprehensive prompt for presentation planning
        prompt = self._build_presentation_plan_prompt(
            paper_analysis,
        )

        if progress_callback:
            progress_callback(
                ProgressStage.PLANNING, 50, "Generating slide structure and content allocation..."
            )

        # Generate structured plan using Gemini
        # This can take a long time, so we'll update progress periodically
        import threading

        progress_update_thread = None
        if progress_callback:
            stop_progress_updates = threading.Event()

            def update_progress_periodically():
                """Update progress message periodically to show system is still working"""
                messages = [
                    "Generating slide structure and content allocation...",
                    "Analyzing paper content and organizing slides...",
                    "Creating presentation structure...",
                    "Still working on presentation plan...",
                ]
                message_index = 0
                while not stop_progress_updates.wait(10):  # Update every 10 seconds
                    message_index = (message_index + 1) % len(messages)
                    progress_callback(
                        ProgressStage.PLANNING,
                        50 + (message_index * 5),  # 50-65% range
                        messages[message_index],
                    )

            progress_update_thread = threading.Thread(
                target=update_progress_periodically, daemon=True
            )
            progress_update_thread.start()

        try:
            plan_schema = self.gemini_client.generate_structured_output(
                prompt=prompt, pdf_path=pdf_path, response_schema=PresentationPlanSchema
            )

            # Stop progress update thread
            if progress_update_thread:
                stop_progress_updates.set()
                progress_update_thread.join(timeout=1)

            logger.info(f"Generated structured plan with {plan_schema.slide_count} slides")
        except Exception as e:
            # Stop progress update thread on error
            if progress_update_thread:
                stop_progress_updates.set()
                progress_update_thread.join(timeout=1)

            logger.error(f"Structured plan generation failed: {e}", exc_info=True)
            if progress_callback:
                progress_callback(ProgressStage.ERROR, 0, f"Planning failed: {str(e)}")
            raise

        # Create presentation plan
        presentation_plan = PresentationPlan(
            analysis=paper_analysis,
            slides=plan_schema.slides,
            style_guidelines={"description": plan_schema.style_description},
            total_slides=len(plan_schema.slides),
        )

        logger.info(f"Created presentation plan with {len(plan_schema.slides)} slides")

        if progress_callback:
            progress_callback(
                ProgressStage.PLANNING,
                100,
                f"Plan created with {presentation_plan.total_slides} slides",
            )

        return presentation_plan

    def _build_presentation_plan_prompt(
        self,
        paper_analysis: PaperAnalysisSchema,
    ) -> str:
        """
        Build comprehensive prompt for creating presentation plan.

        Loads template from file and fills in with paper details.

        Args:
            paper_analysis: Analysis of the paper
            pdf_metadata: PDF metadata
            image_descriptions: Image descriptions

        Returns:
            Formatted prompt string
        """
        # Load template from file
        template = self.gemini_client._load_prompt_template("presentation_plan")

        prompt = template.format(paper_analysis=paper_analysis)

        return prompt
