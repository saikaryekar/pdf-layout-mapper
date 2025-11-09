"""Custom exception classes for PDF mapper errors."""

from __future__ import annotations


class PDFMapperException(Exception):
    """Base exception for PDF mapper errors."""
    pass


class PDFValidationError(PDFMapperException):
    """Raised when PDF path validation fails."""
    pass


class PDFReadError(PDFMapperException):
    """Raised when PDF cannot be opened."""
    pass


class PDFDecryptionError(PDFMapperException):
    """Raised when PDF decryption fails."""
    pass


class PDFAnnotationError(PDFMapperException):
    """Raised when annotation operations fail."""
    pass


class JSONExportError(PDFMapperException):
    """Raised when JSON export fails."""
    pass

