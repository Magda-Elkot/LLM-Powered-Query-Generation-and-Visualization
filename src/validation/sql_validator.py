import sqlparse

class SQLValidator:
    """
    Ensures generated SQL is safe to execute.
    Only SELECT and CTEs (WITH) are allowed.
    Blocks all destructive and DDL commands.
    Provides clear errors for multi-statement or forbidden commands.
    """

    FORBIDDEN = {
        "INSERT", "UPDATE", "DELETE", "CREATE",
        "DROP", "ALTER", "TRUNCATE", "MERGE",
        "GRANT", "REVOKE", "CALL", "EXEC"
    }

    def validate(self, sql_query: str) -> bool:
        if not sql_query:
            raise ValueError("Empty SQL query")

        statements = sqlparse.parse(sql_query)

        # Multi-statement detection
        if len(statements) != 1:
            raise ValueError("Multiple SQL statements are not allowed")

        stmt = statements[0]
        stmt_type = stmt.get_type().upper()

        # Block forbidden statements
        if stmt_type in self.FORBIDDEN:
            raise ValueError(f"Only SELECT queries allowed. Detected: {stmt_type}")

        # Handle CTEs reported as UNKNOWN by sqlparse
        if stmt_type not in ("SELECT", "UNKNOWN"):
            raise ValueError(f"Statement type not allowed: {stmt_type}")

        return True
