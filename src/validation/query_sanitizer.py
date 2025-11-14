import re

class QuerySanitizer:
    """
    Sanitizes SQL to prevent SQL injection
    """

    @staticmethod
    def sanitize(sql_query: str) -> str:
        # Remove dangerous characters or patterns
        sanitized = re.sub(r";", "", sql_query)  # remove semicolons
        sanitized = re.sub(r"--.*", "", sanitized)  # remove inline comments
        sanitized = re.sub(r"/\*.*?\*/", "", sanitized, flags=re.DOTALL)  # remove block comments
        return sanitized.strip()
