# Visualize Text Regions in a PDF

You’re given a multi-page PDF (e.g., a construction plan or technical spec sheet).
Your task is to extract all text elements along with their bounding boxes, visualize them on the corresponding page as rectangles, and export the structured data in a machine-readable format.

Language: Python
Input: Path to a pdf file
Output: A per image visualization image. Showing text regions drawn as rectangles or bounding boxes.

Steps:
1. Read the PDF file from a file path using PyMuPDF and pathlib.Path library.
Validate if path exists and has pdf file. Log error on the console and exit gracefully if not. 
2. Read the file. Decrypt if it is encrypted. Extract the text  along with their bounding boxes regions and save as a hashmap/list. 
    Also save additional metadata like word count and page number.
3. Use opencv to draw bbx rectangles to each page based on the text and it's region coordinates extracted.
4. Use PyMuPDF to append the image to corresponding pages.
5. Store the extracted data of text elements, bbx and metadata as json in the same parent directory as pdffilenametextmap.json.
6. Take the input as a CLI using argparse. Add flags for --save-json with the file name.

Extensions:
1. Use Shapely to analyse overlapping bounding-boxes, text-coverage ratio and filter the overlapping bounding-boxes.

---

## Detailed Architecture & Design Plan

### Clarifications Summary
- **Output**: Modify PDF directly (not separate image files)
- **Visualization**: Use PyMuPDF annotations directly (no OpenCV)
- **Extraction Granularity**: Word-level text extraction
- **Overlap Filtering**: Optional CLI flag `--filter-overlapping`
- **JSON Output**: Include text, PDF name, PDF dimensions (height/width), page number
- **Visualization**: Rectangles overlayed on text (annotations)
- **Coordinates**: Pixel coordinates in JSON
- **Page Range**: CLI argument `--pages` as list for selective processing
- **Color Coding**: No color coding needed
- **Output Directory**: Use PDF's parent directory (not configurable)

---

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI Layer                             │
│                    (CLIHandler class)                        │
│  - Parse arguments (--save-json, --filter-overlapping,       │
│    --pages, input PDF path)                                  │
│  - Validate arguments                                         │
│  - Orchestrate workflow                                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    PDF Processing Layer                       │
│  ┌──────────────────┐      ┌──────────────────┐             │
│  │ PDFReader        │      │ PDFBBoxAnnotator │             │
│  │ - Validate path  │      │ - Draw rectangles│             │
│  │ - Open PDF       │      │ - Add annotations│             │
│  │ - Handle decrypt│      │ - Save PDF        │             │
│  │ - Extract text   │      │                  │             │
│  │ - Get metadata   │      │                  │             │
│  └──────────────────┘      └──────────────────┘             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data Processing Layer                      │
│  ┌──────────────────┐      ┌──────────────────┐             │
│  │ OverlapFilter    │      │ JSONExporter     │             │
│  │ - Detect overlaps│      │ - Format data    │             │
│  │ - Filter bboxes  │      │ - Write JSON     │             │
│  │ - Use Shapely    │      │ - Handle paths   │             │
│  └──────────────────┘      └──────────────────┘             │
└─────────────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Exception Handling Layer                   │
│              (PDFMapperException classes)                     │
│  - PDFValidationError                                        │
│  - PDFReadError                                              │
│  - PDFDecryptionError                                        │
│  - PDFAnnotationError                                        │
│  - JSONExportError                                           │
└─────────────────────────────────────────────────────────────┘
```

---

### Class Design

#### 1. **PDFReader** Class
**Purpose**: Handle PDF file reading, validation, decryption, and text extraction

**Responsibilities**:
- Validate PDF file path and existence
- Open and decrypt PDF files
- Extract word-level text with bounding boxes
- Extract PDF metadata (dimensions, page count)
- Handle encryption/decryption

**Methods**:
```python
class PDFReader:
    def __init__(self, pdf_path: Path)
    def validate_path(self) -> bool
    def open_pdf(self) -> fitz.Document
    def decrypt_pdf(self, password: str = None) -> bool
    def extract_text_blocks(self, page_range: List[int] = None) -> List[TextBlock]
    def get_pdf_metadata(self) -> Dict[str, Any]
    def get_page_dimensions(self, page_num: int) -> Tuple[float, float]
    def close(self) -> None
```

**Data Structures**:
```python
@dataclass
class TextBlock:
    text: str
    bbox: Tuple[float, float, float, float]  # (x0, y0, x1, y1) in pixels
    page_number: int
    word_count: int
    pdf_name: str
    pdf_width: float
    pdf_height: float
```

---

#### 2. **PDFBBoxAnnotator** Class
**Purpose**: Draw bounding box rectangles on PDF pages using PyMuPDF annotations

**Responsibilities**:
- Convert text blocks to annotations
- Draw rectangles on PDF pages
- Save modified PDF

**Methods**:
```python
class PDFBBoxAnnotator:
    def __init__(self, pdf_document: fitz.Document, pdf_path: Path)
    def annotate_page(self, page_num: int, text_blocks: List[TextBlock]) -> None
    def draw_rectangles(self, text_blocks: List[TextBlock]) -> None
    def save_pdf(self, output_path: Path = None) -> None
    def close(self) -> None
