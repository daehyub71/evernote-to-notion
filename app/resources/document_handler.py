"""Document resource handling and validation.

This module provides document processing capabilities for:
- PDF validation
- Office document validation
- Document metadata extraction
- Document type detection
"""

import logging
from pathlib import Path
from typing import Optional, Dict
import mimetypes

logger = logging.getLogger(__name__)


class DocumentHandler:
    """Handles document resource operations for Evernote attachments.

    Supports validation and metadata extraction for various document types
    including PDFs, Office documents, and other file formats.
    """

    # Document MIME types
    PDF_MIME = 'application/pdf'
    WORD_MIME = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    EXCEL_MIME = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    POWERPOINT_MIME = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'

    # File signatures (magic numbers)
    FILE_SIGNATURES = {
        b'%PDF': 'application/pdf',
        b'PK\x03\x04': 'application/zip',  # Also Office docs
        b'\xd0\xcf\x11\xe0': 'application/msword',  # Old Office format
        b'GIF8': 'image/gif',
        b'\x89PNG': 'image/png',
        b'\xff\xd8\xff': 'image/jpeg',
    }

    @staticmethod
    def validate_pdf(pdf_path: str) -> bool:
        """Validate that file is a valid PDF.

        Args:
            pdf_path: Path to PDF file

        Returns:
            True if valid PDF, False otherwise

        Example:
            >>> handler = DocumentHandler()
            >>> is_valid = handler.validate_pdf('document.pdf')
        """
        try:
            with open(pdf_path, 'rb') as f:
                header = f.read(5)
                # PDF files start with %PDF-
                if header.startswith(b'%PDF'):
                    logger.debug(f"Valid PDF: {pdf_path}")
                    return True
                else:
                    logger.warning(f"Invalid PDF header: {pdf_path}")
                    return False
        except Exception as e:
            logger.error(f"Failed to validate PDF {pdf_path}: {e}")
            return False

    @staticmethod
    def validate_office_document(doc_path: str) -> bool:
        """Validate Office document (Word, Excel, PowerPoint).

        Modern Office documents (.docx, .xlsx, .pptx) are ZIP archives.

        Args:
            doc_path: Path to Office document

        Returns:
            True if valid Office document, False otherwise
        """
        try:
            with open(doc_path, 'rb') as f:
                header = f.read(4)
                # Modern Office docs start with PK (ZIP signature)
                if header == b'PK\x03\x04':
                    logger.debug(f"Valid Office document: {doc_path}")
                    return True
                # Old Office format
                elif header[:4] == b'\xd0\xcf\x11\xe0':
                    logger.debug(f"Valid legacy Office document: {doc_path}")
                    return True
                else:
                    logger.warning(f"Invalid Office document header: {doc_path}")
                    return False
        except Exception as e:
            logger.error(f"Failed to validate Office document {doc_path}: {e}")
            return False

    @staticmethod
    def detect_file_type(file_path: str) -> Optional[str]:
        """Detect file type using magic numbers.

        Args:
            file_path: Path to file

        Returns:
            MIME type string or None if undetected

        Example:
            >>> mime = DocumentHandler.detect_file_type('unknown.bin')
            >>> print(mime)  # 'application/pdf'
        """
        try:
            with open(file_path, 'rb') as f:
                header = f.read(8)

                # Check known signatures
                for signature, mime_type in DocumentHandler.FILE_SIGNATURES.items():
                    if header.startswith(signature):
                        logger.debug(f"Detected {mime_type} for {file_path}")
                        return mime_type

                # Fall back to extension-based detection
                mime_type, _ = mimetypes.guess_type(file_path)
                if mime_type:
                    logger.debug(f"Guessed {mime_type} for {file_path}")
                    return mime_type

                logger.warning(f"Could not detect file type for {file_path}")
                return None

        except Exception as e:
            logger.error(f"Failed to detect file type for {file_path}: {e}")
            return None

    @staticmethod
    def get_document_info(doc_path: str) -> Optional[Dict]:
        """Extract document metadata and properties.

        Args:
            doc_path: Path to document file

        Returns:
            Dictionary with document information or None if invalid

        Example:
            >>> info = DocumentHandler.get_document_info('file.pdf')
            >>> print(info['file_size'])
            1024000
        """
        try:
            path = Path(doc_path)

            if not path.exists():
                logger.error(f"Document not found: {doc_path}")
                return None

            stat = path.stat()
            detected_mime = DocumentHandler.detect_file_type(doc_path)

            info = {
                'filename': path.name,
                'extension': path.suffix.lower(),
                'file_size': stat.st_size,
                'file_size_mb': stat.st_size / (1024 * 1024),
                'detected_mime': detected_mime,
                'is_pdf': DocumentHandler.validate_pdf(doc_path) if detected_mime == 'application/pdf' else False,
                'is_office': DocumentHandler.validate_office_document(doc_path) if 'office' in (detected_mime or '') else False,
            }

            logger.debug(f"Document info for {doc_path}: {info}")
            return info

        except Exception as e:
            logger.error(f"Failed to get document info for {doc_path}: {e}")
            return None

    @staticmethod
    def validate_file(file_path: str, expected_mime: Optional[str] = None) -> bool:
        """Validate file integrity and optionally check MIME type.

        Args:
            file_path: Path to file
            expected_mime: Expected MIME type (optional)

        Returns:
            True if valid, False otherwise
        """
        try:
            path = Path(file_path)

            # Check file exists and is readable
            if not path.exists():
                logger.error(f"File not found: {file_path}")
                return False

            if not path.is_file():
                logger.error(f"Not a file: {file_path}")
                return False

            if path.stat().st_size == 0:
                logger.warning(f"File is empty: {file_path}")
                return False

            # Check MIME type if specified
            if expected_mime:
                detected = DocumentHandler.detect_file_type(file_path)
                if detected != expected_mime:
                    logger.warning(f"MIME type mismatch for {file_path}: "
                                 f"expected {expected_mime}, got {detected}")
                    return False

            return True

        except Exception as e:
            logger.error(f"Failed to validate file {file_path}: {e}")
            return False

    @staticmethod
    def is_text_file(file_path: str) -> bool:
        """Check if file is a text file.

        Args:
            file_path: Path to file

        Returns:
            True if text file, False otherwise
        """
        try:
            # Try to read as text
            with open(file_path, 'r', encoding='utf-8') as f:
                f.read(1024)  # Read first 1KB
            return True
        except (UnicodeDecodeError, Exception):
            return False

    @staticmethod
    def get_file_extension(mime_type: str) -> str:
        """Get appropriate file extension for MIME type.

        Args:
            mime_type: MIME type string

        Returns:
            File extension (without dot)

        Example:
            >>> ext = DocumentHandler.get_file_extension('application/pdf')
            >>> print(ext)  # 'pdf'
        """
        # Common MIME type to extension mappings
        mime_to_ext = {
            'application/pdf': 'pdf',
            'application/zip': 'zip',
            'application/msword': 'doc',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
            'application/vnd.ms-excel': 'xls',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
            'application/vnd.ms-powerpoint': 'ppt',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'pptx',
            'text/plain': 'txt',
            'text/html': 'html',
            'text/csv': 'csv',
            'application/json': 'json',
            'application/xml': 'xml',
            'audio/mpeg': 'mp3',
            'audio/wav': 'wav',
            'video/mp4': 'mp4',
            'video/quicktime': 'mov',
        }

        ext = mime_to_ext.get(mime_type)
        if ext:
            return ext

        # Try mimetypes module
        ext = mimetypes.guess_extension(mime_type)
        if ext:
            return ext.lstrip('.')

        # Default to binary
        return 'bin'

    @staticmethod
    def sanitize_filename(filename: str, max_length: int = 255) -> str:
        """Sanitize filename for filesystem compatibility.

        Args:
            filename: Original filename
            max_length: Maximum filename length

        Returns:
            Sanitized filename
        """
        import re

        # Remove or replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', filename)

        # Remove leading/trailing whitespace and dots
        filename = filename.strip('. ')

        # Truncate to max length
        if len(filename) > max_length:
            path = Path(filename)
            stem = path.stem[:max_length - len(path.suffix) - 1]
            filename = f"{stem}{path.suffix}"

        # Ensure filename is not empty
        if not filename:
            filename = 'untitled'

        return filename
