"""Export extracted text data to JSON format."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from exceptions import JSONExportError
from models import TextBlock

logger = logging.getLogger(__name__)


class JSONExporter:
    """Export extracted text data to JSON format."""

    def __init__(self, pdf_path: Path):
        """
        Initialize JSONExporter.

        Args:
            pdf_path: Path to the PDF file
        """
        self.pdf_path = Path(pdf_path)
        self.pdf_name = self.pdf_path.name

    def _get_output_path(self, filename: Optional[str] = None) -> Path:
        """
        Get output path for JSON file.

        Args:
            filename: Optional custom filename. If None, uses default naming.

        Returns:
            Path to output JSON file
        """
        if filename is None:
            # Default: {pdfname}_textmap.json
            pdf_stem = self.pdf_path.stem
            filename = f"{pdf_stem}_textmap.json"

        # Ensure .json extension
        if not filename.endswith('.json'):
            filename = f"{filename}.json"

        # Output in PDF's parent directory
        output_path = self.pdf_path.parent / filename
        return output_path

    def _format_data(
        self,
        text_blocks: List[TextBlock],
        total_pages: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Format text blocks data structure for JSON export.

        Args:
            text_blocks: List of TextBlock objects
            total_pages: Optional total page count. If None, estimates from processed pages.

        Returns:
            Dictionary formatted for JSON export
        """
        # Get unique page numbers (convert from 0-indexed to 1-indexed for JSON)
        pages_processed = sorted(set(block.page_number + 1 for block in text_blocks))

        # Get total pages - use provided value or estimate from processed pages
        if total_pages is None:
            total_pages = max(pages_processed) if pages_processed else 0

        # Format text blocks
        blocks_data = []
        for block in text_blocks:
            block_dict = {
                "text": block.text,
                "bbox": list(block.bbox),  # Convert tuple to list for JSON
                "page_number": block.page_number + 1,  # Convert to 1-indexed
                "word_count": block.word_count,
                "pdf_width": block.pdf_width,
                "pdf_height": block.pdf_height
            }
            blocks_data.append(block_dict)

        data = {
            "pdf_name": self.pdf_name,
            "total_pages": total_pages,
            "pages_processed": pages_processed,
            "text_blocks": blocks_data
        }

        return data

    def export(
        self,
        text_blocks: List[TextBlock],
        output_filename: Optional[str] = None,
        total_pages: Optional[int] = None
    ) -> Path:
        """
        Export text blocks to JSON file.

        Args:
            text_blocks: List of TextBlock objects
            output_filename: Optional custom output filename
            total_pages: Optional total page count from PDF

        Returns:
            Path to the exported JSON file

        Raises:
            JSONExportError: If export fails
        """
        try:
            output_path = self._get_output_path(output_filename)
            data = self._format_data(text_blocks, total_pages=total_pages)

            # Write JSON file with pretty formatting
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"JSON exported successfully: {output_path}")
            return output_path

        except Exception as e:
            error_msg = f"Failed to export JSON: {str(e)}"
            logger.error(error_msg)
            raise JSONExportError(error_msg) from e

