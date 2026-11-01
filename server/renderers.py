import json

from rest_framework.renderers import BaseRenderer
from rest_framework.utils.encoders import JSONEncoder


class EventStreamRenderer(BaseRenderer):
	"""Accepts `text/event-stream` requests, rendering any non-streamed response (such as an error) as JSON."""
	media_type = 'text/event-stream'
	format = 'event-stream'

	def render(self, data, accepted_media_type=None, renderer_context=None) -> bytes:
		return json.dumps(data, cls=JSONEncoder).encode()
