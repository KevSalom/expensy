import asyncio
import json
import os
from pathlib import Path

os.chdir(Path(__file__).parent)

from mcp_client import get_airtable_tools
from config import settings


async def test():
    mode = "personal"
    tools = await get_airtable_tools(mode)
    base_id = settings.airtable_base_id_for_mode(mode)
    table_id = settings.airtable_expenses_table_id
    tm = {t.name: t for t in tools}

    async def call_raw(tool, params):
        """Usa arun con tool_call_id para preservar artifact en el ToolMessage."""
        return await tool.arun(tool_input=params, tool_call_id="debug")

    tests = [
        ("PING", tm["ping"], {}),
        ("LIST BASES", tm["list_bases"], {}),
        ("SEARCH BASES", tm["search_bases"], {"searchQuery": "expensy"}),
        ("LIST TABLES FOR BASE", tm["list_tables_for_base"], {"baseId": base_id}),
        ("GET TABLE SCHEMA", tm["get_table_schema"], {
            "baseId": base_id,
            "tables": [{"tableId": table_id, "fieldIds": ["fldHzzUpKEPz3JcTx"]}]
        }),
        ("LIST RECORDS", tm["list_records_for_table"], {
            "baseId": base_id, "tableId": table_id, "pageSize": 5
        }),
    ]

    for name, tool, params in tests:
        print("=" * 70)
        print(name)
        print("=" * 70)
        try:
            raw = await call_raw(tool, params)
            is_tuple = isinstance(raw, tuple)
            print(f"  raw type={type(raw).__name__} is_tuple={is_tuple} len={len(raw) if isinstance(raw, (list, tuple)) else 'N/A'}")

            from langchain_core.messages import ToolMessage
            if isinstance(raw, ToolMessage):
                print(f"  ToolMessage content type={type(raw.content).__name__}")
                content = raw.content
                artifact = raw.artifact
                if isinstance(content, list):
                    for item in content[:5]:
                        if isinstance(item, dict):
                            t = item.get("type", "?")
                            text = item.get("text", "")
                            print(f"    [{t}] {text[:300]}")
                        else:
                            print(f"    {repr(item)[:200]}")
                elif isinstance(content, str):
                    print(f"  content str: {content[:500]}")
                else:
                    print(f"  content: {repr(content)[:300]}")

                print(f"  artifact present: {artifact is not None}")
                if artifact is not None:
                    sc = artifact.structured_content if hasattr(artifact, "structured_content") else artifact
                    print(f"  structured_content:")
                    try:
                        print(f"    {json.dumps(sc, indent=2, default=str)[:3000]}")
                    except Exception as e:
                        print(f"    (json error: {e}) {repr(sc)[:500]}")
            else:
                print(f"  NOT ToolMessage: type={type(raw).__name__} repr={repr(raw)[:300]}")
        except Exception as e:
            print(f"  ERROR: {type(e).__name__}: {e}")
        print()


if __name__ == "__main__":
    asyncio.run(test())
