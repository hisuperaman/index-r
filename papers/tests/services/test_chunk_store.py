from django.test import TestCase

from enums.Paper import PaperSource
from papers.definitions import ExtractedChunk
from papers.models import Chunk, Paper
from papers.services import ChunkStoreService


class ChunkStoreServiceTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		cls.paper = Paper.objects.create(
			source=PaperSource.ARXIV,
			external_id="1706.03762",
			title="Attention Is All You Need",
			url="https://arxiv.org/abs/1706.03762",
		)

	def test_stores_each_chunk(self):
		ChunkStoreService.store(self.paper, [
			ExtractedChunk(heading="1 Introduction", text="Attention mechanisms.", start_page=1, end_page=2, chunk_index=0),
			ExtractedChunk(heading=None, text="Recurrent models.", start_page=2, end_page=2, chunk_index=1),
		])

		self.assertQuerySetEqual(
			Chunk.objects.filter(paper=self.paper).order_by("chunk_index").values_list(
				"heading", "text", "start_page", "end_page", "chunk_index",
			),
			[
				("1 Introduction", "Attention mechanisms.", 1, 2, 0),
				(None, "Recurrent models.", 2, 2, 1),
			],
		)

	def test_replaces_existing_chunks(self):
		ChunkStoreService.store(self.paper, [
			ExtractedChunk(heading="Old", text="Old text.", start_page=1, end_page=1, chunk_index=0),
		])

		ChunkStoreService.store(self.paper, [
			ExtractedChunk(heading="New", text="New text.", start_page=1, end_page=1, chunk_index=0),
		])

		self.assertQuerySetEqual(Chunk.objects.filter(paper=self.paper).values_list("heading", flat=True), ["New"])

	def test_stored_chunks_are_searchable(self):
		ChunkStoreService.store(self.paper, [
			ExtractedChunk(heading="Intro", text="Transformers use attention.", start_page=1, end_page=1, chunk_index=0),
		])

		self.assertTrue(Chunk.objects.filter(search_vector="transformer").exists())
