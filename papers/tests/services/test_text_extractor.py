from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pymupdf
from django.test import SimpleTestCase

from papers.definitions import ExtractedAuthor
from papers.services import TextExtractorService


def page(number, text, **metadata):
	return {"metadata": {"page_number": number, **metadata}, "text": text}


PAPER_PAGES = [
	page(
		1,
		"# **A Study of Things**\n\n"
		"Ada Lovelace<sup>1</sup> , Alan Turing<sup>2</sup> , and Grace Hopper<sup>1</sup>\n\n"
		"Abstract. We study things.\n\n"
		"https://doi.org/10.1234/abc.567.\n\n"
		"## **1 Introduction**\n\n"
		"Intro body.\n\n",
		title="Untitled-5",
		author="0002624",
	),
	page(
		2,
		"Intro continues.\n\n"
		"## 2 Methods\n\n"
		"### 2.1 Sub\n\n"
		"Methods body.\n\n"
		"## 3 References\n\n"
		"[1] Someone. 10.9999/not.this.one\n",
	),
]


class TextExtractorServiceTests(SimpleTestCase):
	def extract(self, pages, max_chunk_chars=TextExtractorService.MAX_CHUNK_CHARS):
		with (
			patch.object(TextExtractorService, "validate_path", return_value=Path("paper.pdf")),
			patch("papers.services.TextExtractorService.pymupdf4llm.to_markdown", return_value=pages),
		):
			return TextExtractorService.extract("paper.pdf", max_chunk_chars=max_chunk_chars)

	def test_missing_file_raises_file_not_found(self):
		with TemporaryDirectory() as directory, self.assertRaises(FileNotFoundError):
			TextExtractorService.extract(Path(directory) / "missing.pdf")

	def test_directory_raises_value_error(self):
		with TemporaryDirectory() as directory, self.assertRaises(ValueError):
			TextExtractorService.extract(directory)

	def test_non_pdf_raises_value_error(self):
		with TemporaryDirectory() as directory, self.assertRaises(ValueError):
			path = Path(directory) / "notes.txt"
			path.write_text("not a pdf")
			TextExtractorService.extract(path)

	def test_reads_title_from_first_top_level_heading(self):
		self.assertEqual(self.extract(PAPER_PAGES).title, "A Study of Things")

	def test_falls_back_to_title_metadata_without_top_level_heading(self):
		paper = self.extract([page(1, "## Intro\n\nBody.\n", title="Metadata Title")])

		self.assertEqual(paper.title, "Metadata Title")

	def test_reads_authors_in_byline_order(self):
		self.assertEqual(self.extract(PAPER_PAGES).authors, [
			ExtractedAuthor(name="Ada Lovelace"),
			ExtractedAuthor(name="Alan Turing"),
			ExtractedAuthor(name="Grace Hopper"),
		])

	def test_falls_back_to_author_metadata_when_byline_is_not_names(self):
		paper = self.extract([page(1, "# Title\n\nUniversity of Somewhere, 12345\n", author="Ada Lovelace; Alan Turing")])

		self.assertEqual([author.name for author in paper.authors], ["Ada Lovelace", "Alan Turing"])

	def test_ignores_author_metadata_that_is_not_names(self):
		paper = self.extract([page(1, "Body.\n", author="0002624")])

		self.assertEqual(paper.authors, [])

	def test_reads_abstract_paragraph(self):
		self.assertEqual(self.extract(PAPER_PAGES).abstract, "We study things.")

	def test_reads_abstract_section(self):
		paper = self.extract([page(1, "## Abstract\n\nWe study things.\n\n## 1 Intro\n\nBody.\n")])

		self.assertEqual(paper.abstract, "We study things.")

	def test_abstract_is_none_when_absent(self):
		self.assertIsNone(self.extract([page(1, "## Intro\n\nBody.\n")]).abstract)

	def test_reads_doi_from_first_page_only(self):
		self.assertEqual(self.extract(PAPER_PAGES).doi, "10.1234/abc.567")

	def test_starts_a_chunk_at_every_heading(self):
		chunks = self.extract(PAPER_PAGES).chunks

		self.assertEqual(
			[(chunk.heading, chunk.text) for chunk in chunks],
			[
				(None, "Ada Lovelace<sup>1</sup> , Alan Turing<sup>2</sup> , and Grace Hopper<sup>1</sup>"
					   "\n\nAbstract. We study things.\n\nhttps://doi.org/10.1234/abc.567."),
				("1 Introduction", "Intro body.\n\nIntro continues."),
				("2.1 Sub", "Methods body."),
			],
		)

	def test_strips_html_tags_from_headings(self):
		pages = [page(1, "# Title\n\n## 2 Results<sup>*</sup>\n\nBody.\n")]

		self.assertEqual([chunk.heading for chunk in self.extract(pages).chunks], ["2 Results"])

	def test_a_byline_heading_is_not_a_section(self):
		pages = [page(1, "# Title\n\n## Ada Lovelace<sup>†</sup> , Alan Turing<sup>†</sup>\n\nIntro body.\n")]

		self.assertEqual([chunk.heading for chunk in self.extract(pages).chunks], [None])

	def test_the_title_is_not_a_section(self):
		pages = [page(1, "# Ragas: Automated Evaluation\n\nBody.\n\n## RAGAS: Automated Evaluation\n\nMore.\n")]

		self.assertEqual([chunk.heading for chunk in self.extract(pages).chunks], [None, None])

	def test_numbers_chunks_in_order(self):
		self.assertEqual([chunk.chunk_index for chunk in self.extract(PAPER_PAGES).chunks], [0, 1, 2])

	def test_chunk_spans_the_pages_its_text_is_on(self):
		introduction = self.extract(PAPER_PAGES).chunks[1]

		self.assertEqual((introduction.start_page, introduction.end_page), (1, 2))

	def test_drops_back_matter_sections(self):
		headings = [chunk.heading for chunk in self.extract(PAPER_PAGES).chunks]

		self.assertNotIn("3 References", headings)

	def test_keeps_text_before_first_heading_without_a_heading(self):
		chunks = self.extract([page(1, "Preamble.\n\n## Intro\n\nBody.\n")]).chunks

		self.assertEqual([(chunk.heading, chunk.text) for chunk in chunks], [(None, "Preamble."), ("Intro", "Body.")])

	def test_splits_a_long_section_at_paragraphs_under_the_same_heading(self):
		paragraphs = ["a" * 40, "b" * 40, "c" * 40]
		chunks = self.extract([page(1, "## Long\n\n" + "\n\n".join(paragraphs) + "\n")], max_chunk_chars=90).chunks

		self.assertEqual([chunk.text for chunk in chunks], ["a" * 40 + "\n\n" + "b" * 40, "c" * 40])
		self.assertEqual({chunk.heading for chunk in chunks}, {"Long"})

	def test_splits_a_long_paragraph_at_sentences(self):
		paragraph = "First sentence here. Second sentence here. Third sentence here."
		chunks = self.extract([page(1, f"## Long\n\n{paragraph}\n")], max_chunk_chars=45).chunks

		self.assertEqual(
			[chunk.text for chunk in chunks],
			["First sentence here. Second sentence here.", "Third sentence here."],
		)

	def test_never_exceeds_the_chunk_limit(self):
		text = "## Long\n\n" + "word " * 500 + "\n\n" + "x" * 2500 + "\n"
		chunks = self.extract([page(1, text)], max_chunk_chars=100).chunks

		self.assertTrue(all(len(chunk.text) <= 100 for chunk in chunks))
		self.assertEqual("".join(chunk.text for chunk in chunks).count("x"), 2500)

	def test_extracts_a_real_pdf(self):
		with TemporaryDirectory() as directory:
			path = Path(directory) / "paper.pdf"
			document = pymupdf.open()
			first = document.new_page()
			first.insert_text((72, 80), "A Study of Things", fontsize=20, fontname="hebo")
			first.insert_text((72, 120), "Ada Lovelace, Alan Turing", fontsize=10)
			first.insert_text((72, 160), "1 Introduction", fontsize=14, fontname="hebo")
			first.insert_text((72, 190), "Intro body.", fontsize=10)
			second = document.new_page()
			second.insert_text((72, 80), "2 Methods", fontsize=14, fontname="hebo")
			second.insert_text((72, 110), "Methods body.", fontsize=10)
			document.save(path)

			paper = TextExtractorService.extract(path)

		self.assertEqual(paper.title, "A Study of Things")
		self.assertEqual([author.name for author in paper.authors], ["Ada Lovelace", "Alan Turing"])
		self.assertEqual(
			[(chunk.heading, chunk.text, chunk.start_page) for chunk in paper.chunks],
			[
				(None, "Ada Lovelace, Alan Turing", 1),
				("1 Introduction", "Intro body.", 1),
				("2 Methods", "Methods body.", 2),
			],
		)
