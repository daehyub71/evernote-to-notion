"""Batch uploader with multithreading for parallel resource uploads.

This module provides high-performance batch uploading using ThreadPoolExecutor
with progress tracking, retry logic, and failure handling.
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Callable, Tuple
from tqdm import tqdm

from app.parsers.enex_parser import Resource
from app.resources.cloudinary_uploader import CloudinaryUploader

logger = logging.getLogger(__name__)


class BatchUploader:
    """Parallel batch uploader with progress tracking and retry logic.

    Uses ThreadPoolExecutor to upload multiple resources concurrently,
    with configurable worker count, retry logic, and comprehensive
    error handling.

    Attributes:
        uploader: CloudinaryUploader instance
        max_workers: Maximum number of parallel upload threads
        stats: Upload statistics tracking
    """

    def __init__(self, uploader: CloudinaryUploader, max_workers: int = 10):
        """Initialize batch uploader.

        Args:
            uploader: CloudinaryUploader instance for uploads
            max_workers: Maximum parallel workers (default: 10)
        """
        self.uploader = uploader
        self.max_workers = max_workers

        self.stats = {
            'total': 0,
            'uploaded': 0,
            'cached': 0,
            'failed': 0,
            'retry_count': 0,
            'total_time': 0.0
        }

        logger.info(f"BatchUploader initialized with {max_workers} workers")

    def upload_resources(self,
                        resources: List[Resource],
                        progress_callback: Optional[Callable] = None,
                        cache: Optional[Dict[str, str]] = None) -> Dict[str, Optional[str]]:
        """Upload resources in parallel with progress tracking.

        Args:
            resources: List of Resource objects to upload
            progress_callback: Optional callback(current, total, resource, url)
            cache: Optional upload cache {hash: url}

        Returns:
            Dictionary mapping resource hash to public URL (or None on failure)

        Example:
            >>> uploader = CloudinaryUploader()
            >>> batch_uploader = BatchUploader(uploader, max_workers=10)
            >>> urls = batch_uploader.upload_resources(resources)
        """
        self.stats['total'] = len(resources)
        results = {}
        failed_resources = []

        if cache is None:
            cache = {}
        start_time = time.time()

        logger.info(f"Starting batch upload of {len(resources)} resources")

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit upload tasks
            future_to_resource = {}

            for resource in resources:
                # Check cache first
                if resource.hash in cache:
                    url = cache[resource.hash]
                    results[resource.hash] = url
                    resource.uploaded_url = url
                    self.stats['cached'] += 1
                    logger.debug(f"Cache hit for {resource.hash[:16]}...")
                else:
                    # Submit upload task
                    future = executor.submit(self._upload_single, resource)
                    future_to_resource[future] = resource

            # Track progress with tqdm
            with tqdm(total=len(resources),
                     desc="Uploading resources",
                     unit="file",
                     ncols=100) as pbar:

                # Update progress bar for cached items
                if self.stats['cached'] > 0:
                    pbar.update(self.stats['cached'])
                    pbar.set_postfix({'cached': self.stats['cached']})

                # Process completed uploads
                for future in as_completed(future_to_resource):
                    resource = future_to_resource[future]

                    try:
                        url = future.result()

                        if url:
                            results[resource.hash] = url
                            resource.uploaded_url = url
                            self.stats['uploaded'] += 1

                            # Update cache
                            if cache is not None:
                                cache[resource.hash] = url

                            logger.debug(f"Uploaded {resource.hash[:16]}... → {url}")
                        else:
                            results[resource.hash] = None
                            failed_resources.append((resource, "Upload returned None"))
                            self.stats['failed'] += 1
                            logger.warning(f"Upload failed for {resource.hash[:16]}...")

                    except Exception as e:
                        results[resource.hash] = None
                        failed_resources.append((resource, str(e)))
                        self.stats['failed'] += 1
                        logger.error(f"Upload exception for {resource.hash[:16]}...: {e}")

                    # Update progress bar
                    pbar.update(1)
                    pbar.set_postfix({
                        'uploaded': self.stats['uploaded'],
                        'cached': self.stats['cached'],
                        'failed': self.stats['failed']
                    })

                    # Progress callback
                    if progress_callback:
                        progress_callback(
                            self.stats['uploaded'] + self.stats['cached'] + self.stats['failed'],
                            len(resources),
                            resource,
                            results[resource.hash]
                        )

        # Calculate total time
        self.stats['total_time'] = time.time() - start_time

        # Log failures
        if failed_resources:
            self._log_failures(failed_resources)

        # Log summary
        logger.info(f"Batch upload complete: {self.stats['uploaded']} uploaded, "
                   f"{self.stats['cached']} cached, {self.stats['failed']} failed "
                   f"in {self.stats['total_time']:.2f}s")

        return results

    def _upload_single(self, resource: Resource, max_retries: int = 3) -> Optional[str]:
        """Upload single resource with retry logic.

        Args:
            resource: Resource object to upload
            max_retries: Maximum retry attempts

        Returns:
            Public URL of uploaded file, or None on failure
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                # Upload file
                url = self.uploader.upload_file(
                    resource.local_path,
                    public_id=resource.hash,
                    mime_type=resource.mime,
                    tags=['evernote', 'batch-upload']
                )

                if url:
                    if attempt > 0:
                        self.stats['retry_count'] += attempt
                    return url
                else:
                    last_error = "Upload returned None"

            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    logger.debug(f"Retry {attempt + 1}/{max_retries} for {resource.hash[:16]}... "
                               f"after {wait_time}s")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Max retries exceeded for {resource.hash[:16]}...: {e}")

        # All retries failed
        return None

    def _log_failures(self, failed_resources: List[Tuple[Resource, str]]):
        """Log failed uploads to file.

        Args:
            failed_resources: List of (Resource, error_message) tuples
        """
        failure_log = Path("data/checkpoint/upload_failures.log")
        failure_log.parent.mkdir(parents=True, exist_ok=True)

        with open(failure_log, 'a') as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"Batch upload failures - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*80}\n")

            for resource, error in failed_resources:
                f.write(f"\nHash: {resource.hash}\n")
                f.write(f"File: {resource.local_path}\n")
                f.write(f"MIME: {resource.mime}\n")
                f.write(f"Error: {error}\n")

        logger.warning(f"Logged {len(failed_resources)} failures to {failure_log}")

    def get_stats(self) -> Dict:
        """Get upload statistics.

        Returns:
            Dictionary with detailed upload statistics
        """
        success_count = self.stats['uploaded'] + self.stats['cached']
        success_rate = (success_count / self.stats['total'] * 100
                       if self.stats['total'] > 0 else 0)

        avg_time = (self.stats['total_time'] / self.stats['total']
                   if self.stats['total'] > 0 else 0)

        return {
            **self.stats,
            'success_count': success_count,
            'success_rate': success_rate,
            'avg_time_per_file': avg_time
        }

    def print_stats(self):
        """Print upload statistics to console."""
        stats = self.get_stats()

        print("\n" + "="*70)
        print("  Batch Upload Statistics")
        print("="*70)
        print(f"Total files:      {stats['total']}")
        print(f"Uploaded:         {stats['uploaded']}")
        print(f"Cached:           {stats['cached']}")
        print(f"Failed:           {stats['failed']}")
        print(f"Success rate:     {stats['success_rate']:.1f}%")
        print(f"Total time:       {stats['total_time']:.2f}s")
        print(f"Avg time/file:    {stats['avg_time_per_file']:.2f}s")
        print(f"Retry attempts:   {stats['retry_count']}")
        print("="*70)

    def upload_from_extractor(self,
                             resource_map: Dict[str, Resource],
                             progress_callback: Optional[Callable] = None,
                             cache: Optional[Dict[str, str]] = None) -> Dict[str, Optional[str]]:
        """Upload resources from ResourceExtractor output.

        Args:
            resource_map: Dictionary of hash → Resource objects
            progress_callback: Optional progress callback
            cache: Optional upload cache

        Returns:
            Dictionary mapping resource hash to public URL

        Example:
            >>> extractor = ResourceExtractor()
            >>> resource_map = extractor.extract_resources(note)
            >>> batch_uploader = BatchUploader(uploader)
            >>> urls = batch_uploader.upload_from_extractor(resource_map)
        """
        resources = list(resource_map.values())
        return self.upload_resources(resources, progress_callback, cache)
