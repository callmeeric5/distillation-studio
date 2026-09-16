"""REPL entry point. Blank line finishes multi-line code; exit or EOF quits."""

import argparse
import asyncio
import codeop
import os
from agent_smith.mcp.mcp_client import connect_mcp
from agent_smith.models.sandbox import SandboxConfig
from agent_smith.sandbox import Sandbox


async def repl(args: argparse.Namespace) -> None:
    config = (
        SandboxConfig.from_json_file(args.config) if args.config else SandboxConfig()
    )
    async with connect_mcp(stdio=args.mcp_stdio, url=args.mcp_server) as mcp:
        async with Sandbox(args.image, mcp, config) as sandbox:
            print(sandbox.manual())
            print("Enter Python; blank line finishes a block. 'exit' or Ctrl+D quits.")
            lines: list[str] = []
            while True:
                try:
                    line = input("... " if lines else ">>> ")
                except EOFError:
                    break
                if not lines and line.strip() == "exit":
                    break
                lines.append(line)
                source = "\n".join(lines)
                try:
                    compiled = codeop.compile_command(source, symbol="exec")
                    if compiled is None or (
                        len(lines) == 1 and line.rstrip().endswith(":")
                    ):
                        continue
                    if len(lines) > 1 and line.strip():
                        continue
                except (SyntaxError, ValueError):
                    pass  # Execute through the worker so the normal error is shown.
                if source.strip():
                    result = await sandbox.execute(source)
                    print(result.model_dump_json(indent=2))
                lines = []


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", nargs="?", default="config/sandbox.json")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--mcp-stdio")
    group.add_argument("--mcp-server")
    parser.add_argument(
        "--image", default=os.getenv("SANDBOX_IMAGE", "python:3.10-slim")
    )
    args = parser.parse_args()
    try:
        asyncio.run(repl(args))
    except KeyboardInterrupt:
        print("\nSandbox interrupted.")
    except Exception as exc:
        parser.exit(1, f"Sandbox error: {exc}\n")
