import re
from collections import deque
from collections.abc import Iterator
from dataclasses import dataclass

from papers.models import Chunk
from papers.prompts import ANSWER_INSTRUCTIONS, build_answer_prompt
from papers.schemas import GroundedAnswer
from server.services import LLMService


@dataclass
class Answer:
	"""An answer citing passages as [n], with the chunk behind each number it cites."""
	content: str
	citations: dict[int, Chunk]
	is_insufficient_context: bool


class AnswerService:
	"""Writes an answer grounded only in the passages it is given."""

	MARKER_RE = re.compile(r"\s?\[(\d+)]")
	NO_PASSAGES = "I couldn't find papers that answer this question yet."
	NO_ANSWER = "I couldn't write an answer from the papers I found."

	@classmethod
	def answer(cls, question: str, chunks: list[Chunk]) -> Answer:
		"""Answers `question` from `chunks`, keeping only the [n] markers that name a passage it was given."""
		return deque(cls.stream(question, chunks), maxlen=1)[0]

	@classmethod
	def stream(cls, question: str, chunks: list[Chunk]) -> Iterator[Answer]:
		"""Yields the answer as the LLM writes it, ending with the complete one."""
		if not chunks:
			yield Answer(content=cls.NO_PASSAGES, citations={}, is_insufficient_context=True)
			return

		prompt = build_answer_prompt(question, [f"{chunk.citation}\n{chunk.text}" for chunk in chunks])
		draft = None
		for draft in LLMService.stream(prompt, GroundedAnswer, ANSWER_INSTRUCTIONS):
			yield cls.to_answer(draft, chunks)

		if draft is None or not draft.content.strip():
			yield Answer(content=cls.NO_ANSWER, citations={}, is_insufficient_context=True)

	@classmethod
	def to_answer(cls, draft: GroundedAnswer, chunks: list[Chunk]) -> Answer:
		"""Keeps the draft's markers that name a passage and maps each to its chunk."""
		passages = dict(enumerate(chunks, start=1))
		content = cls.MARKER_RE.sub(lambda marker: marker[0] if int(marker[1]) in passages else "", draft.content)
		citations = {int(number): passages[int(number)] for number in cls.MARKER_RE.findall(content)}
		return Answer(
			content=content,
			citations=dict(sorted(citations.items())),
			is_insufficient_context=draft.is_insufficient_context,
		)
