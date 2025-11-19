# scripts/batch_test_queries.py
# Script to run a batch of test queries through the LLM → SQL → DB → Visualization pipeline.
# Useful for QA, regression testing, and checking edge cases.

from collections import defaultdict
from src.run_pipeline import QueryOrchestrator


# -------------------------
# Define test queries grouped by category
# -------------------------
TEST_QUERIES = {
    "basic_counts": [
        "How many subscribers do we have in total?",
        "Number of subscribers by age",
        "How many subscribers signed up in 2024?",
        "Count subscribers per country",
    ],
    "time_series": [
        "Show total charges per month for the latest year available",
        "Daily new subscribers for the last 30 days",
        "Total usage cost per day in January 2024",
        "Number of churned subscribers per month in 2023",
    ],
    "joins_products_channels": [
        "Total revenue per product category last year",
        "Total usage cost by device type",
        "Total revenue by sales channel",
        "Average total charges per payment method",
    ],
    "churn_and_retention": [
        "Number of churned subscribers by churn_reason",
        "Average lifetime_value of churned customers per churn_category",
        "Top 5 countries by number of churned subscribers",
    ],
    "geography_and_network": [
        "Total data consumed in MB per country",
        "Average call minutes per city",
        "Total roaming data MB per region",
        "Number of subscribers by network_type",
    ],
    "age_and_demographics": [
        "Number of subscribers by age group (18-25, 26-35, 36-45, 46-60, 60+)",
        "List subscribers older than 40 years with their country and city",
        "Average total_charges per age group",
    ],
    "billing_and_payments": [
        "Total billing amount (total_due) per billing_cycle in 2024",
        "Total payments per payment_method",
        "Number of unpaid invoices per month",
        "Average time between invoice due_date and paid_date",
    ],
    "edge_cases": [
        "List the first 10 subscribers with their product and device",
        "Explain what a telecom subscriber is in simple words",
        "Show the top 5 products by total revenue",
        "Total revenue in the year 2050",
    ],
}


# -------------------------
# Classify pipeline result into categories for reporting
# -------------------------
def classify_result(result) -> str:
    """
    Classify the pipeline output into:
      - ok
      - db_error (SQL execution failed)
      - viz_error (visualization failed)
      - empty_data (query ran but returned empty result)
      - non_data (rule 0: non-data informational question)
    Uses only PipelineResult fields; does NOT modify pipeline logic.
    """
    df_preview = result.df_preview
    chart_payload = result.chart_payload or {}
    config = chart_payload.get("config", {}) if isinstance(chart_payload, dict) else {}
    message = config.get("message", "") if isinstance(config, dict) else ""

    # Non-data question (rule 0)
    if isinstance(df_preview, str) and df_preview.startswith("Non-data question:"):
        return "non_data"

    # Execution error
    if isinstance(message, str) and message.startswith("Query execution failed:"):
        return "db_error"

    # Visualization error
    if isinstance(message, str) and message.startswith("Visualization failed:"):
        return "viz_error"

    # Empty DataFrame
    if df_preview == "Empty DataFrame":
        return "empty_data"

    # Otherwise assume ok
    return "ok"


# -------------------------
# Main runner
# -------------------------
def main():
    orchestrator = QueryOrchestrator()
    summary_counts = defaultdict(int)
    detailed_results = []

    # Iterate over test queries grouped by category
    for group_name, questions in TEST_QUERIES.items():
        print(f"\n=== Group: {group_name} ===")
        for q in questions:
            print(f"\n▶ Question: {q}")
            result = orchestrator.run(q)
            status = classify_result(result)
            summary_counts[status] += 1

            # Print reduced info for manual inspection
            print(f"Status: {status}")
            print("SQL:")
            print(result.sql_clean)
            print("Preview:")
            print(result.df_preview)

            detailed_results.append(
                {
                    "group": group_name,
                    "question": q,
                    "status": status,
                    "sql": result.sql_clean,
                    "df_preview": result.df_preview,
                    "message": result.chart_payload.get("config", {}).get("message", "")
                    if isinstance(result.chart_payload, dict)
                    else "",
                }
            )

    # Print summary counts for all categories
    print("\n\n===== SUMMARY =====")
    for status, count in summary_counts.items():
        print(f"{status}: {count}")


if __name__ == "__main__":
    main()