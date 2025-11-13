# src/context/context_retriever.py
import json
import os
from typing import List, Dict, Optional

class ContextRetriever:
    """
    Retrieves schema context from the JSON metadata produced by SchemaManager.
    Provides methods to get tables, columns, foreign keys, and LLM-friendly schema descriptions.
    """

    def __init__(self, schema_json_path: str = "config/schema_metadata.json"):
        self.schema_json_path = schema_json_path
        self.schema = self._load_schema()
        self.tables_index = {table["table_name"]: table for table in self.schema.get("tables", [])}

    def _load_schema(self) -> dict:
        """Load JSON schema metadata"""
        if not os.path.exists(self.schema_json_path):
            raise FileNotFoundError(f"Schema metadata file not found: {self.schema_json_path}")
        with open(self.schema_json_path, "r") as f:
            return json.load(f)

    def get_table_names(self) -> List[str]:
        """Return a list of all table names"""
        return list(self.tables_index.keys())

    def get_columns(self, table_name: str) -> List[str]:
        """Return a list of column names for a given table"""
        table = self.tables_index.get(table_name)
        if not table:
            raise ValueError(f"Table '{table_name}' not found in schema metadata")
        return [col["name"] for col in table.get("columns", [])]

    def get_primary_key(self, table_name: str) -> Optional[str]:
        """Return the primary key column of a table"""
        table = self.tables_index.get(table_name)
        return table.get("primary_key") if table else None

    def get_foreign_keys(self, table_name: str) -> List[Dict[str, str]]:
        """Return foreign keys of a table"""
        table = self.tables_index.get(table_name)
        return table.get("foreign_keys", []) if table else []

    def find_tables_by_column(self, column_name: str) -> List[str]:
        """Return tables that contain a given column"""
        tables = []
        for table_name, table in self.tables_index.items():
            if any(col["name"] == column_name for col in table.get("columns", [])):
                tables.append(table_name)
        return tables

    def generate_schema_text(self, table_names: Optional[List[str]] = None) -> str:
        """
        Generate a textual description of schema suitable for LLM prompts.
        If table_names is None, include all tables.
        """
        tables_to_include = table_names or self.get_table_names()
        schema_lines = []
        for table_name in tables_to_include:
            columns = self.get_columns(table_name)
            pk = self.get_primary_key(table_name)
            fks = self.get_foreign_keys(table_name)
            fk_text = ", ".join([f"{fk['column']} -> {fk['ref_table']}.{fk['ref_column']}" for fk in fks]) or "None"
            schema_lines.append(
                f"Table: {table_name}\n"
                f"Columns: {', '.join(columns)}\n"
                f"Primary Key: {pk}\n"
                f"Foreign Keys: {fk_text}\n"
            )
        return "\n".join(schema_lines)
