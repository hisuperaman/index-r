from datetime import date

from django.test import TestCase
from django.utils import timezone

from enums.Paper import DatePrecision, PaperSource
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

	def test_search_matches_any_of_several_queries(self):
		self.assertEqual(list(Chunk.objects.search("dropout", "BLEU")), [self.body_match, self.no_match])

	def test_search_without_queries_returns_nothing(self):
		self.assertEqual(list(Chunk.objects.search()), [])

	def test_search_returns_nothing_for_stop_words_only(self):
		self.assertEqual(list(Chunk.objects.search("the and of")), [])

	def test_search_chains_after_other_filters(self):
		other_paper = create_paper("1810.04805")
		Chunk.objects.create(
			paper=other_paper, heading="Attention", text="Self-attention.", start_page=1, end_page=1, chunk_index=0,
		)

		results = Chunk.objects.filter(paper=self.paper).search("attention")

		self.assertEqual(list(results), [self.heading_match, self.body_match])


def published(year: int) -> dict:
	return {"publication_date": date(year, 1, 1), "publication_date_precision": DatePrecision.YEAR}


class ChunkSearchBoostTests(TestCase):
	this_year = timezone.now().year

	def add_chunk(self, external_id: str, **paper_fields) -> Chunk:
		paper = create_paper(external_id, **paper_fields)
		return Chunk.objects.create(
			paper=paper, heading="Attention", text="Multi-head attention.", start_page=1, end_page=1, chunk_index=0,
		)

	def boost(self, chunk: Chunk) -> float:
		result = Chunk.objects.filter(pk=chunk.pk).search("attention").get()
		return result.score / result.rank

	def test_an_undated_uncited_paper_is_not_boosted(self):
		self.assertAlmostEqual(self.boost(self.add_chunk("1")), 1.0, places=5)

	def test_citations_boost_by_a_tenth_per_power_of_ten(self):
		self.assertAlmostEqual(self.boost(self.add_chunk("1", citation_count=999)), 1.3, places=5)

	def test_recency_boost_falls_from_a_fifth_to_nothing_over_five_years(self):
		self.assertAlmostEqual(self.boost(self.add_chunk("1", **published(self.this_year))), 1.2, places=5)
		self.assertAlmostEqual(self.boost(self.add_chunk("2", **published(self.this_year - 3))), 1.08, places=5)
		self.assertAlmostEqual(self.boost(self.add_chunk("3", **published(self.this_year - 5))), 1.0, places=5)
		self.assertAlmostEqual(self.boost(self.add_chunk("4", **published(self.this_year - 20))), 1.0, places=5)

	def test_a_paper_dated_in_the_future_gets_the_full_recency_boost(self):
		self.assertAlmostEqual(self.boost(self.add_chunk("1", **published(self.this_year + 1))), 1.2, places=5)

	def test_boosts_multiply(self):
		chunk = self.add_chunk("1", citation_count=999, **published(self.this_year))

		self.assertAlmostEqual(self.boost(chunk), 1.3 * 1.2, places=5)

	def test_an_equally_matching_cited_recent_paper_ranks_first(self):
		old = self.add_chunk("1", citation_count=0, **published(2000))
		new = self.add_chunk("2", citation_count=500, **published(self.this_year))

		self.assertEqual(list(Chunk.objects.search("attention")), [new, old])


class ChunkFilterPapersTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		def add(external_id, **fields):
			paper = create_paper(external_id, **fields)
			return Chunk.objects.create(paper=paper, text="Attention.", start_page=1, end_page=1, chunk_index=0)

		cls.neurips_2017 = add("1", venue="NeurIPS 2017", citation_count=100, **published(2017))
		cls.acl_2019 = add("2", venue="ACL", citation_count=10, **published(2019))
		cls.undated = add("3")

	def filtered(self, **filters) -> list[Chunk]:
		return list(Chunk.objects.filter_papers(**filters).order_by("paper__external_id"))

	def test_no_filters_keeps_everything(self):
		self.assertEqual(self.filtered(), [self.neurips_2017, self.acl_2019, self.undated])

	def test_year_range_is_inclusive_and_drops_undated_papers(self):
		self.assertEqual(self.filtered(year_from=2017, year_to=2017), [self.neurips_2017])
		self.assertEqual(self.filtered(year_from=2018), [self.acl_2019])
		self.assertEqual(self.filtered(year_to=2019), [self.neurips_2017, self.acl_2019])

	def test_venue_matches_part_of_the_name_in_any_case(self):
		self.assertEqual(self.filtered(venue="neurips"), [self.neurips_2017])

	def test_min_citations_is_inclusive_and_drops_unknown_counts(self):
		self.assertEqual(self.filtered(min_citations=10), [self.neurips_2017, self.acl_2019])
		self.assertEqual(self.filtered(min_citations=11), [self.neurips_2017])
