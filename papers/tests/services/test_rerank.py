from unittest.mock import MagicMock, patch

from cohere import V2RerankResponse
from cohere.v2.types import V2RerankResponseResultsItem
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase

from enums.Paper import PaperSource
from papers.models import Chunk, Paper
from papers.services import RerankService

QUESTION = "How does multi-head attention work?"


class RerankServiceTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		paper = Paper.objects.create(
			source=PaperSource.ARXIV, external_id="1706.03762", title="Attention Is All You Need",
			url="https://arxiv.org/abs/1706.03762",
		)
		cls.chunks = [
			Chunk.objects.create(paper=paper, heading=heading, text=text, start_page=1, end_page=1, chunk_index=index)
			for index, (heading, text) in enumerate([
				("Training", "We used eight GPUs."),
				("Multi-Head Attention", "Heads attend to different subspaces."),
				(None, "Results on WMT 2014."),
			])
		]

	def setUp(self):
		self.enterContext(self.settings(COHERE_API_KEY="test-key"))
		self.client = MagicMock()
		self.get_client = self.enterContext(patch.object(RerankService, "get_client", return_value=self.client))

	def respond(self, *results: tuple[int, float]) -> None:
		self.client.rerank.return_value = V2RerankResponse(results=[
			V2RerankResponseResultsItem(index=index, relevance_score=score) for index, score in results
		])

	def test_returns_the_chunks_cohere_ranked_with_their_scores(self):
		self.respond((1, 0.92), (2, 0.31))

		self.assertEqual(RerankService.rerank(QUESTION, self.chunks, top_k=2), [
			(self.chunks[1], 0.92), (self.chunks[2], 0.31),
		])

	def test_sends_the_question_and_passages_with_title_and_heading(self):
		self.respond()

		RerankService.rerank(QUESTION, self.chunks, top_k=2)

		self.get_client.assert_called_once_with("test-key")
		self.client.rerank.assert_called_once_with(
			model=RerankService.MODEL,
			query=QUESTION,
			documents=[
				"Attention Is All You Need — Training\nWe used eight GPUs.",
				"Attention Is All You Need — Multi-Head Attention\nHeads attend to different subspaces.",
				"Attention Is All You Need\nResults on WMT 2014.",
			],
			top_n=2,
		)

	def test_scores_every_document_by_default(self):
		self.respond((1, 0.8), (0, 0.2))

		self.assertEqual(RerankService.score(QUESTION, ["first", "second"]), [(1, 0.8), (0, 0.2)])
		self.assertEqual(self.client.rerank.call_args.kwargs["top_n"], 2)

	def test_no_chunks_skips_cohere(self):
		self.assertEqual(RerankService.rerank(QUESTION, []), [])

		self.client.rerank.assert_not_called()

	def test_a_missing_api_key_is_a_configuration_error(self):
		with self.settings(COHERE_API_KEY=None), self.assertRaises(ImproperlyConfigured):
			RerankService.rerank(QUESTION, self.chunks)


class RerankClientTests(TestCase):

	def test_reuses_the_client_for_the_same_key(self):
		first = RerankService.get_client("key-a")

		self.assertIs(RerankService.get_client("key-a"), first)
		self.assertIsNot(RerankService.get_client("key-b"), first)
