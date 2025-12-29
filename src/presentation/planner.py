"""
Plan presentation structure based on paper analysis.

Creates a structured plan for the presentation with content allocation
and visual recommendations for each slide using structured output.
"""

from pathlib import Path
from typing import Dict, List

from src.llm.gemini_client import GeminiClient
from src.utils.config_loader import get_config
from src.utils.logger import get_logger
from src.utils.models import (
    PaperAnalysisSchema,
    PresentationPlan,
    PresentationPlanSchema,
    SlideContent,
    SlideType,
)

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
        pdf_path: Path
    ) -> PresentationPlan:
        """
        Create presentation plan based on paper analysis.
        
        Uses Gemini's structured output to generate a comprehensive plan.
        
        Args:
            paper_analysis: Analysis of the paper
            pdf_metadata: Metadata extracted from PDF
            image_descriptions: Optional descriptions (from extraction or Gemini analysis)
        
        Returns:
            PresentationPlan object with complete presentation structure
        """
        logger.info("Creating presentation plan using structured output")

        
        # Build comprehensive prompt for presentation planning
        prompt = self._build_presentation_plan_prompt(
            paper_analysis,
        )
        
        # Generate structured plan using Gemini
        try:
            plan_schema = self.gemini_client.generate_structured_output(
                prompt=prompt,
                pdf_path=pdf_path,
                response_schema=PresentationPlanSchema
            )
            logger.info(f"Generated structured plan with {plan_schema.slide_count} slides")
        except Exception as e:
            logger.error(f"Structured plan generation failed: {e}")
    
        
        # Create presentation plan
        presentation_plan = PresentationPlan(
            analysis=paper_analysis,
            slides=plan_schema.slides,
            style_guidelines = {
                "description": plan_schema.style_description
            },
            total_slides=len(plan_schema.slides)
        )
        
        logger.info(f"Created presentation plan with {len(plan_schema.slides)} slides")
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

        prompt = template.format(
            paper_analysis=paper_analysis
        )
        
        return prompt
