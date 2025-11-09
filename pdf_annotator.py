"""PDF bounding box annotation using PyMuPDF."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional

import fitz  # PyMuPDF

from exceptions import PDFAnnotationError, PDFReadError
from models import TextBlock

logger = logging.getLogger(__name__)


class PDFBBoxAnnotator:
    """Draw bounding box rectangles on PDF pages using PyMuPDF annotations."""

    def __init__(self, pdf_document: fitz.Document, pdf_path: Path):
        """
        Initialize PDFBBoxAnnotator.

        Args:
            pdf_document: PyMuPDF Document object
            pdf_path: Path to the original PDF file
        """
        if pdf_document is None:
            raise PDFReadError("PDF document cannot be None")

        self.pdf_document = pdf_document
        self.pdf_path = Path(pdf_path)
        self.output_path: Optional[Path] = None

    def annotate_page(self, page_num: int, text_blocks: List[TextBlock]) -> None:
        """
        Annotate a single page with bounding boxes.

        Args:
            page_num: Page number (0-indexed)
            text_blocks: List of TextBlock objects for this page

        Raises:
            PDFAnnotationError: If annotation fails
        """
        if page_num < 0 or page_num >= len(self.pdf_document):
            raise ValueError(f"Invalid page number: {page_num}")

        try:
            page = self.pdf_document[page_num]
            page_blocks = [block for block in text_blocks if block.page_number == page_num]

            for block in page_blocks:
                x0, y0, x1, y1 = block.bbox
                rect = fitz.Rect(x0, y0, x1, y1)

                # Add rectangle annotation
                annot = page.add_rect_annot(rect)
                # Set annotation properties (black border, transparent fill)
                annot.set_border(width=1.0)
                annot.set_colors(stroke=(0, 0, 0))  # Black border
                annot.update()

            logger.debug(f"Annotated page {page_num} with {len(page_blocks)} bounding boxes")

        except Exception as e:
            error_msg = f"Failed to annotate page {page_num}: {str(e)}"
            logger.error(error_msg)
            raise PDFAnnotationError(error_msg) from e

    def draw_rectangles(self, text_blocks: List[TextBlock]) -> None:
        """
        Draw rectangles on all pages based on text blocks.

        Args:
            text_blocks: List of TextBlock objects

        Raises:
            PDFAnnotationError: If drawing fails
        """
        if not text_blocks:
            logger.warning("No text blocks to annotate")
            return

        # Group text blocks by page
        pages_dict = {}
        for block in text_blocks:
            page_num = block.page_number
            if page_num not in pages_dict:
                pages_dict[page_num] = []
            pages_dict[page_num].append(block)

        # Annotate each page
        for page_num in sorted(pages_dict.keys()):
            try:
                self.annotate_page(page_num, text_blocks)
            except Exception as e:
                if isinstance(e, PDFAnnotationError):
                    raise
                error_msg = f"Failed to draw rectangles on page {page_num}: {str(e)}"
                logger.error(error_msg)
                raise PDFAnnotationError(error_msg) from e

        logger.info(f"Drew rectangles on {len(pages_dict)} page(s)")

    def save_pdf(self, output_path: Optional[Path] = None) -> None:
        """
        Save the modified PDF.

        Args:
            output_path: Optional output path. If None, creates a new file with
                        "_annotated" suffix in the same directory.

        Raises:
            PDFAnnotationError: If save fails
        """
        try:
            if output_path is None:
                # Create new file with _annotated suffix
                pdf_stem = self.pdf_path.stem
                pdf_suffix = self.pdf_path.suffix
                output_path = self.pdf_path.parent / f"{pdf_stem}_annotated{pdf_suffix}"

            self.pdf_document.save(output_path)
            self.output_path = output_path
            logger.info(f"PDF saved successfully: {output_path}")

        except Exception as e:
            error_msg = f"Failed to save PDF: {str(e)}"
            logger.error(error_msg)
            raise PDFAnnotationError(error_msg) from e

    def close(self) -> None:
        """Close the PDF document (no-op, document is managed externally)."""
        # Document is managed by PDFReader, so we don't close it here
        pass

