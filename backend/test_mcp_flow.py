import asyncio
import json
import os
import urllib.request
from pathlib import Path

os.chdir(Path(__file__).parent)

from mcp_client import get_airtable_tools, get_writable_field_ids
from config import settings


async def test():
    mode = "personal"

    tools = await get_airtable_tools(mode)
    base_id = settings.airtable_base_id_for_mode(mode)
    table_id = settings.airtable_expenses_table_id

    # 1. Obtener field IDs
    print("1. Field IDs via REST API:")
    field_map = get_writable_field_ids(mode)
    for name, fid in field_map.items():
        print(f"   {name} -> {fid}")
    print()

    # 2. Crear record via MCP con Field IDs
    print("2. Creando record via MCP con Field IDs...")
    cr = next(t for t in tools if t.name == "create_records_for_table")
    result = await cr.ainvoke({
        "baseId": base_id,
        "tableId": table_id,
        "records": [{
            "fields": {
                field_map["Monto"]: 25.00,
                field_map["Tasa"]: "USD",
                field_map["Categoría"]: "test",
                field_map["Fecha de Gasto"]: "2026-05-28",
                field_map["Nota"]: "test field IDs via MCP",
            }
        }],
        "typecast": True,
    })
    print(f"   Resultado MCP: {result}")
    print()

    # 3. Verificar via REST API que se creo
    print("3. Verificando via REST API...")
    pat = settings.airtable_pat_for_mode(mode)
    rest_url = f"https://api.airtable.com/v0/{base_id}/{table_id}?maxRecords=3"
    req = urllib.request.Request(rest_url, headers={"Authorization": f"Bearer {pat}"})
    with urllib.request.urlopen(req) as r:
        data = json.loads(r.read())
        for rec in data.get("records", []):
            fields = rec.get("fields", {})
            print(f"   ID: {rec['id']}")
            print(f"   Monto: {fields.get('Monto')}")
            print(f"   Tasa: {fields.get('Tasa')}")
            print(f"   Categoria: {fields.get('Categoria')}")
            print(f"   Fecha: {fields.get('Fecha de Gasto')}")
            print(f"   Nota: {fields.get('Nota')}")
            print()

    print("Flujo completo OK!")


if __name__ == "__main__":
    asyncio.run(test())
