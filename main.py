"""
arxiv_bm25_search.py

Take a natural-language question, search arXiv for relevant papers,
download the PDFs, extract their text with PyMuPDF, chunk it, rank the
chunks against the question with BM25, and print the best-matching
passages.

Usage:
    python arxiv_bm25_search.py "How does rotary positional embedding work?"
    python arxiv_bm25_search.py "diffusion model guidance" --max-results 6 --top-k 8

Dependencies (install with pip):
    pip install requests pymupdf rank_bm25 --break-system-packages
"""

import argparse
import re
import sys
import tempfile
import urllib.parse
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

import pymupdf
import requests
from rank_bm25 import BM25Okapi


@dataclass
class Paper:
	title: str
	arxiv_id: str
	pdf_url: str
	pdf_path: Path = None
	text: str = ""


@dataclass
class Chunk:
	text: str
	paper_title: str
	arxiv_id: str
	chunk_index: int
	page_number: int
	tokens: list = field(default_factory=list)


class ArxivBM25Search:
	"""
	Pipeline: question -> arXiv search -> download PDFs -> extract text
	-> chunk -> BM25 rank -> print top chunks.

	Every step is a static/class method so the pipeline can be reused,
	tested, or reordered without needing an instance.
	"""

	ARXIV_API_URL = "http://export.arxiv.org/api/query"
	ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}
	REQUEST_TIMEOUT = 30

	# ---------------------------------------------------------------- #
	# Step 1: search
	# ---------------------------------------------------------------- #
	@classmethod
	def search_arxiv(cls, question: str, max_results: int) -> list[Paper]:
		"""Query the arXiv API and return a list of Paper objects (metadata only)."""
		print(f"[1/5] Searching arXiv for: {question!r}")
		params = {
			"search_query": f"all:{question}",
			"start": 0,
			"max_results": max_results,
			"sortBy": "relevance",
			"sortOrder": "descending",
		}
		url = f"{cls.ARXIV_API_URL}?{urllib.parse.urlencode(params)}"

		try:
			resp = requests.get(url, timeout=cls.REQUEST_TIMEOUT)
			resp.raise_for_status()
		except requests.RequestException as e:
			print(f"    ERROR: failed to reach arXiv API: {e}", file=sys.stderr)
			return []

		root = ET.fromstring(resp.content)
		papers = []
		for entry in root.findall("atom:entry", cls.ATOM_NS):
			title_el = entry.find("atom:title", cls.ATOM_NS)
			id_el = entry.find("atom:id", cls.ATOM_NS)
			if title_el is None or id_el is None:
				continue

			title = " ".join(title_el.text.split())
			arxiv_id = id_el.text.strip().rsplit("/", 1)[-1]

			pdf_url = None
			for link in entry.findall("atom:link", cls.ATOM_NS):
				if link.attrib.get("title") == "pdf" or link.attrib.get("type") == "application/pdf":
					pdf_url = link.attrib.get("href")
					break
			if pdf_url is None:
				pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

			papers.append(Paper(title=title, arxiv_id=arxiv_id, pdf_url=pdf_url))

		print(f"    Found {len(papers)} paper(s).")
		return papers

	# ---------------------------------------------------------------- #
	# Step 2: download
	# ---------------------------------------------------------------- #
	@classmethod
	def download_pdfs(cls, papers: list[Paper], out_dir: Path) -> list[Paper]:
		"""Download each paper's PDF. Returns only papers that downloaded successfully."""
		print(f"[2/5] Downloading {len(papers)} PDF(s)...")
		ok_papers = []
		for i, paper in enumerate(papers, 1):
			dest = out_dir / f"{paper.arxiv_id}.pdf"
			try:
				resp = requests.get(paper.pdf_url, timeout=cls.REQUEST_TIMEOUT)
				resp.raise_for_status()
				dest.write_bytes(resp.content)
				paper.pdf_path = dest
				ok_papers.append(paper)
				print(f"    ({i}/{len(papers)}) OK  - {paper.title[:70]}")
			except requests.RequestException as e:
				print(f"    ({i}/{len(papers)}) FAIL - {paper.title[:70]} ({e})")
		return ok_papers

	# ---------------------------------------------------------------- #
	# Step 3: extract text (PyMuPDF)
	# ---------------------------------------------------------------- #
	@staticmethod
	def extract_pdf_text(pdf_path: Path) -> str:
		"""Extract and normalize all text from a single PDF using PyMuPDF."""
		with pymupdf.open(pdf_path) as doc:
			pages_text = [page.get_text() for page in doc]
		full_text = "\n".join(pages_text)
		return re.sub(r"\s+", " ", full_text).strip()

	@classmethod
	def extract_text(cls, papers: list[Paper]) -> list[Paper]:
		"""Extract raw text from each downloaded PDF. Drops papers that fail to parse."""
		print("[3/5] Extracting text from PDFs (PyMuPDF)...")
		ok_papers = []
		for paper in papers:
			try:
				full_text = cls.extract_pdf_text(paper.pdf_path)
				if len(full_text) < 200:
					print(f"    WARN: near-empty text extracted for {paper.title[:60]}")
					continue
				paper.text = full_text
				ok_papers.append(paper)
			except Exception as e:
				print(f"    FAIL: could not extract text for {paper.title[:60]} ({e})")
		print(f"    Extracted text from {len(ok_papers)}/{len(papers)} paper(s).")
		return ok_papers

	# ---------------------------------------------------------------- #
	# Step 4: chunk
	# ---------------------------------------------------------------- #
	@staticmethod
	def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
		"""Split text into overlapping chunks of `chunk_size` words."""
		words = text.split()
		if not words:
			return []
		step = max(chunk_size - overlap, 1)
		chunks = []
		for start in range(0, len(words), step):
			piece = words[start:start + chunk_size]
			if not piece:
				break
			chunks.append(" ".join(piece))
			if start + chunk_size >= len(words):
				break
		return chunks

	@classmethod
	def build_chunks(cls, papers: list[Paper], chunk_size: int, overlap: int) -> list[Chunk]:
		print(f"[4/5] Chunking text (size={chunk_size} words, overlap={overlap} words)...")
		all_chunks = []
		for paper in papers:
			pieces = cls.chunk_text(paper.text, chunk_size, overlap)
			for idx, piece in enumerate(pieces):
				all_chunks.append(
					Chunk(text=piece, paper_title=paper.title, arxiv_id=paper.arxiv_id, chunk_index=idx)
				)
		print(f"    Produced {len(all_chunks)} chunk(s) from {len(papers)} paper(s).")
		return all_chunks

	# ---------------------------------------------------------------- #
	# Step 5: rank with BM25
	# ---------------------------------------------------------------- #
	@staticmethod
	def tokenize(text: str) -> list[str]:
		return re.findall(r"[a-z0-9]+", text.lower())

	@classmethod
	def rank_chunks(cls, question: str, chunks: list[Chunk], top_k: int) -> list[tuple[float, Chunk]]:
		print("[5/5] Ranking chunks with BM25...")
		for c in chunks:
			c.tokens = cls.tokenize(c.text)

		corpus = [c.tokens for c in chunks]
		bm25 = BM25Okapi(corpus)
		query_tokens = cls.tokenize(question)
		scores = bm25.get_scores(query_tokens)

		ranked = sorted(zip(scores, chunks), key=lambda x: x[0], reverse=True)
		return ranked[:top_k]

	# ---------------------------------------------------------------- #
	# Output
	# ---------------------------------------------------------------- #
	@staticmethod
	def print_results(question: str, ranked: list[tuple[float, Chunk]]) -> None:
		print("\n" + "=" * 80)
		print(f"TOP MATCHES FOR: {question!r}")
		print("=" * 80)
		if not ranked:
			print("No results to show.")
			return
		for rank, (score, chunk) in enumerate(ranked, 1):
			print(f"\n#{rank}  score={score:.3f}  paper=\"{chunk.paper_title}\" "
				  f"(arXiv:{chunk.arxiv_id})  chunk={chunk.chunk_index}")
			print("-" * 80)
			snippet = chunk.text
			if len(snippet) > 800:
				snippet = snippet[:800].rsplit(" ", 1)[0] + " [...]"
			print(snippet)
		print("\n" + "=" * 80)

	# ---------------------------------------------------------------- #
	# Orchestration
	# ---------------------------------------------------------------- #
	@classmethod
	def run(
			cls,
			question: str,
			max_results: int = 8,
			top_k: int = 10,
			chunk_size: int = 200,
			chunk_overlap: int = 50,
	) -> list[tuple[float, Chunk]]:
		"""Run the full pipeline end to end and print the results."""
		papers = cls.search_arxiv(question, max_results)
		if not papers:
			print("No papers found or arXiv API unreachable. Exiting.")
			return []

		with tempfile.TemporaryDirectory(prefix="arxiv_pdfs_") as tmp_dir:
			tmp_path = Path(tmp_dir)

			papers = cls.download_pdfs(papers, tmp_path)
			if not papers:
				print("No PDFs could be downloaded. Exiting.")
				return []

			papers = cls.extract_text(papers)
			if not papers:
				print("No text could be extracted from any PDF. Exiting.")
				return []

			chunks = cls.build_chunks(papers, chunk_size, chunk_overlap)
			if not chunks:
				print("No chunks produced. Exiting.")
				return []

			ranked = cls.rank_chunks(question, chunks, top_k)
			cls.print_results(question, ranked)
			return ranked


def main():
	parser = argparse.ArgumentParser(
		description="Search arXiv, extract PDF text, and rank passages against a question using BM25."
	)
	parser.add_argument("question", help="Your natural-language question / search query.")
	parser.add_argument("--max-results", type=int, default=8,
						help="Number of arXiv papers to fetch (default: 8).")
	parser.add_argument("--top-k", type=int, default=10,
						help="Number of top chunks to print (default: 10).")
	parser.add_argument("--chunk-size", type=int, default=200,
						help="Chunk size in words (default: 200).")
	parser.add_argument("--chunk-overlap", type=int, default=50,
						help="Overlap between chunks in words (default: 50).")
	args = parser.parse_args()

	if not (1 <= args.max_results <= 20):
		parser.error("--max-results must be between 1 and 20 (be polite to arXiv's API).")

	ArxivBM25Search.run(
		question=args.question,
		max_results=args.max_results,
		top_k=args.top_k,
		chunk_size=args.chunk_size,
		chunk_overlap=args.chunk_overlap,
	)


if __name__ == "__main__":
	main()
