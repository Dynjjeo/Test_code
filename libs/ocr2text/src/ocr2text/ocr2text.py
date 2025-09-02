from __future__ import annotations

import json
import hashlib
from typing import TYPE_CHECKING
from pathlib import Path
from operator import attrgetter

import pytesseract
from PIL import Image, ImageDraw

from ocr2text.utils import process_tesseract_results
from ocr2text.entities import (
    Line,
    Page,
    Word,
    Document,
    WordData,
    TesseractResults,
)


if TYPE_CHECKING:
    from ocr2text.entities import BoundingBox


class OCRProcessor:
    """Extract and process text from images using Tesseract OCR engine.

    This class handles text extraction from images along with positional
    information (bounding boxes) and builds structured document representations.
    """

    def extract_text_and_coordinates(self, file_path: str) -> Document:
        """Extract text and coordinates from an image file."""
        image = Image.open(file_path).convert("L")  # Convert to grayscale

        results = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

        tesseract_results = TesseractResults(
            level=results["level"],
            text=results["text"],
            left=results["left"],
            top=results["top"],
            width=results["width"],
            height=results["height"],
        )

        output_process = process_tesseract_results(tesseract_results)

        file_hash = hashlib.sha256(Path(file_path).read_bytes()).hexdigest()

        return self._build_document(
            file_path, file_hash, output_process.bounding_boxes, output_process.texts
        )

    def _build_document(
        self,
        file_path: str,
        file_hash: str,
        bounding_boxes: list[BoundingBox],
        text_elements: list[str],
        page_count: int = 1,
    ) -> Document:
        """Create a Document object from extracted text and bounding boxes."""
        # Create words with their bounding boxes
        words_data = [
            WordData(
                x1=bbox.left_top.x,
                y1=bbox.left_top.y,
                x2=bbox.right_bottom.x,
                y2=bbox.right_bottom.y,
                text=text,
            )
            for bbox, text in zip(bounding_boxes, text_elements, strict=False)
        ]

        # Sort words by y-coordinate for line grouping
        words_data.sort(key=attrgetter("y1"))

        # Build pages
        pages = [
            self._build_page(self.generate_id(f"page_{file_path}_{page_idx}"), words_data)
            for page_idx in range(page_count)
        ]

        return Document(
            id=self.generate_id(file_path),
            pdf_path=file_path,
            file_hash=file_hash,
            pages=pages,
        )

    def _build_page(self, page_id: str, words_data: list[WordData]) -> Page:
        """Build a Page object. Groups words into lines based on vertical."""
        # Maximum vertical distance for words to be in the same line
        line_alignment_threshold = 30

        if not words_data:
            return Page(id=page_id, lines=[], line_count=0)

        lines = []
        line_id = 0
        current_line_words: list[Word] = []

        # Group words into lines based on y-coordinate proximity
        current_y = words_data[0].y1
        for word_data in words_data:
            word = self._build_word(page_id, word_data)
            if (
                not current_line_words
                or abs(word_data.y1 - current_y) < line_alignment_threshold
            ):
                current_line_words.append(word)
            else:
                current_line_words.sort(key=lambda word: word.bbox[0])
                lines.append(self._build_line(page_id, line_id, current_line_words))
                line_id += 1
                current_line_words = [word]
                current_y = word_data.y1

        # Add the last line if there are remaining words
        if current_line_words:
            current_line_words.sort(key=lambda word: word.bbox[0])
            lines.append(self._build_line(page_id, line_id, current_line_words))

        return Page(id=page_id, lines=lines, line_count=len(lines))

    def _build_line(self, page_id: str, line_id: int, words: list[Word]) -> Line:
        """Build a Line object. Combines words into a line."""
        text = " ".join(word.text for word in words)
        bbox = [
            min(word.bbox[0] for word in words),  # Left
            min(word.bbox[1] for word in words),  # Top
            max(word.bbox[2] for word in words),  # Right
            max(word.bbox[3] for word in words),  # Bottom
        ]

        line_id_str = self.generate_id(f"{page_id}_line_{line_id}")
        return Line(id=line_id_str, text=text, bbox=bbox, words=words)

    def _build_word(self, page_id: str, word_data: WordData) -> Word:
        """Build a Word object from word data."""
        # Generate a unique ID for the word
        word_id = self.generate_id(
            f"{page_id}_{word_data.x1}_{word_data.y1}_{word_data.text}"
        )

        return Word(
            id=word_id,
            text=word_data.text,
            bbox=[word_data.x1, word_data.y1, word_data.x2, word_data.y2],
        )

    @staticmethod
    def generate_id(input_str: str) -> str:
        """Generate a unique ID using SHA-256 hash."""
        return hashlib.sha256(input_str.encode()).hexdigest()

    @staticmethod
    def save_to_json(document: Document, output_folder: str) -> Path:
        """Save the document structure to a JSON file."""
        # Extract file extension and create output filename
        file_name = Path(document.pdf_path).name
        file_stem = Path(file_name).stem
        output_path = Path(output_folder) / f"{file_stem}.json"

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write JSON data
        with output_path.open("w", encoding="utf-8") as json_file:
            json.dump(document.model_dump(), json_file, ensure_ascii=False, indent=4)

        return output_path

    @staticmethod
    def draw_bounding_boxes(document: Document, output_folder: str) -> Path:
        """Draw bounding boxes around the text in the image."""
        # Open the original image
        image = Image.open(document.pdf_path).convert("RGB")
        draw = ImageDraw.Draw(image)

        # Collect all bounding boxes from the document structure
        bounding_boxes = [
            word.bbox
            for page in document.pages
            for line in page.lines
            for word in line.words
        ]

        # Draw boxes on the image
        for bbox in bounding_boxes:
            draw.rectangle(
                [int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])],
                outline="green",
                width=1,
            )

        # Save the annotated image
        output_path = Path(output_folder) / Path(document.pdf_path).name
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path)

        return output_path

    @staticmethod
    def parse_json_file_to_document(file_path: str) -> Document:
        """Parse a previously saved JSON file back to a Document object."""
        path = Path(file_path)
        with path.open(encoding="utf-8") as json_file:
            data = json.load(json_file)

        return Document.model_validate(data)
