from enums.Paper import PaperSource
from papers.services.fetchers.BaseFetcherService import BaseFetcherService
from papers.services.fetchers.definitions import FetchedAuthor, FetchedPaper


class OpenAlexFetcherService(BaseFetcherService):
	"""Searches the OpenAlex works API."""

	source = PaperSource.OPENALEX
	BASE_URL = "https://api.openalex.org/works"
	MAX_LIMIT = 200

	@classmethod
	def search(cls, query: str, limit: int) -> list[FetchedPaper]:
		response = cls.get({"search": query, "per-page": cls.clamp_limit(limit)})
		papers = [cls.parse_work(work) for work in response.json().get("results", [])]
		return [paper for paper in papers if paper]

	@classmethod
	def parse_work(cls, work: dict) -> FetchedPaper | None:
		"""Maps one OpenAlex work to a FetchedPaper, or None if it has no id or title."""
		external_id = cls.strip_prefix(work.get("id"), "https://openalex.org/")
		title = cls.clean(work.get("title") or work.get("display_name"))
		if not external_id or not title:
			return None
		primary_location = work.get("primary_location") or {}
		best_location = work.get("best_oa_location") or {}
		publication_date, precision = cls.parse_date(work.get("publication_date") or work.get("publication_year") and str(work["publication_year"]))

		return FetchedPaper(
			source=cls.source,
			external_id=external_id,
			title=title,
			url=primary_location.get("landing_page_url") or work.get("doi") or work["id"],
			doi=cls.strip_prefix(work.get("doi"), "https://doi.org/"),
			abstract=cls.rebuild_abstract(work.get("abstract_inverted_index")),
			venue=cls.clean((primary_location.get("source") or {}).get("display_name")),
			citation_count=work.get("cited_by_count"),
			publication_date=publication_date,
			publication_date_precision=precision,
			pdf_url=best_location.get("pdf_url") or primary_location.get("pdf_url"),
			authors=[
				FetchedAuthor(
					name=authorship["author"]["display_name"],
					orcid=cls.strip_prefix(authorship["author"].get("orcid"), "https://orcid.org/"),
				)
				for authorship in work.get("authorships", [])
				if (authorship.get("author") or {}).get("display_name")
			],
		)

	@staticmethod
	def rebuild_abstract(inverted_index: dict[str, list[int]] | None) -> str | None:
		"""Rebuilds the abstract text from OpenAlex's word → positions index."""
		if not inverted_index:
			return None
		positioned = sorted((position, word) for word, positions in inverted_index.items() for position in positions)
		return " ".join(word for _, word in positioned)
