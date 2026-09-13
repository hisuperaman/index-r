from .base import BaseFetcherService, PaperResult


class OpenAlexFetcherService(BaseFetcherService):
    source = "openalex"

    BASE_URL = "https://api.openalex.org/works"

    def fetch(
        self,
        query: str,
        limit: int = 10,
    ) -> list[PaperResult]:
        response = self.get(
            self.BASE_URL,
            params={
                "search": query,
                "per-page": limit,
            },
        )

        data = response.json()

        return [
            self._parse_work(work)
            for work in data.get("results", [])
        ]

    def _parse_work(self, work: dict) -> PaperResult:
        authors = [
            author.get("author", {}).get("display_name", "")
            for author in work.get("authorships", [])
            if author.get("author")
        ]

        return PaperResult(
            title=work.get("title", ""),
            abstract=self._extract_abstract(work),
            authors=authors,
            url=work.get("doi") or work.get("id"),
            published_date=work.get("publication_date"),
            source=self.source,
            external_id=work.get("id", ""),
        )

    @staticmethod
    def _extract_abstract(work: dict) -> str | None:
        inverted_index = work.get("abstract_inverted_index")

        if not inverted_index:
            return None

        words = []

        for word, positions in inverted_index.items():
            for position in positions:
                words.append((position, word))

        words.sort()

        return " ".join(word for _, word in words)