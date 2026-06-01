#!/usr/bin/env python3
"""Script para probar consultas directas a Airtable."""

import sys
from pathlib import Path
from datetime import date, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from airtable_rest import AirtableREST
from config import settings


def main():
    mode = "personal"
    table_id = settings.airtable_expenses_table_id
    today = date.today().isoformat()
    
    print(f"Probando consultas a Airtable")
    print(f"Mode: {mode}")
    print(f"Table ID: {table_id}")
    print(f"Fecha de hoy: {today}")
    print()
    
    client = AirtableREST(mode)
    
    # Test 1: Todos los registros sin filtro
    print("=" * 60)
    print("TEST 1: Todos los registros (sin filtro)")
    print("=" * 60)
    try:
        records = client.list_records(table_id, max_records=10)
        print(f"[OK] Encontrados {len(records)} registros")
        for i, rec in enumerate(records[:5], 1):
            fields = rec.get("fields", {})
            print(f"  {i}. {fields.get('Nota', 'N/A')} - ${fields.get('Monto', 0)} - {fields.get('Fecha de Gasto', 'N/A')}")
    except Exception as e:
        print(f"[ERROR] {e}")
    print()
    
    # Test 2: Registros de hoy
    print("=" * 60)
    print(f"TEST 2: Registros de hoy ({today})")
    print("=" * 60)
    today_date = date.fromisoformat(today)
    tomorrow = (today_date + timedelta(days=1)).isoformat()
    filter_formula = f"AND({{Fecha de Gasto}}>='{today}',{{Fecha de Gasto}}<'{tomorrow}')"
    print(f"Filtro: {filter_formula}")
    try:
        records = client.list_records(
            table_id,
            fields=["Monto", "Nota", "Fecha de Gasto", "Categoría"],
            filter_by_formula=filter_formula,
            max_records=100
        )
        print(f"[OK] Encontrados {len(records)} registros para hoy")
        for i, rec in enumerate(records, 1):
            fields = rec.get("fields", {})
            print(f"  {i}. {fields.get('Nota', 'N/A')} - ${fields.get('Monto', 0)} - {fields.get('Categoría', 'N/A')}")
    except Exception as e:
        print(f"[ERROR] {e}")
    print()
    
    # Test 3: Registros del mes actual
    print("=" * 60)
    print("TEST 3: Registros del mes actual (junio 2026)")
    print("=" * 60)
    first_of_month = "2026-06-01"
    filter_formula = f"{{Fecha de Gasto}}>='{first_of_month}'"
    print(f"Filtro: {filter_formula}")
    try:
        records = client.list_records(
            table_id,
            fields=["Monto", "Nota", "Fecha de Gasto"],
            filter_by_formula=filter_formula,
            sort=[{"field": "Fecha de Gasto", "direction": "desc"}],
            max_records=100
        )
        print(f"[OK] Encontrados {len(records)} registros del mes")
        for i, rec in enumerate(records[:10], 1):
            fields = rec.get("fields", {})
            print(f"  {i}. {fields.get('Fecha de Gasto', 'N/A')} - {fields.get('Nota', 'N/A')} - ${fields.get('Monto', 0)}")
    except Exception as e:
        print(f"[ERROR] {e}")


if __name__ == "__main__":
    main()
