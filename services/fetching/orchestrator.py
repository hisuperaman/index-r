from services.fetching.arxiv import ArxivFetcherService
from services.fetching.base import BaseFetcherService, PaperResult
from services.fetching.openalex import OpenAlexFetcherService
from services.fetching.semantic_scholar import SemanticScholarFetcherService


class OrchestratorFetcherService:
    fetchers: list[BaseFetcherService] = [
        ArxivFetcherService(),
        OpenAlexFetcherService(),
        SemanticScholarFetcherService(),
    ]

    @classmethod
    def fetch(
        cls,
        query: str,
        limit_per_provider: int = 10,
    ) -> list[PaperResult]:
        results: list[PaperResult] = []

        for fetcher in cls.fetchers:
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

        return cls._deduplicate(results)

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