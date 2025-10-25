"""
Notion API Client

Wrapper around notion-client with rate limiting, error handling, and retry logic.
"""

import time
import logging
from typing import List, Dict, Any, Optional
from notion_client import Client
from notion_client.errors import APIResponseError

from app.utils.rate_limiter import NotionRateLimiter
from app.notion.block_builder import BlockValidator

logger = logging.getLogger(__name__)


class NotionAPIError(Exception):
    """Base exception for Notion API errors."""
    pass


class NotionRateLimitError(NotionAPIError):
    """Raised when rate limit is exceeded."""
    pass


class NotionClient:
    """
    Notion API client with rate limiting and error handling.

    Features:
    - Automatic rate limiting (3 requests/second)
    - Exponential backoff retry for transient errors
    - Block validation before sending
    - Batch block appending (100 blocks max per request)
    """

    def __init__(self, api_key: str, max_retries: int = 3):
        """
        Initialize Notion client.

        Args:
            api_key: Notion integration API key
            max_retries: Maximum number of retries for failed requests
        """
        self.client = Client(auth=api_key)
        self.rate_limiter = NotionRateLimiter()
        self.max_retries = max_retries

    def _request_with_retry(self, func, *args, **kwargs) -> Any:
        """
        Execute a request with exponential backoff retry.

        Args:
            func: Function to call
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            NotionAPIError: If request fails after all retries
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                # Apply rate limiting
                self.rate_limiter.wait()

                # Execute request
                result = func(*args, **kwargs)
                return result

            except APIResponseError as e:
                last_error = e
                error_code = e.code
                error_message = str(e)

                # Rate limit exceeded - exponential backoff
                if error_code == 'rate_limited':
                    wait_time = 2 ** attempt  # 1s, 2s, 4s
                    logger.warning(f"Rate limited. Waiting {wait_time}s (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(wait_time)
                    continue

                # Validation error - don't retry
                elif error_code == 'validation_error':
                    logger.error(f"Validation error: {error_message}")
                    raise NotionAPIError(f"Validation error: {error_message}") from e

                # Unauthorized - don't retry
                elif error_code == 'unauthorized':
                    logger.error("Unauthorized - check API key")
                    raise NotionAPIError("Unauthorized - check NOTION_API_KEY") from e

                # Object not found - don't retry
                elif error_code == 'object_not_found':
                    logger.error(f"Object not found: {error_message}")
                    raise NotionAPIError(f"Object not found: {error_message}") from e

                # Service unavailable - retry with backoff
                elif error_code == 'service_unavailable':
                    wait_time = 2 ** attempt
                    logger.warning(f"Service unavailable. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                # Unknown error - retry
                else:
                    wait_time = 2 ** attempt
                    logger.warning(f"API error ({error_code}): {error_message}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue

            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error: {e}")
                raise NotionAPIError(f"Unexpected error: {e}") from e

        # All retries exhausted
        raise NotionAPIError(f"Max retries ({self.max_retries}) exceeded") from last_error

    def create_page(
        self,
        parent_id: str,
        title: str,
        properties: Optional[Dict] = None,
        icon: Optional[Dict] = None,
        cover: Optional[Dict] = None
    ) -> str:
        """
        Create a new page in Notion.

        Args:
            parent_id: Parent page or database ID
            title: Page title
            properties: Additional page properties
            icon: Page icon (emoji or external URL)
            cover: Page cover image

        Returns:
            Created page ID

        Raises:
            NotionAPIError: If page creation fails
        """
        # Build page properties
        page_properties = {
            'title': {
                'title': [{'text': {'content': title}}]
            }
        }

        if properties:
            page_properties.update(properties)

        # Build request payload
        payload = {
            'parent': {'page_id': parent_id},
            'properties': page_properties
        }

        if icon:
            payload['icon'] = icon

        if cover:
            payload['cover'] = cover

        # Create page
        logger.info(f"Creating page: {title}")
        page = self._request_with_retry(self.client.pages.create, **payload)

        page_id = page['id']
        logger.info(f"Created page: {title} (ID: {page_id})")
        return page_id

    def append_blocks(
        self,
        block_id: str,
        blocks: List[Dict[str, Any]],
        validate: bool = True
    ) -> None:
        """
        Append blocks to a page or block.

        Automatically splits into batches of 100 blocks (Notion API limit).

        Args:
            block_id: Parent block or page ID
            blocks: List of Notion block objects
            validate: Whether to validate blocks before sending

        Raises:
            NotionAPIError: If block append fails
        """
        if not blocks:
            logger.warning("No blocks to append")
            return

        # Validate blocks if requested
        if validate:
            is_valid, errors = BlockValidator.validate_blocks(blocks)
            if not is_valid:
                error_msg = f"Invalid blocks: {errors}"
                logger.error(error_msg)
                raise NotionAPIError(error_msg)

        # Split into batches of 100
        batch_size = 100
        total_blocks = len(blocks)
        batches = [blocks[i:i + batch_size] for i in range(0, total_blocks, batch_size)]

        logger.info(f"Appending {total_blocks} blocks in {len(batches)} batch(es)")

        for i, batch in enumerate(batches, 1):
            logger.debug(f"Appending batch {i}/{len(batches)} ({len(batch)} blocks)")

            self._request_with_retry(
                self.client.blocks.children.append,
                block_id=block_id,
                children=batch
            )

            logger.info(f"Batch {i}/{len(batches)} appended successfully")

        logger.info(f"All {total_blocks} blocks appended successfully")

    def update_page(
        self,
        page_id: str,
        properties: Optional[Dict] = None,
        archived: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Update page properties.

        Args:
            page_id: Page ID to update
            properties: Properties to update
            archived: Whether to archive the page

        Returns:
            Updated page object

        Raises:
            NotionAPIError: If update fails
        """
        payload = {}

        if properties is not None:
            payload['properties'] = properties

        if archived is not None:
            payload['archived'] = archived

        if not payload:
            logger.warning("No updates provided")
            return {}

        logger.info(f"Updating page: {page_id}")
        result = self._request_with_retry(
            self.client.pages.update,
            page_id=page_id,
            **payload
        )

        logger.info(f"Page updated successfully: {page_id}")
        return result

    def get_page(self, page_id: str) -> Dict[str, Any]:
        """
        Retrieve a page.

        Args:
            page_id: Page ID

        Returns:
            Page object

        Raises:
            NotionAPIError: If retrieval fails
        """
        logger.debug(f"Retrieving page: {page_id}")
        page = self._request_with_retry(self.client.pages.retrieve, page_id=page_id)
        return page

    def get_block_children(
        self,
        block_id: str,
        page_size: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get all children blocks of a block.

        Args:
            block_id: Parent block ID
            page_size: Number of results per page (max 100)

        Returns:
            List of child blocks

        Raises:
            NotionAPIError: If retrieval fails
        """
        all_blocks = []
        has_more = True
        start_cursor = None

        while has_more:
            response = self._request_with_retry(
                self.client.blocks.children.list,
                block_id=block_id,
                page_size=min(page_size, 100),
                start_cursor=start_cursor
            )

            all_blocks.extend(response.get('results', []))
            has_more = response.get('has_more', False)
            start_cursor = response.get('next_cursor')

        return all_blocks

    def search(
        self,
        query: str = "",
        filter_type: Optional[str] = None,
        sort_direction: str = "descending"
    ) -> List[Dict[str, Any]]:
        """
        Search for pages/databases.

        Args:
            query: Search query text
            filter_type: Filter by "page" or "database"
            sort_direction: "ascending" or "descending"

        Returns:
            List of search results

        Raises:
            NotionAPIError: If search fails
        """
        payload = {
            'query': query,
            'sort': {
                'direction': sort_direction,
                'timestamp': 'last_edited_time'
            }
        }

        if filter_type:
            payload['filter'] = {'value': filter_type, 'property': 'object'}

        response = self._request_with_retry(self.client.search, **payload)
        return response.get('results', [])
