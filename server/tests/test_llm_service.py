import os
from types import SimpleNamespace
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase
from pydantic import BaseModel
from pydantic_ai.exceptions import ModelHTTPError, UserError

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


class FlakyAgent:
	"""Fails with the given errors before succeeding."""

	def __init__(self, *errors: Exception, output=None):
		self.errors = list(errors)
		self.output = output
		self.calls = 0

	def run_sync(self, prompt):
		self.calls += 1
		if self.errors:
			raise self.errors.pop(0)
		return SimpleNamespace(output=self.output)

	def run_stream_sync(self, prompt):
		self.calls += 1
		error = self.errors.pop(0) if self.errors else None

		def outputs():
			if error:
				raise error
			yield self.output

		return SimpleNamespace(stream_output=outputs)


class LLMServiceRetryTests(SimpleTestCase):
	OUTPUT = Queries(queries=["a", "b", "c"])

	def call(self, agent: FlakyAgent, method: str = "run"):
		with (
			patch.object(LLMService, "get_configured_agent", return_value=agent),
			patch("server.services.LLMService.time.sleep") as sleep,
		):
			result = LLMService.run("Q", Queries, "I") if method == "run" else list(LLMService.stream("Q", Queries, "I"))
		return result, sleep

	def test_retries_while_the_model_is_overloaded(self):
		agent = FlakyAgent(ModelHTTPError(503, "m"), ModelHTTPError(429, "m"), output=self.OUTPUT)

		result, sleep = self.call(agent)

		self.assertEqual((result, agent.calls), (self.OUTPUT, 3))
		self.assertEqual([call.args[0] for call in sleep.call_args_list], [2.0, 4.0])

	def test_gives_up_after_the_last_retry(self):
		agent = FlakyAgent(*[ModelHTTPError(503, "m")] * 3)

		with self.assertRaises(ModelHTTPError):
			self.call(agent)
		self.assertEqual(agent.calls, 3)

	def test_does_not_retry_a_client_error(self):
		agent = FlakyAgent(ModelHTTPError(401, "m"), output=self.OUTPUT)

		with self.assertRaises(ModelHTTPError):
			self.call(agent)
		self.assertEqual(agent.calls, 1)

	def test_retries_a_stream_that_failed_before_any_output(self):
		agent = FlakyAgent(ModelHTTPError(503, "m"), output=self.OUTPUT)

		result, _ = self.call(agent, "stream")

		self.assertEqual((result, agent.calls), ([self.OUTPUT], 2))

	def test_does_not_retry_a_stream_that_already_produced_output(self):
		class BreaksMidStream(FlakyAgent):
			def run_stream_sync(self, prompt):
				self.calls += 1

				def outputs():
					yield Queries(queries=["a", "b", "c"])
					raise ModelHTTPError(503, "m")

				return SimpleNamespace(stream_output=outputs)

		agent = BreaksMidStream()

		with self.assertRaises(ModelHTTPError):
			self.call(agent, "stream")
		self.assertEqual(agent.calls, 1)
