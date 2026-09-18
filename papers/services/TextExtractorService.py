import re
from dataclasses import dataclass
from pathlib import Path
from papers.definitions import ExtractedDocument, ExtractedSection
import pymupdf4llm

class TextExtractorService:
    """Extracts structured sections from a PDF using PyMuPDF4LLM."""

    # Matches "# Heading", "## Heading", "### Heading" (H1–H3)
    _HEADING_RE = re.compile(r"^(#{1,3})\s+(.+?)$", flags=re.MULTILINE)

    # Sentinel used to track page boundaries inside the merged text
    _PAGE_MARKER_TEMPLATE = "\n\n<<<PAGE:{}>>>\n\n"
    _PAGE_MARKER_RE = re.compile(r"<<<PAGE:(\d+)>>>")

    # Sections whose heading matches these are dropped (not useful for search)
    _SKIP_HEADINGS = {"references", "bibliography", "acknowledgments"}

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    @classmethod
    def extract(cls, pdf_path: str | Path) -> ExtractedDocument:
        """
        Main entry point. Extract a PDF into a structured document.

        Args:
            pdf_path: path to the PDF file.

        Returns:
            ExtractedDocument with all non-empty sections.

        Raises:
            FileNotFoundError: if the PDF does not exist.
            ValueError: if the PDF cannot be parsed.
        """
        path = cls._validate_path(pdf_path)
        page_chunks = cls._to_markdown_chunks(path)
        merged = cls._merge_with_page_markers(page_chunks)

        sections = cls._split_into_sections(merged)
        sections = [s for s in sections if not s.is_empty]
        sections = [s for s in sections if s.heading.lower().strip() not in cls._SKIP_HEADINGS]
        sections = cls._fix_page_indexing(sections)

        return ExtractedDocument(
            source_path=path,
            total_pages=len(page_chunks),
            sections=sections,
        )

    # ------------------------------------------------------------------ #
    # Internal steps — each does one thing
    # ------------------------------------------------------------------ #

    @staticmethod
    def _validate_path(pdf_path: str | Path) -> Path:
        """Ensure the path exists and points to a file."""
        path = Path(pdf_path).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {path}")
        if not path.is_file():
            raise ValueError(f"Not a file: {path}")
        if path.suffix.lower() != ".pdf":
            raise ValueError(f"Not a PDF: {path}")
        return path

    @staticmethod
    def _to_markdown_chunks(path: Path) -> list:
        """Extract page-by-page Markdown from the PDF."""
        return pymupdf4llm.to_markdown(str(path), page_chunks=True)

    @classmethod
    def _normalize_page_chunk(cls, index: int, page) -> tuple[int, str]:
        """
        Normalize one page chunk into (page_number, text).

        Handles both formats across pymupdf4llm versions:
          - dict: {"metadata": {"page_number": N}, "text": "..."}
          - str:  "page text"
        """
        if isinstance(page, dict):
            meta = page.get("metadata", {}) or {}
            page_num = meta.get("page_number", meta.get("page", index))
            text = page.get("text", "") or ""
        else:
            page_num = index
            text = str(page)
        return int(page_num), text

    @classmethod
    def _merge_with_page_markers(cls, page_chunks: list) -> str:
        """Concatenate all pages, inserting a page-marker between them."""
        parts = []
        for i, page in enumerate(page_chunks):
            page_num, text = cls._normalize_page_chunk(i, page)
            parts.append(cls._PAGE_MARKER_TEMPLATE.format(page_num))
            parts.append(text)
        return "".join(parts)

    @classmethod
    def _split_into_sections(cls, merged: str) -> list[ExtractedSection]:
        """Split the merged text into sections at every heading boundary."""
        matches = list(cls._HEADING_RE.finditer(merged))
        sections: list[ExtractedSection] = []

        for i, match in enumerate(matches):
            level = len(match.group(1))
            heading = match.group(2).strip()
            body_start = match.end()
            body_end = matches[i + 1].start() if i + 1 < len(matches) else len(merged)
            body_raw = merged[body_start:body_end]

            start_page = cls._page_of(merged, body_start)
            end_page = cls._last_page_in(body_raw, default=start_page)

            text = cls._PAGE_MARKER_RE.sub("", body_raw).strip()

            sections.append(ExtractedSection(
                heading=heading,
                level=level,
                start_page=start_page,
                end_page=end_page,
                text=text,
            ))

        return sections

    @classmethod
    def _page_of(cls, merged: str, position: int) -> int:
        """Return the page number that contains the given character position."""
        markers = cls._PAGE_MARKER_RE.findall(merged[:position])
        return int(markers[-1]) if markers else 0

    @classmethod
    def _last_page_in(cls, body_raw: str, default: int) -> int:
        """Return the last page marker inside a body, or `default` if none."""
        markers = [int(p) for p in cls._PAGE_MARKER_RE.findall(body_raw)]
        return max(markers) if markers else default

    @staticmethod
    def _fix_page_indexing(sections: list[ExtractedSection]) -> list[ExtractedSection]:
        """
        Ensure pages are 1-based.

        pymupdf4llm returns 0-based indices in some versions. If the first
        section starts at page 0, shift every page by +1 so it matches the
        PDF viewer's numbering.
        """
        if not sections:
            return sections

        first_page = min(s.start_page for s in sections)
        if first_page == 0:
            for s in sections:
                s.start_page += 1
                s.end_page += 1
        return sections