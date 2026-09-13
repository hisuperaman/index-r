from django.db.models import Q

from papers.models import Paper
from services.fetching.base import PaperResult

class PaperCorpusService:
    def search(self, query: str, limit: int = 20) -> list[Paper]:
        return list(
            Paper.objects.filter(
                Q(title__icontains=query)
                | Q(abstract__icontains=query)
            )[:limit]
        )

    def save(self, papers: list[PaperResult]) -> list[Paper]:
        saved_papers = []

        for paper in papers:
            obj, _ = Paper.objects.update_or_create(
                source=paper.source,
                external_id=paper.external_id,
                defaults={
                    "title": paper.title,
                    "abstract": paper.abstract,
                    "authors": paper.authors,
                    "url": paper.url,
                    "published_date": (
                        paper.published_date[:10]
                        if paper.published_date
                        else None
                    ),
                },
            )
            saved_papers.append(obj)

        return saved_papers