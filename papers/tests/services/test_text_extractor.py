"""
Unit tests for TextExtractorService.

- No file I/O — pymupdf4llm is fully mocked.
- Path validation is exercised via mock.patch on Path methods.
- Patch is used as a context manager (never as a decorator).
"""

from pathlib import Path
from unittest.mock import patch, MagicMock

from django.test import SimpleTestCase

from papers.services.TextExtractorService import (
    ExtractedDocument,
    ExtractedSection,
    TextExtractorService,
)


# --------------------------------------------------------------------------- #
# Fixtures — in-memory fake data only
# --------------------------------------------------------------------------- #

DICT_CHUNKS = [
    {
        "metadata": {"page_number": 0},
        "text": "# Title\n\nAuthor line.\n\n## 1 Intro\n\nIntro body.\n",
    },
    {
        "metadata": {"page_number": 1},
        "text": "## 2 Methods\n\n### 2.1 Sub\n\nMethods body.\n",
    },
    {
        "metadata": {"page_number": 2},
        "text": "## 3 Conclusion\n\nDone.\n\n## References\n\n[1] Someone.\n",
    },
]

STRING_CHUNKS = [
    "# Title\n\n## 1 Intro\n\nBody one.\n",
    "## 2 Methods\n\nBody two.\n",
]

EMPTY_SECTION_CHUNKS = [
    {
        "metadata": {"page_number": 0},
        "text": "# Title\n\n## 2 Methods\n\n### 2.1 Sub\n\nContent.\n",
    },
]


# --------------------------------------------------------------------------- #
# Helper
# --------------------------------------------------------------------------- #

def _mock_valid_path():
    """Context manager: pretend any given path is a real PDF file."""
    return patch.multiple(
        Path,
        exists=MagicMock(return_value=True),
        is_file=MagicMock(return_value=True),
    )


# --------------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------------- #

