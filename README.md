# PDF Layout Mapper

A Python tool for extracting text regions from PDF files, visualizing them as bounding boxes, and exporting structured data in JSON format.

## Features

- **Text Extraction**: Extract word-level text with bounding box coordinates from PDF files
- **Visualization**: Draw bounding box rectangles directly on PDF pages using PyMuPDF annotations
- **Overlap Filtering**: Optional filtering of overlapping bounding boxes using Shapely
- **JSON Export**: Export extracted text data with metadata to JSON format
- **Encrypted PDF Support**: Handle password-protected PDFs
- **Selective Page Processing**: Process specific pages or page ranges

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

Required packages:
- `PyMuPDF>=1.23.0` (imported as `pymupdf`)
- `shapely>=2.0.0`

## Usage

### Basic Usage

```bash
python main.py <pdf_path>
```

This will:
- Extract text blocks from all pages
- Draw bounding boxes on the PDF
- Save the annotated PDF as `<pdfname>_annotated.pdf` in the same directory

### Command-Line Arguments

- `pdf_path` (required): Path to the input PDF file

- `--save-json [FILENAME]`: Save extracted text data to JSON file
  - If flag is provided without filename: uses default name `{pdfname}_textmap.json`
  - If filename is provided: uses that name
  - Example: `--save-json` or `--save-json custom_name.json`

- `--filter-overlapping`: Enable overlap filtering for bounding boxes

- `--overlap-strategy {keep_largest,keep_first}`: Strategy for filtering overlapping boxes (default: `keep_largest`)
  - `keep_largest`: Keep the box with larger area, remove smaller
  - `keep_first`: Keep first occurrence, remove subsequent overlaps

- `--encryption-password PASSWORD`: Password for encrypted PDF files
  - If provided, PDF will be decrypted using this password

- `--pages RANGE`: Page range to process (1-indexed)
  - Examples:
    - `--pages "1,3,5"` - Process pages 1, 3, and 5
    - `--pages "1-5"` - Process pages 1 through 5
    - `--pages "1,3-5,10"` - Process pages 1, 3-5, and 10

- `--log-level {DEBUG,INFO,WARNING,ERROR}`: Set logging level (default: `INFO`)

### Examples

```bash
# Basic usage - annotate all pages
python main.py document.pdf

# Process specific pages and save JSON
python main.py document.pdf --pages "1-5" --save-json

# Filter overlapping boxes and use custom JSON filename
python main.py document.pdf --filter-overlapping --overlap-strategy keep_first --save-json output.json

# Handle encrypted PDF
python main.py encrypted.pdf --encryption-password mypassword

# Full example with all options
python main.py document.pdf \
    --pages "1,3,5-10" \
    --filter-overlapping \
    --overlap-strategy keep_largest \
    --save-json results.json \
    --log-level DEBUG
```

## Output

### Annotated PDF

The tool creates a new PDF file with `_annotated` suffix (e.g., `document_annotated.pdf`) in the same directory as the input PDF. The original PDF is never modified.

### JSON Output

If `--save-json` is used, a JSON file is created with the following structure:

```json
{
  "pdf_name": "document.pdf",
  "total_pages": 10,
  "pages_processed": [1, 2, 3],
  "text_blocks": [
    {
      "text": "Sample text",
      "bbox": [100.5, 200.3, 250.7, 220.1],
      "page_number": 1,
      "word_count": 2,
      "pdf_width": 612.0,
      "pdf_height": 792.0
    }
  ]
}
```

## Project Structure

```
pdf-layout-mapper/
├── main.py                 # Main entry point
├── pdf_reader.py           # PDFReader class
├── pdf_annotator.py        # PDFBBoxAnnotator class
├── overlap_filter.py       # OverlapFilter class
├── json_exporter.py        # JSONExporter class
├── cli_handler.py          # CLIHandler class
├── exceptions.py           # Custom exception classes
├── models.py              # Data models (TextBlock dataclass)
├── requirements.txt       # Dependencies
├── plan.md                # Detailed architecture plan
└── README.md              # This file
```

## Architecture

The tool follows a modular architecture with clear separation of concerns:

- **CLI Layer**: Argument parsing and validation
- **PDF Processing Layer**: Reading, extraction, and annotation
- **Data Processing Layer**: Overlap filtering and JSON export
- **Exception Handling**: Custom exception hierarchy for error handling

## Error Handling

The tool uses a custom exception hierarchy:
- `PDFMapperException`: Base exception
- `PDFValidationError`: Path validation failures
- `PDFReadError`: PDF opening failures
- `PDFDecryptionError`: Decryption failures
- `PDFAnnotationError`: Annotation operation failures
- `JSONExportError`: JSON export failures

