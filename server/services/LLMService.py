from functools import cache

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from pydantic_ai import Agent


class LLMService:
	"""Runs prompts against the model named by the LLM setting."""

	@classmethod
	def run[T](cls, prompt: str, output_type: type[T], instructions: str) -> T:
		"""Sends `prompt` to the configured model and returns its validated output."""
		if not settings.LLM:
			raise ImproperlyConfigured("Set LLM to '<provider>:<model>', e.g. 'anthropic:claude-sonnet-5-5'.")
		return cls.get_agent(settings.LLM, output_type, instructions).run_sync(prompt).output

	@staticmethod
	@cache
	def get_agent[T](model: str, output_type: type[T], instructions: str) -> Agent[object, str]:
		"""Returns the agent for this model, output type and instructions, building it once."""
		return Agent(model, output_type=output_type, instructions=instructions)
