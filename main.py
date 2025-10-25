#!/usr/bin/env python3
"""
Evernote to Notion Migration Tool

Main CLI script for migrating Evernote notes (.enex files) to Notion.

Usage:
    python main.py                           # Process all .enex files
    python main.py --file 냅킨경제학.enex      # Process specific file
    python main.py --resume                  # Resume from checkpoint
    python main.py --dry-run                 # Simulate without uploading
    python main.py --verbose                 # Enable debug logging

Note: This version does not include Notion API integration yet.
      It will parse ENEX files, extract resources, and upload to Cloudinary,
      but will NOT create Notion pages (Phase 3 not implemented yet).
"""

import argparse
import sys
from pathlib import Path
from tqdm import tqdm
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from app.parsers.enex_parser import EnexParser
from app.resources.resource_extractor import ResourceExtractor
from app.resources.cloudinary_uploader import CloudinaryUploader
from app.resources.batch_uploader import BatchUploader
from app.resources.upload_cache import UploadCache
from app.utils.checkpoint import CheckpointManager
from app.utils.logger import setup_migration_logger


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Migrate Evernote (.enex) files to Notion',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           Process all .enex files
  %(prog)s --file 냅킨경제학.enex      Process specific file
  %(prog)s --resume                  Resume from last checkpoint
  %(prog)s --dry-run                 Simulate without uploading
  %(prog)s --verbose                 Enable debug logging

Environment Variables:
  ENEX_SOURCE_DIR                    Directory containing .enex files (default: ~/evernote)
  CLOUDINARY_CLOUD_NAME              Cloudinary cloud name
  CLOUDINARY_API_KEY                 Cloudinary API key
  CLOUDINARY_API_SECRET              Cloudinary API secret

