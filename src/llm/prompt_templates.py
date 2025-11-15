from typing import List, Optional

SQL_PROMPT_TEMPLATE = """
You are a highly skilled AI that converts natural language questions into valid SQL queries for a PostgreSQL database.

Database schema:
{schema_text}

Rules:
1. Understand the user's question carefully.
2. Only return valid PostgreSQL SQL that can execute without errors.
3. Only use columns and tables present in the schema.
4. Include necessary JOINs if the query spans multiple tables.
5. If the question asks for totals, counts, sums, averages, or comparisons, always return **aggregated numeric columns** using COUNT(), SUM(), AVG(), etc.
6. If grouping by a text column (like month_name), always include a numeric column in GROUP BY or use MIN()/MAX() for ordering.
7. Always ensure that any column used in ORDER BY either appears in the GROUP BY or is wrapped in an aggregate function.
8. If calculating age from a date-of-birth column, always cast it to DATE first, e.g.,
   EXTRACT(YEAR FROM CURRENT_DATE) - EXTRACT(YEAR FROM ds.date_of_birth::DATE)
9. Return **only the SQL query**, nothing else.

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

User: "Number of subscribers per month in 2024"
SQL: "SELECT dt.month_name, COUNT(ds.subscriber_key) AS num_subscribers, MIN(dt.month) AS month_num
FROM dim_subscriber ds
JOIN dim_time dt ON ds.time_key = dt.time_key
WHERE dt.year = 2024
GROUP BY dt.month_name
ORDER BY month_num;"

User: "List all subscribers in 2024"
SQL: "SELECT ds.subscriber_key, ds.first_name, ds.last_name, ds.email 
FROM dim_subscriber ds 
JOIN dim_time dt ON ds.time_key = dt.time_key 
WHERE dt.year = 2024;"

User: "Age distribution of subscribers"
SQL: "SELECT EXTRACT(YEAR FROM CURRENT_DATE)::int - EXTRACT(YEAR FROM ds.date_of_birth::DATE)::int AS age,
       COUNT(ds.subscriber_key) AS num_subscribers
FROM dim_subscriber ds
GROUP BY age
ORDER BY age;"

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
