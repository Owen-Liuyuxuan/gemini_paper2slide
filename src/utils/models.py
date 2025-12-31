"""
Core data models for the paper-to-slides system.

This module defines Pydantic models for type safety and validation
across the entire application.
"""

from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ImageFormat(str, Enum):
    """Supported image formats."""

    PNG = "png"
    JPEG = "jpeg"
    JPG = "jpg"


class SlideType(str, Enum):
    """Types of slides in a presentation."""

    TITLE = "title"
    AGENDA = "agenda"
    CONTENT = "content"
    FIGURE = "figure"
    CONCLUSION = "conclusion"


class SlideContent(BaseModel):
    """
    Content specification for a single slide.

    Attributes:
        index: Slide index in presentation
        type: Type of slide
        title: Slide title
        main_points: Main content points
        visual_elements: Description of visual elements
    """

    index: int = Field(..., ge=0, description="Slide index")
    type: SlideType = Field(..., description="Slide type")
    title: str = Field(..., min_length=1, description="Slide title")
    main_points: list[str] = Field(..., description="Main content points")
    visual_elements: str = Field(..., description="Visual elements description")


class GeneratedSlide(BaseModel):
    """
    A generated slide image with metadata.

    Attributes:
        index: Slide index
        type: Slide type
        image: Raw image bytes
        prompt: Generation prompt used
        file_path: Path where image is saved
        generation_time: Time taken to generate
        content: Original content specification
    """

    index: int = Field(..., ge=0, description="Slide index")
    type: SlideType = Field(..., description="Slide type")
    image: bytes = Field(..., description="Generated image data")
    prompt: str = Field(..., description="Generation prompt")
    file_path: Path | None = Field(None, description="Saved file path")
    generation_time: float = Field(..., ge=0.0, description="Generation time in seconds")
    content: SlideContent = Field(..., description="Content specification")

    class Config:
        arbitrary_types_allowed = True

    @property
    def size_mb(self) -> float:
        """Get image size in megabytes."""
        return len(self.image) / (1024 * 1024)


class GenerationConfig(BaseModel):
    """
    Configuration for image generation.

    Attributes:
        aspect_ratio: Image aspect ratio
        quality: Quality setting
        style: Visual style
        safety_filter_level: Safety filter level
        number_of_images: Number of images to generate
    """

    aspect_ratio: str = Field("16:9", description="Aspect ratio")
    quality: str = Field("high", description="Quality setting")
    style: str = Field("professional", description="Visual style")
    safety_filter_level: str = Field("block_some", description="Safety filter")
    number_of_images: int = Field(1, ge=1, le=4, description="Number of images")


class PaperAnalysisSchema(BaseModel):
    """Schema for paper analysis structured output."""

    summary: str = Field(description="Overall summary of the paper")
    core_philosophy: str = Field(
        description="The current state of the research problem, the motivation to discover the improvement and the overall workflow of the work"
    )
    mathematical_formulation: str = Field(
        description="Mathematical formulation of the research question and the proposed solution"
    )
    methodology: str = Field(
        description="Research methodology description, including the core algorithms and methods used"
    )
    key_contributions: list[str] = Field(min_items=1, description="Key contributions of the paper")
    recommended_slide_count: int = Field(
        ge=5,
        le=25,
        description="Recommended number of slides for presenting the paper with enough information and details",
    )
    visual_theme: str = Field(
        description="Describe the suggested visual theme for the presentation. Including color usage and design instructions for creating the visual theme."
    )


class SlideSpec(BaseModel):
    """Schema for a single slide specification (for structured output)."""

    index: int = Field(ge=0, description="Slide index")
    type: str = Field(description="Slide type (title, agenda, content, figure, conclusion)")
    title: str = Field(description="Slide title")
    key_points: list[str] = Field(description="Key points to cover (3-5 items)")
    visual_suggestions: str = Field(description="Visual element suggestions")
    related_figure_pages: list[int] = Field(
        default_factory=list, description="Page numbers of related figures"
    )


class PresentationPlanSchema(BaseModel):
    """Schema for presentation plan structured output."""

    slide_count: int = Field(ge=5, le=25, description="Total number of slides")
    slides: list[SlideContent] = Field(min_items=1, description="Slide specifications")
    style_description: str = Field(description="Overall presentation style description")


class PresentationPlan(BaseModel):
    """
    Complete plan for the presentation.

    Attributes:
        metadata: PDF metadata
        analysis: Paper analysis
        slides: List of slide content specifications
        style_guidelines: Visual style guidelines
        total_slides: Total number of slides
    """

    analysis: PaperAnalysisSchema = Field(..., description="Paper analysis")
    slides: list[SlideContent] = Field(..., min_items=1, description="Slide specifications")
    style_guidelines: dict[str, Any] = Field(..., description="Style guidelines")
    total_slides: int = Field(..., gt=0, description="Total slide count")

    @field_validator("total_slides")
    @classmethod
    def validate_total_slides(cls, v: int, info: Any) -> int:
        """Ensure total_slides matches length of slides list."""
        if "slides" in info.data and len(info.data["slides"]) != v:
            raise ValueError("total_slides must match length of slides list")
        return v
