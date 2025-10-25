"""
Notion Block Builder

Helper utilities for building and validating Notion API block structures.
Handles Notion API limits (2000 chars per rich text, 100 blocks per request).
"""

from typing import List, Dict, Any, Optional, Union
import re


class NotionLimits:
    """Notion API limits and constraints."""
    MAX_RICH_TEXT_LENGTH = 2000  # Max characters in a single rich text object
    MAX_BLOCKS_PER_REQUEST = 100  # Max blocks in a single API request
    MAX_NESTED_DEPTH = 2  # Max depth for nested blocks (children)


class BlockBuilder:
    """
    Helper class for building Notion block structures.

    Provides utility methods for creating and validating Notion blocks,
    handling text length limits, and ensuring API compatibility.
    """

    @staticmethod
    def _rich_text(content: str, annotations: Optional[Dict] = None, link: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a Notion rich text object.

        Args:
            content: Text content (will be truncated if > 2000 chars)
            annotations: Text formatting (bold, italic, etc.)
            link: URL if this is a link

        Returns:
            Notion rich text object
        """
        if annotations is None:
            annotations = {
                'bold': False,
                'italic': False,
                'underline': False,
                'code': False,
                'strikethrough': False,
                'color': 'default'
            }

        # Truncate if too long (should be split before calling this)
        if len(content) > NotionLimits.MAX_RICH_TEXT_LENGTH:
            content = content[:NotionLimits.MAX_RICH_TEXT_LENGTH]

        text_obj = {
            'type': 'text',
            'text': {
                'content': content,
            },
            'annotations': annotations
        }

        if link:
            text_obj['text']['link'] = {'url': link}

        return text_obj

    @staticmethod
    def split_long_text(text: str, max_length: int = NotionLimits.MAX_RICH_TEXT_LENGTH) -> List[str]:
        """
        Split long text into chunks that fit Notion's character limit.

        Tries to split at word boundaries, then sentence boundaries, then anywhere.

        Args:
            text: Text to split
            max_length: Maximum length per chunk (default: 2000)

        Returns:
            List of text chunks
        """
        if len(text) <= max_length:
            return [text]

        chunks = []
        remaining = text

        while len(remaining) > max_length:
            # Try to split at word boundary
            split_pos = remaining.rfind(' ', 0, max_length)

            # If no space found, try newline
            if split_pos == -1:
                split_pos = remaining.rfind('\n', 0, max_length)

            # If still no good split point, try sentence boundary
            if split_pos == -1:
                sentence_endings = ['. ', '! ', '? ', '。', '！', '？']
                for ending in sentence_endings:
                    pos = remaining.rfind(ending, 0, max_length)
                    if pos != -1:
                        split_pos = pos + len(ending)
                        break

            # If still nothing, just hard split
            if split_pos == -1 or split_pos == 0:
                split_pos = max_length

            chunks.append(remaining[:split_pos])
            remaining = remaining[split_pos:].lstrip()

        if remaining:
            chunks.append(remaining)

        return chunks

    @staticmethod
    def split_rich_text_list(rich_text_list: List[Dict], max_length: int = NotionLimits.MAX_RICH_TEXT_LENGTH) -> List[List[Dict]]:
        """
        Split a list of rich text objects into multiple lists if total exceeds limit.

        Args:
            rich_text_list: List of Notion rich text objects
            max_length: Maximum total character length

        Returns:
            List of rich text lists, each under the limit
        """
        if not rich_text_list:
            return [[]]

        result = []
        current_chunk = []
        current_length = 0

        for rt_obj in rich_text_list:
            content = rt_obj.get('text', {}).get('content', '')
            content_length = len(content)

            # If single object exceeds limit, split it
            if content_length > max_length:
                # Save current chunk if not empty
                if current_chunk:
                    result.append(current_chunk)
                    current_chunk = []
                    current_length = 0

                # Split the long content
                chunks = BlockBuilder.split_long_text(content, max_length)
                for chunk in chunks:
                    new_rt = rt_obj.copy()
                    new_rt['text'] = rt_obj['text'].copy()
                    new_rt['text']['content'] = chunk
                    result.append([new_rt])

            # If adding this object would exceed limit, start new chunk
            elif current_length + content_length > max_length:
                if current_chunk:
                    result.append(current_chunk)
                current_chunk = [rt_obj]
                current_length = content_length

            # Otherwise add to current chunk
            else:
                current_chunk.append(rt_obj)
                current_length += content_length

        # Add remaining chunk
        if current_chunk:
            result.append(current_chunk)

        return result if result else [[]]

    @staticmethod
    def paragraph(rich_text: List[Dict], color: str = 'default') -> Dict[str, Any]:
        """Create a paragraph block."""
        return {
            'type': 'paragraph',
            'paragraph': {
                'rich_text': rich_text,
                'color': color
            }
        }

    @staticmethod
    def heading_1(rich_text: List[Dict], color: str = 'default', is_toggleable: bool = False) -> Dict[str, Any]:
        """Create a heading 1 block."""
        return {
            'type': 'heading_1',
            'heading_1': {
                'rich_text': rich_text,
                'color': color,
                'is_toggleable': is_toggleable
            }
        }

    @staticmethod
    def heading_2(rich_text: List[Dict], color: str = 'default', is_toggleable: bool = False) -> Dict[str, Any]:
        """Create a heading 2 block."""
        return {
            'type': 'heading_2',
            'heading_2': {
                'rich_text': rich_text,
                'color': color,
                'is_toggleable': is_toggleable
            }
        }

    @staticmethod
    def heading_3(rich_text: List[Dict], color: str = 'default', is_toggleable: bool = False) -> Dict[str, Any]:
        """Create a heading 3 block."""
        return {
            'type': 'heading_3',
            'heading_3': {
                'rich_text': rich_text,
                'color': color,
                'is_toggleable': is_toggleable
            }
        }

    @staticmethod
    def bulleted_list_item(rich_text: List[Dict], color: str = 'default', children: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Create a bulleted list item block."""
        block = {
            'type': 'bulleted_list_item',
            'bulleted_list_item': {
                'rich_text': rich_text,
                'color': color
            }
        }
        if children:
            block['bulleted_list_item']['children'] = children
        return block

    @staticmethod
    def numbered_list_item(rich_text: List[Dict], color: str = 'default', children: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Create a numbered list item block."""
        block = {
            'type': 'numbered_list_item',
            'numbered_list_item': {
                'rich_text': rich_text,
                'color': color
            }
        }
        if children:
            block['numbered_list_item']['children'] = children
        return block

    @staticmethod
    def to_do(rich_text: List[Dict], checked: bool = False, color: str = 'default') -> Dict[str, Any]:
        """Create a to-do block."""
        return {
            'type': 'to_do',
            'to_do': {
                'rich_text': rich_text,
                'checked': checked,
                'color': color
            }
        }

    @staticmethod
    def quote(rich_text: List[Dict], color: str = 'default') -> Dict[str, Any]:
        """Create a quote block."""
        return {
            'type': 'quote',
            'quote': {
                'rich_text': rich_text,
                'color': color
            }
        }

    @staticmethod
    def divider() -> Dict[str, Any]:
        """Create a divider block."""
        return {
            'type': 'divider',
            'divider': {}
        }

    @staticmethod
    def image(url: str, caption: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Create an image block."""
        block = {
            'type': 'image',
            'image': {
                'type': 'external',
                'external': {'url': url}
            }
        }
        if caption:
            block['image']['caption'] = caption
        return block

    @staticmethod
    def file(url: str, caption: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Create a file block."""
        block = {
            'type': 'file',
            'file': {
                'type': 'external',
                'external': {'url': url}
            }
        }
        if caption:
            block['file']['caption'] = caption
        return block

    @staticmethod
    def pdf(url: str, caption: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Create a PDF block."""
        block = {
            'type': 'pdf',
            'pdf': {
                'type': 'external',
                'external': {'url': url}
            }
        }
        if caption:
            block['pdf']['caption'] = caption
        return block

    @staticmethod
    def table(table_width: int, has_column_header: bool, has_row_header: bool, children: List[Dict]) -> Dict[str, Any]:
        """Create a table block."""
        return {
            'type': 'table',
            'table': {
                'table_width': table_width,
                'has_column_header': has_column_header,
                'has_row_header': has_row_header,
                'children': children
            }
        }

    @staticmethod
    def table_row(cells: List[List[Dict]]) -> Dict[str, Any]:
        """Create a table row block."""
        return {
            'type': 'table_row',
            'table_row': {
                'cells': cells
            }
        }

    @staticmethod
    def code(rich_text: List[Dict], language: str = 'plain text', caption: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Create a code block."""
        block = {
            'type': 'code',
            'code': {
                'rich_text': rich_text,
                'language': language
            }
        }
        if caption:
            block['code']['caption'] = caption
        return block


class BlockValidator:
    """Validates Notion blocks against API requirements."""

    @staticmethod
    def validate_rich_text(rich_text: List[Dict]) -> tuple[bool, Optional[str]]:
        """
        Validate a rich text array.

        Returns:
            (is_valid, error_message)
        """
        if not isinstance(rich_text, list):
            return False, "rich_text must be a list"

        total_length = 0
        for rt_obj in rich_text:
            if not isinstance(rt_obj, dict):
                return False, "Each rich text object must be a dict"

            if 'type' not in rt_obj or rt_obj['type'] != 'text':
                return False, "Rich text object must have type='text'"

            content = rt_obj.get('text', {}).get('content', '')
            total_length += len(content)

            if len(content) > NotionLimits.MAX_RICH_TEXT_LENGTH:
                return False, f"Single rich text content exceeds {NotionLimits.MAX_RICH_TEXT_LENGTH} chars"

        return True, None

    @staticmethod
    def validate_block(block: Dict) -> tuple[bool, Optional[str]]:
        """
        Validate a Notion block structure.

        Returns:
            (is_valid, error_message)
        """
        if not isinstance(block, dict):
            return False, "Block must be a dict"

        if 'type' not in block:
            return False, "Block must have a 'type' field"

        block_type = block['type']

        if block_type not in block:
            return False, f"Block must have a '{block_type}' field matching its type"

        # Validate rich_text if present
        block_data = block[block_type]
        if 'rich_text' in block_data:
            is_valid, error = BlockValidator.validate_rich_text(block_data['rich_text'])
            if not is_valid:
                return False, f"{block_type}: {error}"

        # Validate children if present
        if 'children' in block_data:
            children = block_data['children']
            if not isinstance(children, list):
                return False, f"{block_type}: children must be a list"

            for child in children:
                is_valid, error = BlockValidator.validate_block(child)
                if not is_valid:
                    return False, f"{block_type} child: {error}"

        return True, None

    @staticmethod
    def validate_blocks(blocks: List[Dict]) -> tuple[bool, List[str]]:
        """
        Validate a list of blocks.

        Returns:
            (all_valid, list_of_errors)
        """
        errors = []

        for i, block in enumerate(blocks):
            is_valid, error = BlockValidator.validate_block(block)
            if not is_valid:
                errors.append(f"Block {i}: {error}")

        return len(errors) == 0, errors

    @staticmethod
    def split_blocks_for_api(blocks: List[Dict], max_per_request: int = NotionLimits.MAX_BLOCKS_PER_REQUEST) -> List[List[Dict]]:
        """
        Split blocks into chunks that fit API request limits.

        Args:
            blocks: List of Notion blocks
            max_per_request: Maximum blocks per API request

        Returns:
            List of block chunks
        """
        if len(blocks) <= max_per_request:
            return [blocks]

        chunks = []
        for i in range(0, len(blocks), max_per_request):
            chunks.append(blocks[i:i + max_per_request])

        return chunks


# Convenience functions for simple text blocks
def text_paragraph(text: str, bold: bool = False, italic: bool = False, code: bool = False) -> Dict[str, Any]:
    """Create a simple paragraph with plain text."""
    annotations = {
        'bold': bold,
        'italic': italic,
        'underline': False,
        'code': code,
        'strikethrough': False,
        'color': 'default'
    }

    # Split if too long
    chunks = BlockBuilder.split_long_text(text)
    rich_text = [BlockBuilder._rich_text(chunk, annotations) for chunk in chunks]

    return BlockBuilder.paragraph(rich_text)


def text_heading(text: str, level: int = 1, bold: bool = False) -> Dict[str, Any]:
    """Create a simple heading with plain text."""
    annotations = {
        'bold': bold,
        'italic': False,
        'underline': False,
        'code': False,
        'strikethrough': False,
        'color': 'default'
    }

    # Truncate if too long (headings shouldn't be split)
    if len(text) > NotionLimits.MAX_RICH_TEXT_LENGTH:
        text = text[:NotionLimits.MAX_RICH_TEXT_LENGTH]

    rich_text = [BlockBuilder._rich_text(text, annotations)]

    if level == 1:
        return BlockBuilder.heading_1(rich_text)
    elif level == 2:
        return BlockBuilder.heading_2(rich_text)
    else:
        return BlockBuilder.heading_3(rich_text)
