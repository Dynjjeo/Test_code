from __future__ import annotations

from typing import NamedTuple

from pydantic import BaseModel


class Word(BaseModel):
    id: str
    text: str
    bbox: list[float]


class Line(BaseModel):
    id: str
    text: str
    bbox: list[float]
    words: list[Word]


class Page(BaseModel):
    id: str
    lines: list[Line]
    line_count: int


class Document(BaseModel):
    id: str
    pdf_path: str
    file_hash: str | None = None
    pages: list[Page]


class WordData(NamedTuple):
    x1: float
    y1: float
    x2: float
    y2: float
    text: str


class TesseractResults(BaseModel):
    level: list[int]
    text: list[str]
    left: list[float]
    top: list[float]
    width: list[float]
    height: list[float]


class Position(BaseModel):
    x: float
    y: float


class BoundingBox(BaseModel):
    left_top: Position
    right_top: Position
    right_bottom: Position
    left_bottom: Position


class ProcessResults(BaseModel):
    bounding_boxes: list[BoundingBox]
    texts: list[str]
