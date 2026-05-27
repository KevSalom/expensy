from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Literal

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from config import settings

Mode = Literal["personal", "demo"]


class AirtableMCPError(RuntimeError):
    pass


@dataclass(frozen=True)
class AirtableContext:
    mode: Mode
    base_id: str
    table_id: str
    schema: Any


class AirtableMCP:
    def __init__(self, mode: Mode):
        self.mode = mode
        self.base_name = settings.airtable_base_name_for_mode(mode)
        self.table_name = settings.airtable_expenses_table_name
        self._tools: list[BaseTool] | None = None
        self._context: AirtableContext | None = None

    async def get_tools(self) -> list[BaseTool]:
        if self._tools is not None:
            return self._tools

        pat = settings.airtable_pat_for_mode(self.mode)
        client = MultiServerMCPClient(
            {
                "airtable": {
                    "url": settings.airtable_mcp_url,
                    "transport": "streamable_http",
                    "headers": {"Authorization": f"Bearer {pat}"},
                }
            }
        )
        self._tools = await client.get_tools()
        return self._tools

    async def resolve_context(self) -> AirtableContext:
        if self._context is not None:
            return self._context

        base = await self._resolve_base()
        table = await self._resolve_table(base["id"])
        schema = await self._get_table_schema(base["id"], table["id"])
        self._context = AirtableContext(
            mode=self.mode,
            base_id=base["id"],
            table_id=table["id"],
            schema=schema,
        )
        return self._context

    async def create_expense(self, fields: dict[str, Any]) -> Any:
        context = await self.resolve_context()
        tool = await self._require_tool("create_records_for_table")
        payloads = [
            {
                "baseId": context.base_id,
                "tableId": context.table_id,
                "records": [{"fields": self._remove_empty(fields)}],
            },
            {
                "base_id": context.base_id,
                "table_id": context.table_id,
                "records": [{"fields": self._remove_empty(fields)}],
            },
        ]
        return await self._invoke_first_success(tool, payloads)

    async def retrieve_expenses(
        self,
        query: str | None = None,
        max_records: int = 25,
    ) -> Any:
        context = await self.resolve_context()
        if query:
            tool = await self._optional_tool("search_records")
            if tool is not None:
                payloads = [
                    {
                        "baseId": context.base_id,
                        "tableId": context.table_id,
                        "query": query,
                        "maxRecords": max_records,
                    },
                    {
                        "base_id": context.base_id,
                        "table_id": context.table_id,
                        "query": query,
                        "max_records": max_records,
                    },
                ]
                return await self._invoke_first_success(tool, payloads)

        tool = await self._require_tool("list_records_for_table")
        payloads = [
            {
                "baseId": context.base_id,
                "tableId": context.table_id,
                "maxRecords": max_records,
            },
            {
                "base_id": context.base_id,
                "table_id": context.table_id,
                "max_records": max_records,
            },
        ]
        return await self._invoke_first_success(tool, payloads)

    async def _resolve_base(self) -> dict[str, Any]:
        tool = await self._require_tool("search_bases")
        result = await self._invoke_first_success(
            tool,
            [{"query": self.base_name}, {"name": self.base_name}],
        )
        bases = self._extract_objects(result)
        base = self._find_named_object(bases, self.base_name, id_prefix="app")
        if not base:
            raise AirtableMCPError(f"No encontre la base de Airtable '{self.base_name}'.")
        return base

    async def _resolve_table(self, base_id: str) -> dict[str, Any]:
        tool = await self._require_tool("list_tables_for_base")
        result = await self._invoke_first_success(
            tool,
            [{"baseId": base_id}, {"base_id": base_id}],
        )
        tables = self._extract_objects(result)
        table = self._find_named_object(tables, self.table_name, id_prefix="tbl")
        if not table:
            raise AirtableMCPError(
                f"No encontre la tabla '{self.table_name}' en la base '{self.base_name}'."
            )
        return table

    async def _get_table_schema(self, base_id: str, table_id: str) -> Any:
        tool = await self._require_tool("get_table_schema")
        return await self._invoke_first_success(
            tool,
            [
                {"baseId": base_id, "tableId": table_id},
                {"base_id": base_id, "table_id": table_id},
            ],
        )

    async def _optional_tool(self, name: str) -> BaseTool | None:
        tools = await self.get_tools()
        normalized = name.lower()
        return next((tool for tool in tools if tool.name.lower() == normalized), None)

    async def _require_tool(self, name: str) -> BaseTool:
        tool = await self._optional_tool(name)
        if tool is None:
            available = ", ".join(sorted(tool.name for tool in await self.get_tools()))
            raise AirtableMCPError(
                f"La tool MCP '{name}' no esta disponible. Tools disponibles: {available}"
            )
        return tool

    async def _invoke_first_success(
        self,
        tool: BaseTool,
        payloads: list[dict[str, Any]],
    ) -> Any:
        last_error: Exception | None = None
        for payload in payloads:
            try:
                return await tool.ainvoke(payload)
            except Exception as exc:
                last_error = exc
        raise AirtableMCPError(
            f"Airtable MCP rechazo la llamada a '{tool.name}': {last_error}"
        )

    def _extract_objects(self, value: Any) -> list[dict[str, Any]]:
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                return []

        found: list[dict[str, Any]] = []

        def walk(item: Any) -> None:
            if isinstance(item, dict):
                if "id" in item and ("name" in item or "fields" in item):
                    found.append(item)
                for child in item.values():
                    walk(child)
            elif isinstance(item, list):
                for child in item:
                    walk(child)

        walk(value)
        return found

    def _find_named_object(
        self,
        objects: list[dict[str, Any]],
        name: str,
        id_prefix: str,
    ) -> dict[str, Any] | None:
        normalized = name.strip().lower()
        for item in objects:
            item_id = str(item.get("id", ""))
            item_name = str(item.get("name", "")).strip().lower()
            if item_id.startswith(id_prefix) and item_name == normalized:
                return item
        for item in objects:
            item_id = str(item.get("id", ""))
            item_name = str(item.get("name", "")).strip().lower()
            if item_id.startswith(id_prefix) and normalized in item_name:
                return item
        return None

    def _remove_empty(self, fields: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in fields.items() if value not in (None, "", [])}
