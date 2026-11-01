import time
from collections.abc import Iterator
from functools import cache

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from pydantic_ai import Agent
from pydantic_ai.exceptions import ModelHTTPError, ModelUnavailableError


class LLMService:
	"""Runs prompts against the model named by the LLM setting."""

	RETRIES = 2
	RETRY_SECONDS = 2.0

	@classmethod
	def run[T](cls, prompt: str, output_type: type[T], instructions: str) -> T:
		"""Sends `prompt` to the configured model and returns its validated output."""
		for attempt in range(cls.RETRIES + 1):
			try:
				return cls.get_configured_agent(output_type, instructions).run_sync(prompt).output
			except Exception as error:
				if not cls.should_retry(error, attempt):
					raise
				time.sleep(cls.RETRY_SECONDS * (attempt + 1))

	@classmethod
	def stream[T](cls, prompt: str, output_type: type[T], instructions: str) -> Iterator[T]:
		"""Sends `prompt` to the configured model and yields its output as it grows, ending with the complete one."""
		for attempt in range(cls.RETRIES + 1):
			started = False
			try:
				for output in cls.get_configured_agent(output_type, instructions).run_stream_sync(prompt).stream_output():
					started = True
					yield output
				return
			except Exception as error:
				if started or not cls.should_retry(error, attempt):
					raise
				time.sleep(cls.RETRY_SECONDS * (attempt + 1))

	@classmethod
	def should_retry(cls, error: Exception, attempt: int) -> bool:
		"""Whether `error` is a temporary model outage worth another attempt."""
		if attempt >= cls.RETRIES:
			return False
		if isinstance(error, ModelUnavailableError):
			return True
		return isinstance(error, ModelHTTPError) and (error.status_code == 429 or error.status_code >= 500)

	@classmethod
	def get_configured_agent[T](cls, output_type: type[T], instructions: str) -> Agent[None, T]:
		"""Returns the agent for the LLM setting, raising if it is unset."""
		if not settings.LLM:
			raise ImproperlyConfigured("Set LLM to '<provider>:<model>', e.g. 'anthropic:claude-sonnet-5-5'.")
		return cls.get_agent(settings.LLM, output_type, instructions)

	@staticmethod
	@cache
	def get_agent[T](model: str, output_type: type[T], instructions: str) -> Agent[None, T]:
		"""Returns the agent for this model, output type and instructions, building it once."""
		return Agent(model, output_type=output_type, instructions=instructions)
