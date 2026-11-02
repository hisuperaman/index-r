from io import BytesIO

import pymupdf
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from enums.Paper import PaperSource
from iam.models import User
from papers.exceptions import PaperUploadError
from papers.services import PaperUploadService


def pdf(*lines: tuple[str, int]) -> SimpleUploadedFile:
	document = pymupdf.open()
	page = document.new_page()
	for index, (text, size) in enumerate(lines):
		page.insert_text((72, 80 + index * 40), text, fontsize=size, fontname="hebo" if size > 12 else "helv")
	buffer = BytesIO()
	document.save(buffer)
	return SimpleUploadedFile("my-draft.pdf", buffer.getvalue(), content_type="application/pdf")


PAPER = (("A Study of Things", 20), ("Ada Lovelace, Alan Turing", 10), ("1 Introduction", 14), ("Intro body.", 10))


class PaperUploadServiceTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		cls.user = User.objects.create_user(email="ada@example.com", password="password")

	def test_stores_a_private_searchable_paper(self):
		paper = PaperUploadService.upload(self.user, pdf(*PAPER))

		self.assertEqual((paper.source, paper.owner, paper.title), (PaperSource.UPLOAD, self.user, "A Study of Things"))
		self.assertTrue(paper.is_private)
		self.assertIsNotNone(paper.ingested_at)
		self.assertEqual(paper.author_names, ["Ada Lovelace", "Alan Turing"])
		self.assertQuerySetEqual(paper.chunks.order_by("chunk_index").values_list("heading", "text"), [(None, "Ada Lovelace, Alan Turing"), ("1 Introduction", "Intro body.")])

	def test_uploading_the_same_file_again_reuses_the_paper(self):
		content = pdf(*PAPER).read()
		first = PaperUploadService.upload(self.user, SimpleUploadedFile("draft.pdf", content))

		again = PaperUploadService.upload(self.user, SimpleUploadedFile("draft-copy.pdf", content))

		self.assertEqual(again, first)
		self.assertEqual(self.user.uploaded_papers.count(), 1)

	def test_another_user_uploading_the_same_file_gets_their_own_copy(self):
		other = User.objects.create_user(email="grace@example.com", password="password")
		content = pdf(*PAPER).read()
		mine = PaperUploadService.upload(self.user, SimpleUploadedFile("draft.pdf", content))

		theirs = PaperUploadService.upload(other, SimpleUploadedFile("draft.pdf", content))

		self.assertNotEqual(theirs, mine)
		self.assertEqual(theirs.owner, other)

	def test_a_given_title_wins(self):
		self.assertEqual(PaperUploadService.upload(self.user, pdf(*PAPER), "My draft").title, "My draft")

	def test_rejects_a_pdf_without_text(self):
		with self.assertRaisesMessage(PaperUploadError, "couldn't find any text"):
			PaperUploadService.upload(self.user, pdf())

	def test_rejects_a_broken_pdf(self):
		broken = SimpleUploadedFile("broken.pdf", b"%PDF-1.7 not really", content_type="application/pdf")

		with self.assertRaisesMessage(PaperUploadError, "couldn't read this PDF"):
			PaperUploadService.upload(self.user, broken)
