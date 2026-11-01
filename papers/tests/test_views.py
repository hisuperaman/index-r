from unittest.mock import patch

from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from datetime import date

from enums.Paper import DatePrecision, PaperSource
from iam.models import User
from papers.models import Chunk, Paper
from papers.views import ChunkSearchView

URL = reverse("chunk-search")


class ChunkSearchViewTests(APITestCase):
	@classmethod
	def setUpTestData(cls):
		cls.user = User.objects.create_user(email="ada@example.com", password="password")
		cls.paper = Paper.objects.create(
			source=PaperSource.ARXIV, external_id="1706.03762", title="Attention Is All You Need",
			url="https://arxiv.org/abs/1706.03762",
		)

	def setUp(self):
		self.client.force_authenticate(self.user)

	def add_chunks(self, count: int) -> None:
		start = Chunk.objects.count()
		Chunk.objects.bulk_create(
			Chunk(paper=self.paper, heading="Attention", text="Multi-head attention.", start_page=1, end_page=2,
				  chunk_index=start + index)
			for index in range(count)
		)

	def test_returns_matching_chunks_with_their_paper_and_rank(self):
		self.add_chunks(1)

		response = self.client.get(URL, {"q": "attention"})

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		[result] = response.data
		self.assertEqual(
			{key: result[key] for key in ("heading", "text", "start_page", "end_page", "chunk_index")},
			{"heading": "Attention", "text": "Multi-head attention.", "start_page": 1, "end_page": 2, "chunk_index": 0},
		)
		self.assertEqual(result["paper"]["id"], str(self.paper.id))
		self.assertEqual(result["paper"]["title"], "Attention Is All You Need")
		self.assertGreater(result["rank"], 0)

	def test_returns_the_score_alongside_the_rank(self):
		self.add_chunks(1)

		[result] = self.client.get(URL, {"q": "attention"}).data

		self.assertAlmostEqual(result["score"], result["rank"], places=5)

	def test_applies_the_paper_filters(self):
		self.add_chunks(1)
		recent = Paper.objects.create(
			source=PaperSource.ARXIV, external_id="2005.14165", title="Language Models are Few-Shot Learners",
			url="https://arxiv.org/abs/2005.14165", venue="NeurIPS", citation_count=500,
			publication_date=date(2020, 5, 28), publication_date_precision=DatePrecision.DAY,
		)
		Chunk.objects.create(paper=recent, heading="Attention", text="Sparse attention.", start_page=1, end_page=1,
							 chunk_index=0)

		response = self.client.get(URL, {
			"q": "attention", "year_from": 2019, "year_to": 2021, "venue": "neurips", "min_citations": 100,
		})

		self.assertEqual([result["paper"]["id"] for result in response.data], [str(recent.id)])

	def test_a_year_range_that_ends_before_it_starts_is_a_400_on_year_to(self):
		response = self.client.get(URL, {"q": "attention", "year_from": 2021, "year_to": 2019})

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("year_to", response.data)

	def test_a_negative_minimum_citation_count_is_a_400_on_min_citations(self):
		response = self.client.get(URL, {"q": "attention", "min_citations": -1})

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("min_citations", response.data)

	def test_a_missing_or_blank_query_is_a_400_on_q(self):
		for params in ({}, {"q": "   "}):
			response = self.client.get(URL, params)

			self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
			self.assertIn("q", response.data)

	def test_an_overlong_query_is_a_400_on_q(self):
		response = self.client.get(URL, {"q": "a" * 501})

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("q", response.data)

	def test_the_query_is_not_echoed_in_results(self):
		self.add_chunks(1)

		[result] = self.client.get(URL, {"q": "attention"}).data

		self.assertNotIn("q", result)

	def test_ignores_an_ordering_parameter(self):
		self.add_chunks(1)

		response = self.client.get(URL, {"q": "attention", "ordering": "heading"})

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(len(response.data), 1)

	def test_returns_at_most_the_limit(self):
		self.add_chunks(3)

		with patch.object(ChunkSearchView, "limit", 2):
			response = self.client.get(URL, {"q": "attention"})

		self.assertEqual(len(response.data), 2)

	def test_requires_login(self):
		self.client.force_authenticate(None)

		self.assertEqual(self.client.get(URL, {"q": "attention"}).status_code, status.HTTP_401_UNAUTHORIZED)

	def test_query_count_does_not_grow_with_results(self):
		self.add_chunks(1)
		with CaptureQueriesContext(connection) as one:
			self.client.get(URL, {"q": "attention"})

		self.add_chunks(4)
		with CaptureQueriesContext(connection) as five:
			response = self.client.get(URL, {"q": "attention"})

		self.assertEqual(len(response.data), 5)
		self.assertEqual(len(five), len(one))
