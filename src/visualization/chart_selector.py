#src/visualization/chart_selector.py
from dataclasses import dataclass
from typing import List, Optional, Literal
import pandas as pd

ChartType = Literal["line", "bar", "pie", "scatter", "histogram", "table"]

@dataclass
class ChartSpec:
    chart_type: ChartType
    x: Optional[str] = None
    y: Optional[List[str]] = None
    color: Optional[str] = None
    title: Optional[str] = None
    x_label: Optional[str] = None
    y_label: Optional[str] = None
    is_time_series: bool = False


TIME_LIKE_COLS = {"date", "usage_date", "year", "month", "billing_cycle"}

def infer_chart(
    df: pd.DataFrame,
    user_question: str | None = None,
    sql_query: str | None = None
) -> ChartSpec:

    # FIX: Convert numeric text columns to numeric
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="ignore")

    # (all NaN) datasets → show message instead of empty chart    
    if df.isna().all().all():
        return ChartSpec(
            chart_type="table",
            title="No data available for the selected query or filters"
        )

    if df.empty or df.shape[1] == 0:
        return ChartSpec(chart_type="table", title="No data returned")

    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    non_numeric_cols = df.select_dtypes(exclude=["number", "bool"]).columns.tolist()

    # 1) Time-series
    time_cols = [c for c in df.columns if c.lower() in TIME_LIKE_COLS]
    if time_cols and numeric_cols:
        x_col = time_cols[0]
        y_col = numeric_cols[0]
        return ChartSpec(
            chart_type="line",
            x=x_col,
            y=[y_col],
            title=f"{y_col} over {x_col}",
            x_label=x_col,
            y_label=y_col,
            is_time_series=True,
        )

    # 2) Categorical bar/pie
    if non_numeric_cols and numeric_cols:
        cat = non_numeric_cols[0]
        metric = numeric_cols[0]
        nunique = df[cat].nunique()

        if nunique <= 6:
            return ChartSpec(chart_type="pie", x=cat, y=[metric], title=f"Distribution of {metric} by {cat}")
        else:
            return ChartSpec(chart_type="bar", x=cat, y=[metric], title=f"{metric} by {cat}", x_label=cat, y_label=metric)

    # 3) Scatter
    if len(numeric_cols) >= 2:
        return ChartSpec(chart_type="scatter", x=numeric_cols[0], y=[numeric_cols[1]], title=f"{numeric_cols[1]} vs {numeric_cols[0]}")

    # 4) Histogram
    if len(numeric_cols) == 1:
        metric = numeric_cols[0]
        return ChartSpec(chart_type="histogram", x=metric, title=f"Distribution of {metric}", x_label=metric)

    return ChartSpec(chart_type="table", title="Query result")
