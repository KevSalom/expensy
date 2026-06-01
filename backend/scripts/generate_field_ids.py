#!/usr/bin/env python3
"""Genera field_ids.py con los field IDs de Airtable para ambos modos."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from airtable_rest import get_writable_field_ids
from config import settings


def format_dict(d: dict[str, str], indent: int = 4) -> str:
    """Formatea un diccionario como string Python."""
    if not d:
        return "{}"
    
    lines = ["{"]
    for name, field_id in sorted(d.items()):
        lines.append(f"{' ' * indent}\"{name}\": \"{field_id}\",")
    lines.append("}")
    return "\n".join(lines)


def main():
    print("Obteniendo field IDs para modo 'demo'...")
    demo_fields = get_writable_field_ids("demo")
    print(f"  {len(demo_fields)} campos encontrados")
    
    print("Obteniendo field IDs para modo 'personal'...")
    personal_fields = get_writable_field_ids("personal")
    print(f"  {len(personal_fields)} campos encontrados")
    
    output = f'''"""Field IDs de Airtable generados automáticamente.

Este archivo fue generado por scripts/generate_field_ids.py
No editar manualmente - regenerar si cambian los campos en Airtable.
"""

DEMO_FIELD_IDS = {format_dict(demo_fields)}

PERSONAL_FIELD_IDS = {format_dict(personal_fields)}


def get_field_ids(mode: str) -> dict[str, str]:
    """Retorna el mapeo de field IDs para el modo especificado."""
    if mode == "demo":
        return DEMO_FIELD_IDS
    elif mode == "personal":
        return PERSONAL_FIELD_IDS
    else:
        raise ValueError(f"Modo inválido: {{mode}}")
'''
    
    output_path = Path(__file__).parent.parent / "field_ids.py"
    output_path.write_text(output, encoding="utf-8")
    print(f"\nArchivo generado: {output_path}")


if __name__ == "__main__":
    main()
