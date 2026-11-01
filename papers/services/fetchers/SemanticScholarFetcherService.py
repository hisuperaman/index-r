from enums.Paper import PaperSource
from papers.services.fetchers.BaseFetcherService import BaseFetcherService
from papers.services.fetchers.definitions import FetchedAuthor, FetchedPaper


class SemanticScholarFetcherService(BaseFetcherService):
	"""Searches the Semantic Scholar Graph API."""

	source = PaperSource.SEMANTIC_SCHOLAR
	BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
	MAX_LIMIT = 100
	FIELDS = "title,abstract,url,venue,year,publicationDate,citationCount,externalIds,openAccessPdf,authors"

	@classmethod
	def search(cls, query: str, limit: int) -> list[FetchedPaper]:
		response = cls.get({"query": query, "limit": cls.clamp_limit(limit), "fields": cls.FIELDS})
		papers = [cls.parse_paper(paper) for paper in response.json().get("data") or []]
		return [paper for paper in papers if paper]

	@classmethod
	def parse_paper(cls, paper: dict) -> FetchedPaper | None:
		"""Maps one Semantic Scholar paper to a FetchedPaper, or None if it has no id or title."""
		title = cls.clean(paper.get("title"))
		if not paper.get("paperId") or not title:
			return None
		publication_date, precision = cls.parse_date(paper.get("publicationDate") or paper.get("year") and str(paper["year"]))

		return FetchedPaper(
			source=cls.source,
			external_id=paper["paperId"],
			title=title,
			url=paper.get("url") or f"https://www.semanticscholar.org/paper/{paper['paperId']}",
			doi=(paper.get("externalIds") or {}).get("DOI"),
			abstract=cls.clean(paper.get("abstract")),
			venue=cls.clean(paper.get("venue")),
			citation_count=paper.get("citationCount"),
			publication_date=publication_date,
			publication_date_precision=precision,
			pdf_url=(paper.get("openAccessPdf") or {}).get("url") or None,
			authors=[FetchedAuthor(name=author["name"]) for author in paper.get("authors") or [] if author.get("name")],
		)
