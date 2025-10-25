"""
Checkpoint Manager for tracking migration progress.

Saves progress to JSON files to allow resuming failed migrations.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class CheckpointManager:
    """
    Manages migration checkpoints to track processed files and notes.

    Allows resuming migration from the last successful checkpoint.

    Example:
        >>> checkpoint_mgr = CheckpointManager()
        >>> checkpoint_mgr.mark_file_started("냅킨경제학.enex")
        >>> checkpoint_mgr.mark_note_completed("Note Title", "notion_page_123")
        >>> checkpoint_mgr.mark_file_completed("냅킨경제학.enex")
        >>> checkpoint_mgr.save()
    """

    def __init__(self, checkpoint_file: str = "data/checkpoint/migration_checkpoint.json"):
        """
        Initialize checkpoint manager.

        Args:
            checkpoint_file: Path to checkpoint JSON file
        """
        self.checkpoint_file = Path(checkpoint_file)
        self.checkpoint_file.parent.mkdir(parents=True, exist_ok=True)

        # Load existing checkpoint
        self.checkpoint = self._load()

        logger.info(f"CheckpointManager initialized: {len(self.checkpoint.get('completed_files', []))} files completed")

    def _load(self) -> Dict:
        """Load checkpoint from file."""
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"Loaded checkpoint: {len(data.get('completed_files', []))} completed files")
                    return data
            except Exception as e:
                logger.error(f"Failed to load checkpoint: {e}")
                return self._create_empty_checkpoint()
        else:
            return self._create_empty_checkpoint()

    def _create_empty_checkpoint(self) -> Dict:
        """Create empty checkpoint structure."""
        return {
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'version': '1.0'
            },
            'completed_files': [],
            'in_progress_files': [],
            'completed_notes': {},  # {note_title: {notion_page_id, completed_at}}
            'failed_notes': {},  # {note_title: {error, failed_at}}
            'statistics': {
                'total_files_processed': 0,
                'total_notes_processed': 0,
                'total_notes_failed': 0,
                'total_resources_uploaded': 0
            }
        }

    def save(self):
        """Save checkpoint to file."""
        self.checkpoint['metadata']['last_updated'] = datetime.now().isoformat()

        with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(self.checkpoint, f, indent=2, ensure_ascii=False)

        logger.debug(f"Checkpoint saved to {self.checkpoint_file}")

    # File-level tracking
    def mark_file_started(self, file_path: str):
        """Mark a file as started processing."""
        if file_path not in self.checkpoint['in_progress_files']:
            self.checkpoint['in_progress_files'].append(file_path)
            logger.info(f"File started: {Path(file_path).name}")
            self.save()

    def mark_file_completed(self, file_path: str):
        """Mark a file as completed."""
        if file_path in self.checkpoint['in_progress_files']:
            self.checkpoint['in_progress_files'].remove(file_path)

        if file_path not in self.checkpoint['completed_files']:
            self.checkpoint['completed_files'].append(file_path)
            self.checkpoint['statistics']['total_files_processed'] += 1
            logger.info(f"File completed: {Path(file_path).name}")
            self.save()

    def is_file_completed(self, file_path: str) -> bool:
        """Check if a file has been completed."""
        return file_path in self.checkpoint['completed_files']

    def load_processed_files(self) -> Set[str]:
        """Load set of processed file paths."""
        return set(self.checkpoint['completed_files'])

    # Note-level tracking
    def mark_note_completed(self, note_title: str, notion_page_id: Optional[str] = None):
        """
        Mark a note as successfully processed.

        Args:
            note_title: Title of the note
            notion_page_id: Notion page ID (if created)
        """
        self.checkpoint['completed_notes'][note_title] = {
            'notion_page_id': notion_page_id,
            'completed_at': datetime.now().isoformat()
        }
        self.checkpoint['statistics']['total_notes_processed'] += 1

        # Remove from failed if it was previously failed
        if note_title in self.checkpoint['failed_notes']:
            del self.checkpoint['failed_notes'][note_title]
            self.checkpoint['statistics']['total_notes_failed'] -= 1

        logger.debug(f"Note completed: {note_title[:60]}")

    def mark_note_failed(self, note_title: str, error: str):
        """Mark a note as failed."""
        self.checkpoint['failed_notes'][note_title] = {
            'error': str(error),
            'failed_at': datetime.now().isoformat()
        }
        self.checkpoint['statistics']['total_notes_failed'] += 1
        logger.warning(f"Note failed: {note_title[:60]} - {error}")

    def is_note_processed(self, note_title: str) -> bool:
        """Check if a note has been processed."""
        return note_title in self.checkpoint['completed_notes']

    def get_notion_page_id(self, note_title: str) -> Optional[str]:
        """Get Notion page ID for a processed note."""
        if note_title in self.checkpoint['completed_notes']:
            return self.checkpoint['completed_notes'][note_title].get('notion_page_id')
        return None

    # Resource tracking
    def increment_resources_uploaded(self, count: int = 1):
        """Increment the count of uploaded resources."""
        self.checkpoint['statistics']['total_resources_uploaded'] += count

    # Statistics
    def get_statistics(self) -> Dict:
        """Get migration statistics."""
        return self.checkpoint['statistics'].copy()

    def get_summary(self) -> str:
        """Get human-readable summary."""
        stats = self.checkpoint['statistics']
        return f"""
Migration Progress:
  Files processed: {stats['total_files_processed']}
  Notes processed: {stats['total_notes_processed']}
  Notes failed: {stats['total_notes_failed']}
  Resources uploaded: {stats['total_resources_uploaded']}

  Completed files: {len(self.checkpoint['completed_files'])}
  In-progress files: {len(self.checkpoint['in_progress_files'])}
        """.strip()

    # Context manager support
    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - auto-save."""
        self.save()
        return False


# Example usage
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)

    # Example usage
    checkpoint = CheckpointManager()

    print("Current checkpoint:")
    print(checkpoint.get_summary())

    # Simulate processing
    checkpoint.mark_file_started("test.enex")
    checkpoint.mark_note_completed("Test Note", "notion_page_123")
    checkpoint.increment_resources_uploaded(5)
    checkpoint.mark_file_completed("test.enex")

    print("\nUpdated checkpoint:")
    print(checkpoint.get_summary())
