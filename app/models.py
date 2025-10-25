"""
Data models for Evernote to Notion migration.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Resource:
    """
    Represents an Evernote resource (image, file, etc.).

    Attributes:
        data: Raw binary data (Base64 decoded)
        mime: MIME type (e.g., 'image/jpeg', 'application/pdf')
        filename: Original filename (from resource-attributes)
        width: Image width in pixels (None for non-images)
        height: Image height in pixels (None for non-images)
        hash: MD5 hash of the data (used for ENML <en-media> matching)
        source_url: Original source URL (if available)
        uploaded_url: URL after uploading to S3/Cloudinary (None initially)
        local_path: Local temporary file path (None initially)
    """
    data: bytes
    mime: str
    hash: str  # MD5 hash
    filename: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    source_url: Optional[str] = None
    uploaded_url: Optional[str] = None
    local_path: Optional[str] = None

    def get_extension(self) -> str:
        """
        Get file extension from MIME type.

        Returns:
            File extension (e.g., 'jpg', 'png', 'pdf')
        """
        mime_map = {
            'image/jpeg': 'jpg',
            'image/png': 'png',
            'image/svg+xml': 'svg',
            'image/webp': 'webp',
            'image/gif': 'gif',
            'application/pdf': 'pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'pptx',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
            'text/markdown': 'md',
            'text/plain': 'txt',
            'application/zip': 'zip',
            'application/x-zip-compressed': 'zip',
        }
        return mime_map.get(self.mime, 'bin')

    def is_image(self) -> bool:
        """Check if resource is an image."""
        return self.mime.startswith('image/')

    def is_document(self) -> bool:
        """Check if resource is a document (PDF, Office)."""
        return self.mime in [
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        ]


@dataclass
class EvernoteNote:
    """
    Represents an Evernote note.

    Attributes:
        title: Note title
        content: Note content in ENML (Evernote Markup Language) format
        created: Creation timestamp
        updated: Last update timestamp
        tags: List of tags
        author: Note author (if available)
        source: Note source (e.g., 'web.clip', 'mobile.android')
        source_url: Original source URL (for web clips)
        resources: List of attached resources (images, files)
    """
    title: str
    content: str  # ENML format
    created: datetime
    updated: datetime
    tags: List[str] = field(default_factory=list)
    author: Optional[str] = None
    source: Optional[str] = None
    source_url: Optional[str] = None
    resources: List[Resource] = field(default_factory=list)

    def has_resources(self) -> bool:
        """Check if note has any resources."""
        return len(self.resources) > 0

    def get_resource_by_hash(self, hash_value: str) -> Optional[Resource]:
        """
        Find resource by MD5 hash.

        Args:
            hash_value: MD5 hash to search for

        Returns:
            Resource if found, None otherwise
        """
        for resource in self.resources:
            if resource.hash == hash_value:
                return resource
        return None

    def __repr__(self) -> str:
        return (
            f"EvernoteNote(title='{self.title}', "
            f"created={self.created.date()}, "
            f"tags={len(self.tags)}, "
            f"resources={len(self.resources)})"
        )