```

**Implementation Details**:
- Use `page.add_rect_annot()` or `page.draw_rect()` for drawing
- Rectangle coordinates: (x0, y0, x1, y1) from TextBlock.bbox
- Use default annotation style (black border, transparent fill)

---

#### 3. **OverlapFilter** Class
**Purpose**: Detect and filter overlapping bounding boxes using Shapely

**Responsibilities**:
- Convert bounding boxes to Shapely polygons
- Detect overlaps using intersection analysis
- Calculate text coverage ratio
- Filter overlapping boxes based on strategy

**Methods**:
```python
class OverlapFilter:
    def __init__(self, overlap_threshold: float = 0.5)
    def detect_overlaps(self, text_blocks: List[TextBlock]) -> List[Tuple[int, int, float]]
    def calculate_coverage_ratio(self, box1: TextBlock, box2: TextBlock) -> float
    def filter_overlapping(self, text_blocks: List[TextBlock], 
                          strategy: str = "keep_largest") -> List[TextBlock]
    def _bbox_to_polygon(self, bbox: Tuple[float, float, float, float]) -> Polygon
```

**Filtering Strategies**:
- `keep_largest`: Keep the box with larger area, remove smaller
- `keep_first`: Keep first occurrence, remove subsequent overlaps
- `merge`: Merge overlapping boxes (future extension)

---

#### 4. **JSONExporter** Class
**Purpose**: Export extracted text data to JSON format

**Responsibilities**:
- Format text blocks data structure
- Write JSON to file in PDF's parent directory
- Handle file I/O errors

**Methods**:
```python
class JSONExporter:
    def __init__(self, pdf_path: Path)
    def export(self, text_blocks: List[TextBlock], 
               output_filename: str = None) -> Path
    def _format_data(self, text_blocks: List[TextBlock]) -> Dict[str, Any]
    def _get_output_path(self, filename: str) -> Path
```

**JSON Schema**:
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

---

#### 5. **CLIHandler** Class
**Purpose**: Handle command-line argument parsing and validation

**Responsibilities**:
- Parse CLI arguments using argparse
- Validate input arguments
- Provide help messages
- Return structured configuration

**Methods**:
```python
class CLIHandler:
    @staticmethod
    def parse_arguments() -> argparse.Namespace
    @staticmethod
    def validate_arguments(args: argparse.Namespace) -> bool
    @staticmethod
    def parse_page_range(page_str: str) -> List[int]
```

**CLI Arguments**:
- `pdf_path` (positional): Path to input PDF file
- `--save-json` (optional): JSON output filename (default: `{pdfname}_textmap.json`)
- `--filter-overlapping` (flag): Enable overlap filtering
- `--pages` (optional): Page range as comma-separated list (e.g., "1,3,5-10")

---

#### 6. **PDFMapperException** Classes
**Purpose**: Custom exception hierarchy for error handling and logging

**Exception Hierarchy**:
```python
class PDFMapperException(Exception):
    """Base exception for PDF mapper errors"""
    pass

class PDFValidationError(PDFMapperException):
    """Raised when PDF path validation fails"""
    pass

class PDFReadError(PDFMapperException):
    """Raised when PDF cannot be opened"""
    pass

class PDFDecryptionError(PDFMapperException):
    """Raised when PDF decryption fails"""
    pass

class PDFAnnotationError(PDFMapperException):
    """Raised when annotation operations fail"""
    pass

class JSONExportError(PDFMapperException):
    """Raised when JSON export fails"""
    pass
```

**Logging Strategy**:
- Use Python `logging` module
- Log errors with appropriate exception types
- Console output for user-facing errors
- Detailed logging for debugging

---

### Module Structure

```
pdf-layout-mapper/
├── pdf_text_mapper.py          # Main entry point
├── pdf_reader.py               # PDFReader class
├── pdf_annotator.py            # PDFBBoxAnnotator class
├── overlap_filter.py           # OverlapFilter class
├── json_exporter.py            # JSONExporter class
├── cli_handler.py              # CLIHandler class
├── exceptions.py               # Custom exception classes
├── models.py                   # Data models (TextBlock dataclass)
├── requirements.txt            # Dependencies
└── plan.md                     # This file
```

---

### Data Flow

```
1. CLIHandler.parse_arguments()
   ↓
2. CLIHandler.validate_arguments()
   ↓
3. PDFReader.__init__(pdf_path)
   ↓
4. PDFReader.validate_path()
   ↓
5. PDFReader.open_pdf()
   ↓
6. PDFReader.decrypt_pdf() [if encrypted]
   ↓
7. PDFReader.extract_text_blocks(page_range)
   ↓
8. OverlapFilter.filter_overlapping() [if --filter-overlapping]
   ↓
9. PDFBBoxAnnotator.draw_rectangles(text_blocks)
   ↓
10. PDFBBoxAnnotator.save_pdf()
   ↓
11. JSONExporter.export(text_blocks) [if --save-json]
```

---

### Implementation Details

#### Text Extraction (Word-Level)
- Use `page.get_text("words")` for word-level extraction
- Returns list of tuples: `(x0, y0, x1, y1, "word", block_no, line_no, word_no)`
- Convert coordinates to pixel space (PyMuPDF uses points, 1 point = 1/72 inch)
- For pixel coordinates, use page's transformation matrix or render at specific DPI

#### Bounding Box Annotation
- Use `page.add_rect_annot(rect)` where `rect = fitz.Rect(x0, y0, x1, y1)`
- Or use `page.draw_rect(rect)` for drawing operations
- Coordinates must match PDF coordinate system (origin at top-left)

#### Overlap Detection Algorithm
1. Convert each bbox to Shapely Polygon
2. For each pair of polygons, calculate intersection area
3. Calculate coverage ratio: `intersection_area / min(area1, area2)`
4. If coverage ratio > threshold, mark as overlapping
5. Apply filtering strategy (keep_largest, keep_first, etc.)




