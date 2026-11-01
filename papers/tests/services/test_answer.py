from unittest.mock import patch

from django.test import TestCase

from enums.Paper import PaperSource
from papers.models import Chunk, Paper
from papers.prompts import ANSWER_INSTRUCTIONS
from papers.schemas import GroundedAnswer
from papers.services import AnswerService
from server.services import LLMService

QUESTION = "How does multi-head attention work?"


class AnswerServiceTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		paper = Paper.objects.create(
			source=PaperSource.ARXIV, external_id="1706.03762", title="Attention Is All You Need",
			url="https://arxiv.org/abs/1706.03762",
		)
		cls.attention = Chunk.objects.create(
			paper=paper, heading="3.2.2 Multi-Head Attention", text="Heads attend jointly.", start_page=4, end_page=5,
			chunk_index=0,
		)
		cls.dropout = Chunk.objects.create(
			paper=paper, heading="5.4 Regularization", text="Residual dropout.", start_page=7, end_page=7, chunk_index=1,
		)

	def answer(self, content: str, insufficient: bool = False):
		draft = GroundedAnswer(content=content, is_insufficient_context=insufficient)
		with patch.object(LLMService, "stream", return_value=iter([draft])) as run:
			answer = AnswerService.answer(QUESTION, [self.attention, self.dropout])
		self.run = run
		return answer

	def test_maps_each_marker_to_its_chunk(self):
		answer = self.answer("Heads attend jointly [1], with dropout [2][1].")

		self.assertEqual(answer.content, "Heads attend jointly [1], with dropout [2][1].")
		self.assertEqual(answer.citations, {1: self.attention, 2: self.dropout})
		self.assertFalse(answer.is_insufficient_context)

	def test_lists_only_the_passages_it_cites(self):
		self.assertEqual(self.answer("Heads attend jointly [1].").citations, {1: self.attention})

	def test_drops_markers_for_passages_it_was_not_given(self):
		answer = self.answer("Heads attend jointly [1] and scale well [3].")

		self.assertEqual(answer.content, "Heads attend jointly [1] and scale well.")
		self.assertEqual(answer.citations, {1: self.attention})

	def test_passes_on_insufficient_context(self):
		answer = self.answer("The passages describe attention but not its cost.", insufficient=True)

		self.assertTrue(answer.is_insufficient_context)
		self.assertEqual(answer.citations, {})

	def test_sends_the_numbered_passages_with_their_citations(self):
		self.answer("Answer [1].")

		prompt, output_type, instructions = self.run.call_args.args
		self.assertIn(f"Question: {QUESTION}", prompt)
		self.assertIn(
			"[1] Attention Is All You Need, §3.2.2 Multi-Head Attention, pp.4–5\nHeads attend jointly.", prompt,
		)
		self.assertIn("[2] Attention Is All You Need, §5.4 Regularization, p.7\nResidual dropout.", prompt)
		self.assertEqual((output_type, instructions), (GroundedAnswer, ANSWER_INSTRUCTIONS))

	def test_streams_the_answer_as_it_grows(self):
		drafts = [GroundedAnswer(content="Heads"), GroundedAnswer(content="Heads attend [1] [9]")]

		with patch.object(LLMService, "stream", return_value=iter(drafts)):
			answers = list(AnswerService.stream(QUESTION, [self.attention, self.dropout]))

		self.assertEqual([answer.content for answer in answers], ["Heads", "Heads attend [1]"])
		self.assertEqual(answers[-1].citations, {1: self.attention})

	def test_a_blank_answer_ends_with_a_fallback(self):
		answer = self.answer("   ")

		self.assertEqual(answer.content, AnswerService.NO_ANSWER)
		self.assertTrue(answer.is_insufficient_context)

	def test_no_passages_is_insufficient_without_calling_the_llm(self):
		with patch.object(LLMService, "stream") as run:
			answer = AnswerService.answer(QUESTION, [])

		run.assert_not_called()
		self.assertTrue(answer.is_insufficient_context)
		self.assertEqual(answer.citations, {})
