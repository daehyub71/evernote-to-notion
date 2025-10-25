"""
Notion Page Creator

Creates Notion pages from Evernote notes with metadata preservation.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from app.models import EvernoteNote, Resource
from app.notion.client import NotionClient, NotionAPIError
from app.parsers.enml_converter import EnmlConverter

logger = logging.getLogger(__name__)


class PageCreationError(Exception):
    """Raised when page creation fails."""
    pass


class PageCreator:
    """
    Creates Notion pages from Evernote notes.

    Handles:
    - Page creation with metadata
    - ENML to Notion block conversion
    - Resource mapping
    - Error handling
    """

    def __init__(self, client: NotionClient, parent_id: str):
        """
        Initialize page creator.

        Args:
            client: Notion API client
            parent_id: Parent page ID where notes will be created
        """
        self.client = client
        self.parent_id = parent_id

    def create_from_note(
        self,
        note: EvernoteNote,
        include_metadata: bool = True,
        dry_run: bool = False
    ) -> Optional[str]:
        """
        Create a Notion page from an Evernote note.

        Args:
            note: Evernote note to convert
            include_metadata: Whether to include metadata properties
            dry_run: If True, only convert blocks without creating page

        Returns:
            Created page ID (None if dry_run=True)

        Raises:
            PageCreationError: If page creation fails
        """
        logger.info(f"Creating page from note: {note.title}")

        try:
            # Build resource map
            resource_map = self._build_resource_map(note)
            logger.debug(f"Resource map: {len(resource_map)} resources")

            # Convert ENML to Notion blocks
            converter = EnmlConverter(resource_map)
            blocks = converter.convert(note.content)
            logger.info(f"Converted {len(blocks)} blocks from ENML")

            # Dry run - just return block count
            if dry_run:
                logger.info(f"Dry run: Would create page with {len(blocks)} blocks")
                return None

            # Create page with metadata
            page_id = self._create_page_with_metadata(note, include_metadata)

            # Append blocks
            logger.info(f"Appending {len(blocks)} blocks to page {page_id}")
            self.client.append_blocks(page_id, blocks)

            logger.info(f"Successfully created page: {note.title} (ID: {page_id})")
            return page_id

        except NotionAPIError as e:
            error_msg = f"Failed to create page '{note.title}': {e}"
            logger.error(error_msg)
            raise PageCreationError(error_msg) from e

        except Exception as e:
            error_msg = f"Unexpected error creating page '{note.title}': {e}"
            logger.error(error_msg)
            raise PageCreationError(error_msg) from e

    def _create_page_with_metadata(
        self,
        note: EvernoteNote,
        include_metadata: bool
    ) -> str:
        """
        Create Notion page with metadata properties.

        Note: Notion requires properties to be defined in the parent database.
        For pages under pages (not databases), properties are limited to title.
        Metadata is added as blocks at the top of the page instead.

        Args:
            note: Evernote note
            include_metadata: Whether to include metadata

        Returns:
            Created page ID
        """
        # Create page with title only
        # (Properties only work if parent is a database)
        page_id = self.client.create_page(
            parent_id=self.parent_id,
            title=note.title,
            icon=self._get_page_icon(note)
        )

        # Add metadata as blocks at the top if requested
        if include_metadata:
            metadata_blocks = self._create_metadata_blocks(note)
            if metadata_blocks:
                logger.debug(f"Adding {len(metadata_blocks)} metadata blocks")
                self.client.append_blocks(page_id, metadata_blocks)

        return page_id

    def _create_metadata_blocks(self, note: EvernoteNote) -> list:
        """
        Create metadata blocks to add at top of page.

        Args:
            note: Evernote note

        Returns:
            List of Notion blocks with metadata
        """
        from app.notion.block_builder import text_paragraph, BlockBuilder

        blocks = []

        # Metadata section
        metadata_lines = []

        # Created date
        if note.created:
            created_str = note.created.strftime("%Y-%m-%d %H:%M:%S")
            metadata_lines.append(f"📅 Created: {created_str}")

        # Updated date
        if note.updated:
            updated_str = note.updated.strftime("%Y-%m-%d %H:%M:%S")
            metadata_lines.append(f"🔄 Updated: {updated_str}")

        # Author
        if note.author:
            metadata_lines.append(f"👤 Author: {note.author}")

        # Source URL
        if note.source_url:
            metadata_lines.append(f"🔗 Source: {note.source_url}")

        # Source application
        if note.source:
            metadata_lines.append(f"📱 Source App: {note.source}")

        # Tags
        if note.tags:
            tags_str = ", ".join(f"#{tag}" for tag in note.tags)
            metadata_lines.append(f"🏷️ Tags: {tags_str}")

        # Resource count
        if note.resources:
            metadata_lines.append(f"📎 Attachments: {len(note.resources)}")

        # Create callout block with metadata
        if metadata_lines:
            metadata_text = "\n".join(metadata_lines)
            blocks.append({
                'type': 'callout',
                'callout': {
                    'rich_text': [BlockBuilder._rich_text(metadata_text)],
                    'icon': {'emoji': 'ℹ️'},
                    'color': 'gray_background'
                }
            })

            # Add divider after metadata
            blocks.append(BlockBuilder.divider())

        return blocks

    def _build_resource_map(self, note: EvernoteNote) -> Dict[str, Resource]:
        """
        Build resource hash map from note resources.

        Args:
            note: Evernote note

        Returns:
            Dictionary mapping MD5 hash to Resource object
        """
        return {resource.hash: resource for resource in note.resources}

    def _get_page_icon(self, note: EvernoteNote) -> Optional[Dict[str, str]]:
        """
        Get page icon based on note properties.

        Args:
            note: Evernote note

        Returns:
            Icon dict or None
        """
        # Check if note has images
        has_images = any(r.mime.startswith('image/') for r in note.resources)

        # Check if note has PDFs
        has_pdfs = any(r.mime == 'application/pdf' for r in note.resources)

        # Check if note has code (rough heuristic)
        has_code = '<code>' in note.content or 'class="code"' in note.content

        # Select icon based on content
        if has_code:
            return {'emoji': '💻'}
        elif has_pdfs:
            return {'emoji': '📄'}
        elif has_images:
            return {'emoji': '🖼️'}
        elif note.tags:
            return {'emoji': '🏷️'}
        else:
            return {'emoji': '📝'}

    def create_batch(
        self,
        notes: list[EvernoteNote],
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Create multiple pages from notes.

        Args:
            notes: List of Evernote notes
            progress_callback: Optional callback(current, total, note_title)

        Returns:
            Dictionary with results:
            {
                'success': int,
                'failed': int,
                'page_ids': List[str],
                'errors': List[Dict]
            }
        """
        results = {
            'success': 0,
            'failed': 0,
            'page_ids': [],
            'errors': []
        }

        total = len(notes)
        logger.info(f"Creating {total} pages...")

        for i, note in enumerate(notes, 1):
            try:
                # Progress callback
                if progress_callback:
                    progress_callback(i, total, note.title)

                # Create page
                page_id = self.create_from_note(note)

                results['success'] += 1
                results['page_ids'].append(page_id)

                logger.info(f"[{i}/{total}] ✅ Created: {note.title}")

            except PageCreationError as e:
                results['failed'] += 1
                results['errors'].append({
                    'note_title': note.title,
                    'error': str(e)
                })

                logger.error(f"[{i}/{total}] ❌ Failed: {note.title} - {e}")

        logger.info(f"Batch complete: {results['success']} success, {results['failed']} failed")
        return results


