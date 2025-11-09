"""Data models for PDF text extraction."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass
class TextBlock:
    """Represents a text block with bounding box and metadata."""
    text: str
    bbox: Tuple[float, float, float, float]  # (x0, y0, x1, y1) in pixels
    page_number: int
    word_count: int
    pdf_name: str
    pdf_width: float
    pdf_height: float

