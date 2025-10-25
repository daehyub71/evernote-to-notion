"""Upload cache for preventing duplicate uploads and enabling resumable uploads.

This module provides persistent caching of uploaded resource URLs to avoid
re-uploading the same files and enable resumable batch uploads.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class UploadCache:
    """Persistent cache for uploaded resource URLs.

    Stores mapping of resource hash to public URL in JSON file,
    enabling deduplication and resumable uploads.

    Attributes:
        cache_file: Path to cache JSON file
        cache: Dictionary of hash → URL mappings
    """

    def __init__(self, cache_file: str = "data/checkpoint/upload_cache.json"):
        """Initialize upload cache.

        Args:
            cache_file: Path to cache file (JSON)
        """
        self.cache_file = Path(cache_file)
        self.cache = self._load()

        logger.info(f"UploadCache initialized: {len(self.cache)} entries loaded")

    def _load(self) -> Dict[str, str]:
        """Load cache from file.

        Returns:
            Dictionary of hash → URL mappings
        """
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Handle both old and new format
                if isinstance(data, dict):
                    # New format: {"entries": {...}, "metadata": {...}}
                    if 'entries' in data:
                        return data['entries']
                    # Old format: direct hash → URL mapping
                    else:
                        return data
                else:
                    logger.warning(f"Invalid cache format in {self.cache_file}")
                    return {}

            except Exception as e:
                logger.error(f"Failed to load cache: {e}")
                return {}
        else:
            logger.info(f"Cache file not found, starting fresh: {self.cache_file}")
            return {}

    def get(self, hash_value: str) -> Optional[str]:
        """Get cached URL for resource hash.

        Args:
            hash_value: Resource MD5 hash

        Returns:
            Public URL if cached, None otherwise
        """
        url = self.cache.get(hash_value)

        if url:
            logger.debug(f"Cache hit: {hash_value[:16]}... → {url}")
        else:
            logger.debug(f"Cache miss: {hash_value[:16]}...")

        return url

    def set(self, hash_value: str, url: str):
        """Cache URL for resource hash.

        Args:
            hash_value: Resource MD5 hash
            url: Public URL of uploaded file
        """
        self.cache[hash_value] = url
        logger.debug(f"Cached: {hash_value[:16]}... → {url}")

    def set_batch(self, mappings: Dict[str, str]):
        """Cache multiple URL mappings at once.

        Args:
            mappings: Dictionary of hash → URL mappings
        """
        self.cache.update(mappings)
        logger.info(f"Cached {len(mappings)} entries")

    def has(self, hash_value: str) -> bool:
        """Check if resource is cached.

        Args:
            hash_value: Resource MD5 hash

        Returns:
            True if cached, False otherwise
        """
        return hash_value in self.cache

    def remove(self, hash_value: str) -> bool:
        """Remove entry from cache.

        Args:
            hash_value: Resource MD5 hash

        Returns:
            True if removed, False if not found
        """
        if hash_value in self.cache:
            del self.cache[hash_value]
            logger.debug(f"Removed from cache: {hash_value[:16]}...")
            return True
        return False

    def save(self):
        """Save cache to file with metadata."""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)

        # Create cache data with metadata
        cache_data = {
            'metadata': {
                'total_entries': len(self.cache),
                'last_updated': datetime.now().isoformat(),
                'version': '1.0'
            },
            'entries': self.cache
        }

        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved {len(self.cache)} entries to {self.cache_file}")

        except Exception as e:
            logger.error(f"Failed to save cache: {e}")

    def clear(self):
        """Clear all cache entries."""
        self.cache.clear()
        logger.info("Cache cleared")

    def get_stats(self) -> Dict:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        return {
            'total_entries': len(self.cache),
            'cache_file': str(self.cache_file),
            'file_exists': self.cache_file.exists(),
            'file_size': self.cache_file.stat().st_size if self.cache_file.exists() else 0
        }

    def print_stats(self):
        """Print cache statistics to console."""
        stats = self.get_stats()

        print("\n" + "="*70)
        print("  Upload Cache Statistics")
        print("="*70)
        print(f"Total entries:    {stats['total_entries']}")
        print(f"Cache file:       {stats['cache_file']}")
        print(f"File exists:      {stats['file_exists']}")

        if stats['file_exists']:
            print(f"File size:        {stats['file_size']:,} bytes")

        print("="*70)

    def export_list(self) -> List[Dict[str, str]]:
        """Export cache as list of entries.

        Returns:
            List of {'hash': ..., 'url': ...} dictionaries
        """
        return [
            {'hash': hash_val, 'url': url}
            for hash_val, url in self.cache.items()
        ]

    def import_list(self, entries: List[Dict[str, str]]):
        """Import cache from list of entries.

        Args:
            entries: List of {'hash': ..., 'url': ...} dictionaries
        """
        for entry in entries:
            if 'hash' in entry and 'url' in entry:
                self.cache[entry['hash']] = entry['url']

        logger.info(f"Imported {len(entries)} entries")

    def merge(self, other_cache: 'UploadCache'):
        """Merge another cache into this one.

        Args:
            other_cache: Another UploadCache instance
        """
        before_count = len(self.cache)
        self.cache.update(other_cache.cache)
        after_count = len(self.cache)

        added = after_count - before_count
        logger.info(f"Merged cache: {added} new entries added")

    def get_missing_hashes(self, all_hashes: List[str]) -> List[str]:
        """Get list of hashes not in cache.

        Args:
            all_hashes: List of all resource hashes

        Returns:
            List of hashes not in cache
        """
        missing = [h for h in all_hashes if h not in self.cache]
        logger.info(f"Missing from cache: {len(missing)}/{len(all_hashes)}")
        return missing

    def __len__(self) -> int:
        """Get number of cached entries."""
        return len(self.cache)

    def __contains__(self, hash_value: str) -> bool:
        """Check if hash is in cache (supports 'in' operator)."""
        return hash_value in self.cache

    def __getitem__(self, hash_value: str) -> Optional[str]:
        """Get URL by hash (supports [] operator)."""
        return self.cache.get(hash_value)

    def __setitem__(self, hash_value: str, url: str):
        """Set URL by hash (supports [] operator)."""
        self.cache[hash_value] = url

    def __enter__(self):
        """Context manager entry (loads cache)."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit (saves cache)."""
        self.save()
        return False  # Don't suppress exceptions
