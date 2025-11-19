# scripts/test_db.py
# Utility script to test PostgreSQL connectivity and schema metadata
# Verifies that the database connection works and that schema access functions return expected results
# Also tests sample query execution and scalar queries for basic validation

import sys
from src import ContextRetriever, DBConnector, QueryExecutor


def main():
    # -------------------------
    # Test Database Connectivity
    # -------------------------
    print("=== Database Connectivity Test ===")
    db = DBConnector()
    if db.test_connection():
        print("PostgreSQL connection successful")
    else:
        print("Failed to connect to PostgreSQL")
        sys.exit(1)

    # -------------------------
    # Test Schema Metadata Access
    # -------------------------
    print("\n=== Schema Metadata Test ===")
    context = ContextRetriever()
    table_names = context.get_table_names()
    print(f"Tables found ({len(table_names)}): {table_names}")

    # Test each schema access method
    # Inspect each table's schema: primary keys, columns, foreign keys
    for table in table_names:
        pk = context.get_primary_key(table)
        cols = context.get_columns(table)
        fks = context.get_foreign_keys(table)
        print(f"\nTable: {table}")
        print(f"  Primary Key: {pk}")
        print(f"  Columns ({len(cols)}): {cols}")
        print(f"  Foreign Keys: {fks or 'None'}")

    # Test find_tables_by_column
    sample_column = "subscriber_key"
    tables_with_column = context.find_tables_by_column(sample_column)
    print(f"\nTables containing column '{sample_column}': {tables_with_column or 'None'}")

    # Test generate_schema_text
    # Generate and preview schema text (for first 3 tables)
    schema_text = context.generate_schema_text(table_names[:3])  # limit output
    print("\n=== Schema Text Snippet (first 3 tables) ===")
    print(schema_text[:800])  # show a snippet only

    # -------------------------
    # Test Query Execution
    print("\n=== Query Execution Test ===")
    executor = QueryExecutor(db)

    # Execute sample SELECT queries for first 2 tables
    for table in table_names[:2]:
        sql = f"SELECT * FROM {table} LIMIT 5"
        df = executor.execute(sql)
        print(f"\nSample data from {table}:")
        if not df.empty:
            print(df)
        else:
            print("  No rows returned or query failed.")

    # Execute a scalar query for a count
    first_table = table_names[0]
    count_sql = f"SELECT COUNT(*) FROM {first_table}"

    count = executor.execute_scalar(count_sql)
    print(f"\nRow count in {first_table}: {count}")

    print("\n=== Test Completed Successfully ===")


if __name__ == "__main__":
    main()
