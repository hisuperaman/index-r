from services.corpus.service import PaperCorpusService
from services.fetching.orchestrator import OrchestratorFetcherService


class DiscoveryService:
    def __init__(
        self,
        corpus: PaperCorpusService | None = None,
        fetcher: OrchestratorFetcherService | None = None,
    ):
        self.corpus = corpus or PaperCorpusService()
        self.fetcher = fetcher or OrchestratorFetcherService()

    def discover(
        self,
        query: str,
        limit: int = 20,
    ):
        corpus_results = self.corpus.search(query, limit=limit)

        if len(corpus_results) >= limit:
            return corpus_results

        fetched_results = self.fetcher.fetch(
            query,
            limit_per_provider=limit,
        )

        new_papers = self.corpus.save(fetched_results)

        return corpus_results + new_papers