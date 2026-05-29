import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from airtable_rest import AirtableREST
from config import settings

def test():
    mode = "personal"
    client = AirtableREST(mode)
    table_id = settings.airtable_expenses_table_id
    
    print(f"Base ID: {client.base_id}")
    print(f"Table ID: {table_id}")
    print()
    
    print("1. Listando todos los registros...")
    try:
        records = client.list_records(
            table_id=table_id,
            fields=["Monto", "Nota", "Fecha de Gasto"],
            max_records=5
        )
        print(f"OK - {len(records)} registros")
        for rec in records[:3]:
            print(f"  - {rec.get('fields', {})}")
    except Exception as e:
        print(f"Error: {e}")
    
    print()
    
    print("2. Filtrando por fecha simple (string comparison)...")
    try:
        records = client.list_records(
            table_id=table_id,
            fields=["Monto", "Nota", "Fecha de Gasto"],
            filter_by_formula="{Fecha de Gasto}>='2026-05-01'",
            max_records=5
        )
        print(f"OK - {len(records)} registros")
        for rec in records[:3]:
            print(f"  - {rec.get('fields')}")
    except Exception as e:
        print(f"Error: {e}")
    
    print()
    print("2b. Filtrando por fecha con AND y texto...")
    try:
        records = client.list_records(
            table_id=table_id,
            fields=["Monto", "Nota", "Fecha de Gasto"],
            filter_by_formula="AND({Fecha de Gasto}>='2026-05-01',FIND('pollo',{Nota})>0)",
            max_records=5
        )
        print(f"OK - {len(records)} registros")
        total = sum(r.get('fields', {}).get('Monto', 0) for r in records)
        print(f"  Total: {total}")
        for rec in records[:3]:
            print(f"  - {rec.get('fields')}")
    except Exception as e:
        print(f"Error: {e}")
    
    print()
    
    print("3. Filtrando por texto en Nota (pollo)...")
    try:
        records = client.list_records(
            table_id=table_id,
            fields=["Monto", "Nota"],
            filter_by_formula="FIND('pollo',{Nota})>0",
            max_records=5
        )
        print(f"OK - {len(records)} registros con 'pollo'")
        total = sum(r.get('fields', {}).get('Monto', 0) for r in records)
        print(f"  Total: {total}")
        for rec in records[:3]:
            print(f"  - {rec.get('fields', {})}")
    except Exception as e:
        print(f"Error: {e}")
    
    print()
    print("Test completo!")


if __name__ == "__main__":
    test()
