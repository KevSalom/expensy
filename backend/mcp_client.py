from __future__ import annotations

from typing import Literal

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from config import settings

Mode = Literal["personal", "demo"]


async def get_airtable_tools(mode: Mode) -> list[BaseTool]:
    """Carga todas las herramientas MCP de Airtable para el modo dado."""
    pat = settings.airtable_pat_for_mode(mode)
    client = MultiServerMCPClient(
        {
            "airtable": {
                "url": settings.airtable_mcp_url,
                "transport": "streamable_http",
                "headers": {"Authorization": f"Bearer {pat}"},
            }
        }
    )
    return await client.get_tools()