class DatabasePageCreator(PageCreator):
    """
    Page creator for database parents.

    Supports property assignment when parent is a Notion database.
    """

    def _create_page_with_metadata(
        self,
        note: EvernoteNote,
        include_metadata: bool
    ) -> str:
        """
        Create page with database properties.

        Args:
            note: Evernote note
            include_metadata: Whether to include metadata properties

        Returns:
            Created page ID
        """
        properties = None

        if include_metadata:
            properties = self._build_database_properties(note)

        # Create page
        page_id = self.client.create_page(
            parent_id=self.parent_id,
            title=note.title,
            properties=properties,
            icon=self._get_page_icon(note)
        )

        return page_id

    def _build_database_properties(self, note: EvernoteNote) -> Dict[str, Any]:
        """
        Build Notion database properties from note metadata.

        Note: This assumes the parent database has these properties defined.
        Property types must match the database schema.

        Args:
            note: Evernote note

        Returns:
            Dictionary of Notion properties
        """
        props = {}

        # Tags (Multi-select)
        if note.tags:
            props['Tags'] = {
                'multi_select': [{'name': tag} for tag in note.tags]
            }

        # Created date (Date)
        if note.created:
            props['Created'] = {
                'date': {'start': note.created.isoformat()}
            }

        # Updated date (Date)
        if note.updated:
            props['Updated'] = {
                'date': {'start': note.updated.isoformat()}
            }

        # Author (Rich text)
        if note.author:
            props['Author'] = {
                'rich_text': [{'text': {'content': note.author}}]
            }

        # Source URL (URL)
        if note.source_url:
            props['Source URL'] = {
                'url': note.source_url
            }

        # Source (Rich text)
        if note.source:
            props['Source'] = {
                'rich_text': [{'text': {'content': note.source}}]
            }

        return props
