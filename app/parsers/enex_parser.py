"""
ENEX (Evernote Export) file parser.

Parses Evernote export files (.enex) and extracts notes with their metadata and resources.
"""

import base64
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Generator, List, Optional
from lxml import etree as ET

from app.models import EvernoteNote, Resource


class EnexParser:
    """
    Parser for Evernote ENEX files.

    Uses streaming XML parsing (iterparse) to handle large files efficiently.
    """

    def __init__(self, file_path: str):
        """
        Initialize parser with ENEX file path.

        Args:
            file_path: Path to .enex file
        """
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"ENEX file not found: {file_path}")
        if not self.file_path.suffix == '.enex':
            raise ValueError(f"Not an ENEX file: {file_path}")

    def parse(self) -> Generator[EvernoteNote, None, None]:
        """
        Parse ENEX file and yield notes one by one.

        Uses streaming parsing to minimize memory usage for large files.

        Yields:
            EvernoteNote objects

        Raises:
            ET.ParseError: If XML is malformed
        """
        # Create parser with huge_tree option to handle large text nodes (e.g., base64 images)
        parser = ET.XMLParser(huge_tree=True, recover=True)

        try:
            # Parse the entire tree (needed for huge_tree to work)
            tree = ET.parse(str(self.file_path), parser=parser)
            root = tree.getroot()

            # Iterate through note elements
            for note_elem in root.findall('note'):
                try:
                    note = self._parse_note(note_elem)
                    yield note
                except Exception as e:
                    # Log error but continue parsing other notes
                    print(f"Warning: Failed to parse note: {e}")
                finally:
                    # Clear element to free memory after processing
                    note_elem.clear()

        except ET.XMLSyntaxError as e:
            print(f"XML Syntax Error: {e}")
            return


    def parse_all(self) -> List[EvernoteNote]:
        """
        Parse all notes and return as a list.

        Use this for smaller files. For large files, use parse() instead.

        Returns:
            List of EvernoteNote objects
        """
        return list(self.parse())

    def _parse_note(self, note_element: ET.Element) -> EvernoteNote:
        """
        Parse a single <note> element.

        Args:
            note_element: XML element for <note>

        Returns:
            EvernoteNote object
        """
        # Extract title
        title_elem = note_element.find('title')
        title = title_elem.text if title_elem is not None and title_elem.text else "Untitled"

        # Extract content (ENML)
        content_elem = note_element.find('content')
        content = content_elem.text if content_elem is not None and content_elem.text else ""

        # Extract timestamps
        created_elem = note_element.find('created')
        created = self._parse_datetime(created_elem.text) if created_elem is not None else datetime.now()

        updated_elem = note_element.find('updated')
        updated = self._parse_datetime(updated_elem.text) if updated_elem is not None else created

        # Extract tags
        tags = [tag.text for tag in note_element.findall('tag') if tag.text]

        # Extract note attributes
        attributes = note_element.find('note-attributes')
        author = None
        source = None
        source_url = None

        if attributes is not None:
            author_elem = attributes.find('author')
            author = author_elem.text if author_elem is not None else None

            source_elem = attributes.find('source')
            source = source_elem.text if source_elem is not None else None

            source_url_elem = attributes.find('source-url')
            source_url = source_url_elem.text if source_url_elem is not None else None

        # Extract resources
        resources = self._parse_resources(note_element)

        return EvernoteNote(
            title=title,
            content=content,
            created=created,
            updated=updated,
            tags=tags,
            author=author,
            source=source,
            source_url=source_url,
            resources=resources
        )

    def _parse_resources(self, note_element: ET.Element) -> List[Resource]:
        """
        Parse all <resource> elements in a note.

        Args:
            note_element: XML element for <note>

        Returns:
            List of Resource objects
        """
        resources = []

        for resource_elem in note_element.findall('resource'):
            try:
                resource = self._parse_single_resource(resource_elem)
                if resource:
                    resources.append(resource)
            except Exception as e:
                print(f"Warning: Failed to parse resource: {e}")

        return resources

    def _parse_single_resource(self, resource_elem: ET.Element) -> Optional[Resource]:
        """
        Parse a single <resource> element.

        Args:
            resource_elem: XML element for <resource>

        Returns:
            Resource object or None if parsing fails
        """
        # Extract data (Base64 encoded)
        data_elem = resource_elem.find('data')
        if data_elem is None or not data_elem.text:
            return None

        encoding = data_elem.get('encoding', 'base64')
        if encoding != 'base64':
            print(f"Warning: Unsupported encoding: {encoding}")
            return None

        # Decode Base64 data
        try:
            data = base64.b64decode(data_elem.text)
        except Exception as e:
            print(f"Warning: Failed to decode Base64 data: {e}")
            return None

        # Calculate MD5 hash
        md5_hash = self._calculate_md5(data)

        # Extract MIME type
        mime_elem = resource_elem.find('mime')
        mime = mime_elem.text if mime_elem is not None else 'application/octet-stream'

        # Extract dimensions (for images)
        width_elem = resource_elem.find('width')
        width = int(width_elem.text) if width_elem is not None and width_elem.text else None

        height_elem = resource_elem.find('height')
        height = int(height_elem.text) if height_elem is not None and height_elem.text else None

        # Extract resource attributes
        attributes = resource_elem.find('resource-attributes')
        filename = None
        source_url = None

        if attributes is not None:
            filename_elem = attributes.find('file-name')
            filename = filename_elem.text if filename_elem is not None else None

            source_url_elem = attributes.find('source-url')
            source_url = source_url_elem.text if source_url_elem is not None else None

        return Resource(
            data=data,
            mime=mime,
            hash=md5_hash,
            filename=filename,
            width=width,
            height=height,
            source_url=source_url
        )

    @staticmethod
    def _parse_datetime(date_str: str) -> datetime:
        """
        Parse Evernote datetime format.

        Format: 20200101T120000Z (ISO 8601)

        Args:
            date_str: Date string from ENEX

        Returns:
            datetime object
        """
        try:
            return datetime.strptime(date_str, '%Y%m%dT%H%M%SZ')
        except ValueError:
            # Try alternative formats if needed
            try:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except ValueError:
                print(f"Warning: Failed to parse datetime: {date_str}")
                return datetime.now()

    @staticmethod
    def _calculate_md5(data: bytes) -> str:
        """
        Calculate MD5 hash of binary data.

        This hash is used to match resources with <en-media> tags in ENML.

        Args:
            data: Binary data

        Returns:
            MD5 hash as hexadecimal string
        """
        return hashlib.md5(data).hexdigest()
