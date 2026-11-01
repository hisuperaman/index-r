import time
from collections.abc import Iterator
from dataclasses import dataclass

from django.conf import settings
from django.db import transaction

from enums.Paper import IngestionStatus
from enums.Workspace import AskStage, MessageRole
from papers.models import Paper
from papers.services import AnswerService, DiscoveryService, QueryExpansionService, RetrievalService
from papers.services.AnswerService import Answer
from workspaces.models import Message, MessageCitation, Workspace, WorkspacePaper


@dataclass
class AskStatus:
	"""The ask has reached `stage`."""
	stage: AskStage


@dataclass
class AskDelta:
	"""The answer written so far."""
	content: str


@dataclass
class AskDone:
	"""The saved assistant message."""
	message: Message


type AskEvent = AskStatus | AskDelta | AskDone


class AskService:
	"""Answers a question posted to a workspace from the corpus, discovering new papers when it must."""

	POLL_SECONDS = 1

	@classmethod
	def ask(cls, question: Message) -> Iterator[AskEvent]:
		"""Yields each stage, the answer as it is written, and finally the saved assistant message."""
		text = question.content

		yield AskStatus(AskStage.EXPANDING)
		queries = QueryExpansionService.expand(text)

		yield AskStatus(AskStage.SEARCHING)
		retrieval = RetrievalService.retrieve(text, queries)

		if retrieval.needs_discovery:
			yield AskStatus(AskStage.DISCOVERING)
			papers = DiscoveryService.discover(text, queries)
			pending = [paper.pk for paper in papers if paper.ingestion_status == IngestionStatus.PENDING]
			if pending:
				yield AskStatus(AskStage.INGESTING)
				cls.wait_for_ingestion(pending)
				yield AskStatus(AskStage.SEARCHING)
				retrieval = RetrievalService.retrieve(text, queries)

		yield AskStatus(AskStage.ANSWERING)
		answer = None
		for answer in AnswerService.stream(text, [chunk for chunk, _ in retrieval.passages]):
			yield AskDelta(answer.content)

		yield AskDone(cls.save_answer(question.workspace, answer))

	@classmethod
	def wait_for_ingestion(cls, paper_ids: list) -> None:
		"""Waits until none of the papers is pending, or INGESTION_WAIT_SECONDS pass."""
		deadline = time.monotonic() + settings.INGESTION_WAIT_SECONDS
		while Paper.objects.pending().filter(pk__in=paper_ids).exists() and time.monotonic() < deadline:
			time.sleep(cls.POLL_SECONDS)

	@staticmethod
	@transaction.atomic
	def save_answer(workspace: Workspace, answer: Answer) -> Message:
		"""Saves the answer as an assistant message with its citations, and adds the cited papers to the workspace."""
		message = Message.objects.create(workspace=workspace, role=MessageRole.ASSISTANT, content=answer.content)
		MessageCitation.objects.bulk_create(
			MessageCitation(message=message, chunk=chunk, number=number) for number, chunk in answer.citations.items()
		)
		paper_ids = {chunk.paper_id for chunk in answer.citations.values()}
		WorkspacePaper.objects.bulk_create(
			(WorkspacePaper(workspace=workspace, paper_id=paper_id) for paper_id in paper_ids), ignore_conflicts=True,
		)
		return message
