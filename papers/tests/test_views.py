from datetime import date
from io import BytesIO
from unittest.mock import patch

import pymupdf
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from enums.Paper import DatePrecision, PaperSource
from iam.models import User
from papers.models import Author, Chunk, Paper, PaperAuthor
from papers.services import PdfDownloadService
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
		self.assertEqual(result["citation"], "Attention Is All You Need, §Attention, pp.1–2")
		self.assertNotIn("authors", result["paper"])
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



class PaperViewSetTests(APITestCase):
	@classmethod
	def setUpTestData(cls):
		cls.user = User.objects.create_user(email="ada@example.com", password="password")
		cls.attention = cls.create_paper("1706.03762", "Attention Is All You Need", doi="10.48550/arxiv.1706.03762")
		cls.bert = cls.create_paper("1810.04805", "BERT: Pre-training of Deep Bidirectional Transformers")

	@staticmethod
	def create_paper(external_id: str, title: str, doi: str | None = None, authors: tuple[str, ...] = ()) -> Paper:
		paper = Paper.objects.create(
			source=PaperSource.ARXIV, external_id=external_id, title=title, doi=doi,
			url=f"https://arxiv.org/abs/{external_id}",
		)
		for order, name in enumerate(authors, start=1):
			PaperAuthor.objects.create(paper=paper, author=Author.objects.create(name=name), order=order)
		return paper

	def setUp(self):
		self.client.force_authenticate(self.user)

	def list(self, **params):
		return self.client.get(reverse("paper-list"), params)

	def test_lists_the_corpus_newest_first(self):
		self.assertEqual([row["id"] for row in self.list().data["results"]], [str(self.bert.id), str(self.attention.id)])

	def test_searches_titles_and_dois(self):
		self.assertEqual([row["id"] for row in self.list(search="bidirectional").data["results"]], [str(self.bert.id)])
		self.assertEqual([row["id"] for row in self.list(search="1706.03762").data["results"]], [str(self.attention.id)])

	def test_lists_authors_in_byline_order(self):
		paper = self.create_paper("2005.14165", "Language Models are Few-Shot Learners", authors=("Tom Brown", "Ben Mann"))

		response = self.client.get(reverse("paper-detail", args=[paper.pk]))

		self.assertEqual(response.data["authors"], ["Tom Brown", "Ben Mann"])

	def test_query_count_does_not_grow_with_papers_or_authors(self):
		with CaptureQueriesContext(connection) as two:
			self.list()

		for index in range(3):
			self.create_paper(str(index), f"Paper {index}", authors=("A", "B"))
		with CaptureQueriesContext(connection) as five:
			response = self.list()

		self.assertEqual(len(response.data["results"]), 5)
		self.assertEqual(len(five), len(two))

	def test_a_malformed_id_is_a_404(self):
		self.assertEqual(self.client.get("/api/papers/not-a-uuid/").status_code, status.HTTP_404_NOT_FOUND)

	def test_requires_login(self):
		self.client.force_authenticate(None)

		self.assertEqual(self.list().status_code, status.HTTP_401_UNAUTHORIZED)


class PaperPrivacyAndUploadTests(APITestCase):
	@classmethod
	def setUpTestData(cls):
		cls.me = User.objects.create_user(email="ada@example.com", password="password")
		cls.someone = User.objects.create_user(email="grace@example.com", password="password")
		cls.public = Paper.objects.create(
			source=PaperSource.ARXIV, external_id="1", title="Public attention", url="https://arxiv.org/abs/1",
		)
		cls.mine = Paper.objects.create(source=PaperSource.UPLOAD, external_id="u1", title="My attention notes", owner=cls.me)
		cls.theirs = Paper.objects.create(
			source=PaperSource.UPLOAD, external_id="u2", title="Their attention notes", owner=cls.someone,
		)
		for paper in (cls.public, cls.mine, cls.theirs):
			Chunk.objects.create(paper=paper, heading="Attention", text="Attention heads.", start_page=1, end_page=1,
								 chunk_index=0)

	def setUp(self):
		self.client.force_authenticate(self.me)

	def test_search_shows_the_corpus_and_my_uploads_only(self):
		rows = self.client.get(reverse("paper-list"), {"search": "attention"}).data["results"]

		self.assertEqual({row["id"] for row in rows}, {str(self.public.id), str(self.mine.id)})
		self.assertEqual({row["id"]: row["is_private"] for row in rows}[str(self.mine.id)], True)

	def test_another_users_upload_is_not_found(self):
		response = self.client.get(reverse("paper-detail", args=[self.theirs.pk]))

		self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

	def test_chunk_search_never_returns_another_users_upload(self):
		rows = self.client.get(reverse("chunk-search"), {"q": "attention"}).data

		self.assertEqual({row["paper"]["id"] for row in rows}, {str(self.public.id), str(self.mine.id)})

	def upload(self, content: bytes, name: str = "draft.pdf", **data):
		return self.client.post(
			reverse("paper-list"), {"file": SimpleUploadedFile(name, content, "application/pdf"), **data}, format="multipart",
		)

	def test_uploads_a_private_paper(self):
		document = pymupdf.open()
		page = document.new_page()
		page.insert_text((72, 80), "Notes on Sparse Attention", fontsize=20, fontname="hebo")
		page.insert_text((72, 120), "Sparse attention scales linearly.", fontsize=10)
		buffer = BytesIO()
		document.save(buffer)

		response = self.upload(buffer.getvalue(), title="My notes")

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual((response.data["title"], response.data["is_private"]), ("My notes", True))
		self.assertNotIn("file", response.data)
		paper = Paper.objects.get(pk=response.data["id"])
		self.assertEqual(paper.owner, self.me)
		self.assertTrue(paper.chunks.exists())

	def test_rejects_a_file_that_is_not_a_pdf(self):
		response = self.upload(b"<html>nope</html>", name="page.pdf")

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("file", response.data)

	def test_rejects_a_file_over_the_limit(self):
		with patch.object(PdfDownloadService, "MAX_BYTES", 10):
			response = self.upload(b"%PDF-1.7 " + b"x" * 20)

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("file", response.data)

	def test_a_pdf_without_text_is_a_400_on_file(self):
		buffer = BytesIO()
		document = pymupdf.open()
		document.new_page()
		document.save(buffer)

		response = self.upload(buffer.getvalue())

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("couldn't find any text", response.data["file"][0])
		self.assertFalse(Paper.objects.filter(owner=self.me).exclude(pk=self.mine.pk).exists())

	def test_requires_a_file(self):
		response = self.client.post(reverse("paper-list"), {"title": "Nothing"}, format="multipart")

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("file", response.data)
