import logging
from collections.abc import Callable
from typing import Annotated, Any
from urllib.parse import urlparse

from asgiref.sync import sync_to_async
from django.conf import settings
from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.auth.provider import AccessToken
from mcp.server.auth.settings import AuthSettings
from mcp.server.mcpserver import Context, MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import Field

from integrations.exceptions import ToolInputError
from integrations.models import ApiToken
from integrations.services import ResearchToolsService
from enums.Workspace import AskStage
from workspaces.services import AskDone, AskService, AskStatus

logger = logging.getLogger(__name__)

INSTRUCTIONS = (
	"IndexR finds research papers and answers questions with citations to the exact section and page. "
	"Use search_papers to find passages. To get a written, cited answer, pick a workspace with list_workspaces "
	"(or make one with create_workspace) and call ask; it can take a minute when new papers have to be found. "
	"Each workspace keeps its questions, answers and papers together."
)
ANSWER_FAILED = "Something went wrong while generating the answer. Please try again."
ASK_STEPS = len(AskStage)


class ApiTokenVerifier:
	"""Accepts IndexR personal access tokens as bearer tokens."""

	async def verify_token(self, token: str) -> AccessToken | None:
		api_token = await sync_to_async(ApiToken.objects.authenticate)(token)
		if api_token is None:
			return None
		return AccessToken(token=token, client_id=str(api_token.pk), scopes=[], subject=str(api_token.user_id))


class LocalUser:
	"""The user a local (stdio) server acts as, set when it starts."""
	user_id: int | None = None


def current_user_id() -> int:
	"""The IndexR user behind the current call."""
	access = get_access_token()
	if access is not None and access.subject:
		return int(access.subject)
	if LocalUser.user_id is not None:
		return LocalUser.user_id
	raise ToolError("Not signed in. Connect with an IndexR access token.")


async def run(function: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
	"""Runs a tool's service method as the current user, turning input problems into tool errors."""
	try:
		return await sync_to_async(function)(current_user_id(), *args, **kwargs)
	except ToolInputError as error:
		raise ToolError(str(error)) from error


def register_tools(server: MCPServer) -> None:
	@server.tool(description=(
			"Search passages in research papers (the shared corpus plus the user's own uploads). "
			"Returns the best-matching passages with their paper, section and page, best first."
	))
	async def search_papers(
			query: Annotated[str, Field(description="Keywords, e.g. 'sparse attention long documents'")],
			year_from: Annotated[int | None, Field(description="Earliest publication year")] = None,
			year_to: Annotated[int | None, Field(description="Latest publication year")] = None,
			venue: Annotated[str | None, Field(description="Part of a venue name, e.g. 'NeurIPS'")] = None,
			min_citations: Annotated[int | None, Field(description="Minimum citation count")] = None,
			limit: Annotated[int, Field(ge=1, le=25, description="How many passages to return")] = 10,
	) -> list[dict[str, Any]]:
		return await run(
			ResearchToolsService.search_papers, query, year_from=year_from, year_to=year_to, venue=venue,
			min_citations=min_citations, limit=limit,
		)

	@server.tool(description="List the user's workspaces, most recently active first, with paper and question counts.")
	async def list_workspaces(
			search: Annotated[str | None, Field(description="Only workspaces whose name contains this")] = None,
	) -> list[dict[str, Any]]:
		return await run(ResearchToolsService.list_workspaces, search=search)

	@server.tool(description="Create a workspace for a research topic. Returns the new workspace with its ID.")
	async def create_workspace(name: Annotated[str, Field(description="The research topic")]) -> dict[str, Any]:
		return await run(ResearchToolsService.create_workspace, name)

	@server.tool(description="List the papers in one of the user's workspaces.")
	async def list_workspace_papers(workspace_id: Annotated[str, Field(description="Workspace ID")]) -> list[dict[str, Any]]:
		return await run(ResearchToolsService.list_workspace_papers, workspace_id)

	@server.tool(description="Get a paper's details: title, authors, venue, year, citation count and links.")
	async def get_paper(paper_id: Annotated[str, Field(description="Paper ID")]) -> dict[str, Any]:
		return await run(ResearchToolsService.get_paper, paper_id)

	@server.tool(description="Add a paper to one of the user's workspaces.")
	async def add_paper_to_workspace(
			workspace_id: Annotated[str, Field(description="Workspace ID")],
			paper_id: Annotated[str, Field(description="Paper ID, e.g. from search_papers")],
	) -> dict[str, Any]:
		return await run(ResearchToolsService.add_paper_to_workspace, workspace_id, paper_id)

	@server.tool(description="Remove a paper from one of the user's workspaces. The paper itself isn't deleted.")
	async def remove_paper_from_workspace(
			workspace_id: Annotated[str, Field(description="Workspace ID")],
			paper_id: Annotated[str, Field(description="Paper ID")],
	) -> dict[str, Any]:
		return await run(ResearchToolsService.remove_paper_from_workspace, workspace_id, paper_id)

	@server.tool(description=(
			"Ask a research question in one of the user's workspaces. IndexR finds the relevant papers (searching for "
			"new ones when needed) and returns an answer whose [n] markers map to the cited passages. The question and "
			"answer are saved to the workspace's chat. Can take up to a minute or two."
	))
	async def ask(
			workspace_id: Annotated[str, Field(description="Workspace ID, from list_workspaces or create_workspace")],
			question: Annotated[str, Field(description="The research question")],
			ctx: Context,
	) -> dict[str, Any]:
		message = await run(ResearchToolsService.start_question, workspace_id, question)
		events = iter(AskService.ask(message))
		step = 0
		answer = None
		try:
			while (event := await sync_to_async(next)(events, None)) is not None:
				if isinstance(event, AskStatus):
					step += 1
					await ctx.report_progress(step, ASK_STEPS, event.stage.label)
				elif isinstance(event, AskDone):
					answer = event.message
		except Exception as error:
			logger.exception("MCP ask failed for message %s", message.pk)
			raise ToolError(ANSWER_FAILED) from error
		if answer is None:
			raise ToolError(ANSWER_FAILED)
		return await sync_to_async(ResearchToolsService.answer)(answer.pk)


def build_server(http: bool = False) -> MCPServer:
	"""The IndexR MCP server; over HTTP it requires an IndexR access token."""
	auth = None
	if http:
		parsed = urlparse(settings.MCP_PUBLIC_URL)
		auth = AuthSettings(issuer_url=f"{parsed.scheme}://{parsed.netloc}", resource_server_url=settings.MCP_PUBLIC_URL)
	server = MCPServer(
		name="IndexR",
		instructions=INSTRUCTIONS,
		token_verifier=ApiTokenVerifier() if http else None,
		auth=auth,
	)
	register_tools(server)
	return server
