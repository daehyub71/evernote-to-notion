"""Cloudinary file uploader for Evernote resources.

This module handles uploading extracted resources (images, PDFs, documents)
to Cloudinary and generates public URLs for use in Notion.
"""

import logging
import os
from pathlib import Path
from typing import Optional, Dict, List, Callable
import hashlib
import time

import cloudinary
import cloudinary.uploader
import cloudinary.api
from cloudinary.exceptions import Error as CloudinaryError

logger = logging.getLogger(__name__)


class CloudinaryUploader:
    """Uploads files to Cloudinary and manages upload operations.

    Handles all file types supported by Cloudinary including images,
    PDFs, videos, and raw files (documents). Provides progress tracking,
    error handling, and retry logic.

    Attributes:
        cloud_name: Cloudinary cloud name
        stats: Dictionary tracking upload statistics
    """

    # Resource type mapping
    RESOURCE_TYPE_MAP = {
        'image/jpeg': 'image',
        'image/png': 'image',
        'image/gif': 'image',
        'image/webp': 'image',
        'image/bmp': 'image',
        'image/tiff': 'image',
        'image/svg+xml': 'image',
        'application/pdf': 'image',  # Cloudinary supports PDF as image
        'video/mp4': 'video',
        'video/quicktime': 'video',
        'audio/mpeg': 'video',  # Audio as video type
        'audio/wav': 'video',
    }

    def __init__(self, cloud_name: Optional[str] = None,
                 api_key: Optional[str] = None,
                 api_secret: Optional[str] = None,
                 folder: str = "evernote-migration"):
        """Initialize Cloudinary uploader.

        Args:
            cloud_name: Cloudinary cloud name (defaults to env var)
            api_key: Cloudinary API key (defaults to env var)
            api_secret: Cloudinary API secret (defaults to env var)
            folder: Folder name in Cloudinary for organizing uploads

        Raises:
            ValueError: If credentials are not provided or found in environment
        """
        # Get credentials from parameters or environment
        self.cloud_name = cloud_name or os.getenv('CLOUDINARY_CLOUD_NAME')
        api_key = api_key or os.getenv('CLOUDINARY_API_KEY')
        api_secret = api_secret or os.getenv('CLOUDINARY_API_SECRET')

        if not all([self.cloud_name, api_key, api_secret]):
            raise ValueError(
                "Cloudinary credentials not found. "
                "Set CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, "
                "and CLOUDINARY_API_SECRET in .env file"
            )

        # Configure Cloudinary
        cloudinary.config(
            cloud_name=self.cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            secure=True  # Always use HTTPS
        )

        self.folder = folder

        # Upload statistics
        self.stats = {
            'total': 0,
            'uploaded': 0,
            'skipped': 0,
            'failed': 0,
            'total_bytes': 0,
            'uploaded_bytes': 0,
            'by_type': {}
        }

        logger.info(f"CloudinaryUploader initialized with cloud: {self.cloud_name}")

    def upload_file(self, file_path: str,
                    public_id: Optional[str] = None,
                    resource_type: Optional[str] = None,
                    mime_type: Optional[str] = None,
                    tags: Optional[List[str]] = None) -> Optional[str]:
        """Upload a single file to Cloudinary.

        Args:
            file_path: Path to file to upload
            public_id: Custom public ID (defaults to hash-based)
            resource_type: Cloudinary resource type (image/video/raw)
            mime_type: MIME type of file for auto-detection
            tags: List of tags to apply to uploaded file

        Returns:
            Public URL of uploaded file, or None on failure

        Example:
            >>> uploader = CloudinaryUploader()
            >>> url = uploader.upload_file('image.jpg', mime_type='image/jpeg')
            >>> print(url)
            https://res.cloudinary.com/cloud/image/upload/v123/abc.jpg
        """
        try:
            path = Path(file_path)

            if not path.exists():
                logger.error(f"File not found: {file_path}")
                self.stats['failed'] += 1
                return None

            file_size = path.stat().st_size
            self.stats['total'] += 1
            self.stats['total_bytes'] += file_size

            # Determine resource type
            if resource_type is None:
                resource_type = self._detect_resource_type(mime_type)

            # Generate public_id if not provided
            if public_id is None:
                # Use file hash as public_id for deduplication
                file_hash = hashlib.md5(path.read_bytes()).hexdigest()
                public_id = f"{self.folder}/{file_hash}"
            else:
                public_id = f"{self.folder}/{public_id}"

            # Prepare upload options
            upload_options = {
                'public_id': public_id,
                'resource_type': resource_type,
                'overwrite': False,  # Don't overwrite existing files
                'unique_filename': False,  # Use our public_id as-is
            }

            if tags:
                upload_options['tags'] = tags

            # Upload to Cloudinary
            logger.debug(f"Uploading {file_path} as {resource_type}...")
            result = cloudinary.uploader.upload(file_path, **upload_options)

            # Extract URL
            url = result.get('secure_url')

            if url:
                self.stats['uploaded'] += 1
                self.stats['uploaded_bytes'] += file_size

                # Track by type
                type_key = mime_type or 'unknown'
                self.stats['by_type'][type_key] = \
                    self.stats['by_type'].get(type_key, 0) + 1

                logger.info(f"Uploaded: {path.name} → {url}")
                return url
            else:
                logger.error(f"Upload succeeded but no URL returned: {file_path}")
                self.stats['failed'] += 1
                return None

        except CloudinaryError as e:
            # Check if file already exists
            if 'already exists' in str(e).lower():
                logger.info(f"File already exists, retrieving URL: {file_path}")
                try:
                    # Try to get existing resource
                    resource_info = cloudinary.api.resource(
                        public_id,
                        resource_type=resource_type
                    )
                    url = resource_info.get('secure_url')
                    if url:
                        self.stats['skipped'] += 1
                        return url
                except:
                    pass

            logger.error(f"Cloudinary error uploading {file_path}: {e}")
            self.stats['failed'] += 1
            return None

        except Exception as e:
            logger.error(f"Failed to upload {file_path}: {e}")
            self.stats['failed'] += 1
            return None

    def upload_batch(self, file_paths: List[str],
                    mime_types: Optional[Dict[str, str]] = None,
                    progress_callback: Optional[Callable] = None) -> Dict[str, Optional[str]]:
        """Upload multiple files in batch.

        Args:
            file_paths: List of file paths to upload
            mime_types: Dictionary mapping file_path to MIME type
            progress_callback: Callback function(current, total, file_path)

        Returns:
            Dictionary mapping file_path to public URL (or None on failure)

        Example:
            >>> uploader = CloudinaryUploader()
            >>> urls = uploader.upload_batch(['img1.jpg', 'img2.png'])
            >>> print(urls['img1.jpg'])
            https://res.cloudinary.com/...
        """
        results = {}
        mime_types = mime_types or {}

        logger.info(f"Starting batch upload of {len(file_paths)} files")

        for i, file_path in enumerate(file_paths, 1):
            mime_type = mime_types.get(file_path)

            # Upload file
            url = self.upload_file(file_path, mime_type=mime_type)
            results[file_path] = url

            # Progress callback
            if progress_callback:
                progress_callback(i, len(file_paths), file_path, url)

            # Small delay to avoid rate limits
            if i % 10 == 0:
                time.sleep(0.1)

        logger.info(f"Batch upload complete: {self.stats['uploaded']} uploaded, "
                   f"{self.stats['failed']} failed, {self.stats['skipped']} skipped")

        return results

    def upload_resource_map(self, resource_map: Dict,
                           progress_callback: Optional[Callable] = None) -> Dict[str, Optional[str]]:
        """Upload resources from ResourceExtractor output.

        Args:
            resource_map: Dictionary of hash → Resource objects
            progress_callback: Callback function(current, total, hash, url)

        Returns:
            Dictionary mapping resource hash to public URL

        Example:
            >>> extractor = ResourceExtractor()
            >>> resource_map = extractor.extract_resources(note)
            >>> uploader = CloudinaryUploader()
            >>> urls = uploader.upload_resource_map(resource_map)
        """
        results = {}
        total = len(resource_map)

        logger.info(f"Uploading {total} resources from resource map")

        for i, (hash_val, resource) in enumerate(resource_map.items(), 1):
            if not resource.local_path:
                logger.warning(f"Resource {hash_val} has no local_path, skipping")
                self.stats['skipped'] += 1
                continue

            # Upload file
            url = self.upload_file(
                resource.local_path,
                public_id=hash_val,  # Use hash as public_id
                mime_type=resource.mime,
                tags=['evernote', 'migration']
            )

            results[hash_val] = url

            # Progress callback
            if progress_callback:
                progress_callback(i, total, hash_val, url)

        return results

    def _detect_resource_type(self, mime_type: Optional[str]) -> str:
        """Detect Cloudinary resource type from MIME type.

        Args:
            mime_type: MIME type string

        Returns:
            Cloudinary resource type: 'image', 'video', or 'raw'
        """
        if not mime_type:
            return 'raw'

        # Check predefined mappings
        resource_type = self.RESOURCE_TYPE_MAP.get(mime_type)
        if resource_type:
            return resource_type

        # Fallback to generic type detection
        if mime_type.startswith('image/'):
            return 'image'
        elif mime_type.startswith('video/') or mime_type.startswith('audio/'):
            return 'video'
        else:
            return 'raw'  # Documents, text files, etc.

    def get_stats(self) -> Dict:
        """Get upload statistics.

        Returns:
            Dictionary with detailed upload statistics
        """
        return {
            **self.stats,
            'success_rate': (self.stats['uploaded'] / self.stats['total'] * 100
                           if self.stats['total'] > 0 else 0),
            'total_mb': self.stats['total_bytes'] / (1024 * 1024),
            'uploaded_mb': self.stats['uploaded_bytes'] / (1024 * 1024)
        }

    def print_stats(self):
        """Print upload statistics to console."""
        stats = self.get_stats()

        print("\n" + "="*70)
        print("  Cloudinary Upload Statistics")
        print("="*70)
        print(f"Total files:      {stats['total']}")
        print(f"Uploaded:         {stats['uploaded']}")
        print(f"Skipped:          {stats['skipped']}")
        print(f"Failed:           {stats['failed']}")
        print(f"Success rate:     {stats['success_rate']:.1f}%")
        print(f"Total size:       {stats['total_mb']:.2f} MB")
        print(f"Uploaded size:    {stats['uploaded_mb']:.2f} MB")
        print()
        print("By MIME type:")

        for mime_type, count in sorted(stats['by_type'].items(),
                                       key=lambda x: x[1],
                                       reverse=True):
            print(f"  {mime_type:40s}: {count:4d}")

        print("="*70)

    def delete_resource(self, public_id: str,
                       resource_type: str = 'image') -> bool:
        """Delete a resource from Cloudinary.

        Args:
            public_id: Public ID of resource to delete
            resource_type: Resource type (image/video/raw)

        Returns:
            True if deletion successful, False otherwise
        """
        try:
            result = cloudinary.uploader.destroy(
                public_id,
                resource_type=resource_type
            )
            success = result.get('result') == 'ok'

            if success:
                logger.info(f"Deleted resource: {public_id}")
            else:
                logger.warning(f"Failed to delete resource: {public_id}")

            return success

        except Exception as e:
            logger.error(f"Error deleting resource {public_id}: {e}")
            return False

    def get_usage_stats(self) -> Optional[Dict]:
        """Get Cloudinary account usage statistics.

        Returns:
            Dictionary with usage information or None on failure
        """
        try:
            usage = cloudinary.api.usage()
            return {
                'credits_used': usage.get('credits', {}).get('usage', 0),
                'credits_limit': usage.get('credits', {}).get('limit', 0),
                'bandwidth_used_mb': usage.get('bandwidth', {}).get('usage', 0) / (1024 * 1024),
                'bandwidth_limit_mb': usage.get('bandwidth', {}).get('limit', 0) / (1024 * 1024),
                'storage_used_mb': usage.get('storage', {}).get('usage', 0) / (1024 * 1024),
                'resources': usage.get('resources', 0),
            }
        except Exception as e:
            logger.error(f"Failed to get usage stats: {e}")
            return None

    def print_usage_stats(self):
        """Print Cloudinary account usage statistics."""
        usage = self.get_usage_stats()

        if not usage:
            print("❌ Could not retrieve usage statistics")
            return

        print("\n" + "="*70)
        print("  Cloudinary Account Usage")
        print("="*70)
        print(f"Storage used:     {usage['storage_used_mb']:.2f} MB")
        print(f"Resources:        {usage['resources']}")
        print(f"Bandwidth used:   {usage['bandwidth_used_mb']:.2f} MB / "
              f"{usage['bandwidth_limit_mb']:.0f} MB")
        print(f"Credits used:     {usage['credits_used']} / {usage['credits_limit']}")
        print("="*70)
