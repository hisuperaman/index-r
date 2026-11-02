class PdfDownloadError(Exception):
	"""The PDF could not be downloaded, or what was downloaded is not a PDF."""


class PaperUploadError(Exception):
	"""An uploaded PDF could not be turned into a paper."""
