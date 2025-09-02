from __future__ import annotations

from typing import TYPE_CHECKING

from ocr2text.entities import Position, BoundingBox, ProcessResults


if TYPE_CHECKING:
    from ocr2text.entities import TesseractResults


def process_tesseract_results(
    results: TesseractResults,
) -> ProcessResults:
    """Process Tesseract OCR results to extract bounding boxes and text."""
    all_bbox = []
    all_text = []

    for i in range(len(results.level)):
        text = results.text[i].strip()
        if text:
            # Extract position and dimension information
            x = results.left[i]
            y = results.top[i]
            w = results.width[i]
            h = results.height[i]

            # Create bounding box in format [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            bbox = BoundingBox(
                left_top=Position(x=x, y=y),
                right_top=Position(x=x + w, y=y),
                right_bottom=Position(x=x + w, y=y + h),
                left_bottom=Position(x=x, y=y + h),
            )

            all_bbox.append(bbox)
            all_text.append(text)

    return ProcessResults(bounding_boxes=all_bbox, texts=all_text)
