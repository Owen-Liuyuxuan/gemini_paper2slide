"""
Progress reporting infrastructure for workflow components.

Provides standardized progress callback interface for reporting
workflow progress to web frontend or other consumers.
"""

from enum import Enum
from typing import Any, Protocol


class ProgressStage(Enum):
    """Workflow stages for progress reporting"""

    ANALYZING = "analyzing"
    PLANNING = "planning"
    GENERATING_SLIDES = "generating_slides"
    SAVING = "saving"
    COMPLETE = "complete"
    ERROR = "error"


class ProgressCallback(Protocol):
    """
    Protocol for progress reporting callbacks.

    Components can accept an optional ProgressCallback to report
    progress updates during long-running operations.
    """

    def __call__(
        self,
        stage: ProgressStage,
        progress: int,  # 0-100
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Report progress update.

        Args:
            stage: Current workflow stage
            progress: Progress percentage (0-100)
            message: Human-readable progress message
            details: Optional additional details (e.g., current_slide, total_slides)
        """
        ...


def create_noop_callback() -> ProgressCallback:
    """
    Create a no-op callback that does nothing.

    Useful for maintaining backward compatibility when callbacks are optional.

    Returns:
        A callback function that accepts all parameters but does nothing
    """

    def noop(
        stage: ProgressStage, progress: int, message: str, details: dict[str, Any] | None = None
    ) -> None:
        pass

    return noop
