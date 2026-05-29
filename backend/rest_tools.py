from __future__ import annotations

from typing import Any, Literal

from langchain_core.tools import tool

from airtable_rest import AirtableREST, get_airtable_rest
from config import settings

Mode = Literal["personal", "demo"]


def _get_client(mode: Mode) -> AirtableREST:
    return AirtableREST(mode)


@tool
def list_records_tool(
    mode: Literal["personal", "demo"],
    table_id: str,
    fields: list[str] | None = None,
    filter_by_formula: str | None = None,
    sort_field: str | None = None,
    sort_direction: Literal["asc", "desc"] | None = None,
    max_records: int = 100,
) -> list[dict]:
    """List records from an Airtable table.
    
    Args:
        mode: The Airtable mode (personal or demo)
        table_id: The table ID to query
        fields: List of field names to include in results
        filter_by_formula: Airtable formula string for filtering (e.g., "{Monto}>10")
        sort_field: Field name to sort by
        sort_direction: Sort direction ("asc" or "desc")
        max_records: Maximum number of records to return (default 100)
    
    Returns:
        List of records with id, fields, and createdTime
    """
    client = _get_client(mode)
    
    sort = None
    if sort_field and sort_direction:
        sort = [{"field": sort_field, "direction": sort_direction}]
    
    return client.list_records(
        table_id=table_id,
        fields=fields,
        filter_by_formula=filter_by_formula,
        sort=sort,
        max_records=max_records,
    )


@tool
def create_record_tool(
    mode: Literal["personal", "demo"],
    table_id: str,
    fields: dict[str, Any],
) -> dict:
    """Create a new record in an Airtable table.
    
    Args:
        mode: The Airtable mode (personal or demo)
        table_id: The table ID to create the record in
        fields: Dictionary of field names and their values
    
    Returns:
        The created record with id and fields
    """
    client = _get_client(mode)
    return client.create_record(table_id, fields)


@tool
def search_records_tool(
    mode: Literal["personal", "demo"],
    table_id: str,
    query: str,
    fields: list[str] | None = None,
) -> list[dict]:
    """Search records by text in the Nota field.
    
    Args:
        mode: The Airtable mode (personal or demo)
        table_id: The table ID to search
        query: Text to search for in the Nota field
        fields: List of field names to include in results
    
    Returns:
        List of matching records
    """
    client = _get_client(mode)
    return client.search_records(table_id, query, fields)


def get_rest_tools(mode: Mode) -> list:
    """Get all REST-based tools for an agent."""
    return [list_records_tool, create_record_tool, search_records_tool]
