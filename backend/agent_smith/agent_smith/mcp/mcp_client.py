"""Connect to an MCP server, discover its capabilities, and call them."""

import json
import os
import shlex
from collections.abc import AsyncIterator, Awaitable, Callable, Mapping
from contextlib import asynccontextmanager
from datetime import timedelta
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client
from agent_smith.models.sandbox import SandboxTool


@asynccontextmanager
async def connect_mcp(
    stdio: str | None = None,
    url: str | None = None,
    environment: Mapping[str, str] | None = None,
    read_timeout_seconds: float = 120,
) -> AsyncIterator["MCPConnection | None"]:
    """Open one stdio or HTTP MCP connection and close it on context exit."""
    if stdio and url:
        raise ValueError("Choose either stdio or HTTP")
    if not stdio and not url:
        yield None
        return
    if stdio:
        command = shlex.split(stdio)
        transport = stdio_client(
            StdioServerParameters(
                command=command[0],
                args=command[1:],
                env={**os.environ, **(environment or {})},
            )
        )
    else:
        if url is None:
            raise ValueError("An MCP server URL is required")
        transport = streamable_http_client(url)
    async with transport as streams:
        # The SDK owns the MCP wire format on both streams.
        async with ClientSession(
            streams[0],
            streams[1],
            read_timeout_seconds=timedelta(seconds=read_timeout_seconds),
        ) as session:
            info = await session.initialize()
            connection = MCPConnection(session)
            await connection.discover(info.capabilities)
            yield connection


class MCPConnection:
    def __init__(self, session: ClientSession) -> None:
        self.session = session
        self.tools: list[SandboxTool] = []
        self.resources: list[Any] = []
        self.prompts: list[Any] = []
        self.templates: list[Any] = []

    async def pages(
        self, method: Callable[..., Awaitable[Any]], field: str
    ) -> list[Any]:
        """Read every page returned by an MCP list operation."""
        items, cursor = [], None
        while True:
            page = await method(cursor=cursor)
            items.extend(getattr(page, field))
            cursor = page.nextCursor
            if not cursor:
                return items

    async def discover(self, capabilities: Any) -> None:
        if capabilities.tools:
            tools = await self.pages(self.session.list_tools, "tools")
            self.tools = [
                SandboxTool(
                    name=t.name,
                    description=t.description or "",
                    input_schema=t.inputSchema,
                )
                for t in tools
            ]
        if capabilities.resources:
            self.resources = await self.pages(self.session.list_resources, "resources")
            self.templates = await self.pages(
                self.session.list_resource_templates, "resourceTemplates"
            )
            self.tools.append(
                SandboxTool(
                    name="mcp_read_resource",
                    description="Read a resource URI.",
                    input_schema={
                        "type": "object",
                        "properties": {"uri": {"type": "string"}},
                        "required": ["uri"],
                    },
                )
            )
        if capabilities.prompts:
            self.prompts = await self.pages(self.session.list_prompts, "prompts")
            self.tools.append(
                SandboxTool(
                    name="mcp_get_prompt",
                    description="Get an MCP prompt.",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "arguments": {"type": "object"},
                        },
                        "required": ["name"],
                    },
                )
            )

    async def call(self, name: str, arguments: Mapping[str, Any]) -> Any:
        """Call a tool, resource, or prompt and return plain Python data."""
        if name == "mcp_read_resource":
            result = await self.session.read_resource(arguments["uri"])
        elif name == "mcp_get_prompt":
            result = await self.session.get_prompt(
                arguments["name"], arguments.get("arguments")
            )
        else:
            result = await self.session.call_tool(name, arguments)
            text = "\n".join(c.text for c in result.content if c.type == "text")
            if result.isError:
                raise RuntimeError(text)
            if text:
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return text
            structured = result.structuredContent
            if isinstance(structured, dict) and "result" in structured:
                return structured["result"]
            return structured if structured is not None else ""
        return result.model_dump(mode="json", by_alias=True)

    def manual(self) -> str:
        return "\n".join(
            [
                "MCP resources: " + str([str(r.uri) for r in self.resources]),
                "MCP resource templates: "
                + str([str(t.uriTemplate) for t in self.templates]),
                "MCP prompts: " + str([p.name for p in self.prompts]),
            ]
        )
