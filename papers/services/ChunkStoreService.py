from django.db import transaction

from papers.definitions import ExtractedChunk
from papers.models import Chunk, Paper


class ChunkStoreService:
	"""Saves extracted chunks as a paper's Chunk rows."""

	@staticmethod
	@transaction.atomic
	def store(paper: Paper, chunks: list[ExtractedChunk]) -> list[Chunk]:
		"""Replaces the paper's chunks with `chunks`."""
		Chunk.objects.filter(paper=paper).delete()
		return Chunk.objects.bulk_create(
			Chunk(
				paper=paper,
				heading=chunk.heading,
				text=chunk.text,
				start_page=chunk.start_page,
				end_page=chunk.end_page,
				chunk_index=chunk.chunk_index,
			)
			for chunk in chunks
		)
