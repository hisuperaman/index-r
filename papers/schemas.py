from pydantic import BaseModel, Field


class SearchQueries(BaseModel):
	"""Keyword queries the LLM wrote for one research question."""
	queries: list[str] = Field(min_length=3, max_length=5, description="Short keyword queries for full-text search")
