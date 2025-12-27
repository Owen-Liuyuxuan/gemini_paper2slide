"""
Manage visual style consistency across slides.

Ensures all slides follow consistent design principles,
color schemes, fonts, and layouts.
"""

from typing import Dict

from src.utils.config_loader import get_config
from src.utils.logger import get_logger

logger = get_logger("style_manager")


class StyleManager:
    """
    Manage visual style consistency across slides.
    
    Ensures all slides follow consistent design principles,
    color schemes, fonts, and layouts.
    """
    
    def __init__(self):
        """
        Initialize style manager.
        """
        self.config = get_config("image_generation", {})
        self.style_guidelines = self._load_style_guidelines()
        self.logger = logger
        
        logger.info("StyleManager initialized")
    
    def get_style_prompt(self) -> str:
        """
        Get style guidelines as a prompt for image generation.
        
        Returns:
            Formatted style prompt string
        """
        guidelines = self.style_guidelines
        
        style_prompt = f"""
        Visual Style Guidelines:
        - Color Scheme: {guidelines.get('color_scheme', 'professional')}
        - Layout: {guidelines.get('layout', 'modern')}
        - Font Style: {guidelines.get('font_style', 'clean sans-serif')}
        - Aspect Ratio: {guidelines.get('aspect_ratio', '16:9')}
        - Quality: {guidelines.get('quality', 'high')}
        
        Design Principles:
        - Maintain consistency with previous slides
        - Use clean, professional layouts
        - Ensure text is readable and well-spaced
        - Apply color schemes uniformly
        - Use appropriate visual hierarchy
        """
        
        return style_prompt
    
    def validate_style_consistency(self, slides: list) -> bool:
        """
        Validate that all slides maintain style consistency.
        
        Args:
            slides: List of generated slides to validate
        
        Returns:
            True if consistent, False otherwise
        """
        logger.debug(f"Validating style consistency for {len(slides)} slides")
        
        # In a complete implementation, we would analyze visual features
        # of the slides to check for consistency. For now, we'll just
        # return True as a placeholder.
        
        # Future implementation could:
        # - Analyze color histograms
        # - Check for consistent layouts
        # - Validate font usage
        # - Verify spacing and alignment
        
        logger.debug("Style consistency validation completed")
        return True
    
    def _load_style_guidelines(self) -> Dict:
        """
        Load style guidelines from configuration.
        
        Returns:
            Dictionary of style guidelines
        """
        # Get style guidelines from image generation config
        guidelines = get_config("image_generation", {}).get("style_guidelines", {})
        
        # Default guidelines if not specified
        defaults = {
            "color_scheme": "professional",
            "layout": "modern",
            "font_style": "clean sans-serif"
        }
        
        # Merge defaults with config values
        for key, default_value in defaults.items():
            if key not in guidelines:
                guidelines[key] = default_value
        
        logger.debug(f"Loaded style guidelines: {list(guidelines.keys())}")
        return guidelines