import re
import sqlparse

class QuerySanitizer:
    """
    Safely sanitizes SQL results from the LLM.
    Removes comments, code fences, extra semicolons,
    and ensures a single clean SQL statement.
    """

    @staticmethod
    def sanitize(sql_query: str) -> str:
        if not sql_query:
            return ""

        # Remove markdown fences
        sql_query = sql_query.strip()
        sql_query = sql_query.replace("```sql", "").replace("```", "")

        # Remove outer quotes
        if (sql_query.startswith('"') and sql_query.endswith('"')) or \
           (sql_query.startswith("'") and sql_query.endswith("'")):
            sql_query = sql_query[1:-1]

        # Split into statements safely
        statements = sqlparse.split(sql_query)
        cleaned_statements = []

        for stmt in statements:
            # Remove inline comments
            stmt_no_comment = re.sub(r"--.*?$", "", stmt, flags=re.MULTILINE)
            # Remove block comments
            stmt_no_comment = re.sub(r"/\*.*?\*/", "", stmt_no_comment, flags=re.DOTALL)
            # Remove trailing semicolons (keep semicolons inside strings)
            stmt_no_comment = stmt_no_comment.rstrip(";")
            if stmt_no_comment.strip():
                cleaned_statements.append(stmt_no_comment.strip())

        # Always return the first valid statement
        return cleaned_statements[0] if cleaned_statements else ""
