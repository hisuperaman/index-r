import os
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase
from pydantic import BaseModel
from pydantic_ai.exceptions import UserError

from server.services import LLMService


class Queries(BaseModel):
	queries: list[str]


class LLMServiceTests(SimpleTestCase):

	def test_returns_the_output_as_the_requested_type(self):
		with self.settings(LLM='test'):
			output = LLMService.run("Expand: MMLU F1", Queries, "Return keyword queries.")

		self.assertIsInstance(output, Queries)

	def test_streams_ending_with_the_complete_output(self):
		with self.settings(LLM='test'):
			outputs = list(LLMService.stream("Expand: MMLU F1", Queries, "Return keyword queries."))

		self.assertIsInstance(outputs[-1], Queries)

	def test_streaming_without_a_model_is_a_configuration_error(self):
		with self.settings(LLM=None), self.assertRaises(ImproperlyConfigured):
			list(LLMService.stream("Expand: MMLU F1", Queries, "Return keyword queries."))

	def test_reuses_the_agent_for_the_same_model_and_instructions(self):
		first = LLMService.get_agent('test', Queries, "Return keyword queries.")

		self.assertIs(LLMService.get_agent('test', Queries, "Return keyword queries."), first)
		self.assertIsNot(LLMService.get_agent('test', Queries, "Other instructions."), first)

	def test_an_unset_model_is_a_configuration_error(self):
		with self.settings(LLM=None), self.assertRaises(ImproperlyConfigured):
			LLMService.run("Expand: MMLU F1", Queries, "Return keyword queries.")

	def test_a_missing_provider_key_names_the_variable_to_set(self):
		environ = {key: value for key, value in os.environ.items() if key != 'ANTHROPIC_API_KEY'}

		with (
			self.settings(LLM='anthropic:claude-haiku-5-5'),
			patch.dict(os.environ, environ, clear=True),
			self.assertRaisesMessage(UserError, 'ANTHROPIC_API_KEY'),
		):
			LLMService.run("Expand: MMLU F1", Queries, "Return keyword queries.")
