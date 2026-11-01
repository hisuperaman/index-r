import re
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
	NO_PASSAGES = "No passages in the corpus answer this question yet."

	@classmethod
	def answer(cls, question: str, chunks: list[Chunk]) -> Answer:
		"""Answers `question` from `chunks`, keeping only the [n] markers that name a passage it was given."""
		if not chunks:
			return Answer(content=cls.NO_PASSAGES, citations={}, is_insufficient_context=True)

		prompt = build_answer_prompt(question, [f"{chunk.citation}\n{chunk.text}" for chunk in chunks])
		draft = LLMService.run(prompt, GroundedAnswer, ANSWER_INSTRUCTIONS)

		passages = dict(enumerate(chunks, start=1))
		content = cls.MARKER_RE.sub(lambda marker: marker[0] if int(marker[1]) in passages else "", draft.content)
		citations = {int(number): passages[int(number)] for number in cls.MARKER_RE.findall(content)}
		return Answer(
			content=content,
			citations=dict(sorted(citations.items())),
			is_insufficient_context=draft.is_insufficient_context,
		)
