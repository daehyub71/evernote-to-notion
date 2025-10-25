"""Resource extraction from Evernote notes.

This module handles extracting resources (images, PDFs, attachments)
from EvernoteNote objects and saving them to local storage.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional
import hashlib
import re

from app.parsers.enex_parser import EvernoteNote, Resource

logger = logging.getLogger(__name__)


class ResourceExtractor:
    """Extracts and saves resources from Evernote notes to local storage.

    Resources are organized by note title into subdirectories under the
    output directory. Files are named using their MD5 hash to ensure
    uniqueness and consistency.

    Attributes:
        output_dir: Root directory for saving extracted resources
        stats: Dictionary tracking extraction statistics
    """

    def __init__(self, output_dir: str = "data/temp"):
        """Initialize the resource extractor.

        Args:
            output_dir: Directory path for saving extracted resources
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.stats = {
            'total_resources': 0,
            'extracted': 0,
            'failed': 0,
            'skipped': 0,
            'by_mime_type': {}
        }

        logger.info(f"ResourceExtractor initialized with output_dir: {self.output_dir}")

    def extract_resources(self, note: EvernoteNote) -> Dict[str, Resource]:
        """Extract all resources from a note and save to local storage.

        Args:
            note: EvernoteNote object containing resources to extract

        Returns:
            Dictionary mapping resource hash to Resource object with local_path set

        Example:
            >>> extractor = ResourceExtractor("data/temp")
            >>> resource_map = extractor.extract_resources(note)
            >>> print(resource_map['abc123'].local_path)
            data/temp/Note Title/abc123.jpg
        """
        if not note.resources:
            logger.debug(f"Note '{note.title}' has no resources")
            return {}

        resource_map = {}

        # Create note-specific directory (sanitize title for filesystem)
        note_dir_name = self._sanitize_filename(note.title[:50])
        note_dir = self.output_dir / note_dir_name
        note_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Extracting {len(note.resources)} resources from '{note.title}'")

        for i, resource in enumerate(note.resources, 1):
            try:
                # Get file extension from MIME type
                ext = resource.get_extension()
                filename = f"{resource.hash}.{ext}"
                filepath = note_dir / filename

                # Save resource data to file
                with open(filepath, 'wb') as f:
                    f.write(resource.data)

                # Update resource object with local path
                resource.local_path = str(filepath)
                resource_map[resource.hash] = resource

                # Update statistics
                self.stats['extracted'] += 1
                mime_type = resource.mime or 'unknown'
                self.stats['by_mime_type'][mime_type] = \
                    self.stats['by_mime_type'].get(mime_type, 0) + 1

                logger.debug(f"Extracted [{i}/{len(note.resources)}]: {filename} ({mime_type})")

            except Exception as e:
                logger.error(f"Failed to extract resource {resource.hash}: {e}")
                self.stats['failed'] += 1

        self.stats['total_resources'] += len(note.resources)

        return resource_map

    def extract_batch(self, notes: List[EvernoteNote]) -> Dict[str, Dict[str, Resource]]:
        """Extract resources from multiple notes.

        Args:
            notes: List of EvernoteNote objects

        Returns:
            Dictionary mapping note title to resource_map for that note

        Example:
            >>> extractor = ResourceExtractor()
            >>> results = extractor.extract_batch(notes)
            >>> print(f"Extracted {len(results)} notes")
        """
        results = {}

        logger.info(f"Starting batch extraction for {len(notes)} notes")

        for i, note in enumerate(notes, 1):
            logger.info(f"[{i}/{len(notes)}] Processing note: {note.title}")

            resource_map = self.extract_resources(note)
            if resource_map:
                results[note.title] = resource_map

        logger.info(f"Batch extraction complete: {len(results)} notes with resources")
        return results

    def get_stats(self) -> Dict:
        """Get extraction statistics.

        Returns:
            Dictionary with extraction statistics
        """
        return {
            **self.stats,
            'success_rate': (self.stats['extracted'] / self.stats['total_resources'] * 100
                           if self.stats['total_resources'] > 0 else 0)
        }

    def print_stats(self):
        """Print extraction statistics to console."""
        stats = self.get_stats()

        print("\n" + "="*70)
        print("  Resource Extraction Statistics")
        print("="*70)
        print(f"Total resources:  {stats['total_resources']}")
        print(f"Extracted:        {stats['extracted']}")
        print(f"Failed:           {stats['failed']}")
        print(f"Success rate:     {stats['success_rate']:.1f}%")
        print()
        print("By MIME type:")

        for mime_type, count in sorted(stats['by_mime_type'].items(),
                                       key=lambda x: x[1],
                                       reverse=True):
            print(f"  {mime_type:40s}: {count:4d}")

        print("="*70)

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem compatibility.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename safe for all filesystems
        """
        # Remove or replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)

        # Remove leading/trailing whitespace and dots
        filename = filename.strip('. ')

        # Replace multiple underscores with single
        filename = re.sub(r'_+', '_', filename)

        # Ensure filename is not empty
        if not filename:
            filename = 'untitled'

        return filename

    def verify_extraction(self, resource_map: Dict[str, Resource]) -> bool:
        """Verify that all extracted resources exist and match their hashes.

        Args:
            resource_map: Dictionary of resources to verify

        Returns:
            True if all resources are valid, False otherwise
        """
        all_valid = True

        for hash_val, resource in resource_map.items():
            if not resource.local_path:
                logger.error(f"Resource {hash_val} has no local_path")
                all_valid = False
                continue

            filepath = Path(resource.local_path)

            # Check if file exists
            if not filepath.exists():
                logger.error(f"Resource file not found: {filepath}")
                all_valid = False
                continue

            # Verify file hash matches
            with open(filepath, 'rb') as f:
                data = f.read()
                computed_hash = hashlib.md5(data).hexdigest()

                if computed_hash != hash_val:
                    logger.error(f"Hash mismatch for {filepath}: "
                               f"expected {hash_val}, got {computed_hash}")
                    all_valid = False

        return all_valid

    def cleanup(self):
        """Remove all extracted resources from disk.

        Warning: This permanently deletes all extracted files!
        """
        import shutil

        if self.output_dir.exists():
            logger.warning(f"Cleaning up extracted resources: {self.output_dir}")
            shutil.rmtree(self.output_dir)
            self.output_dir.mkdir(parents=True, exist_ok=True)

            # Reset statistics
            self.stats = {
                'total_resources': 0,
                'extracted': 0,
                'failed': 0,
                'skipped': 0,
                'by_mime_type': {}
            }
