"""
ENML to Notion Block Converter

Converts Evernote Markup Language (ENML) to Notion API block format.
Based on ENML pattern analysis in docs/ENML_PATTERNS.md.
"""

import html
import re
from typing import Dict, List, Optional, Any, Union
from bs4 import BeautifulSoup, Tag, NavigableString

from app.models import Resource


class EnmlConverter:
    """Converts ENML content to Notion blocks."""

    # Notion supported colors
    NOTION_COLORS = {
        'gray', 'brown', 'orange', 'yellow', 'green', 'blue',
        'purple', 'pink', 'red', 'gray_background', 'brown_background',
        'orange_background', 'yellow_background', 'green_background',
        'blue_background', 'purple_background', 'pink_background', 'red_background'
    }

    def __init__(self, resource_hash_map: Dict[str, Resource]):
        """
        Initialize converter.

        Args:
            resource_hash_map: Dictionary mapping MD5 hash to Resource objects
        """
        self.resources = resource_hash_map

    def convert(self, enml: str) -> List[Dict[str, Any]]:
        """
        Convert ENML content to Notion blocks.

        Args:
            enml: ENML content string

        Returns:
            List of Notion block dictionaries
        """
        # Extract from CDATA if present
        enml = self._extract_from_cdata(enml)

        # Parse with BeautifulSoup (use 'xml' parser to preserve case)
        soup = BeautifulSoup(enml, 'xml')

        # Find en-note root element
        en_note = soup.find('en-note')
        if not en_note:
            # Fallback: try without en-note wrapper
            en_note = soup

        # Convert child elements to blocks
        blocks = []
        for element in en_note.children:
            if isinstance(element, NavigableString):
                # Text node outside of tags
                text = str(element).strip()
                if text:
                    blocks.append(self._create_paragraph([self._create_text(text)]))
            elif isinstance(element, Tag):
                block = self._convert_element(element)
                if block:
                    if isinstance(block, list):
                        blocks.extend(block)
                    else:
                        blocks.append(block)

        # If no blocks created, return empty paragraph
        if not blocks:
            blocks.append(self._create_paragraph([self._create_text("")]))

        return blocks

    def _extract_from_cdata(self, enml: str) -> str:
        """Extract ENML from CDATA section if present."""
        cdata_pattern = r'<!\[CDATA\[(.*?)\]\]>'
        match = re.search(cdata_pattern, enml, re.DOTALL)
        if match:
            return match.group(1)
        return enml

    def _convert_element(self, element: Tag) -> Optional[Union[Dict[str, Any], List[Dict[str, Any]]]]:
        """
        Convert a single ENML element to Notion block(s).

        Args:
            element: BeautifulSoup Tag element

        Returns:
            Notion block dictionary, list of blocks, or None
        """
        tag_name = element.name.lower()

        # Headings (h1-h6)
        if tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            return self._convert_heading(element)

        # Paragraphs
        elif tag_name in ['div', 'p']:
            return self._convert_paragraph(element)

        # Lists
        elif tag_name == 'ul':
            return self._convert_list(element, ordered=False)
        elif tag_name == 'ol':
            return self._convert_list(element, ordered=True)

        # Line break
        elif tag_name == 'br':
            # Line breaks are handled within paragraph processing
            return None

        # Horizontal rule
        elif tag_name == 'hr':
            return {'type': 'divider', 'divider': {}}

        # Blockquote
        elif tag_name == 'blockquote':
            return self._convert_blockquote(element)

        # Table
        elif tag_name == 'table':
            return self._convert_table(element)

        # Evernote-specific: media
        elif tag_name == 'en-media':
            return self._convert_media(element)

        # Evernote-specific: todo
        elif tag_name == 'en-todo':
            return self._convert_todo(element)

        # Skip structural elements (handled by their parents)
        elif tag_name in ['tbody', 'colgroup', 'col', 'en-note']:
            return None

        # Unknown tag - convert as paragraph
        else:
            rich_text = self._extract_rich_text(element)
            if rich_text:
                return self._create_paragraph(rich_text)
            return None

    def _convert_heading(self, element: Tag) -> Dict[str, Any]:
        """Convert h1-h6 to Notion heading."""
        level = int(element.name[1])  # h1 -> 1, h2 -> 2, etc.

        # Notion only supports heading_1, heading_2, heading_3
        if level > 3:
            # Convert h4-h6 to heading_3 with bold
            heading_type = 'heading_3'
            rich_text = self._extract_rich_text(element, force_bold=True)
        else:
            heading_type = f'heading_{level}'
            rich_text = self._extract_rich_text(element)

        return {
            'type': heading_type,
            heading_type: {
                'rich_text': rich_text,
                'color': 'default',
                'is_toggleable': False
            }
        }

    def _convert_paragraph(self, element: Tag) -> Optional[Dict[str, Any]]:
        """Convert div/p to Notion paragraph."""
        # Check if this is just a container for other block-level elements
        has_block_children = any(
            child.name in ['ul', 'ol', 'table', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'hr']
            for child in element.children if isinstance(child, Tag)
        )

        if has_block_children:
            # Don't create paragraph, let children be converted as blocks
            blocks = []
            for child in element.children:
                if isinstance(child, Tag):
                    block = self._convert_element(child)
                    if block:
                        if isinstance(block, list):
                            blocks.extend(block)
                        else:
                            blocks.append(block)
            return blocks if blocks else None

        # Extract rich text
        rich_text = self._extract_rich_text(element)

        # Skip empty paragraphs (except if it's just <br/>)
        if not rich_text or all(rt['text']['content'].strip() == '' for rt in rich_text):
            # Check if it contains only <br>
            if element.find('br'):
                rich_text = [self._create_text("")]
            else:
                return None

        return self._create_paragraph(rich_text)

    def _convert_list(self, element: Tag, ordered: bool = False) -> List[Dict[str, Any]]:
        """Convert ul/ol to Notion list items."""
        blocks = []
        list_type = 'numbered_list_item' if ordered else 'bulleted_list_item'

        for li in element.find_all('li', recursive=False):
            # Extract rich text from li
            rich_text = self._extract_rich_text(li)

            if not rich_text:
                rich_text = [self._create_text("")]

            block = {
                'type': list_type,
                list_type: {
                    'rich_text': rich_text,
                    'color': 'default'
                }
            }

            # Handle nested lists
            nested_lists = li.find_all(['ul', 'ol'], recursive=False)
            if nested_lists:
                children = []
                for nested_list in nested_lists:
                    nested_blocks = self._convert_list(
                        nested_list,
                        ordered=(nested_list.name == 'ol')
                    )
                    children.extend(nested_blocks)

                if children:
                    block[list_type]['children'] = children

            blocks.append(block)

        return blocks

    def _convert_blockquote(self, element: Tag) -> Dict[str, Any]:
        """Convert blockquote to Notion quote."""
        rich_text = self._extract_rich_text(element)

        if not rich_text:
            rich_text = [self._create_text("")]

        return {
            'type': 'quote',
            'quote': {
                'rich_text': rich_text,
                'color': 'default'
            }
        }

    def _convert_table(self, element: Tag) -> Dict[str, Any]:
        """Convert table to Notion table."""
        # Find all rows
        rows = element.find_all('tr')

        if not rows:
            return None

        # Check if first row has th elements (header row)
        has_header = bool(rows[0].find('th'))

        # Count columns from first row
        first_row_cells = rows[0].find_all(['td', 'th'])
        num_columns = len(first_row_cells)

        if num_columns == 0:
            return None

        # Create table block
        table_block = {
            'type': 'table',
            'table': {
                'table_width': num_columns,
                'has_column_header': has_header,
                'has_row_header': False,
                'children': []
            }
        }

        # Convert rows
        for row in rows:
            cells = row.find_all(['td', 'th'])

            # Pad cells if needed
            cell_blocks = []
            for i in range(num_columns):
                if i < len(cells):
                    cell_rich_text = self._extract_rich_text(cells[i])
                    if not cell_rich_text:
                        cell_rich_text = [self._create_text("")]
                else:
                    cell_rich_text = [self._create_text("")]

                cell_blocks.append(cell_rich_text)

            table_block['table']['children'].append({
                'type': 'table_row',
                'table_row': {
                    'cells': cell_blocks
                }
            })

        return table_block

    def _convert_media(self, element: Tag) -> Optional[Dict[str, Any]]:
        """Convert en-media to Notion image or file block."""
        hash_value = element.get('hash')
        mime_type = element.get('type', '')

        if not hash_value:
            return None

        resource = self.resources.get(hash_value)
        if not resource:
            # Resource not found - create a placeholder
            return self._create_paragraph([
                self._create_text(f"[Missing resource: {hash_value}]")
            ])

        # Check if resource has been uploaded
        if not resource.uploaded_url:
            # Not yet uploaded - will be handled later
            return self._create_paragraph([
                self._create_text(f"[Resource pending upload: {resource.filename or hash_value}]")
            ])

        # Create appropriate block based on MIME type
        if mime_type.startswith('image/'):
            return {
                'type': 'image',
                'image': {
                    'type': 'external',
                    'external': {'url': resource.uploaded_url}
                }
            }
        elif mime_type == 'application/pdf':
            return {
                'type': 'pdf',
                'pdf': {
                    'type': 'external',
                    'external': {'url': resource.uploaded_url}
                }
            }
        else:
            # Generic file
            return {
                'type': 'file',
                'file': {
                    'type': 'external',
                    'external': {'url': resource.uploaded_url}
                }
            }

    def _convert_todo(self, element: Tag) -> Dict[str, Any]:
        """Convert en-todo to Notion to_do block."""
        checked = element.get('checked') == 'true'

        # Get text after the en-todo element
        next_text = ""
        if element.next_sibling:
            if isinstance(element.next_sibling, NavigableString):
                next_text = str(element.next_sibling).strip()
            elif isinstance(element.next_sibling, Tag):
                next_text = element.next_sibling.get_text().strip()

        rich_text = [self._create_text(next_text)] if next_text else [self._create_text("")]

        return {
            'type': 'to_do',
            'to_do': {
                'rich_text': rich_text,
                'checked': checked,
                'color': 'default'
            }
        }

    def _extract_rich_text(self, element: Tag, force_bold: bool = False) -> List[Dict[str, Any]]:
        """
        Extract rich text from an element, preserving formatting.

        Args:
            element: BeautifulSoup Tag element
            force_bold: Force all text to be bold (for h4-h6)

        Returns:
            List of Notion rich text objects
        """
        rich_text_parts = []

        # Process all descendants
        self._process_node(element, rich_text_parts, {
            'bold': force_bold,
            'italic': False,
            'underline': False,
            'code': False,
            'strikethrough': False,
            'color': 'default'
        })

        # Merge consecutive text parts with same annotations
        merged = self._merge_rich_text(rich_text_parts)

        # Handle line breaks
        merged = self._handle_line_breaks(merged)

        return merged if merged else [self._create_text("")]

    def _process_node(self, node, rich_text_parts: List[Dict], current_annotations: Dict, current_link: Optional[str] = None):
        """Recursively process node and extract text with annotations."""
        if isinstance(node, NavigableString):
            text = str(node)

            # Decode HTML entities
            text = html.unescape(text)

            if text:
                text_obj = self._create_text(text, current_annotations.copy(), current_link)
                rich_text_parts.append(text_obj)

        elif isinstance(node, Tag):
            tag_name = node.name.lower()

            # Skip en-todo (handled separately)
            if tag_name == 'en-todo':
                return

            # Skip nested block elements in rich text context (but NOT div - div can contain inline text)
            if tag_name in ['ul', 'ol', 'table', 'blockquote', 'hr']:
                # These should be handled as separate blocks
                return

            # Update annotations based on tag
            new_annotations = current_annotations.copy()
            new_link = current_link

            if tag_name in ['b', 'strong']:
                new_annotations['bold'] = True
            elif tag_name in ['i', 'em']:
                new_annotations['italic'] = True
            elif tag_name == 'u':
                new_annotations['underline'] = True
            elif tag_name == 'code':
                new_annotations['code'] = True
            elif tag_name == 's' or tag_name == 'strike':
                new_annotations['strikethrough'] = True
            elif tag_name == 'a':
                href = node.get('href', '')
                if href:
                    new_link = href
            elif tag_name == 'br':
                # Insert newline
                rich_text_parts.append(self._create_text('\n', current_annotations.copy()))
                return
            elif tag_name in ['span', 'div', 'p']:
                # These are often just containers - check for color styling
                style = node.get('style', '')
                color = self._extract_color(style)
                if color:
                    new_annotations['color'] = color
                # Just pass through to children with same or updated annotations

            # Process children
            for child in node.children:
                self._process_node(child, rich_text_parts, new_annotations, new_link)

    def _extract_color(self, style: str) -> Optional[str]:
        """Extract color from CSS style string and map to Notion color."""
        # Look for color:rgb(...) pattern
        color_match = re.search(r'color:\s*rgb\((\d+),\s*(\d+),\s*(\d+)\)', style)
        if color_match:
            r, g, b = map(int, color_match.groups())
            return self._rgb_to_notion_color(r, g, b)

        # Look for color:#hex pattern
        hex_match = re.search(r'color:\s*#([0-9a-fA-F]{6})', style)
        if hex_match:
            hex_color = hex_match.group(1)
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return self._rgb_to_notion_color(r, g, b)

        return None

    def _rgb_to_notion_color(self, r: int, g: int, b: int) -> str:
        """Map RGB color to closest Notion color."""
        # Simple heuristic mapping to Notion colors
        # This is very basic - you could improve with color distance calculations

        if r > 200 and g < 100 and b < 100:
            return 'red'
        elif r > 200 and g > 150 and b < 100:
            return 'orange'
        elif r > 200 and g > 200 and b < 100:
            return 'yellow'
        elif r < 100 and g > 200 and b < 100:
            return 'green'
        elif r < 100 and g < 100 and b > 200:
            return 'blue'
        elif r > 150 and g < 100 and b > 150:
            return 'purple'
        elif r > 200 and g < 150 and b > 150:
            return 'pink'
        elif r < 150 and g < 150 and b < 150:
            return 'gray'

        return 'default'

    def _merge_rich_text(self, rich_text_parts: List[Dict]) -> List[Dict]:
        """Merge consecutive rich text parts with identical annotations."""
        if not rich_text_parts:
            return []

        merged = [rich_text_parts[0]]

        for part in rich_text_parts[1:]:
            last = merged[-1]

            # Check if annotations and link match
            if (last['annotations'] == part['annotations'] and
                last.get('text', {}).get('link') == part.get('text', {}).get('link')):
                # Merge text content
                last['text']['content'] += part['text']['content']
            else:
                merged.append(part)

        return merged

    def _handle_line_breaks(self, rich_text_parts: List[Dict]) -> List[Dict]:
        """Handle line breaks in rich text."""
        # Notion doesn't support \n in paragraph rich text well
        # We keep them for now, but they might need special handling
        return rich_text_parts

    def _create_text(self, content: str, annotations: Optional[Dict] = None, link: Optional[str] = None) -> Dict[str, Any]:
        """Create a Notion rich text object."""
        if annotations is None:
            annotations = {
                'bold': False,
                'italic': False,
                'underline': False,
                'code': False,
                'strikethrough': False,
                'color': 'default'
            }

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

    def _create_paragraph(self, rich_text: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a Notion paragraph block."""
        return {
            'type': 'paragraph',
            'paragraph': {
                'rich_text': rich_text,
                'color': 'default'
            }
        }
