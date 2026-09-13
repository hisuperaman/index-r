from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


import requests


@dataclass
class PaperResult:
    title: str
    abstract: str | None
    authors: list[str]
    url: str | None
    published_date: str | None
    source: str
    external_id: str


class BaseFetcherService(ABC):
    source: str

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()

    def get(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> requests.Response:
        response = self.session.get(
            url,
            params=params,
            headers=headers,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response

    @abstractmethod
    def fetch(
        self,
        query: str,
        limit: int = 10,
    ) -> list[PaperResult]:
        raise NotImplementedError