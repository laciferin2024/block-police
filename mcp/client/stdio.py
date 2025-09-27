"""
MCP Stdio Client Implementation

Provides a client interface for communicating with MCP servers via stdio.
"""
import asyncio
import sys
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Dict, Optional, TextIO


@dataclass
class StdioServerParameters:
    """Parameters for stdio server connection"""
    command: str
    args: list = None
    env: Dict[str, str] = None


@asynccontextmanager
async def stdio_client(server: StdioServerParameters, errlog: TextIO = sys.stderr):
    """
    Create a client connection to an MCP server via stdio.

    Args:
        server: Parameters for connecting to the server
        errlog: Where to log errors

    Yields:
        A tuple of (reader, writer) streams for communicating with the server
    """
    # Create a subprocess to run the MCP server
    proc = await asyncio.create_subprocess_exec(
        server.command,
        *(server.args or []),
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=server.env
    )

    # Return the process streams
    try:
        yield proc.stdout, proc.stdin
    finally:
        if proc.returncode is None:
            proc.terminate()
            await proc.wait()