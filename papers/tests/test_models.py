from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from enums.Paper import IngestionStatus, PaperSource
from papers.definitions import ExtractedChunk
from papers.models import Chunk, Citation, Paper


def create_paper(external_id: str) -> Paper:
	return Paper.objects.create(
		source=PaperSource.ARXIV,
		external_id=external_id,
		title=f"Paper {external_id}",
		url=f"https://arxiv.org/abs/{external_id}",
	)


class CitationTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		cls.citing = create_paper("2005.14165")
		cls.cited = create_paper("1706.03762")

	def test_paper_lists_its_references_and_what_cites_it(self):
		Citation.objects.create(citing_paper=self.citing, cited_paper=self.cited)

		self.assertQuerySetEqual(self.citing.references.all(), [self.cited])
		self.assertQuerySetEqual(self.cited.cited_by.all(), [self.citing])
		self.assertQuerySetEqual(self.cited.references.all(), [])

	def test_a_citation_is_stored_once(self):
		Citation.objects.create(citing_paper=self.citing, cited_paper=self.cited)

		with self.assertRaises(IntegrityError):
			Citation.objects.create(citing_paper=self.citing, cited_paper=self.cited)

	def test_a_paper_cannot_cite_itself(self):
		with self.assertRaises(IntegrityError):
			Citation.objects.create(citing_paper=self.citing, cited_paper=self.citing)

	def test_deleting_a_paper_removes_its_citations(self):
		Citation.objects.create(citing_paper=self.citing, cited_paper=self.cited)

		self.cited.delete()

		self.assertFalse(Citation.objects.exists())


class PaperIngestionTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		cls.paper = create_paper("1706.03762")

	def test_a_new_paper_is_pending(self):
		self.assertEqual(self.paper.ingestion_status, IngestionStatus.PENDING)

	def test_status_follows_the_ingestion_timestamps(self):
		self.paper.ingested_at = timezone.now()
		self.assertEqual(self.paper.ingestion_status, IngestionStatus.COMPLETED)

		self.paper.ingested_at, self.paper.ingestion_failed_at = None, timezone.now()
		self.assertEqual(self.paper.ingestion_status, IngestionStatus.FAILED)

	def test_a_paper_cannot_be_both_ingested_and_failed(self):
		with self.assertRaises(IntegrityError):
			Paper.objects.filter(pk=self.paper.pk).update(ingested_at=timezone.now(), ingestion_failed_at=timezone.now())


class ReplaceChunksTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		cls.paper = create_paper("1706.03762")

	def test_stores_each_chunk(self):
		self.paper.replace_chunks([
			ExtractedChunk(heading="1 Introduction", text="Attention mechanisms.", start_page=1, end_page=2, chunk_index=0),
			ExtractedChunk(heading=None, text="Recurrent models.", start_page=2, end_page=2, chunk_index=1),
		])

		self.assertQuerySetEqual(
			self.paper.chunks.order_by("chunk_index").values_list(
				"heading", "text", "start_page", "end_page", "chunk_index",
			),
			[
				("1 Introduction", "Attention mechanisms.", 1, 2, 0),
				(None, "Recurrent models.", 2, 2, 1),
			],
		)

	def test_replaces_existing_chunks(self):
		self.paper.replace_chunks([
			ExtractedChunk(heading="Old", text="Old text.", start_page=1, end_page=1, chunk_index=0),
		])

		self.paper.replace_chunks([
			ExtractedChunk(heading="New", text="New text.", start_page=1, end_page=1, chunk_index=0),
		])

		self.assertQuerySetEqual(self.paper.chunks.values_list("heading", flat=True), ["New"])

	def test_leaves_other_papers_chunks_alone(self):
		other = create_paper("1810.04805")
		other.replace_chunks([ExtractedChunk(heading="BERT", text="Masked LM.", start_page=1, end_page=1, chunk_index=0)])

		self.paper.replace_chunks([])

		self.assertQuerySetEqual(other.chunks.values_list("heading", flat=True), ["BERT"])

	def test_stored_chunks_are_searchable(self):
		self.paper.replace_chunks([
			ExtractedChunk(heading="Intro", text="Transformers use attention.", start_page=1, end_page=1, chunk_index=0),
		])

		self.assertTrue(Chunk.objects.filter(search_vector="transformer").exists())


class ChunkCitationTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		cls.paper = create_paper("1706.03762")

	def chunk(self, **fields) -> Chunk:
		return Chunk(paper=self.paper, text="Text.", chunk_index=0, **fields)

	def test_cites_the_paper_section_and_page(self):
		chunk = self.chunk(heading="3.2 Attention", start_page=4, end_page=4)

		self.assertEqual(chunk.citation, "Paper 1706.03762, §3.2 Attention, p.4")

	def test_cites_a_page_range(self):
		self.assertEqual(self.chunk(heading="Results", start_page=7, end_page=8).citation, "Paper 1706.03762, §Results, pp.7–8")

	def test_leaves_out_a_missing_section(self):
		self.assertEqual(self.chunk(heading=None, start_page=1, end_page=1).citation, "Paper 1706.03762, p.1")
