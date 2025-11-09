"""PDF file reading, validation, decryption, and text extraction."""

from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import fitz  # PyMuPDF

from exceptions import PDFValidationError, PDFReadError, PDFDecryptionError
from models import TextBlock

logger = logging.getLogger(__name__)


class PDFReader:
    """Handle PDF file reading, validation, decryption, and text extraction."""

    def __init__(self, pdf_path: Path):
        """
        Initialize PDFReader with PDF file path.

        Args:
            pdf_path: Path to the PDF file
        """
        self.pdf_path = Path(pdf_path)
        self.pdf_document: Optional[fitz.Document] = None
        self.pdf_name = self.pdf_path.name

    def validate_path(self) -> bool:
        """
        Validate PDF file path and existence.

        Returns:
            True if path is valid

        Raises:
            PDFValidationError: If path is invalid or file doesn't exist
        """
        if not self.pdf_path.exists():
            error_msg = f"PDF file not found: {self.pdf_path}"
            logger.error(error_msg)
            raise PDFValidationError(error_msg)

        if not self.pdf_path.is_file():
            error_msg = f"Path is not a file: {self.pdf_path}"
            logger.error(error_msg)
            raise PDFValidationError(error_msg)

        if self.pdf_path.suffix.lower() != '.pdf':
            error_msg = f"File is not a PDF: {self.pdf_path}"
            logger.error(error_msg)
            raise PDFValidationError(error_msg)

        logger.info(f"PDF path validated: {self.pdf_path}")
        return True

    def open_pdf(self) -> fitz.Document:
        """
        Open PDF file.

        Returns:
            Opened PyMuPDF Document object

        Raises:
            PDFReadError: If PDF cannot be opened
        """
        try:
            self.pdf_document = fitz.open(self.pdf_path)
            logger.info(f"PDF opened successfully: {self.pdf_path}")
            return self.pdf_document
        except Exception as e:
            error_msg = f"Failed to open PDF: {self.pdf_path}. Error: {str(e)}"
            logger.error(error_msg)
            raise PDFReadError(error_msg) from e

    def decrypt_pdf(self, password: str = None) -> bool:
        """
        Decrypt PDF if encrypted.

        Args:
            password: Optional password for encrypted PDF

        Returns:
            True if decryption successful or PDF is not encrypted

        Raises:
            PDFDecryptionError: If decryption fails
        """
        if self.pdf_document is None:
            raise PDFReadError("PDF document not opened. Call open_pdf() first.")

        if not self.pdf_document.needs_pass:
            logger.info("PDF is not encrypted")
            return True

        try:
            if password:
                result = self.pdf_document.authenticate(password)
            else:
                # Try empty password
                result = self.pdf_document.authenticate("")
                if not result:
                    error_msg = "PDF is encrypted and requires a password"
                    logger.error(error_msg)
                    raise PDFDecryptionError(error_msg)
        except Exception as e:
            if isinstance(e, PDFDecryptionError):
                raise
            error_msg = f"Failed to decrypt PDF: {str(e)}"
            logger.error(error_msg)
            raise PDFDecryptionError(error_msg) from e

        if result:
            logger.info("PDF decrypted successfully")
            return True
        else:
            error_msg = "PDF decryption failed: Invalid password"
            logger.error(error_msg)
            raise PDFDecryptionError(error_msg)

    def get_page_dimensions(self, page_num: int) -> Tuple[float, float]:
        """
        Get page dimensions in pixels.

        Args:
            page_num: Page number (0-indexed)

        Returns:
            Tuple of (width, height) in pixels
        """
        if self.pdf_document is None:
            raise PDFReadError("PDF document not opened. Call open_pdf() first.")

        if page_num < 0 or page_num >= len(self.pdf_document):
            raise ValueError(f"Invalid page number: {page_num}")

        page = self.pdf_document[page_num]
        rect = page.rect
        return rect.width, rect.height

    def _validate_bbox(
        self,
        bbox: Tuple[float, float, float, float],
        page_width: float,
        page_height: float
    ) -> bool:
        """
        Validate bounding box coordinates.

        Args:
            bbox: Tuple of (x0, y0, x1, y1)
            page_width: Page width in pixels
            page_height: Page height in pixels

        Returns:
            True if bbox is valid, False otherwise
        """
        x0, y0, x1, y1 = bbox

        # Check for finite values
        if not all(math.isfinite(coord) for coord in bbox):
            logger.warning(f"Bbox contains non-finite values: {bbox}")
            return False

        # Check for valid rectangle (x1 > x0 and y1 > y0)
        if x1 <= x0 or y1 <= y0:
            logger.warning(f"Invalid bbox dimensions: {bbox} (x1 <= x0 or y1 <= y0)")
            return False

        # Warn if bbox extends beyond page bounds (but don't fail)
        if x0 < 0 or y0 < 0 or x1 > page_width or y1 > page_height:
            logger.warning(
                f"Bbox {bbox} extends beyond page bounds "
                f"({page_width}x{page_height})"
            )

        return True

    def extract_text_blocks(self, page_range: Optional[List[int]] = None) -> List[TextBlock]:
        """
        Extract word-level text with bounding boxes.

        Args:
            page_range: Optional list of page numbers to process (0-indexed).
                       If None, processes all pages.

        Returns:
            List of TextBlock objects

        Raises:
            PDFReadError: If PDF is not opened or extraction fails
        """
        if self.pdf_document is None:
            raise PDFReadError("PDF document not opened. Call open_pdf() first.")

        text_blocks = []
        total_pages = len(self.pdf_document)

        # Determine which pages to process
        if page_range is None:
            pages_to_process = list(range(total_pages))
        else:
            # Validate page range
            pages_to_process = []
            for page_num in page_range:
                if page_num < 0 or page_num >= total_pages:
                    logger.warning(f"Page {page_num} is out of range (0-{total_pages-1}), skipping")
                    continue
                pages_to_process.append(page_num)

        logger.info(f"Extracting text from {len(pages_to_process)} page(s)")

        for page_num in pages_to_process:
            try:
                page = self.pdf_document[page_num]
                pdf_width, pdf_height = self.get_page_dimensions(page_num)

                # Extract words using PyMuPDF
                words = page.get_text("words")

                # Group words into text blocks (by block number)
                blocks_dict = {}
                for word_info in words:
                    # Defensive check for unexpected format
                    if len(word_info) < 8:
                        logger.warning(f"Unexpected word format: {word_info}, skipping")
                        continue

                    try:
                        x0, y0, x1, y1, word_text, block_no, line_no, word_no = word_info
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Failed to unpack word info: {word_info}, error: {e}, skipping")
                        continue

                    # Handle None block_no
                    if block_no is None:
                        block_no = -1  # Use sentinel value for ungrouped words

                    if block_no not in blocks_dict:
                        blocks_dict[block_no] = {
                            'words': [],
                            'bbox': [x0, y0, x1, y1]
                        }

                    blocks_dict[block_no]['words'].append(word_text)
                    # Expand bounding box to include this word
                    blocks_dict[block_no]['bbox'][0] = min(blocks_dict[block_no]['bbox'][0], x0)
                    blocks_dict[block_no]['bbox'][1] = min(blocks_dict[block_no]['bbox'][1], y0)
                    blocks_dict[block_no]['bbox'][2] = max(blocks_dict[block_no]['bbox'][2], x1)
                    blocks_dict[block_no]['bbox'][3] = max(blocks_dict[block_no]['bbox'][3], y1)

                # Create TextBlock objects
                for block_no, block_data in blocks_dict.items():
                    # Skip empty blocks
                    if not block_data['words']:
                        logger.debug(f"Skipping empty block {block_no} on page {page_num}")
                        continue

                    text = ' '.join(block_data['words'])
                    bbox = tuple(block_data['bbox'])

                    # Validate bounding box
                    if not self._validate_bbox(bbox, pdf_width, pdf_height):
                        logger.warning(
                            f"Skipping invalid bbox {bbox} for block {block_no} "
                            f"on page {page_num}"
                        )
                        continue

                    word_count = len(block_data['words'])

                    text_block = TextBlock(
                        text=text,
                        bbox=bbox,
                        page_number=page_num,
                        word_count=word_count,
                        pdf_name=self.pdf_name,
                        pdf_width=pdf_width,
                        pdf_height=pdf_height
                    )
                    text_blocks.append(text_block)

                logger.debug(f"Extracted {len(blocks_dict)} text blocks from page {page_num}")

            except Exception as e:
                error_msg = f"Failed to extract text from page {page_num}: {str(e)}"
                logger.error(error_msg)
                raise PDFReadError(error_msg) from e

        logger.info(f"Extracted {len(text_blocks)} total text blocks")
        return text_blocks

    def get_pdf_metadata(self) -> Dict[str, Any]:
        """
        Get PDF metadata.

        Returns:
            Dictionary containing PDF metadata

        Raises:
            PDFReadError: If PDF is not opened
        """
        if self.pdf_document is None:
            raise PDFReadError("PDF document not opened. Call open_pdf() first.")

        metadata = {
            'pdf_name': self.pdf_name,
            'total_pages': len(self.pdf_document),
            'is_encrypted': self.pdf_document.needs_pass,
            'metadata': self.pdf_document.metadata
        }
        return metadata

    def close(self) -> None:
        """Close the PDF document."""
        if self.pdf_document is not None:
            self.pdf_document.close()
            self.pdf_document = None
            logger.info("PDF document closed")

