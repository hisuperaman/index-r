from hashlib import sha256
from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import uuid4

from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from django.utils import timezone

from enums.Paper import PaperSource
from papers.exceptions import PaperUploadError
from papers.models import Paper
from papers.services.PaperStoreService import PaperStoreService
from papers.services.TextExtractorService import TextExtractorService


class PaperUploadService:
	"""Turns a user's PDF into a private paper that is searchable straight away."""

	@staticmethod
	def upload(owner, file: UploadedFile, title: str = "") -> Paper:
		"""Extracts `file` into a paper only `owner` can see, reusing their earlier upload of the same file."""
		with NamedTemporaryFile(suffix=".pdf") as copy:
			digest = sha256()
			for part in file.chunks():
				digest.update(part)
				copy.write(part)
			copy.flush()

			existing = Paper.objects.filter(owner=owner, content_hash=digest.hexdigest()).first()
			if existing is not None:
				return existing

			try:
				extracted = TextExtractorService.extract(copy.name)
			except Exception as error:
				raise PaperUploadError("We couldn't read this PDF.") from error

		if not extracted.chunks:
			raise PaperUploadError("We couldn't find any text in this PDF. Scanned documents aren't supported yet.")

		with transaction.atomic():
			paper = Paper.objects.create(
				source=PaperSource.UPLOAD,
				external_id=uuid4().hex,
				owner=owner,
				content_hash=digest.hexdigest(),
				title=title.strip() or extracted.title or Path(file.name).stem,
				abstract=extracted.abstract,
				doi=extracted.doi.lower() if extracted.doi else None,
				ingested_at=timezone.now(),
			)
			PaperStoreService.add_authors(paper, extracted.authors)
			paper.replace_chunks(extracted.chunks)
		return paper
