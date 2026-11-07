import time
from abc import ABC, abstractmethod
from datetime import date, datetime
from http import HTTPStatus
from typing import Any

import requests

from enums.Paper import DatePrecision, PaperSource
from papers.services.fetchers.definitions import FetchedPaper


class BaseFetcherService(ABC):
	"""Searches one external paper provider."""

	source: PaperSource
	BASE_URL: str
	TIMEOUT_SECONDS = 10
	RATE_LIMIT_WAIT_SECONDS = 1.5
	MAX_LIMIT: int

	@classmethod
	def get(cls, params: dict[str, Any], path: str = "") -> requests.Response:
		"""Sends a GET to the provider's API, retrying once if rate-limited, and raises on an error status."""
		url = cls.BASE_URL + path
		response = requests.get(url, params=params, headers=cls.headers(), timeout=cls.TIMEOUT_SECONDS)
		if response.status_code == HTTPStatus.TOO_MANY_REQUESTS:
			time.sleep(cls.RATE_LIMIT_WAIT_SECONDS)
			response = requests.get(url, params=params, headers=cls.headers(), timeout=cls.TIMEOUT_SECONDS)
		response.raise_for_status()
		return response

	@classmethod
	def headers(cls) -> dict[str, str]:
		"""Extra request headers, such as an API key."""
		return {}

	@classmethod
	@abstractmethod
	def search(cls, query: str, limit: int, since: date | None = None) -> list[FetchedPaper]:
		"""Returns up to `limit` papers matching `query`, only those published since `since` when given."""

	@classmethod
	def clamp_limit(cls, limit: int) -> int:
		"""Keeps `limit` within what the provider accepts."""
		return max(1, min(limit, cls.MAX_LIMIT))

	@staticmethod
	def parse_date(value: str | None) -> tuple[date | None, DatePrecision | None]:
		"""Parses 'YYYY', 'YYYY-MM' or 'YYYY-MM-DD…' into a date and the precision it was given at."""
		try:
			numbers = [int(part) for part in (value or "")[:10].split("-")]
			if len(numbers) == 1:
				return date(numbers[0], 1, 1), DatePrecision.YEAR
			if len(numbers) == 2:
				return date(numbers[0], numbers[1], 1), DatePrecision.MONTH
			return date(*numbers), DatePrecision.DAY
		except (TypeError, ValueError):
			return None, None

	@staticmethod
	def parse_datetime(value: str | None) -> datetime | None:
		"""Parses an ISO 8601 timestamp such as '2023-08-02T00:41:18Z'."""
		try:
			return datetime.fromisoformat(value.strip()) if value else None
		except ValueError:
			return None

	@staticmethod
	def clean(value: str | None) -> str | None:
		"""Collapses whitespace, returning None for blank values."""
		return (" ".join(value.split()) or None) if value else None

	@staticmethod
	def strip_prefix(value: str | None, prefix: str) -> str | None:
		"""Removes a URL prefix such as 'https://doi.org/' from an identifier."""
		if not value:
			return None
		return value[len(prefix):] if value.lower().startswith(prefix) else value
