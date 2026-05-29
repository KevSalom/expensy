import os
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from airtable_rest import AirtableREST
from config import settings

def test():
    mode = "personal"
    client = AirtableREST(mode)
    table_id = settings.airtable_expenses_table_id
    
    print(f"Table ID: {table_id}")
    print()
    
    print("1. Sin fields (funciona)...")
    try:
        result = client.list_records(table_id=table_id, max_records=2)
        print(f"OK - {len(result)} registros")
    except Exception as e:
        print(f"Error: {e}")
    
    print()
    print("2. Con fields simple (sin espacios)...")
    try:
        result = client.list_records(table_id=table_id, fields=["Monto", "Nota"], max_records=2)
        print(f"OK - {len(result)} registros")
        for rec in result:
            print(f"   - {rec.get('fields')}")
    except Exception as e:
        print(f"Error: {e}")
    
    print()
    print("3. Con fields con espacios (URL encoded)...")
    try:
        fields = ["Monto", "Nota", "Fecha de Gasto"]
        fields_encoded = urllib.parse.quote(','.join(fields), safe='')
        url = f"{client.base_url}/{urllib.parse.quote(table_id, safe='')}?fields={fields_encoded}&maxRecords=2"
        print(f"   URL: {url}")
        result = client.list_records(table_id=table_id, fields=fields, max_records=2)
        print(f"OK - {len(result)} registros")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test()
