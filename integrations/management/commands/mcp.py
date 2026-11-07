import os
from functools import partial
from urllib.parse import urlparse

import anyio
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from mcp.server.transport_security import TransportSecuritySettings

from integrations.mcp_server import LocalUser, build_server
from integrations.models import ApiToken

TOKEN_VARIABLE = "INDEXR_ACCESS_TOKEN"


class Command(BaseCommand):
	help = "Runs the IndexR MCP server: locally over stdio by default, or over HTTP with --http."

	def add_arguments(self, parser):
		parser.add_argument("--http", action="store_true", help="Serve over streamable HTTP for remote clients.")

	def handle(self, *args, http=False, **options):
		if http:
			return self.serve_http()

		token = ApiToken.objects.authenticate(os.environ.get(TOKEN_VARIABLE, ""))
		if token is None:
			raise CommandError(f"Set {TOKEN_VARIABLE} to an access token from Settings → Integrations.")
		LocalUser.user_id = token.user_id
		build_server().run(transport="stdio")

	def serve_http(self):
		public = urlparse(settings.MCP_PUBLIC_URL)
		local = f"{settings.MCP_HOST}:{settings.MCP_PORT}"
		security = TransportSecuritySettings(
			enable_dns_rebinding_protection=True,
			allowed_hosts=[public.netloc, local, f"localhost:{settings.MCP_PORT}"],
			allowed_origins=[f"{public.scheme}://{public.netloc}"],
		)
		self.stderr.write(f"IndexR MCP server on http://{local}{public.path or '/mcp'} (public URL {settings.MCP_PUBLIC_URL})")
		anyio.run(partial(
			build_server(http=True).run_streamable_http_async,
			host=settings.MCP_HOST, port=settings.MCP_PORT, streamable_http_path=public.path or "/mcp",
			transport_security=security,
		))
