"""Image resource handling and optimization.

This module provides image processing capabilities including:
- Image optimization (resizing, compression)
- Format conversion (WebP to PNG, etc.)
- Image validation
- Metadata extraction
"""

import logging
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image, ImageFile
import io

logger = logging.getLogger(__name__)

# Allow loading of truncated images
ImageFile.LOAD_TRUNCATED_IMAGES = True


class ImageHandler:
    """Handles image processing operations for Evernote resources.

    Supports optimization, format conversion, and validation of images
    to ensure compatibility with Notion's requirements.
    """

    # Notion's recommended image size limits
    MAX_IMAGE_WIDTH = 2000
    MAX_IMAGE_HEIGHT = 2000
    DEFAULT_QUALITY = 85

    # Supported image formats
    SUPPORTED_FORMATS = {
        'image/jpeg': 'jpg',
        'image/png': 'png',
        'image/gif': 'gif',
        'image/webp': 'webp',
        'image/bmp': 'bmp',
        'image/tiff': 'tiff'
    }

    @staticmethod
    def optimize(image_path: str,
                 max_size: int = MAX_IMAGE_WIDTH,
                 quality: int = DEFAULT_QUALITY,
                 in_place: bool = True) -> str:
        """Optimize image size and quality.

        Args:
            image_path: Path to image file
            max_size: Maximum width/height in pixels
            quality: JPEG quality (1-100)
            in_place: If True, overwrites original file. If False, creates new file.

        Returns:
            Path to optimized image file

        Example:
            >>> handler = ImageHandler()
            >>> optimized_path = handler.optimize('large_image.jpg', max_size=1500)
        """
        try:
            img = Image.open(image_path)
            original_size = img.size
            modified = False

            logger.debug(f"Optimizing image: {image_path} ({original_size})")

            # Convert RGBA to RGB for JPEG
            if img.mode == 'RGBA' and image_path.lower().endswith(('.jpg', '.jpeg')):
                # Create white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
                img = background
                modified = True

            # Resize if too large
            if max(img.size) > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                modified = True
                logger.info(f"Resized image from {original_size} to {img.size}")

            # Determine output path
            if in_place:
                output_path = image_path
            else:
                path = Path(image_path)
                output_path = str(path.parent / f"{path.stem}_optimized{path.suffix}")

            # Save with optimization
            save_kwargs = {'optimize': True}

            if image_path.lower().endswith(('.jpg', '.jpeg')):
                save_kwargs['quality'] = quality
                save_kwargs['progressive'] = True

            img.save(output_path, **save_kwargs)

            if modified:
                logger.info(f"Optimized: {image_path} -> {output_path}")

            return output_path

        except Exception as e:
            logger.error(f"Failed to optimize image {image_path}: {e}")
            return image_path  # Return original path on failure

    @staticmethod
    def convert_webp_to_png(webp_path: str) -> str:
        """Convert WebP image to PNG format.

        WebP may have limited support in some contexts, so conversion
        to PNG ensures maximum compatibility.

        Args:
            webp_path: Path to WebP image file

        Returns:
            Path to converted PNG file

        Example:
            >>> handler = ImageHandler()
            >>> png_path = handler.convert_webp_to_png('image.webp')
            >>> print(png_path)  # 'image.png'
        """
        try:
            img = Image.open(webp_path)
            png_path = webp_path.replace('.webp', '.png')

            # Convert RGBA to RGB if no transparency
            if img.mode == 'RGBA':
                # Check if image has actual transparency
                if img.getextrema()[3][0] == 255:  # Alpha channel is all 255 (opaque)
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3])
                    img = background

            img.save(png_path, 'PNG', optimize=True)
            logger.info(f"Converted WebP to PNG: {webp_path} -> {png_path}")

            return png_path

        except Exception as e:
            logger.error(f"Failed to convert WebP to PNG {webp_path}: {e}")
            return webp_path

    @staticmethod
    def validate_image(image_path: str) -> bool:
        """Validate that file is a valid image.

        Args:
            image_path: Path to image file

        Returns:
            True if valid image, False otherwise
        """
        try:
            with Image.open(image_path) as img:
                img.verify()
            return True
        except Exception as e:
            logger.warning(f"Invalid image {image_path}: {e}")
            return False

    @staticmethod
    def get_image_info(image_path: str) -> Optional[dict]:
        """Extract image metadata and properties.

        Args:
            image_path: Path to image file

        Returns:
            Dictionary with image information or None if invalid

        Example:
            >>> info = ImageHandler.get_image_info('photo.jpg')
            >>> print(info['size'])
            (1920, 1080)
        """
        try:
            with Image.open(image_path) as img:
                return {
                    'format': img.format,
                    'mode': img.mode,
                    'size': img.size,
                    'width': img.width,
                    'height': img.height,
                    'file_size': Path(image_path).stat().st_size,
                    'needs_resize': max(img.size) > ImageHandler.MAX_IMAGE_WIDTH
                }
        except Exception as e:
            logger.error(f"Failed to get image info for {image_path}: {e}")
            return None

    @staticmethod
    def create_thumbnail(image_path: str,
                        max_size: int = 300,
                        suffix: str = '_thumb') -> Optional[str]:
        """Create a thumbnail version of an image.

        Args:
            image_path: Path to source image
            max_size: Maximum thumbnail dimension
            suffix: Suffix to add to filename

        Returns:
            Path to thumbnail file or None on failure
        """
        try:
            img = Image.open(image_path)

            # Calculate thumbnail size
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

            # Generate thumbnail path
            path = Path(image_path)
            thumb_path = str(path.parent / f"{path.stem}{suffix}{path.suffix}")

            # Save thumbnail
            img.save(thumb_path, optimize=True, quality=80)
            logger.info(f"Created thumbnail: {thumb_path}")

            return thumb_path

        except Exception as e:
            logger.error(f"Failed to create thumbnail for {image_path}: {e}")
            return None

    @staticmethod
    def is_animated_gif(image_path: str) -> bool:
        """Check if image is an animated GIF.

        Args:
            image_path: Path to image file

        Returns:
            True if animated GIF, False otherwise
        """
        try:
            with Image.open(image_path) as img:
                if img.format != 'GIF':
                    return False
                # Try to seek to second frame
                try:
                    img.seek(1)
                    return True
                except EOFError:
                    return False
        except:
            return False

    @staticmethod
    def convert_to_rgb(image_path: str) -> str:
        """Convert image to RGB mode (no transparency).

        Useful for converting PNG with transparency to JPEG.

        Args:
            image_path: Path to image file

        Returns:
            Path to converted image (may be same as input)
        """
        try:
            img = Image.open(image_path)

            if img.mode not in ('RGB', 'L'):
                # Create white background
                if img.mode == 'RGBA' or img.mode == 'LA':
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if 'A' in img.mode:
                        background.paste(img, mask=img.split()[-1])
                    else:
                        background.paste(img)
                    img = background
                else:
                    img = img.convert('RGB')

                # Save as JPEG
                path = Path(image_path)
                output_path = str(path.parent / f"{path.stem}.jpg")
                img.save(output_path, 'JPEG', quality=ImageHandler.DEFAULT_QUALITY, optimize=True)

                logger.info(f"Converted to RGB: {image_path} -> {output_path}")
                return output_path

            return image_path

        except Exception as e:
            logger.error(f"Failed to convert to RGB {image_path}: {e}")
            return image_path

    @staticmethod
    def get_dimensions(image_path: str) -> Optional[Tuple[int, int]]:
        """Get image dimensions without loading full image.

        Args:
            image_path: Path to image file

        Returns:
            Tuple of (width, height) or None on failure
        """
        try:
            with Image.open(image_path) as img:
                return img.size
        except:
            return None
