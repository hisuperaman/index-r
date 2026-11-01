from django.test import SimpleTestCase
from pydantic import ValidationError

from papers.schemas import SearchQueries


class SearchQueriesTests(SimpleTestCase):

	def test_accepts_three_to_five_queries(self):
		for count in (3, 5):
			self.assertEqual(len(SearchQueries(queries=["q"] * count).queries), count)

	def test_rejects_fewer_than_three_or_more_than_five(self):
		for count in (2, 6):
			with self.assertRaises(ValidationError):
				SearchQueries(queries=["q"] * count)

