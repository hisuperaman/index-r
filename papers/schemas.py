from pydantic import BaseModel, Field


class SearchQueries(BaseModel):
	"""Keyword queries the LLM wrote for one research question."""
	queries: list[str] = Field(min_length=3, max_length=5, description="Short keyword queries for full-text search")


class GroundedAnswer(BaseModel):
	"""An answer the LLM wrote from numbered passages."""
	content: str = Field(description="The answer, citing passages inline as [n] with the passage numbers given")
	is_insufficient_context: bool = Field(
		default=False, description="True only if the passages do not contain enough to answer",
	)
