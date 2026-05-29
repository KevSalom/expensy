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
    print(f"URL base: {client.base_url}")
    print()
    
    print("1. Test simple - solo table_id...")
    try:
        url = f"{client.base_url}/{urllib.parse.quote(table_id, safe='')}"
        print(f"   URL: {url}")
        result = client.list_records(table_id=table_id)
        print(f"OK - {len(result)} registros")
    except Exception as e:
        print(f"Error: {e}")
    
    print()
    print("2. Test con solo max_records...")
    try:
        result = client.list_records(table_id=table_id, max_records=3)
        print(f"OK - {len(result)} registros")
        for rec in result[:2]:
            print(f"   - id={rec.get('id')}, fields={rec.get('fields')}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    import urllib.parse
    test()