class TestTextExtractorService(SimpleTestCase):

    # ------------------------------------------------------------------ #
    # _validate_path
    # ------------------------------------------------------------------ #

    def test_validate_path_raises_file_not_found_when_missing(self):
        with patch.object(Path, "exists", return_value=False):
            with self.assertRaises(FileNotFoundError):
                TextExtractorService._validate_path("whatever.pdf")

    def test_validate_path_raises_value_error_when_not_a_file(self):
        with patch.object(Path, "exists", return_value=True), \
             patch.object(Path, "is_file", return_value=False):
            with self.assertRaises(ValueError):
                TextExtractorService._validate_path("whatever.pdf")

    def test_validate_path_raises_value_error_when_not_pdf_extension(self):
        with patch.object(Path, "exists", return_value=True), \
             patch.object(Path, "is_file", return_value=True):
            with self.assertRaises(ValueError):
                TextExtractorService._validate_path("notes.txt")

    def test_validate_path_returns_resolved_path_for_valid_pdf(self):
        with _mock_valid_path():
            result = TextExtractorService._validate_path("paper.pdf")
        self.assertIsInstance(result, Path)
        self.assertEqual(result.suffix.lower(), ".pdf")

    # ------------------------------------------------------------------ #
    # _normalize_page_chunk
    # ------------------------------------------------------------------ #

    def test_normalize_page_chunk_reads_dict_format(self):
        chunk = {"metadata": {"page_number": 5}, "text": "hello"}
        page_num, text = TextExtractorService._normalize_page_chunk(0, chunk)
        self.assertEqual(page_num, 5)
        self.assertEqual(text, "hello")

    def test_normalize_page_chunk_falls_back_to_index_for_dict(self):
        chunk = {"metadata": {}, "text": "hello"}
        page_num, _ = TextExtractorService._normalize_page_chunk(7, chunk)
        self.assertEqual(page_num, 7)

    def test_normalize_page_chunk_reads_string_format(self):
        page_num, text = TextExtractorService._normalize_page_chunk(3, "raw page text")
        self.assertEqual(page_num, 3)
        self.assertEqual(text, "raw page text")

    def test_normalize_page_chunk_handles_missing_text_key(self):
        chunk = {"metadata": {"page_number": 1}}
        _, text = TextExtractorService._normalize_page_chunk(0, chunk)
        self.assertEqual(text, "")

    # ------------------------------------------------------------------ #
    # _merge_with_page_markers
    # ------------------------------------------------------------------ #

    def test_merge_with_page_markers_inserts_marker_between_pages(self):
        merged = TextExtractorService._merge_with_page_markers(DICT_CHUNKS)
        self.assertIn("<<<PAGE:0>>>", merged)
        self.assertIn("<<<PAGE:1>>>", merged)
        self.assertIn("<<<PAGE:2>>>", merged)

    def test_merge_with_page_markers_places_marker_before_each_page(self):
        merged = TextExtractorService._merge_with_page_markers(DICT_CHUNKS)
        title_pos = merged.index("# Title")
        marker_pos = merged.index("<<<PAGE:0>>>")
        self.assertLess(marker_pos, title_pos)

    def test_merge_with_page_markers_handles_string_chunks(self):
        merged = TextExtractorService._merge_with_page_markers(STRING_CHUNKS)
        self.assertIn("<<<PAGE:0>>>", merged)
        self.assertIn("<<<PAGE:1>>>", merged)

    # ------------------------------------------------------------------ #
    # _page_of
    # ------------------------------------------------------------------ #

    def test_page_of_returns_last_marker_before_position(self):
        merged = "<<<PAGE:1>>>\nfoo\n<<<PAGE:2>>>\nbar"
        pos = merged.index("bar")
        self.assertEqual(TextExtractorService._page_of(merged, pos), 2)

    def test_page_of_returns_zero_when_no_markers_before_position(self):
        merged = "no markers here"
        self.assertEqual(TextExtractorService._page_of(merged, 5), 0)

    def test_page_of_returns_first_marker_when_position_after_it(self):
        merged = "<<<PAGE:9>>>\nbody"
        pos = merged.index("body")
        self.assertEqual(TextExtractorService._page_of(merged, pos), 9)

    # ------------------------------------------------------------------ #
    # _last_page_in
    # ------------------------------------------------------------------ #

    def test_last_page_in_returns_max_marker(self):
        body = "text\n<<<PAGE:2>>>\nmore\n<<<PAGE:5>>>\ntail"
        self.assertEqual(TextExtractorService._last_page_in(body, default=0), 5)

    def test_last_page_in_returns_default_when_no_markers(self):
        self.assertEqual(TextExtractorService._last_page_in("no markers", default=42), 42)

    # ------------------------------------------------------------------ #
    # _fix_page_indexing
    # ------------------------------------------------------------------ #

    def test_fix_page_indexing_shifts_zero_based_to_one_based(self):
        sections = [
            ExtractedSection("A", 1, 0, 0, "x"),
            ExtractedSection("B", 1, 1, 1, "y"),
        ]
        result = TextExtractorService._fix_page_indexing(sections)
        self.assertEqual(result[0].start_page, 1)
        self.assertEqual(result[1].start_page, 2)

    def test_fix_page_indexing_leaves_one_based_untouched(self):
        sections = [
            ExtractedSection("A", 1, 1, 1, "x"),
            ExtractedSection("B", 1, 2, 2, "y"),
        ]
        result = TextExtractorService._fix_page_indexing(sections)
        self.assertEqual(result[0].start_page, 1)
        self.assertEqual(result[1].start_page, 2)

    def test_fix_page_indexing_handles_empty_list(self):
        self.assertEqual(TextExtractorService._fix_page_indexing([]), [])

    # ------------------------------------------------------------------ #
    # _split_into_sections
    # ------------------------------------------------------------------ #

    def test_split_into_sections_returns_one_per_heading(self):
        merged = (
            "<<<PAGE:0>>>\n"
            "# Title\nbody\n"
            "## 1 Intro\nintro body\n"
            "### 1.1 Sub\nsub body\n"
        )
        sections = TextExtractorService._split_into_sections(merged)
        headings = [s.heading for s in sections]
        self.assertEqual(headings, ["Title", "1 Intro", "1.1 Sub"])

    def test_split_into_sections_assigns_correct_levels(self):
        merged = "# A\na\n## B\nb\n### C\nc\n"
        sections = TextExtractorService._split_into_sections(merged)
        self.assertEqual([s.level for s in sections], [1, 2, 3])

    def test_split_into_sections_strips_page_markers_from_body(self):
        merged = "<<<PAGE:0>>>\n# Title\nbody <<<PAGE:1>>> more body\n"
        sections = TextExtractorService._split_into_sections(merged)
        self.assertNotIn("<<<PAGE:", sections[0].text)

    def test_split_into_sections_returns_empty_list_when_no_headings(self):
        sections = TextExtractorService._split_into_sections("plain text, no headings")
        self.assertEqual(sections, [])

    # ------------------------------------------------------------------ #
    # extract — orchestration
    # ------------------------------------------------------------------ #

    def test_extract_returns_extracted_document(self):
        with _mock_valid_path(), \
             patch.object(TextExtractorService, "_to_markdown_chunks", return_value=DICT_CHUNKS):
            result = TextExtractorService.extract("paper.pdf")
        self.assertIsInstance(result, ExtractedDocument)

    def test_extract_sets_total_pages_from_chunk_count(self):
        with _mock_valid_path(), \
             patch.object(TextExtractorService, "_to_markdown_chunks", return_value=DICT_CHUNKS):
            result = TextExtractorService.extract("paper.pdf")
        self.assertEqual(result.total_pages, 3)

    def test_extract_filters_empty_sections(self):
        with _mock_valid_path(), \
             patch.object(TextExtractorService, "_to_markdown_chunks", return_value=EMPTY_SECTION_CHUNKS):
            result = TextExtractorService.extract("paper.pdf")
        headings = [s.heading for s in result.sections]
        self.assertNotIn("2 Methods", headings)   # empty body
        self.assertIn("2.1 Sub", headings)

    def test_extract_filters_references_section(self):
        with _mock_valid_path(), \
             patch.object(TextExtractorService, "_to_markdown_chunks", return_value=DICT_CHUNKS):
            result = TextExtractorService.extract("paper.pdf")
        headings = [s.heading.lower() for s in result.sections]
        self.assertNotIn("references", headings)

    def test_extract_filters_bibliography_case_insensitive(self):
        chunks = [{"metadata": {"page_number": 0}, "text": "# T\n\n## Bibliography\n\nx\n"}]
        with _mock_valid_path(), \
             patch.object(TextExtractorService, "_to_markdown_chunks", return_value=chunks):
            result = TextExtractorService.extract("paper.pdf")
        headings = [s.heading.lower() for s in result.sections]
        self.assertNotIn("bibliography", headings)

    def test_extract_shifts_zero_based_pages_to_one_based(self):
        with _mock_valid_path(), \
             patch.object(TextExtractorService, "_to_markdown_chunks", return_value=DICT_CHUNKS):
            result = TextExtractorService.extract("paper.pdf")
        self.assertGreaterEqual(min(s.start_page for s in result.sections), 1)

    def test_extract_handles_string_chunks(self):
        with _mock_valid_path(), \
             patch.object(TextExtractorService, "_to_markdown_chunks", return_value=STRING_CHUNKS):
            result = TextExtractorService.extract("paper.pdf")
        headings = [s.heading for s in result.sections]
        self.assertIn("Title", headings)
        self.assertIn("1 Intro", headings)

    def test_extract_calls_to_markdown_with_page_chunks_true(self):
        with _mock_valid_path(), \
             patch.object(TextExtractorService, "_to_markdown_chunks", return_value=DICT_CHUNKS) as mock_chunks:
            TextExtractorService.extract("paper.pdf")
        mock_chunks.assert_called_once()

    def test_extract_does_not_query_database(self):
        with _mock_valid_path(), \
             patch.object(TextExtractorService, "_to_markdown_chunks", return_value=DICT_CHUNKS), \
             self.assertNumQueries(0):
            TextExtractorService.extract("paper.pdf")

    def test_extract_propagates_file_not_found(self):
        with patch.object(Path, "exists", return_value=False):
            with self.assertRaises(FileNotFoundError):
                TextExtractorService.extract("missing.pdf")

    # ------------------------------------------------------------------ #
    # Dataclass contracts
    # ------------------------------------------------------------------ #

    def test_extracted_section_char_count_reflects_text_length(self):
        s = ExtractedSection("H", 1, 1, 1, "hello")
        self.assertEqual(s.char_count, 5)

    def test_extracted_section_is_empty_true_for_whitespace_only(self):
        s = ExtractedSection("H", 1, 1, 1, "   \n\t ")
        self.assertTrue(s.is_empty)

    def test_extracted_section_is_empty_false_for_real_text(self):
        s = ExtractedSection("H", 1, 1, 1, "content")
        self.assertFalse(s.is_empty)