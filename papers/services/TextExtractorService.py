import re
from dataclasses import dataclass, field
from pathlib import Path

import pymupdf4llm

from papers.definitions import ExtractedAuthor, ExtractedChunk, ExtractedPaper


@dataclass
class Block:
	"""A paragraph or heading line of the Markdown, with the page it is on."""
	text: str
	page: int


@dataclass
class Section:
	"""The blocks between one heading and the next."""
	heading: str | None
	level: int
	blocks: list[Block] = field(default_factory=list)


class TextExtractorService:
	"""Extracts a paper's metadata and section chunks from a PDF."""

	MAX_CHUNK_CHARS = 1000
	MAX_HEADING_CHARS = 500

	_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
	_EMPHASIS_RE = re.compile(r"[*_`]+")
	_TAG_RE = re.compile(r"<(\w+)[^>]*>.*?</\1>|<[^>]+>", re.DOTALL)
	_ABSTRACT_RE = re.compile(r"^[\s*_>#-]*abstract\b[\s*_.:—–-]*(?P<body>\S.*)$", re.IGNORECASE | re.DOTALL)
	_DOI_RE = re.compile(r"\b10\.\d{4,9}/[^\s\"<>]+")
	_AUTHOR_SEPARATOR_RE = re.compile(r",|;|&|\band\b")
	_NAME_RE = re.compile(r"^[^\W\d_][\w.'\-]*(?:\s+[^\W\d_][\w.'\-]*){1,4}$")
	_SPLITTERS = (
		(re.compile(r"\n+"), "\n"),
		(re.compile(r"(?<=[.!?])\s+"), " "),
		(re.compile(r"\s+"), " "),
	)
	_SKIP_HEADINGS = {"references", "bibliography", "acknowledgments", "acknowledgements"}

	@classmethod
	def extract(cls, pdf_path: str | Path, max_chunk_chars: int = MAX_CHUNK_CHARS) -> ExtractedPaper:
		"""Reads the PDF at `pdf_path` into an ExtractedPaper."""
		path = cls.validate_path(pdf_path)
		pages = cls.to_markdown_pages(path)
		metadata = cls.read_metadata(pages)
		sections = cls.group_into_sections(cls.split_into_blocks(pages))

		return ExtractedPaper(
			title=cls.find_title(sections, metadata),
			abstract=cls.find_abstract(sections),
			doi=cls.find_doi(pages),
			authors=cls.find_authors(sections, metadata),
			chunks=cls.chunk_sections(sections, max_chunk_chars),
		)

	@staticmethod
	def validate_path(pdf_path: str | Path) -> Path:
		"""Returns the resolved path if it is an existing .pdf file."""
		path = Path(pdf_path).expanduser().resolve()
		if not path.exists():
			raise FileNotFoundError(f"PDF not found: {path}")
		if not path.is_file():
			raise ValueError(f"Not a file: {path}")
		if path.suffix.lower() != ".pdf":
			raise ValueError(f"Not a PDF: {path}")
		return path

	@staticmethod
	def to_markdown_pages(path: Path) -> list[dict]:
		"""Converts the PDF to one Markdown page dict per page."""
		return pymupdf4llm.to_markdown(str(path), page_chunks=True)

	@staticmethod
	def read_metadata(pages: list[dict]) -> dict:
		"""Returns the document metadata pymupdf4llm attaches to each page."""
		return (pages[0].get("metadata") or {}) if pages else {}

	@classmethod
	def split_into_blocks(cls, pages: list[dict]) -> list[Block]:
		"""Splits every page into paragraphs, keeping each heading line as its own block."""
		blocks = []
		for page in pages:
			page_number = page["metadata"]["page_number"]
			paragraph = []
			for line in page.get("text", "").splitlines():
				if cls._HEADING_RE.match(line.strip()) or not line.strip():
					if paragraph:
						blocks.append(Block("\n".join(paragraph), page_number))
						paragraph = []
					if line.strip():
						blocks.append(Block(line.strip(), page_number))
				else:
					paragraph.append(line.rstrip())
			if paragraph:
				blocks.append(Block("\n".join(paragraph), page_number))
		return blocks

	@classmethod
	def group_into_sections(cls, blocks: list[Block]) -> list[Section]:
		"""Groups blocks into sections that start at each heading; text before the first heading has none."""
		sections = [Section(heading=None, level=0)]
		for block in blocks:
			match = cls._HEADING_RE.match(block.text)
			if match:
				sections.append(Section(heading=cls.clean_heading(match.group(2)), level=len(match.group(1))))
			else:
				sections[-1].blocks.append(block)
		return [section for section in sections if section.heading or section.blocks]

	@classmethod
	def clean_heading(cls, heading: str) -> str:
		"""Strips Markdown emphasis and extra whitespace from a heading."""
		return " ".join(cls._EMPHASIS_RE.sub("", heading).split())[:cls.MAX_HEADING_CHARS]

	@classmethod
	def is_skipped(cls, heading: str | None) -> bool:
		"""Whether a section is back matter that is not worth searching."""
		if not heading:
			return False
		words = re.sub(r"^[\d.\s]+", "", heading).strip().lower()
		return words in cls._SKIP_HEADINGS

	@classmethod
	def chunk_sections(cls, sections: list[Section], max_chars: int) -> list[ExtractedChunk]:
		"""Turns each section into one or more chunks of at most `max_chars` characters."""
		chunks = []
		for section in sections:
			if cls.is_skipped(section.heading):
				continue
			for text, start_page, end_page in cls.split_section(section.blocks, max_chars):
				chunks.append(ExtractedChunk(
					heading=section.heading,
					text=text,
					start_page=start_page,
					end_page=end_page,
					chunk_index=len(chunks),
				))
		return chunks

	@classmethod
	def split_section(cls, blocks: list[Block], max_chars: int) -> list[tuple[str, int, int]]:
		"""Packs a section's paragraphs into (text, start_page, end_page) pieces of at most `max_chars`."""
		pieces = [
			(piece, block.page)
			for block in blocks
			for piece in cls.split_text(block.text.strip(), max_chars)
			if piece.strip()
		]
		return cls.pack(pieces, "\n\n", max_chars)

	@classmethod
	def split_text(cls, text: str, max_chars: int) -> list[str]:
		"""Splits text longer than `max_chars` at lines, then sentences, then words, then anywhere."""
		if len(text) <= max_chars:
			return [text]
		for pattern, joiner in cls._SPLITTERS:
			parts = [part for part in pattern.split(text) if part.strip()]
			if len(parts) > 1:
				pieces = [(piece, 0) for part in parts for piece in cls.split_text(part, max_chars)]
				return [piece for piece, _, _ in cls.pack(pieces, joiner, max_chars)]
		return [text[i:i + max_chars] for i in range(0, len(text), max_chars)]

	@staticmethod
	def pack(pieces: list[tuple[str, int]], joiner: str, max_chars: int) -> list[tuple[str, int, int]]:
		"""Greedily joins consecutive (text, page) pieces while the result fits in `max_chars`."""
		packed = []
		buffer, pages = [], []
		for text, page in pieces:
			if buffer and len(joiner.join(buffer + [text])) > max_chars:
				packed.append((joiner.join(buffer), min(pages), max(pages)))
				buffer, pages = [], []
			buffer.append(text)
			pages.append(page)
		if buffer:
			packed.append((joiner.join(buffer), min(pages), max(pages)))
		return packed

	@classmethod
	def find_title(cls, sections: list[Section], metadata: dict) -> str:
		"""Returns the first top-level heading, else the PDF's title metadata."""
		for section in sections:
			if section.level == 1:
				return section.heading
		return (metadata.get("title") or "").strip()

	@classmethod
	def find_abstract(cls, sections: list[Section]) -> str | None:
		"""Returns the body of an 'Abstract' section, or of a paragraph that starts with 'Abstract'."""
		for section in sections:
			if section.heading and section.heading.strip(" .:").lower() == "abstract":
				return "\n\n".join(block.text for block in section.blocks) or None
			for block in section.blocks:
				match = cls._ABSTRACT_RE.match(block.text)
				if match:
					return match.group("body").strip()
		return None

	@classmethod
	def find_doi(cls, pages: list[dict]) -> str | None:
		"""Returns the first DOI on the first page."""
		if not pages:
			return None
		match = cls._DOI_RE.search(pages[0].get("text", ""))
		return match.group(0).rstrip(".,;)]") if match else None

	@classmethod
	def find_authors(cls, sections: list[Section], metadata: dict) -> list[ExtractedAuthor]:
		"""Reads the byline under the title, else the PDF's author metadata."""
		title_section = next((section for section in sections if section.level == 1), None)
		if title_section and title_section.blocks:
			names = cls.parse_names(cls._TAG_RE.sub("", title_section.blocks[0].text))
			if names:
				return [ExtractedAuthor(name=name) for name in names]
		return [ExtractedAuthor(name=name) for name in cls.parse_names(metadata.get("author") or "")]

	@classmethod
	def parse_names(cls, byline: str) -> list[str]:
		"""Splits a byline into names, or returns none if any part does not look like a name."""
		parts = [" ".join(cls._EMPHASIS_RE.sub("", part).split()) for part in cls._AUTHOR_SEPARATOR_RE.split(byline)]
		names = [part for part in parts if part]
		if names and all(cls._NAME_RE.match(name) for name in names):
			return names
		return []
