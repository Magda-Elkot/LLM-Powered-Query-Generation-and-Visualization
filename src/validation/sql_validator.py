import sqlparse

class SQLValidator:
    def validate(self, sql_query: str) -> bool:
        """
        Only block queries that modify data (INSERT, UPDATE, DELETE, CREATE).
        Everything else (SELECT, JOIN, etc.) is allowed.
        """
        parsed = sqlparse.parse(sql_query)
        if not parsed:
            raise ValueError("Empty or invalid SQL")

        stmt = parsed[0]
        stmt_type = stmt.get_type().upper()

        # Block modifying statements
        if stmt_type in ("INSERT", "UPDATE", "DELETE", "CREATE"):
            raise ValueError(f"Only SELECT statements allowed. Got {stmt_type}.")

        # Otherwise, allow
        return True
