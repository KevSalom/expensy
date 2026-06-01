"""Field IDs de Airtable generados automáticamente.

Este archivo fue generado por scripts/generate_field_ids.py
No editar manualmente - regenerar si cambian los campos en Airtable.
"""

DEMO_FIELD_IDS = {
    "Categoría": "fldFYNgQXgf4gOnia",
    "Constante Tasa": "fldBmc9nqwcTr58w6",
    "Fecha de Gasto": "fldFfYs2y29z8XBmu",
    "Monto": "fldswbX1f5EN0TotO",
    "Nota": "fldRmSYlvuDVLStic",
    "Tasa": "fldFKTyxZOWzDv1JQ",
}

PERSONAL_FIELD_IDS = {
    "Categoría": "fldFYNgQXgf4gOnia",
    "Constante Tasa": "fldBmc9nqwcTr58w6",
    "Fecha de Gasto": "fldFfYs2y29z8XBmu",
    "Monto": "fldswbX1f5EN0TotO",
    "Nota": "fldRmSYlvuDVLStic",
    "Tasa": "fldFKTyxZOWzDv1JQ",
}


def get_field_ids(mode: str) -> dict[str, str]:
    """Retorna el mapeo de field IDs para el modo especificado."""
    if mode == "demo":
        return DEMO_FIELD_IDS
    elif mode == "personal":
        return PERSONAL_FIELD_IDS
    else:
        raise ValueError(f"Modo inválido: {mode}")
