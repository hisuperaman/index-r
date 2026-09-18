from dataclasses import dataclass
from pathlib import Path

@dataclass
class ExtractedSection:
    """A single section of a paper, ready to be mapped to a Chunk model row."""
    heading: str
    level: int
    start_page: int
    end_page: int
    text: str

    @property
    def char_count(self) -> int:
        return len(self.text)

    @property
    def is_empty(self) -> bool:
        return not self.text.strip()


@dataclass
class ExtractedDocument:
    """The result of extracting a PDF: metadata + all sections."""
    source_path: Path
    total_pages: int
    sections: list[ExtractedSection]