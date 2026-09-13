import xml.etree.ElementTree as ET

from .base import BaseFetcherService, PaperResult


class ArxivFetcherService(BaseFetcherService):
    source = "arxiv"

    BASE_URL = "https://export.arxiv.org/api/query"

    def fetch(
        self,
        query: str,
        limit: int = 10,
    ) -> list[PaperResult]:
        response = self.get(
            self.BASE_URL,
            params={
                "search_query": f"all:{query}",
                "start": 0,
                "max_results": limit,
            },
        )

        return self._parse_response(response.text)

    def _parse_response(
        self,
        content: str,
    ) -> list[PaperResult]:
        root = ET.fromstring(content)

        namespace = {
            "atom": "http://www.w3.org/2005/Atom",
        }

        papers = []

        for entry in root.findall("atom:entry", namespace):
            title = entry.findtext(
                "atom:title",
                default="",
                namespaces=namespace,
            ).strip()

            abstract = entry.findtext(
                "atom:summary",
                default="",
                namespaces=namespace,
            ).strip()

            published_date = entry.findtext(
                "atom:published",
                default=None,
                namespaces=namespace,
            )

            external_id = entry.findtext(
                "atom:id",
                default="",
                namespaces=namespace,
            )

            authors = [
                author.findtext(
                    "atom:name",
                    default="",
                    namespaces=namespace,
                )
                for author in entry.findall(
                    "atom:author",
                    namespace,
                )
            ]

            papers.append(
                PaperResult(
                    title=title,
                    abstract=abstract or None,
                    authors=authors,
                    url=external_id,
                    published_date=published_date,
                    source=self.source,
                    external_id=external_id,
                )
            )

        return papers