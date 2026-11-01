import uuid

from django.test import SimpleTestCase

from server.renderers import EventStreamRenderer


class EventStreamRendererTests(SimpleTestCase):

	def test_renders_data_as_json(self):
		value = uuid.uuid4()

		self.assertEqual(
			EventStreamRenderer().render({"detail": "Bad", "id": value}),
			f'{{"detail": "Bad", "id": "{value}"}}'.encode(),
		)
