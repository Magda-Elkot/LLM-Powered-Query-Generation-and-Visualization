from typing import List, Optional

SQL_PROMPT_TEMPLATE = """
You are a highly skilled AI that converts natural language questions into valid SQL queries for a PostgreSQL database.

Database schema:
{schema_text}

Task:
1. Understand the user's question.
2. Generate a precise SQL query that answers the question.
3. Only use columns and tables provided in the schema above.
4. Use proper SQL syntax for PostgreSQL.
5. Include necessary joins if the question spans multiple tables.
6. Avoid using any tables/columns not present in the schema.
7. Return only the SQL query, nothing else.

Examples:
User: "What are the average sales from 2022 till now?"
SQL: "SELECT AVG(sales_amount) FROM fact_sales WHERE year >= 2022;"

User: "How many devices were sold per network?"
SQL: "SELECT d.network_id, COUNT(*) FROM dim_device d JOIN dim_network n ON d.network_id = n.network_id GROUP BY d.network_id;"

User question:
{user_question}
SQL:
"""


def build_sql_prompt(user_question: str, schema_text: str) -> str:
    """
    Constructs a prompt for the LLM including the database schema and user question.

    Args:
        user_question (str): Natural language question from user.
        schema_text (str): Textual description of database schema.

    Returns:
        str: Fully formatted prompt ready for LLM.
    """
    return SQL_PROMPT_TEMPLATE.format(user_question=user_question, schema_text=schema_text)


def build_few_shot_prompt(
    user_question: str, 
    schema_text: str, 
    examples: Optional[List[dict]] = None
) -> str:
    """
    Builds a prompt for the LLM including optional few-shot examples.

    Args:
        user_question (str): Natural language question.
        schema_text (str): Database schema as text.
        examples (Optional[List[dict]]): Each dict should have 'question' and 'sql' keys.

    Returns:
        str: Complete LLM prompt.
    """
    prompt_lines = [
        "You are an expert SQL generator AI for PostgreSQL.",
        "Database schema:",
        schema_text
    ]

    if examples:
        prompt_lines.append("Follow these examples:")
        for ex in examples:
            prompt_lines.append(f"User: \"{ex['question']}\"\nSQL: \"{ex['sql']}\"")

    # Append the actual user question at the end
    prompt_lines.append(f"User: \"{user_question}\"\nSQL:")

    return "\n".join(prompt_lines)
