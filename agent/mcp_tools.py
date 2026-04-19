"""MCP (Model Context Protocol) tool integration for the recruitment agent."""

import asyncio
import json
import logging
import threading
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).resolve().parent.parent / "mcp_servers.json"

_mcp_client = None
_background_loop: asyncio.AbstractEventLoop | None = None
_loop_lock = threading.Lock()


def _load_config() -> dict[str, Any] | None:
    if not CONFIG_PATH.exists():
        logger.info("MCP config not found at %s, skipping", CONFIG_PATH)
        return None
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        logger.warning("Failed to read MCP config: %s", exc)
        return None


def _build_connections(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Convert mcp_servers.json into the dict expected by MultiServerMCPClient."""
    connections: dict[str, dict[str, Any]] = {}
    for server in config.get("servers", []):
        name = server.get("name")
        if not name:
            logger.warning("MCP server entry missing 'name', skipped")
            continue

        transport = server.get("transport", "stdio")
        if transport == "stdio":
            conn: dict[str, Any] = {
                "transport": "stdio",
                "command": server["command"],
                "args": server.get("args", []),
            }
            if server.get("env"):
                conn["env"] = server["env"]
        elif transport in ("sse", "streamable_http"):
            conn = {
                "transport": transport,
                "url": server["url"],
            }
            if server.get("headers"):
                conn["headers"] = server["headers"]
        else:
            logger.warning(
                "Unknown transport '%s' for server '%s'", transport, name
            )
            continue

        connections[name] = conn
    return connections


def _ensure_background_loop() -> asyncio.AbstractEventLoop:
    """Return a long-lived event loop running in a daemon thread."""
    global _background_loop
    with _loop_lock:
        if _background_loop is None or _background_loop.is_closed():
            _background_loop = asyncio.new_event_loop()
            t = threading.Thread(
                target=_background_loop.run_forever,
                daemon=True,
                name="mcp-event-loop",
            )
            t.start()
    return _background_loop


async def load_mcp_tools() -> list:
    """Connect to MCP servers and return LangChain-compatible tools.

    Returns an empty list when the adapter library is missing, the
    config file is absent, or servers are unreachable.
    """
    global _mcp_client

    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient
    except ImportError:
        logger.info(
            "langchain-mcp-adapters not installed, MCP tools disabled"
        )
        return []

    config = _load_config()
    if not config:
        return []

    connections = _build_connections(config)
    if not connections:
        logger.info("No valid MCP server connections in config")
        return []

    try:
        client = MultiServerMCPClient(connections)
        await client.__aenter__()
        tools = client.get_tools()
        _mcp_client = client
        logger.info(
            "Loaded %d MCP tool(s): %s",
            len(tools),
            [t.name for t in tools],
        )
        return list(tools)
    except Exception as exc:
        logger.warning("Failed to load MCP tools: %s", exc)
        return []


def get_mcp_tools_sync() -> list:
    """Synchronous wrapper that loads MCP tools via a background loop."""
    loop = _ensure_background_loop()
    future = asyncio.run_coroutine_threadsafe(load_mcp_tools(), loop)
    try:
        return future.result(timeout=60)
    except Exception as exc:
        logger.warning("Sync MCP tool loading failed: %s", exc)
        return []
