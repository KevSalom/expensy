from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Union

from config import settings

Mode = Union["personal", "demo"]


def _get_auth(mode: Mode) -> tuple[str, str]:
    """Returns (base_id, pat)."""
    base_id = settings.airtable_base_id_for_mode(mode)
    pat = settings.airtable_pat_for_mode(mode)
    return base_id, pat


def _make_request(method: str, url: str, pat: str, data: dict | None = None) -> dict:
    """Make HTTP request to Airtable API."""
    req = urllib.request.Request(url, method=method, headers={"Authorization": f"Bearer {pat}"})
    if data is not None:
        req.add_header("Content-Type", "application/json")
        req.data = json.dumps(data).encode()
    
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        print(f"HTTP Error {e.code}: {error_body[:500]}")
        raise


class AirtableREST:
    """Client for Airtable REST API."""

    def __init__(self, mode: Mode):
        self.base_id, self.pat = _get_auth(mode)
        self.base_url = f"https://api.airtable.com/v0/{self.base_id}"

    def list_records(
        self,
        table_id: str,
        fields: list[str] | None = None,
        filter_by_formula: str | None = None,
        sort: list[dict] | None = None,
        max_records: int = 100,
    ) -> list[dict]:
        """List records from a table.
        
        Args:
            table_id: The table ID
            fields: List of field names to include
            filter_by_formula: Airtable filter formula string
            sort: List of dicts with 'field' and 'direction' keys
            max_records: Maximum number of records (default 100)
        
        Returns:
            List of record dicts with 'id', 'fields', 'createdTime'
        """
        params = []
        if fields:
            for f in fields:
                params.append(f"fields={urllib.parse.quote(f, safe='')}")
        if filter_by_formula:
            params.append(f"filterByFormula={urllib.parse.quote(filter_by_formula, safe='')}")
        if sort:
            for i, s in enumerate(sort):
                field = s.get("field", "")
                direction = s.get("direction", "asc")
                params.append(f"sort[{i}][field]={urllib.parse.quote(field, safe='')}&sort[{i}][direction]={direction}")
        params.append(f"maxRecords={max_records}")
        
        query = "&".join(params)
        url = f"{self.base_url}/{urllib.parse.quote(table_id, safe='')}?{query}"
        
        print(f"URL: {url[:200]}")
        result = _make_request("GET", url, self.pat)
        return result.get("records", [])

    def create_record(self, table_id: str, fields: dict[str, Any], typecast: bool = True) -> dict:
        """Create a single record.
        
        Args:
            table_id: The table ID
            fields: Dict of field names to values
            typecast: Enable type casting
        
        Returns:
            Created record dict
        """
        url = f"{self.base_url}/{urllib.parse.quote(table_id, safe='')}"
        data = {"records": [{"fields": fields}], "typecast": typecast}
        result = _make_request("POST", url, self.pat, data)
        records = result.get("records", [])
        return records[0] if records else {}

    def create_records(self, table_id: str, records: list[dict[str, Any]], typecast: bool = True) -> list[dict]:
        """Create multiple records.
        
        Args:
            table_id: The table ID
            records: List of dicts with 'fields' key
            typecast: Enable type casting
        
        Returns:
            List of created record dicts
        """
        url = f"{self.base_url}/{urllib.parse.quote(table_id, safe='')}"
        data = {"records": records, "typecast": typecast}
        result = _make_request("POST", url, self.pat, data)
        return result.get("records", [])

    def search_records(self, table_id: str, query: str, fields: list[str] | None = None) -> list[dict]:
        """Search records using a formula.
        
        Args:
            table_id: The table ID
            query: Search query (will use SEARCH formula)
            fields: List of field names to include
        
        Returns:
            List of record dicts
        """
        formula = f'SEARCH("{query}",{{Nota}})>0'
        return self.list_records(table_id, fields=fields, filter_by_formula=formula)

    def get_table_fields(self, table_id: str) -> list[dict]:
        """Get field definitions for a table.
        
        Returns:
            List of field dicts with id, name, type
        """
        url = f"https://api.airtable.com/v0/meta/bases/{self.base_id}/tables"
        result = _make_request("GET", url, self.pat)
        
        for table in result.get("tables", []):
            if table.get("id") == table_id:
                return table.get("fields", [])
        return []


def get_airtable_rest(mode: Mode) -> AirtableREST:
    """Get Airtable REST client instance."""
    return AirtableREST(mode)


def list_records(
    mode: Mode,
    table_id: str,
    fields: list[str] | None = None,
    filter_by_formula: str | None = None,
    sort: list[dict] | None = None,
    max_records: int = 100,
) -> list[dict]:
    """Convenience function to list records."""
    client = AirtableREST(mode)
    return client.list_records(table_id, fields, filter_by_formula, sort, max_records)


def create_record(
    mode: Mode,
    table_id: str,
    fields: dict[str, Any],
    typecast: bool = True,
) -> dict:
    """Convenience function to create a record."""
    client = AirtableREST(mode)
    return client.create_record(table_id, fields, typecast)


def search_records(
    mode: Mode,
    table_id: str,
    query: str,
    fields: list[str] | None = None,
) -> list[dict]:
    """Convenience function to search records."""
    client = AirtableREST(mode)
    return client.search_records(table_id, query, fields)


READ_ONLY_TYPES = {"formula", "rollup", "lookup", "count", "autoNumber"}


def _fetch_table_schema(mode: Mode) -> list[dict]:
    """Fetch the full table schema from Airtable REST API."""
    client = AirtableREST(mode)
    return client.get_table_fields(settings.airtable_expenses_table_id)


def get_writable_field_ids(mode: Mode) -> dict[str, str]:
    """Mapeo nombre -> field ID solo para campos editables."""
    fields = _fetch_table_schema(mode)
    return {
        f["name"]: f["id"]
        for f in fields
        if f.get("type") not in READ_ONLY_TYPES
    }
