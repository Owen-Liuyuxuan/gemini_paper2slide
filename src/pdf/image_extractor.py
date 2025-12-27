"""
Extract and process images from PDF documents.

Uses PyMuPDF for image extraction with quality filtering and preprocessing.
"""

from io import BytesIO
from pathlib import Path
from typing import List, Optional

import fitz  # PyMuPDF
from PIL import Image

from src.utils.config_loader import get_config
from src.utils.logger import get_logger
from src.utils.models import ExtractedImage, ImageFormat

logger = get_logger("image_extractor")


class ImageExtractor:
    """
    Extract and filter images from PDF documents.
    
    Extracts all images from PDF pages, filters by quality and size,
    and prepares them for use in slide generation.
    
    Attributes:
        min_size: Minimum image dimensions (width, height)
        max_size: Maximum image dimensions
        quality_threshold: Minimum quality score (0-1)
    """
    
    def __init__(
        self,
        min_size: Optional[tuple[int, int]] = None,
        max_size: Optional[tuple[int, int]] = None,
        quality_threshold: Optional[float] = None
    ) -> None:
        """
        Initialize image extractor.
        
        Args:
            min_size: Minimum (width, height) in pixels
            max_size: Maximum (width, height) in pixels
            quality_threshold: Minimum quality score (0-1)
        """
        pdf_config = get_config("pdf", {})
        
        self.min_size = min_size or tuple(pdf_config.get("min_image_size", [100, 100]))
        self.max_size = max_size or tuple(pdf_config.get("max_image_size", [4096, 4096]))
        self.quality_threshold = quality_threshold or pdf_config.get("image_quality_threshold", 0.5)
        
        logger.info(
            f"ImageExtractor initialized: min_size={self.min_size}, "
            f"max_size={self.max_size}, quality_threshold={self.quality_threshold}"
        )
    
    def extract_images(self, pdf_path: Path) -> List[ExtractedImage]:
        """
        Extract all images from PDF.
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            List of ExtractedImage objects
        
        Raises:
            FileNotFoundError: If PDF file doesn't exist
        
        Example:
            >>> extractor = ImageExtractor()
            >>> images = extractor.extract_images(Path("paper.pdf"))
            >>> print(f"Found {len(images)} images")
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        logger.info(f"Extracting images from {pdf_path}")
        
        try:
            doc = fitz.open(pdf_path)
            extracted_images = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                image_list = page.get_images(full=True)
                
                logger.debug(f"Page {page_num}: found {len(image_list)} images")
                
                for img_index, img in enumerate(image_list):
                    try:
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        
                        # Get image data
                        image_data = base_image["image"]
                        image_ext = base_image["ext"]
                        
                        # Convert extension to ImageFormat
                        if image_ext == "png":
                            img_format = ImageFormat.PNG
                        elif image_ext in ["jpeg", "jpg"]:
                            img_format = ImageFormat.JPEG
                        else:
                            # Convert unsupported formats to PNG
                            img_format = ImageFormat.PNG
                            image_data = self._convert_to_png(image_data)
                        
                        # Get dimensions
                        width = base_image.get("width", 0)
                        height = base_image.get("height", 0)
                        
                        # Calculate quality score
                        quality_score = self._calculate_quality_score(
                            image_data, width, height
                        )
                        
                        extracted_image = ExtractedImage(
                            page_num=page_num,
                            index=img_index,
                            data=image_data,
                            format=img_format,
                            width=width,
                            height=height,
                            quality_score=quality_score
                        )
                        
                        extracted_images.append(extracted_image)
                        
                    except Exception as e:
                        logger.warning(
                            f"Failed to extract image {img_index} from page {page_num}: {e}"
                        )
                        continue
            
            doc.close()
            
            logger.info(f"Extracted {len(extracted_images)} images from {pdf_path.name}")
            
            return extracted_images
            
        except Exception as e:
            logger.error(f"Failed to extract images from {pdf_path}: {e}")
            raise
    
    def filter_images(self, images: List[ExtractedImage]) -> List[ExtractedImage]:
        """
        Filter images by size and quality.
        
        Args:
            images: List of extracted images
        
        Returns:
            Filtered list of images
        
        Example:
            >>> extractor = ImageExtractor()
            >>> all_images = extractor.extract_images(Path("paper.pdf"))
            >>> good_images = extractor.filter_images(all_images)
        """
        logger.info(f"Filtering {len(images)} images")
        
        filtered = []
        
        for img in images:
            # Check size constraints
            if img.width < self.min_size[0] or img.height < self.min_size[1]:
                logger.debug(
                    f"Skipping image (too small): {img.width}x{img.height} "
                    f"on page {img.page_num}"
                )
                continue
            
            if img.width > self.max_size[0] or img.height > self.max_size[1]:
                logger.debug(
                    f"Skipping image (too large): {img.width}x{img.height} "
                    f"on page {img.page_num}"
                )
                continue
            
            # Check quality
            if img.quality_score < self.quality_threshold:
                logger.debug(
                    f"Skipping image (low quality): score={img.quality_score:.2f} "
                    f"on page {img.page_num}"
                )
                continue
            
            filtered.append(img)
        
        logger.info(f"Filtered to {len(filtered)} high-quality images")
        
        return filtered
    
    def save_images(
        self,
        images: List[ExtractedImage],
        output_dir: Path,
        prefix: str = "extracted"
    ) -> List[ExtractedImage]:
        """
        Save extracted images to disk.
        
        Args:
            images: List of images to save
            output_dir: Output directory
            prefix: Filename prefix
        
        Returns:
            List of images with updated file_path
        
        Example:
            >>> extractor = ImageExtractor()
            >>> images = extractor.extract_images(Path("paper.pdf"))
            >>> saved = extractor.save_images(images, Path("output/images"))
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Saving {len(images)} images to {output_dir}")
        
        saved_images = []
        
        for img in images:
            filename = f"{prefix}_p{img.page_num}_i{img.index}.{img.format.value}"
            file_path = output_dir / filename
            
            try:
                with open(file_path, 'wb') as f:
                    f.write(img.data)
                
                # Update image with file path
                img.file_path = file_path
                saved_images.append(img)
                
                logger.debug(f"Saved image to {file_path}")
                
            except Exception as e:
                logger.warning(f"Failed to save image {filename}: {e}")
                continue
        
        logger.info(f"Successfully saved {len(saved_images)} images")
        
        return saved_images
    
    def _convert_to_png(self, image_data: bytes) -> bytes:
        """
        Convert image data to PNG format.
        
        Args:
            image_data: Raw image bytes
        
        Returns:
            PNG image bytes
        """
        try:
            img = Image.open(BytesIO(image_data))
            output = BytesIO()
            img.save(output, format='PNG')
            return output.getvalue()
        except Exception as e:
            logger.warning(f"Failed to convert image to PNG: {e}")
            return image_data
    
    def _calculate_quality_score(
        self,
        image_data: bytes,
        width: int,
        height: int
    ) -> float:
        """
        Calculate image quality score.
        
        Considers:
        - Resolution (higher is better)
        - Aspect ratio (closer to common ratios is better)
        - File size relative to dimensions
        
        Args:
            image_data: Raw image bytes
            width: Image width
            height: Image height
        
        Returns:
            Quality score between 0 and 1
        """
        try:
            # Resolution score (normalize to 0-1)
            resolution = width * height
            resolution_score = min(resolution / (1920 * 1080), 1.0)
            
            # Aspect ratio score (prefer 16:9, 4:3, 1:1)
            aspect_ratio = width / height if height > 0 else 0
            common_ratios = [16/9, 4/3, 1.0, 3/4, 9/16]
            aspect_score = max(
                1.0 - abs(aspect_ratio - ratio) / ratio
                for ratio in common_ratios
            )
            
            # File size score (bytes per pixel)
            bytes_per_pixel = len(image_data) / resolution if resolution > 0 else 0
            # Expect 1-4 bytes per pixel for good quality
            size_score = 1.0 if 1 <= bytes_per_pixel <= 4 else 0.5
            
            # Weighted average
            quality_score = (
                0.4 * resolution_score +
                0.3 * aspect_score +
                0.3 * size_score
            )
            
            return min(max(quality_score, 0.0), 1.0)
            
        except Exception as e:
            logger.warning(f"Failed to calculate quality score: {e}")
            return 0.5