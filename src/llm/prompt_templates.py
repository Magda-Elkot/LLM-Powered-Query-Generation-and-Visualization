from typing import List, Optional

SQL_PROMPT_TEMPLATE = """

You are a highly skilled AI that converts natural language questions into valid SQL queries for a PostgreSQL database.
 
Database schema:

{schema_text}
 
Rules:

0. If the user question is NOT related to data, metrics, revenue, counts, averages, trends, subscribers, products, billing, or any measurable information in the database, then DO NOT generate SQL from the schema. 

   Instead return exactly:
   SELECT 'Non-data question: ask about measurable telecom information.' AS message;

1. Understand the user's question carefully.
2. Only return valid PostgreSQL SQL that can execute without errors.
3. Only use columns and tables present in the schema.
4. Include necessary JOINs if the query spans multiple tables.
5. If the question asks for totals, counts, sums, averages, or comparisons, always return aggregated numeric columns (COUNT, SUM, AVG, etc).
6. If grouping by a text column, include the numeric column in GROUP BY or use MIN()/MAX() to order.
7. Ensure ORDER BY columns are either in GROUP BY or aggregated.
8. If calculating age from date_of_birth, always cast to DATE.
9. Return ONLY the SQL query, nothing else.
 
Examples:

User: "What is the total revenue per product category last year?"

SQL: "SELECT p.category, SUM(fb.total_charges) AS total_revenue

FROM fact_billing fb

JOIN dim_subscriber ds ON fb.subscriber_key = ds.subscriber_key

JOIN dim_product p ON ds.product_key = p.product_key

JOIN dim_time dt ON fb.time_key = dt.time_key

WHERE dt.year = (SELECT MAX(year)-1 FROM dim_time)

GROUP BY p.category;"
 
User: "How many subscribers signed up in 2024?"

SQL: "SELECT COUNT(subscriber_key) AS num_subscribers

FROM dim_subscriber ds

JOIN dim_time dt ON ds.time_key = dt.time_key

WHERE dt.year = 2024;"
 
User: "List all subscribers in 2024"

SQL: "SELECT ds.subscriber_key, ds.first_name, ds.last_name, ds.email

FROM dim_subscriber ds

JOIN dim_time dt ON ds.time_key = dt.time_key

WHERE dt.year = 2024;"
 
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
