from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile

import requests

from papers.exceptions import PdfDownloadError


class PdfDownloadService:
	"""Downloads a paper's PDF to a temporary file."""

	TIMEOUT_SECONDS = 30
	MAX_BYTES = 50 * 1024 * 1024
	CHUNK_BYTES = 64 * 1024
	PDF_SIGNATURE = b"%PDF-"

	@classmethod
	@contextmanager
	def download(cls, url: str) -> Iterator[Path]:
		"""Yields the path of a temporary copy of the PDF at `url`, deleting it on exit."""
		with NamedTemporaryFile(suffix=".pdf") as file:
			cls.write(url, file)
			yield Path(file.name)

	@classmethod
	def write(cls, url: str, file) -> None:
		"""Streams the PDF at `url` into `file`, raising PdfDownloadError if it fails or is not a PDF."""
		try:
			with requests.get(url, stream=True, timeout=cls.TIMEOUT_SECONDS) as response:
				response.raise_for_status()
				size = 0
				for chunk in response.iter_content(cls.CHUNK_BYTES):
					if not chunk:
						continue
					if size == 0 and not chunk.startswith(cls.PDF_SIGNATURE):
						raise PdfDownloadError(f"{url} did not return a PDF")
					size += len(chunk)
					if size > cls.MAX_BYTES:
						raise PdfDownloadError(f"{url} is larger than {cls.MAX_BYTES} bytes")
					file.write(chunk)
		except requests.RequestException as error:
			raise PdfDownloadError(f"Could not download {url}: {error}") from error

		if size == 0:
			raise PdfDownloadError(f"{url} returned an empty file")
		file.flush()
