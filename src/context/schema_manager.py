# src/context/schema_manager.py
import os
import json
import pandas as pd
from sqlalchemy import (
    create_engine, MetaData, Table, Column, Integer, String,
    Numeric, Date, Boolean, Time, ForeignKey
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.dialects.postgresql import insert
from config.settings import get_settings

settings = get_settings()

# Map Excel/JSON types to SQLAlchemy/PostgreSQL types
SQLALCHEMY_TYPE_MAP = {
    "INTEGER": Integer,
    "TEXT": String,
    "NUMERIC": Numeric,
    "DATE": Date,
    "BOOLEAN": Boolean,
    "TIME": Time
}


class SchemaManager:
    def __init__(self, excel_path: str, schema_json_path: str = "config/schema_metadata.json"):
        self.excel_path = excel_path
        self.schema_json_path = schema_json_path
        self.tables = {}  # Dictionary of table_name: DataFrame
        self.schema_metadata = {}
        self.engine = create_engine(
            f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@"
            f"{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
        )

    def load_schema(self):
        """Load Excel sheets into DataFrames"""
        xls = pd.ExcelFile(self.excel_path)
        for sheet_name in xls.sheet_names:
            self.tables[sheet_name] = pd.read_excel(xls, sheet_name)
        return self.tables

    def generate_metadata(self):
        """Generate JSON schema metadata with automatic PK/FK detection"""
        schema = {"database": settings.POSTGRES_DB, "dialect": "postgresql", "tables": []}

        # Track table primary keys
        table_pks = {}

        # First pass: create table metadata with columns & PK
        for table_name, df in self.tables.items():
            columns = []
            primary_key = df.columns[0]  # Assume first column is PK
            table_pks[table_name] = primary_key

            for col in df.columns:
                dtype = df[col].dtype
                if "int" in str(dtype):
                    col_type = "INTEGER"
                elif "float" in str(dtype):
                    col_type = "NUMERIC"
                elif "bool" in str(dtype):
                    col_type = "BOOLEAN"
                elif "datetime" in str(dtype):
                    col_type = "DATE"
                else:
                    col_type = "TEXT"

                columns.append({"name": col, "data_type": col_type, "nullable": False})

            schema["tables"].append({
                "table_name": table_name,
                "primary_key": primary_key,
                "columns": columns,
                "foreign_keys": []  # will populate next
            })

        # Second pass: infer foreign keys
        for table in schema["tables"]:
            fks = []
            for col in table["columns"]:
                col_name = col["name"]
                if col_name == table["primary_key"]:
                    continue

                # Match only if column exactly equals a PK of another table
                for ref_table, ref_pk in table_pks.items():
                    if ref_table != table["table_name"]:
                        if col_name == ref_pk:
                            fks.append({"column": col_name, "ref_table": ref_table, "ref_column": ref_pk})

                # Special case: invoice_key → billing_key
                if col_name == "invoice_key" and "fact_billing" in table_pks:
                    fks.append({"column": col_name, "ref_table": "fact_billing", "ref_column": "billing_key"})

            # Remove duplicate foreign keys
            fks = [dict(t) for t in {tuple(d.items()) for d in fks}]
            table["foreign_keys"] = fks

        self.schema_metadata = schema
        return schema

    def save_metadata(self):
        """Save schema metadata to JSON file"""
        os.makedirs(os.path.dirname(self.schema_json_path), exist_ok=True)
        with open(self.schema_json_path, "w") as f:
            json.dump(self.schema_metadata, f, indent=4)

    def create_tables(self):
        """Drop existing tables and create new PostgreSQL tables from schema metadata"""
        metadata = MetaData()
        metadata.reflect(bind=self.engine)
        metadata.drop_all(self.engine)  # drop existing tables safely

        tables = {}

        # Create columns first
        for table in self.schema_metadata["tables"]:
            cols = []
            for col in table["columns"]:
                col_type = SQLALCHEMY_TYPE_MAP.get(col["data_type"], String)
                is_pk = col["name"] == table["primary_key"]
                cols.append(Column(col["name"], col_type, primary_key=is_pk, nullable=col["nullable"]))
            tables[table["table_name"]] = Table(table["table_name"], metadata, *cols)

        # Add foreign keys safely
        for table in self.schema_metadata["tables"]:
            for fk in table.get("foreign_keys", []):
                fk_col = fk["column"]
                if fk_col not in [c.name for c in tables[table["table_name"]].columns]:
                    tables[table["table_name"]].append_column(
                        Column(fk_col, Integer, ForeignKey(f"{fk['ref_table']}.{fk['ref_column']}"))
                    )

        try:
            metadata.create_all(self.engine)
            print(f"PostgreSQL tables created in database {settings.POSTGRES_DB}.")
        except SQLAlchemyError as e:
            print("Error creating tables:", e)

    def load_data(self):
        """Insert or update data into PostgreSQL tables (UPSERT)"""
        metadata = MetaData()
        metadata.reflect(bind=self.engine)

        for table_name, df in self.tables.items():
            table = Table(table_name, metadata, autoload_with=self.engine)
            pk_col = list(table.primary_key.columns)[0].name

            df = df.drop_duplicates(subset=[pk_col])

            with self.engine.begin() as conn:
                for _, row in df.iterrows():
                    stmt = insert(table).values(**row.to_dict())
                    update_cols = {c.name: stmt.excluded[c.name] for c in table.columns if c.name != pk_col}
                    stmt = stmt.on_conflict_do_update(index_elements=[pk_col], set_=update_cols)
                    conn.execute(stmt)

            print(f"Data upserted into table: {table_name}")

    def build(self):
        """Full pipeline: load Excel → generate metadata → save JSON → create tables → load data"""
        self.load_schema()
        self.generate_metadata()
        self.save_metadata()
        self.create_tables()
        self.load_data()
