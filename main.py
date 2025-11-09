"""Main entry point for PDF text mapper application."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from cli_handler import CLIHandler
from exceptions import PDFDecryptionError, PDFMapperException
from json_exporter import JSONExporter
from overlap_filter import OverlapFilter
from pdf_annotator import PDFBBoxAnnotator
from pdf_reader import PDFReader

logger = logging.getLogger(__name__)

# Default overlap threshold constant
OVERLAP_THRESHOLD_DEFAULT = 0.5


def main():
    """Main entry point for the PDF text mapper."""
    try:
        # Parse arguments first
        args = CLIHandler.parse_arguments()

        # Configure logging with user's preferred level
        logging.basicConfig(
            level=getattr(logging, args.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Validate arguments
        CLIHandler.validate_arguments(args)

        pdf_path = Path(args.pdf_path)
        logger.info(f"Processing PDF: {pdf_path}")

        # Parse page range if provided
        page_range = None
        if args.pages:
            page_range = CLIHandler.parse_page_range(args.pages)
            logger.info(f"Processing pages: {[p + 1 for p in page_range]} (1-indexed)")

        # Initialize PDFReader
        pdf_reader = PDFReader(pdf_path)
        pdf_reader.validate_path()
        pdf_reader.open_pdf()

        try:
            # Try to decrypt if needed
            try:
                # Use provided password if available
                password = args.encryption_password if args.encryption_password else None
                pdf_reader.decrypt_pdf(password=password)
            except PDFDecryptionError as e:
                logger.error(f"PDF decryption failed: {e}")
                if not args.encryption_password:
                    logger.error("Please provide --encryption-password if PDF is encrypted")
                sys.exit(1)

            # Extract text blocks
            text_blocks = pdf_reader.extract_text_blocks(page_range=page_range)

            # Filter overlapping if requested
            if args.filter_overlapping:
                logger.info(f"Filtering overlapping bounding boxes using strategy: {args.overlap_strategy}")
                overlap_filter = OverlapFilter(overlap_threshold=OVERLAP_THRESHOLD_DEFAULT)
                text_blocks = overlap_filter.filter_overlapping(
                    text_blocks,
                    strategy=args.overlap_strategy
                )
                logger.info(f"After filtering: {len(text_blocks)} text blocks")

            # Annotate PDF with bounding boxes
            pdf_annotator = PDFBBoxAnnotator(pdf_reader.pdf_document, pdf_path)
            pdf_annotator.draw_rectangles(text_blocks)
            pdf_annotator.save_pdf()  # Saves as new file with _annotated suffix

            # Export to JSON if requested
            if args.save_json is not None:
                json_exporter = JSONExporter(pdf_path)
                # If empty string (flag provided without value), use default name
                # Otherwise use provided filename
                output_filename = None if args.save_json == '' else args.save_json
                # Get total pages from PDF metadata
                pdf_metadata = pdf_reader.get_pdf_metadata()
                total_pages = pdf_metadata['total_pages']
                output_path = json_exporter.export(
                    text_blocks,
                    output_filename=output_filename,
                    total_pages=total_pages
                )
                logger.info(f"JSON exported to: {output_path}")

        finally:
            # Ensure PDF is always closed, even if errors occur
            pdf_reader.close()

        logger.info("PDF processing completed successfully")

    except PDFMapperException as e:
        logger.error(f"PDF Mapper Error: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Validation Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

