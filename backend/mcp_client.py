from __future__ import annotations

import json
import urllib.request
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


READ_ONLY_TYPES = {"formula", "rollup", "lookup", "count", "autoNumber"}


def _fetch_table_schema(mode: Mode) -> list[dict]:
    """Fetch the full table schema from Airtable REST API."""
    pat = settings.airtable_pat_for_mode(mode)
    base_id = settings.airtable_base_id_for_mode(mode)
    table_id = settings.airtable_expenses_table_id

    url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {pat}"})

    with urllib.request.urlopen(req) as r:
        data = json.loads(r.read())

    for tbl in data.get("tables", []):
        if tbl["id"] == table_id:
            return tbl.get("fields", [])
    return []


def get_table_field_ids(mode: Mode) -> dict[str, str]:
    """Mapeo nombre -> field ID para TODOS los campos (incluyendo computados)."""
    return {f["name"]: f["id"] for f in _fetch_table_schema(mode)}


def get_writable_field_ids(mode: Mode) -> dict[str, str]:
    """Mapeo nombre -> field ID solo para campos editables."""
    fields = _fetch_table_schema(mode)
    return {
        f["name"]: f["id"]
        for f in fields
        if f.get("type") not in READ_ONLY_TYPES
    }
