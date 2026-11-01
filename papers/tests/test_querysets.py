from django.test import TestCase
from django.utils import timezone

from enums.Paper import PaperSource
from papers.models import Author, Chunk, Paper


def create_paper(external_id: str, **fields) -> Paper:
	return Paper.objects.create(
		source=PaperSource.ARXIV, external_id=external_id, title=f"Paper {external_id}",
		url=f"https://arxiv.org/abs/{external_id}", **fields,
	)


class AuthorQuerySetTests(TestCase):

	def test_finds_an_author_by_orcid_whatever_the_name(self):
		author = Author.objects.create(name="Ashish Vaswani", orcid="0000-0001-2345-6789")

		self.assertEqual(Author.objects.find_or_create("A. Vaswani", "0000-0001-2345-6789"), author)

	def test_finds_an_author_by_name_without_an_orcid(self):
		author = Author.objects.create(name="Noam Shazeer")

		self.assertEqual(Author.objects.find_or_create("Noam Shazeer"), author)

	def test_creates_an_author_it_cannot_find(self):
		author = Author.objects.find_or_create("Niki Parmar", "0000-0002-0000-0000")

		self.assertEqual((author.name, author.orcid), ("Niki Parmar", "0000-0002-0000-0000"))
		self.assertEqual(Author.objects.count(), 1)


class PaperQuerySetTests(TestCase):

	def test_matching_finds_a_paper_by_source_id_or_doi(self):
		by_id = create_paper("1706.03762")
		by_doi = Paper.objects.create(
			source=PaperSource.OPENALEX, external_id="W1", title="BERT", url="https://openalex.org/W1",
			doi="10.1000/bert",
		)
		create_paper("unrelated")

		matches = Paper.objects.matching(PaperSource.ARXIV, "1706.03762", "10.1000/bert")

		self.assertQuerySetEqual(matches, [by_id, by_doi], ordered=False)

	def test_matching_without_a_doi_uses_the_source_id_only(self):
		paper = create_paper("1706.03762")
		Paper.objects.create(
			source=PaperSource.OPENALEX, external_id="1706.03762", title="Same ID, other source",
			url="https://openalex.org/W1",
		)

		self.assertQuerySetEqual(Paper.objects.matching(PaperSource.ARXIV, "1706.03762", None), [paper])

	def test_pending_excludes_ingested_and_failed_papers(self):
		pending = create_paper("1")
		create_paper("2", ingested_at=timezone.now())
		create_paper("3", ingestion_failed_at=timezone.now())

		self.assertQuerySetEqual(Paper.objects.pending(), [pending])


class ChunkQuerySetTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		cls.paper = create_paper("1706.03762")
		cls.heading_match = Chunk.objects.create(
			paper=cls.paper, heading="Scaled Dot-Product Attention", text="We compute queries and keys.",
			start_page=3, end_page=3, chunk_index=0,
		)
		cls.body_match = Chunk.objects.create(
			paper=cls.paper, heading="Training", text="Dropout is applied to the attention weights.",
			start_page=7, end_page=7, chunk_index=1,
		)
		cls.no_match = Chunk.objects.create(
			paper=cls.paper, heading="Results", text="BLEU scores on WMT 2014.", start_page=8, end_page=8,
			chunk_index=2,
		)

	def test_search_returns_matching_chunks_with_heading_matches_ranked_first(self):
		results = list(Chunk.objects.search("attention"))

		self.assertEqual(results, [self.heading_match, self.body_match])
		self.assertGreater(results[0].rank, results[1].rank)

	def test_search_matches_word_forms(self):
		self.assertEqual(list(Chunk.objects.search("applying dropouts")), [self.body_match])

	def test_search_accepts_websearch_syntax(self):
		self.assertEqual(list(Chunk.objects.search('"BLEU scores" -attention')), [self.no_match])

	def test_search_returns_nothing_for_stop_words_only(self):
		self.assertEqual(list(Chunk.objects.search("the and of")), [])

	def test_search_chains_after_other_filters(self):
		other_paper = create_paper("1810.04805")
		Chunk.objects.create(
			paper=other_paper, heading="Attention", text="Self-attention.", start_page=1, end_page=1, chunk_index=0,
		)

		results = Chunk.objects.filter(paper=self.paper).search("attention")

		self.assertEqual(list(results), [self.heading_match, self.body_match])
