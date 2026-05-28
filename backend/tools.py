from __future__ import annotations

import json
from typing import Literal

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from mcp_client import AirtableMCP

Mode = Literal["personal", "demo"]


class RegisterExpenseInput(BaseModel):
    amount: float = Field(..., description="Monto numerico del gasto.")
    currency: str = Field(..., description="Moneda del gasto, por ejemplo USD, VES o EUR.")
    category: str = Field(..., description="Categoria del gasto, por ejemplo comida.")
    date: str | None = Field(
        default=None,
        description="Fecha del gasto en formato ISO YYYY-MM-DD si el usuario la indico.",
    )
    description: str | None = Field(
        default=None,
        description="Descripcion breve del gasto.",
    )
    account: str | None = Field(
        default=None,
        description="Cuenta, tarjeta, wallet o fuente de pago si el usuario la indico.",
    )


class RetrieveExpensesInput(BaseModel):
    query: str | None = Field(
        default=None,
        description="Texto de busqueda o resumen solicitado por el usuario.",
    )
    start_date: str | None = Field(
        default=None,
        description="Fecha inicial en formato ISO YYYY-MM-DD si aplica.",
    )
    end_date: str | None = Field(
        default=None,
        description="Fecha final en formato ISO YYYY-MM-DD si aplica.",
    )
    category: str | None = Field(default=None, description="Categoria a filtrar.")
    currency: str | None = Field(default=None, description="Moneda a filtrar.")
    max_records: int = Field(
        default=25,
        ge=1,
        le=100,
        description="Cantidad maxima de registros a recuperar.",
    )


class BolivarRateInput(BaseModel):
    source: str | None = Field(
        default=None,
        description="Fuente preferida para la tasa, si el usuario la especifica.",
    )


def create_expensy_tools(mode: Mode):
    airtable = AirtableMCP(mode=mode)

    @tool(args_schema=RegisterExpenseInput)
    async def register_expense(
        amount: float,
        currency: str,
        category: str,
        date: str | None = None,
        description: str | None = None,
        account: str | None = None,
    ) -> str:
        """Registra un gasto en Airtable cuando el usuario indica monto, moneda y categoria.

        Requiere amount, currency y category. No inventes datos faltantes; pide aclaracion.
        """
        fields = {
            "Amount": amount,
            "Currency": currency.upper().strip(),
            "Category": category.strip(),
            "Date": date,
            "Description": description,
            "Account": account,
        }
        result = await airtable.create_expense(fields)
        return (
            "Gasto registrado en Airtable. Resultado MCP:\n"
            f"{json.dumps(result, ensure_ascii=False, default=str)}"
        )

    @tool(args_schema=RetrieveExpensesInput)
    async def retrieve_expenses(
        query: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        category: str | None = None,
        currency: str | None = None,
        max_records: int = 25,
    ) -> str:
        """Consulta gastos en Airtable por texto, rango de fechas, categoria o moneda."""
        query_parts = [
            query,
            f"desde {start_date}" if start_date else None,
            f"hasta {end_date}" if end_date else None,
            f"categoria {category}" if category else None,
            f"moneda {currency}" if currency else None,
        ]
        search_query = " ".join(part for part in query_parts if part)
        result = await airtable.retrieve_expenses(
            query=search_query or None,
            max_records=max_records,
        )
        return (
            "Gastos recuperados desde Airtable. Resultado MCP:\n"
            f"{json.dumps(result, ensure_ascii=False, default=str)}"
        )

    @tool(args_schema=BolivarRateInput)
    async def get_bolivar_rate(source: str | None = None) -> str:
        """Placeholder para obtener la tasa actual del bolivar.

        Avisa que aun no tiene integracion real.
        """
        result = {
            "rate": None,
            "status": "placeholder",
            "source": source,
            "message": "La logica real de tasa del bolivar sera agregada despues.",
        }
        return json.dumps(result, ensure_ascii=False)

    return register_expense, retrieve_expenses, get_bolivar_rate
