from services.fetching.orchestrator import OrchestratorFetcherService
from services.corpus.paper_corpus_service import PaperCorpusService

class DiscoveryService:
    def discover(
        self,
        query: str,
        limit: int = 20,
    ):
        corpus = PaperCorpusService()

        corpus_results = corpus.search(query, limit=limit)

        if len(corpus_results) >= limit:
            return corpus_results

        fetched_results = OrchestratorFetcherService.fetch(
            query,
            limit_per_provider=limit,
        )

        new_papers = corpus.save(fetched_results)

        return corpus_results + new_papers