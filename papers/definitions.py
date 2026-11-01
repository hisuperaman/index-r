from dataclasses import dataclass, field


@dataclass
class ExtractedAuthor:
	"""An author read from a PDF, shaped like the Author model."""
	name: str
	orcid: str | None = None


@dataclass
class ExtractedChunk:
	"""A piece of one section of a PDF, shaped like the Chunk model."""
	heading: str | None
	text: str
	start_page: int
	end_page: int
	chunk_index: int


@dataclass
class ExtractedPaper:
	"""Everything read from a PDF, shaped like the Paper model; authors are in byline order."""
	title: str
	abstract: str | None = None
	doi: str | None = None
	authors: list[ExtractedAuthor] = field(default_factory=list)
	chunks: list[ExtractedChunk] = field(default_factory=list)