Note: Notion API integration (Phase 3) not yet implemented.
      This will parse files and upload resources only.
        """
    )

    parser.add_argument(
        '--file',
        type=str,
        help='Process only the specified .enex file'
    )

    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume from last checkpoint (skip already processed files)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate migration without actually uploading resources'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose (DEBUG) logging'
    )

    parser.add_argument(
        '--max-workers',
        type=int,
        default=10,
        help='Number of parallel workers for uploading (default: 10)'
    )

    return parser.parse_args()


def get_enex_files(source_dir: Path, file_arg: str = None, checkpoint_mgr: CheckpointManager = None, resume: bool = False):
    """
    Get list of .enex files to process.

    Args:
        source_dir: Directory containing .enex files
        file_arg: Specific file to process (optional)
        checkpoint_mgr: Checkpoint manager for resume
        resume: Whether to resume from checkpoint

    Returns:
        List of Path objects for .enex files
    """
    if file_arg:
        # Process specific file
        file_path = source_dir / file_arg
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        return [file_path]
    else:
        # Process all .enex files
        files = list(source_dir.glob('*.enex'))

        if not files:
            raise FileNotFoundError(f"No .enex files found in {source_dir}")

        # Filter out completed files if resuming
        if resume and checkpoint_mgr:
            processed_files = checkpoint_mgr.load_processed_files()
            files = [f for f in files if str(f) not in processed_files]

        return sorted(files)


def process_file(
    enex_file: Path,
    batch_uploader: BatchUploader,
    upload_cache: UploadCache,
    checkpoint_mgr: CheckpointManager,
    dry_run: bool,
    logger
):
    """
    Process a single .enex file.

    Args:
        enex_file: Path to .enex file
        batch_uploader: Batch uploader instance
        upload_cache: Upload cache instance
        checkpoint_mgr: Checkpoint manager
        dry_run: If True, skip actual uploading
        logger: Logger instance
    """
    logger.info(f"Processing: {enex_file.name}")

    # Mark file as started
    checkpoint_mgr.mark_file_started(str(enex_file))

    # Parse ENEX file
    parser = EnexParser(str(enex_file))
    notes = list(parser.parse())

    logger.info(f"  Parsed {len(notes)} notes")

    # Extract resources
    extractor = ResourceExtractor(output_dir=f"data/temp/{enex_file.stem}")
    all_resources = []

    for note in tqdm(notes, desc=f"  Processing {enex_file.stem}", unit="note", leave=False):
        # Skip if already processed
        if checkpoint_mgr.is_note_processed(note.title):
            logger.debug(f"  Skipping already processed note: {note.title[:60]}")
            continue

        try:
            # Extract resources
            if note.resources:
                resource_map = extractor.extract_resources(note)
                all_resources.extend(resource_map.values())

            # TODO: Phase 3 - Create Notion page here
            # if not dry_run:
            #     page_id = page_creator.create_from_note(note, resource_map)
            #     checkpoint_mgr.mark_note_completed(note.title, page_id)
            # else:
            #     checkpoint_mgr.mark_note_completed(note.title, None)

            # For now, just mark as completed without Notion page
            checkpoint_mgr.mark_note_completed(note.title, notion_page_id=None)

        except Exception as e:
            logger.error(f"  Failed to process note '{note.title[:60]}': {e}")
            checkpoint_mgr.mark_note_failed(note.title, str(e))
            continue

    # Upload resources
    if all_resources:
        logger.info(f"  Uploading {len(all_resources)} resources...")

        if not dry_run:
            with upload_cache:  # Auto-save on exit
                urls = batch_uploader.upload_resources(all_resources, cache=upload_cache.cache)

                # Update statistics
                stats = batch_uploader.get_stats()
                checkpoint_mgr.increment_resources_uploaded(stats['uploaded'])

                logger.info(f"  Uploaded: {stats['uploaded']}, Cached: {stats['cached']}, Failed: {stats['failed']}")
        else:
            logger.info(f"  DRY RUN: Skipped uploading {len(all_resources)} resources")

    # Mark file as completed
    checkpoint_mgr.mark_file_completed(str(enex_file))
    logger.info(f"  Completed: {enex_file.name}")


def main():
    """Main entry point."""
    args = parse_arguments()

    # Setup logger
    logger = setup_migration_logger(verbose=args.verbose)

    logger.info("="*80)
    logger.info("Evernote to Notion Migration Tool")
    logger.info("="*80)

    if args.dry_run:
        logger.warning("DRY RUN MODE: No resources will be uploaded")

    # Get source directory
    source_dir = Path(os.getenv('ENEX_SOURCE_DIR', '~/evernote')).expanduser()

    if not source_dir.exists():
        logger.error(f"Source directory not found: {source_dir}")
        logger.error("Set ENEX_SOURCE_DIR environment variable or create ~/evernote directory")
        return 1

    logger.info(f"Source directory: {source_dir}")

    # Initialize checkpoint manager
    checkpoint_mgr = CheckpointManager()

    if args.resume:
        logger.info("RESUME mode: Skipping already processed files")
        logger.info(checkpoint_mgr.get_summary())

    # Get files to process
    try:
        files = get_enex_files(source_dir, args.file, checkpoint_mgr, args.resume)
        logger.info(f"Files to process: {len(files)}")
    except FileNotFoundError as e:
        logger.error(str(e))
        return 1

    # Initialize uploaders
    if not args.dry_run:
        cloudinary_uploader = CloudinaryUploader()
        batch_uploader = BatchUploader(cloudinary_uploader, max_workers=args.max_workers)
        upload_cache = UploadCache("data/checkpoint/migration_upload_cache.json")
        logger.info(f"Upload cache: {len(upload_cache)} existing entries")
    else:
        batch_uploader = None
        upload_cache = None

    # Process files
    with checkpoint_mgr:  # Auto-save on exit
        for enex_file in files:
            try:
                process_file(
                    enex_file,
                    batch_uploader,
                    upload_cache,
                    checkpoint_mgr,
                    args.dry_run,
                    logger
                )
            except Exception as e:
                logger.error(f"Failed to process {enex_file.name}: {e}")
                import traceback
                logger.debug(traceback.format_exc())
                continue

    # Final summary
    logger.info("="*80)
    logger.info("Migration Complete!")
    logger.info("="*80)
    logger.info(checkpoint_mgr.get_summary())

    logger.info("")
    logger.info("Note: Notion API integration (Phase 3) not yet implemented.")
    logger.info("      Resources have been uploaded to Cloudinary.")
    logger.info("      Notion pages will be created once Phase 3 is complete.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
