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

    def __post_init__(self) -> None:
        """Validate TextBlock data after initialization."""
        # Validate bbox has 4 elements
        if len(self.bbox) != 4:
            raise ValueError(f"bbox must have 4 elements, got {len(self.bbox)}")

        # Validate page_number is non-negative
        if self.page_number < 0:
            raise ValueError(
                f"page_number must be non-negative, got {self.page_number}"
            )

        # Validate PDF dimensions are positive
        if self.pdf_width <= 0 or self.pdf_height <= 0:
            raise ValueError(
                f"Invalid PDF dimensions: {self.pdf_width}x{self.pdf_height}"
            )

        # Note: word_count validation against actual text word count
        # is not enforced here as it may be expensive and text may be empty

