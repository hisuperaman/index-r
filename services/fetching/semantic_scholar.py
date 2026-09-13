from .base import BaseFetcherService, PaperResult


class SemanticScholarFetcherService(BaseFetcherService):
    source = "semantic_scholar"

    BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/search"

    def fetch(
        self,
        query: str,
        limit: int = 10,
    ) -> list[PaperResult]:
        response = self.get(
            self.BASE_URL,
            params={
                "query": query,
                "limit": limit,
                "fields": (
                    "paperId,title,abstract,authors,"
                    "url,publicationDate"
                ),
            },
        )

        data = response.json()

        return [
            self._parse_paper(paper)
            for paper in data.get("data", [])
        ]

    def _parse_paper(self, paper: dict) -> PaperResult:
        authors = [
            author.get("name", "")
            for author in paper.get("authors", [])
        ]

        return PaperResult(
            title=paper.get("title", ""),
            abstract=paper.get("abstract"),
            authors=authors,
            url=paper.get("url"),
            published_date=paper.get("publicationDate"),
            source=self.source,
            external_id=paper.get("paperId", ""),
        )