"""Overlap detection and filtering for bounding boxes using Shapely."""

from __future__ import annotations

import logging
from typing import List, Tuple

from shapely.geometry import Polygon

from models import TextBlock

logger = logging.getLogger(__name__)


class OverlapFilter:
    """Detect and filter overlapping bounding boxes using Shapely."""

    def __init__(self, overlap_threshold: float = 0.5):
        """
        Initialize OverlapFilter.

        Args:
            overlap_threshold: Minimum coverage ratio to consider boxes as overlapping (0.0-1.0)
        """
        if not 0.0 <= overlap_threshold <= 1.0:
            raise ValueError("overlap_threshold must be between 0.0 and 1.0")

        self.overlap_threshold = overlap_threshold

    def _bbox_to_polygon(self, bbox: Tuple[float, float, float, float]) -> Polygon:
        """
        Convert bounding box to Shapely Polygon.

        Args:
            bbox: Tuple of (x0, y0, x1, y1)

        Returns:
            Shapely Polygon object
        """
        x0, y0, x1, y1 = bbox
        return Polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])

    def calculate_coverage_ratio(self, box1: TextBlock, box2: TextBlock) -> float:
        """
        Calculate coverage ratio between two bounding boxes.

        Coverage ratio = intersection_area / min(area1, area2)

        Args:
            box1: First TextBlock
            box2: Second TextBlock

        Returns:
            Coverage ratio (0.0-1.0)
        """
        poly1 = self._bbox_to_polygon(box1.bbox)
        poly2 = self._bbox_to_polygon(box2.bbox)

        if not poly1.intersects(poly2):
            return 0.0

        intersection = poly1.intersection(poly2)
        intersection_area = intersection.area

        area1 = poly1.area
        area2 = poly2.area

        if area1 == 0 or area2 == 0:
            return 0.0

        coverage_ratio = intersection_area / min(area1, area2)
        return coverage_ratio

    def detect_overlaps(self, text_blocks: List[TextBlock]) -> List[Tuple[int, int, float]]:
        """
        Detect overlapping bounding boxes.

        Args:
            text_blocks: List of TextBlock objects

        Returns:
            List of tuples (index1, index2, coverage_ratio) for overlapping pairs
        """
        overlaps = []
        n = len(text_blocks)

        for i in range(n):
            for j in range(i + 1, n):
                # Only check overlaps on the same page
                if text_blocks[i].page_number != text_blocks[j].page_number:
                    continue

                coverage_ratio = self.calculate_coverage_ratio(text_blocks[i], text_blocks[j])

                if coverage_ratio >= self.overlap_threshold:
                    overlaps.append((i, j, coverage_ratio))
                    logger.debug(
                        f"Overlap detected: blocks {i} and {j} "
                        f"(coverage: {coverage_ratio:.2f})"
                    )

        logger.info(f"Detected {len(overlaps)} overlapping pairs")
        return overlaps

    def filter_overlapping(
        self,
        text_blocks: List[TextBlock],
        strategy: str = "keep_largest"
    ) -> List[TextBlock]:
        """
        Filter overlapping bounding boxes based on strategy.

        Args:
            text_blocks: List of TextBlock objects
            strategy: Filtering strategy ("keep_largest" or "keep_first")

        Returns:
            Filtered list of TextBlock objects

        Raises:
            ValueError: If strategy is not supported
        """
        if strategy not in ["keep_largest", "keep_first"]:
            raise ValueError(f"Unsupported filtering strategy: {strategy}")

        if not text_blocks:
            return text_blocks

        overlaps = self.detect_overlaps(text_blocks)
        if not overlaps:
            logger.info("No overlaps detected, returning original blocks")
            return text_blocks

        # Create a set of indices to remove
        indices_to_remove = set()

        if strategy == "keep_largest":
            for i, j, coverage_ratio in overlaps:
                # Calculate areas
                poly_i = self._bbox_to_polygon(text_blocks[i].bbox)
                poly_j = self._bbox_to_polygon(text_blocks[j].bbox)

                area_i = poly_i.area
                area_j = poly_j.area

                # Remove the smaller one
                if area_i > area_j:
                    indices_to_remove.add(j)
                elif area_j > area_i:
                    indices_to_remove.add(i)
                else:
                    # If equal area, keep the first one
                    indices_to_remove.add(j)

        elif strategy == "keep_first":
            for i, j, coverage_ratio in overlaps:
                # Always remove the second one (j)
                indices_to_remove.add(j)

        # Create filtered list
        filtered_blocks = [
            block for idx, block in enumerate(text_blocks)
            if idx not in indices_to_remove
        ]

        logger.info(
            f"Filtered {len(indices_to_remove)} overlapping blocks "
            f"(strategy: {strategy}). "
            f"Remaining: {len(filtered_blocks)} blocks"
        )

        return filtered_blocks

