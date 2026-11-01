from unittest.mock import MagicMock, patch

import requests
from django.test import SimpleTestCase

from papers.exceptions import PdfDownloadError
from papers.services import PdfDownloadService

PDF_URL = "https://arxiv.org/pdf/1706.03762"


def fake_response(*chunks: bytes) -> MagicMock:
	response = MagicMock()
	response.__enter__.return_value = response
	response.iter_content.return_value = iter(chunks)
	return response


class PdfDownloadServiceTests(SimpleTestCase):

	def setUp(self):
		self.get = self.enterContext(patch.object(requests, "get"))

	def test_yields_a_local_copy_of_the_pdf(self):
		self.get.return_value = fake_response(b"%PDF-1.7 first", b" second")

		with PdfDownloadService.download(PDF_URL) as path:
			self.assertEqual(path.read_bytes(), b"%PDF-1.7 first second")
			self.assertEqual(path.suffix, ".pdf")

		self.get.assert_called_once_with(PDF_URL, stream=True, timeout=PdfDownloadService.TIMEOUT_SECONDS)

	def test_deletes_the_file_on_exit(self):
		self.get.return_value = fake_response(b"%PDF-1.7")

		with PdfDownloadService.download(PDF_URL) as path:
			pass

		self.assertFalse(path.exists())

	def test_rejects_a_response_that_is_not_a_pdf(self):
		self.get.return_value = fake_response(b"<!DOCTYPE html>")

		with self.assertRaises(PdfDownloadError), PdfDownloadService.download(PDF_URL):
			pass

	def test_rejects_an_empty_response(self):
		self.get.return_value = fake_response()

		with self.assertRaises(PdfDownloadError), PdfDownloadService.download(PDF_URL):
			pass

	def test_rejects_a_file_over_the_size_limit(self):
		self.get.return_value = fake_response(b"%PDF-1.7", b"x" * 10)

		with patch.object(PdfDownloadService, "MAX_BYTES", 12), self.assertRaises(PdfDownloadError):
			with PdfDownloadService.download(PDF_URL):
				pass

	def test_wraps_a_request_failure(self):
		self.get.side_effect = requests.ConnectionError("unreachable")

		with self.assertRaises(PdfDownloadError), PdfDownloadService.download(PDF_URL):
			pass

	def test_wraps_an_error_status(self):
		response = fake_response()
		response.raise_for_status.side_effect = requests.HTTPError("404")
		self.get.return_value = response

		with self.assertRaises(PdfDownloadError), PdfDownloadService.download(PDF_URL):
			pass
