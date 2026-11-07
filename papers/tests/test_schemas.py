from django.test import SimpleTestCase
from pydantic import ValidationError

from papers.schemas import GroundedAnswer, SearchQueries


class SearchQueriesTests(SimpleTestCase):

	def test_accepts_three_to_five_queries(self):
		for count in (3, 5):
			self.assertEqual(len(SearchQueries(queries=["q"] * count).queries), count)

	def test_rejects_fewer_than_three_or_more_than_five(self):
		for count in (2, 6):
			with self.assertRaises(ValidationError):
				SearchQueries(queries=["q"] * count)



class GroundedAnswerTests(SimpleTestCase):

	def test_context_is_sufficient_unless_the_llm_says_otherwise(self):
		self.assertFalse(GroundedAnswer(content="Heads attend jointly [1].").is_insufficient_context)

	def test_content_comes_before_the_flag_so_it_can_stream(self):
		self.assertEqual(list(GroundedAnswer.model_fields), ["content", "is_insufficient_context"])
