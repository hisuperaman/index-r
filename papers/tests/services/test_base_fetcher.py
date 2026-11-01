from datetime import date

from django.test import SimpleTestCase

from enums.Paper import DatePrecision
from papers.services.fetchers import BaseFetcherService


class BaseFetcherServiceTests(SimpleTestCase):
	def test_parses_day_month_and_year_dates(self):
		self.assertEqual(BaseFetcherService.parse_date("2017-06-12"), (date(2017, 6, 12), DatePrecision.DAY))
		self.assertEqual(BaseFetcherService.parse_date("2017-06"), (date(2017, 6, 1), DatePrecision.MONTH))
		self.assertEqual(BaseFetcherService.parse_date("2017"), (date(2017, 1, 1), DatePrecision.YEAR))

	def test_parses_a_timestamp_as_its_day(self):
		self.assertEqual(BaseFetcherService.parse_date("2017-06-12T17:57:34Z"), (date(2017, 6, 12), DatePrecision.DAY))

	def test_unparseable_dates_are_none(self):
		for value in (None, "", "June 2017", "2017-13-40"):
			with self.subTest(value=value):
				self.assertEqual(BaseFetcherService.parse_date(value), (None, None))
