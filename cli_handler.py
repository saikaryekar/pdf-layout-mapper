"""Command-line argument parsing and validation."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


class CLIHandler:
    """Handle command-line argument parsing and validation."""

    @staticmethod
    def parse_page_range(page_str: str) -> List[int]:
        """
        Parse page range string into list of page numbers.

        Supports formats:
        - "1,3,5" -> [0, 2, 4] (0-indexed)
        - "1-5" -> [0, 1, 2, 3, 4]
        - "1,3-5,10" -> [0, 2, 3, 4, 9]

        Args:
            page_str: Comma-separated page range string (1-indexed)

        Returns:
            List of page numbers (0-indexed)

        Raises:
            ValueError: If page range format is invalid
        """
        if not page_str:
            return []

        pages = []
        parts = page_str.split(',')

        for part in parts:
            part = part.strip()
            if '-' in part:
                # Range format: "start-end"
                try:
                    start, end = part.split('-', 1)
                    start = int(start.strip())
                    end = int(end.strip())

                    if start < 1 or end < 1:
                        raise ValueError(f"Page numbers must be >= 1: {part}")

                    if start > end:
                        raise ValueError(f"Start page must be <= end page: {part}")

                    # Convert to 0-indexed and add range
                    pages.extend(range(start - 1, end))
                except ValueError as e:
                    if "must be" in str(e):
                        raise
                    raise ValueError(f"Invalid page range format: {part}") from e
            else:
                # Single page number
                try:
                    page_num = int(part)
                    if page_num < 1:
                        raise ValueError(f"Page numbers must be >= 1: {part}")
                    # Convert to 0-indexed
                    pages.append(page_num - 1)
                except ValueError as e:
                    if "must be" in str(e):
                        raise
                    raise ValueError(f"Invalid page number: {part}") from e

        # Remove duplicates and sort
        pages = sorted(set(pages))
        return pages

    @staticmethod
    def parse_arguments() -> argparse.Namespace:
        """
        Parse command-line arguments.

        Returns:
            Parsed arguments namespace
        """
        parser = argparse.ArgumentParser(
            description="Extract text regions from PDF and visualize as bounding boxes",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )

        parser.add_argument(
            'pdf_path',
            type=str,
            help='Path to input PDF file'
        )

        parser.add_argument(
            '--save-json',
            type=str,
            nargs='?',
            const='',
            default=None,
            metavar='FILENAME',
            help='Save extracted text data to JSON file. '
                 'If flag is provided without filename, uses default: {pdfname}_textmap.json. '
                 'If filename is provided, uses that name.'
        )

        parser.add_argument(
            '--filter-overlapping',
            action='store_true',
            help='Filter overlapping bounding boxes using Shapely'
        )

        parser.add_argument(
            '--overlap-strategy',
            type=str,
            default='keep_largest',
            choices=['keep_largest', 'keep_first'],
            help='Strategy for filtering overlapping boxes when --filter-overlapping is used. '
                 'Options: keep_largest (default), keep_first'
        )

        parser.add_argument(
            '--encryption-password',
            type=str,
            default=None,
            metavar='PASSWORD',
            help='Password for encrypted PDF. If provided, PDF will be decrypted using this password.'
        )

        parser.add_argument(
            '--pages',
            type=str,
            default=None,
            metavar='RANGE',
            help='Page range to process (1-indexed). '
                 'Examples: "1,3,5" or "1-5" or "1,3-5,10"'
        )

        parser.add_argument(
            '--log-level',
            type=str,
            default='INFO',
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
            help='Set logging level (default: INFO)'
        )

        return parser.parse_args()

    @staticmethod
    def validate_arguments(args: argparse.Namespace) -> bool:
        """
        Validate parsed arguments.

        Args:
            args: Parsed arguments namespace

        Returns:
            True if arguments are valid

        Raises:
            ValueError: If arguments are invalid
        """
        # Validate PDF path
        pdf_path = Path(args.pdf_path)
        if not pdf_path.exists():
            raise ValueError(f"PDF file not found: {pdf_path}")

        if not pdf_path.is_file():
            raise ValueError(f"Path is not a file: {pdf_path}")

        if pdf_path.suffix.lower() != '.pdf':
            raise ValueError(f"File is not a PDF: {pdf_path}")

        # Validate page range if provided
        if args.pages:
            try:
                CLIHandler.parse_page_range(args.pages)
            except ValueError as e:
                raise ValueError(f"Invalid page range: {e}") from e

        # Validate JSON filename if provided
        if args.save_json is not None and args.save_json.strip() == '':
            raise ValueError("--save-json filename cannot be empty")

        return True

