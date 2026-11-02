from django.db import IntegrityError, transaction

from papers.models import Author, Paper, PaperAuthor
from papers.services.fetchers.definitions import FetchedAuthor, FetchedPaper


class PaperStoreService:
	"""Saves fetched papers and their authors, reusing rows the corpus already has."""

	FILLABLE_FIELDS = (Paper.fields.abstract, Paper.fields.venue, Paper.fields.pdf_url)

	@classmethod
	def store(cls, fetched_papers: list[FetchedPaper]) -> list[Paper]:
		"""Returns the stored Paper for each fetched paper, creating the ones not stored yet."""
		return [cls.store_one(fetched) for fetched in fetched_papers]

	@classmethod
	def store_one(cls, fetched: FetchedPaper) -> Paper:
		"""Returns the stored Paper for `fetched`, creating it and its authors if it is new."""
		doi = fetched.doi.lower() if fetched.doi else None
		paper = Paper.objects.public().matching(fetched.source, fetched.external_id, doi).first()
		if paper is not None:
			return cls.refresh(paper, fetched)

		try:
			with transaction.atomic():
				paper = Paper.objects.create(
					source=fetched.source,
					external_id=fetched.external_id,
					doi=doi,
					title=fetched.title,
					abstract=fetched.abstract,
					venue=fetched.venue,
					citation_count=fetched.citation_count,
					publication_date=fetched.publication_date,
					publication_date_precision=fetched.publication_date_precision,
					url=fetched.url,
					pdf_url=fetched.pdf_url,
				)
				cls.add_authors(paper, fetched.authors)
			cls.queue_ingestion(paper)
			return paper
		except IntegrityError:
			# A concurrent store saved the same paper between the lookup and the insert.
			paper = Paper.objects.public().matching(fetched.source, fetched.external_id, doi).first()
			if paper is None:
				raise
			return cls.refresh(paper, fetched)

	@classmethod
	def refresh(cls, paper: Paper, fetched: FetchedPaper) -> Paper:
		"""Fills the paper's blank fields from `fetched` and keeps the higher citation count."""
		changed = [field for field in cls.FILLABLE_FIELDS if not getattr(paper, field) and getattr(fetched, field)]
		for field in changed:
			setattr(paper, field, getattr(fetched, field))

		if fetched.citation_count is not None and fetched.citation_count > (paper.citation_count or 0):
			paper.citation_count = fetched.citation_count
			changed.append(Paper.fields.citation_count)

		if changed:
			paper.save(update_fields=[*changed, Paper.fields.updated_at])
		return paper

	@staticmethod
	def queue_ingestion(paper: Paper) -> None:
		"""Queues the paper's ingestion when it has an open-access PDF."""
		from papers.tasks import queue_ingest_paper

		if paper.pdf_url:
			queue_ingest_paper(paper)

	@staticmethod
	def add_authors(paper: Paper, authors: list[FetchedAuthor]) -> None:
		"""Links `authors` to the paper in byline order, skipping repeats."""
		links: list[PaperAuthor] = []
		linked_ids = set()
		for fetched in authors:
			author = Author.objects.find_or_create(fetched.name, fetched.orcid)
			if author.pk not in linked_ids:
				linked_ids.add(author.pk)
				links.append(PaperAuthor(paper=paper, author=author, order=len(links) + 1))
		PaperAuthor.objects.bulk_create(links)
