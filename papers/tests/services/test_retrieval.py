from unittest.mock import patch

from django.test import TestCase

from enums.Paper import PaperSource
from iam.models import User
from papers.models import Chunk, Paper
from papers.services import RerankService, Retrieval, RetrievalService

QUESTION = "How does multi-head attention work?"


class RetrievalServiceTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		paper = Paper.objects.create(
			source=PaperSource.ARXIV, external_id="1706.03762", title="Attention Is All You Need",
			url="https://arxiv.org/abs/1706.03762",
		)
		cls.attention = Chunk.objects.create(
			paper=paper, heading="Multi-Head Attention", text="Heads attend jointly.", start_page=4, end_page=4,
			chunk_index=0,
		)
		cls.dropout = Chunk.objects.create(
			paper=paper, heading="Regularization", text="Residual dropout.", start_page=7, end_page=7, chunk_index=1,
		)
		Chunk.objects.create(paper=paper, heading="Results", text="BLEU on WMT.", start_page=8, end_page=8, chunk_index=2)

	def retrieve(self, queries: list[str], rerank: list | None = None) -> tuple[Retrieval, object]:
		with patch.object(RerankService, "rerank", return_value=rerank or []) as mock:
			return RetrievalService.retrieve(QUESTION, queries), mock

	def test_reranks_the_chunks_any_query_matches(self):
		retrieval, rerank = self.retrieve(["attention", "dropout"], rerank=[(self.attention, 0.9)])

		self.assertEqual(retrieval.passages, [(self.attention, 0.9)])
		self.assertEqual(retrieval.candidate_count, 2)
		question, candidates, top_k = rerank.call_args.args
		self.assertEqual((question, set(candidates), top_k), (QUESTION, {self.attention, self.dropout}, RerankService.TOP_K))

	def test_reranks_at_most_the_rerank_candidates(self):
		with patch.object(RetrievalService, "RERANK_CANDIDATES", 1):
			_, rerank = self.retrieve(["attention", "dropout"])

		self.assertEqual(len(rerank.call_args.args[1]), 1)

	def test_searches_only_the_shared_corpus_by_default(self):
		user = User.objects.create_user(email="ada@example.com", password="password")
		private = Paper.objects.create(source=PaperSource.UPLOAD, external_id="u1", title="Private", owner=user)
		Chunk.objects.create(paper=private, heading="Attention", text="Private attention.", start_page=1, end_page=1, chunk_index=0)

		retrieval, _ = self.retrieve(["attention"])

		self.assertEqual(retrieval.candidate_count, 1)

	def test_no_queries_finds_no_candidates(self):
		retrieval, _ = self.retrieve([])

		self.assertEqual(retrieval.candidate_count, 0)

	def test_loads_the_papers_with_the_candidates(self):
		with patch.object(RerankService, "rerank", return_value=[]) as rerank:
			RetrievalService.retrieve(QUESTION, ["attention", "dropout"])

		with self.assertNumQueries(0):
			[chunk.paper.title for chunk in rerank.call_args.args[1]]


class RetrievalNeedsDiscoveryTests(TestCase):

	def needs_discovery(self, candidate_count: int, scores: list[float]) -> bool:
		passages = [(Chunk(), score) for score in scores]
		with self.settings(DISCOVERY_MIN_CANDIDATES=5, DISCOVERY_MIN_SCORE=0.6):
			return Retrieval(passages=passages, candidate_count=candidate_count).needs_discovery

	def test_not_needed_with_enough_candidates_and_a_confident_best_passage(self):
		self.assertFalse(self.needs_discovery(5, [0.6, 0.2]))

	def test_needed_with_too_few_candidates(self):
		self.assertTrue(self.needs_discovery(4, [0.95]))

	def test_needed_when_the_best_passage_scores_too_low(self):
		self.assertTrue(self.needs_discovery(50, [0.59]))

	def test_needed_without_passages(self):
		self.assertTrue(self.needs_discovery(50, []))
