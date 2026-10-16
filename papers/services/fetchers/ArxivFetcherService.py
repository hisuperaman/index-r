from xml.etree import ElementTree

from enums.Paper import PaperSource
from papers.services.fetchers.BaseFetcherService import BaseFetcherService
from papers.services.fetchers.definitions import FetchedAuthor, FetchedPaper


class ArxivFetcherService(BaseFetcherService):
	"""Searches the arXiv API."""

	source = PaperSource.ARXIV
	BASE_URL = "https://export.arxiv.org/api/query"
	MAX_LIMIT = 2000
	NAMESPACES = {
		"atom": "http://www.w3.org/2005/Atom",
		"arxiv": "http://arxiv.org/schemas/atom",
	}
	ABS_PREFIX = "http://arxiv.org/abs/"

	@classmethod
	def search(cls, query: str, limit: int) -> list[FetchedPaper]:
		response = cls.get({
			"search_query": " AND ".join(f"all:{term}" for term in query.split()),
			"start": 0,
			"max_results": cls.clamp_limit(limit),
		})
		root = ElementTree.fromstring(response.content)
		papers = [cls.parse_entry(entry) for entry in root.findall("atom:entry", cls.NAMESPACES)]
		return [paper for paper in papers if paper]

	@classmethod
	def parse_entry(cls, entry: ElementTree.Element) -> FetchedPaper | None:
		"""Maps one Atom <entry> to a FetchedPaper, or None if it has no arXiv id."""
		entry_id = entry.findtext("atom:id", "", cls.NAMESPACES).strip()
		if not entry_id.startswith(cls.ABS_PREFIX):
			return None
		external_id = cls.strip_version(entry_id[len(cls.ABS_PREFIX):])
		publication_date, precision = cls.parse_date(entry.findtext("atom:published", None, cls.NAMESPACES))
		pdf_link = entry.find("atom:link[@title='pdf']", cls.NAMESPACES)

		return FetchedPaper(
			source=cls.source,
			external_id=external_id,
			title=cls.clean(entry.findtext("atom:title", "", cls.NAMESPACES)) or "",
			url=f"https://arxiv.org/abs/{external_id}",
			doi=cls.clean(entry.findtext("arxiv:doi", None, cls.NAMESPACES)),
			abstract=cls.clean(entry.findtext("atom:summary", None, cls.NAMESPACES)),
			venue=cls.clean(entry.findtext("arxiv:journal_ref", None, cls.NAMESPACES)),
			publication_date=publication_date,
			publication_date_precision=precision,
			pdf_url=pdf_link.get("href") if pdf_link is not None else None,
			authors=[
				FetchedAuthor(name=cls.clean(author.findtext("atom:name", "", cls.NAMESPACES)))
				for author in entry.findall("atom:author", cls.NAMESPACES)
				if cls.clean(author.findtext("atom:name", "", cls.NAMESPACES))
			],
		)

	@staticmethod
	def strip_version(arxiv_id: str) -> str:
		"""Turns '2101.00001v2' into '2101.00001' so every version maps to one paper."""
		head, _, version = arxiv_id.rpartition("v")
		return head if head and version.isdigit() else arxiv_id
