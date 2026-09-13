from .arxiv import ArxivFetcherService
from .base import BaseFetcherService, PaperResult
from .openalex import OpenAlexFetcherService
from .semantic_scholar import SemanticScholarFetcherService


class OrchestratorFetcherService:
    def __init__(
        self,
        fetchers: list[BaseFetcherService] | None = None,
    ):
        self.fetchers = fetchers or [
            ArxivFetcherService(),
            OpenAlexFetcherService(),
            SemanticScholarFetcherService(),
        ]

    def fetch(
        self,
        query: str,
        limit_per_provider: int = 10,
    ) -> list[PaperResult]:
        results: list[PaperResult] = []

        for fetcher in self.fetchers:
            try:
                papers = fetcher.fetch(
                    query,
                    limit=limit_per_provider,
                )
                results.extend(papers)

            except Exception as exc:
                print(
                    f"{fetcher.source} fetch failed: {exc}"
                )

        return self._deduplicate(results)

    @staticmethod
    def _deduplicate(
        papers: list[PaperResult],
    ) -> list[PaperResult]:
        seen: set[tuple[str, str]] = set()
        unique_papers: list[PaperResult] = []

        for paper in papers:
            key = (
                paper.source,
                paper.external_id,
            )

            if key in seen:
                continue

            seen.add(key)
            unique_papers.append(paper)

        return unique_papers