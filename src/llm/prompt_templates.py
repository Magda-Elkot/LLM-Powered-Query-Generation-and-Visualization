from typing import List, Optional

SQL_PROMPT_TEMPLATE = """
You are a highly skilled AI that converts natural language questions into valid SQL queries for a PostgreSQL database.
 
Database schema — Understand it very well:

{schema_text}

Rules:

0. If the user question is NOT related to data, metrics, revenue, counts, averages, trends, subscribers, products, billing,
   or any measurable information in the database, then DO NOT generate SQL.
   Instead return exactly:
   SELECT 'Non-data question: ask about measurable telecom information.' AS message;

1. Only return valid PostgreSQL SQL that can execute without errors.
2. Only use columns and tables that exist in the schema.
   - NEVER invent new names.
   - If needed columns do not exist, return the fallback in rule 0.
3. Include JOINs only on keys that exist.
4. Aggregate all numeric fields when grouping by a dimension.
5. ORDER BY columns must be grouped or aggregated.
6. Age calculation:
   - Use only dim_subscriber.date_of_birth
   - Cast to DATE before calculation.
7. Aliases must be valid:
   - Use only letters, numbers, underscores.
   - Never use hyphens.
8. All date-like columns must be cast to DATE when used in comparisons or calculations.
9. For date differences:
   AVG(CAST(paid_date AS DATE) - CAST(due_date AS DATE))
10. Do NOT use non-PostgreSQL functions (example: DATEDIFF).
11. Geography and churn rules:
   - Use fact_churn joined to dim_subscriber → dim_geography.
   - Do NOT reference tables that do not exist.
12. Billing and payments:
   - fact_payment: payment_amount, payment_method
   - fact_billing: totals, statuses.
13. Daily new subscribers:
   - Use CAST(ds.subscription_date AS DATE)
14. Output rules:
   - Return ONLY SQL.
   - No explanations.
   - Must start with SELECT or WITH.
15. If unsure, return fallback rule 0 exactly.

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
SQL: "SELECT COUNT(ds.subscriber_key) AS num_subscribers
FROM dim_subscriber ds
JOIN dim_time dt ON ds.time_key = dt.time_key
WHERE dt.year = 2024;"

User question:
{user_question}

SQL:
"""


def build_sql_prompt(user_question: str, schema_text: str) -> str:
    """
    Build a complete SQL-generation prompt using the main template.
    """
    return SQL_PROMPT_TEMPLATE.format(
        user_question=user_question.strip(),
        schema_text=schema_text.strip()
    )


def build_few_shot_prompt(
    user_question: str,
    schema_text: str,
    examples: Optional[List[dict]] = None
) -> str:
    """
    Build a few-shot SQL prompt with optional examples.
    """
    prompt_lines = [
        "You are an expert SQL generator AI for PostgreSQL.",
        "Database schema:",
        schema_text.strip()
    ]

    if examples:
        prompt_lines.append("Follow these examples:")
        for ex in examples:
            question = ex.get("question", "").strip()
            sql = ex.get("sql", "").strip()
            prompt_lines.append(f'User: "{question}"\nSQL: "{sql}"')

    prompt_lines.append(f'User: "{user_question.strip()}"')
    prompt_lines.append("SQL:")

    return "\n".join(prompt_lines)
