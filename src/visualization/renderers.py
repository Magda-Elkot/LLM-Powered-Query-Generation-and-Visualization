#src/visualization/renderers.py
from typing import Dict, Any, Literal
import json
import urllib.parse
import pandas as pd

from .chart_selector import ChartSpec

Backend = Literal["quickchart"]

def render(df: pd.DataFrame, spec: ChartSpec, backend: Backend = "quickchart") -> Dict[str, Any]:
    if backend == "quickchart":
        return render_quickchart(df, spec)
    else:
        raise ValueError(f"Unsupported backend: {backend}")


def render_quickchart(df: pd.DataFrame, spec: ChartSpec) -> Dict[str, Any]:

    # --- LINE & BAR ---
    if spec.chart_type in ("line", "bar"):
        labels = df[spec.x].astype(str).tolist()
        datasets = [{"label": metric, "data": df[metric].tolist()} for metric in (spec.y or [])]

        config = {
            "type": spec.chart_type,
            "data": {"labels": labels, "datasets": datasets},
            "options": {
                "plugins": {"title": {"display": True, "text": spec.title or ""}},
                "scales": {
                    "x": {"title": {"display": True, "text": spec.x_label or spec.x or ""}},
                    "y": {
                        "title": {
                            "display": True,
                            "text": spec.y_label or (spec.y[0] if spec.y else "")
                        }
                    },
                },
            },
        }

    # --- PIE ---
    elif spec.chart_type == "pie":
        labels = df[spec.x].astype(str).tolist()
        metric = spec.y[0]
        data = df[metric].tolist()

        config = {
            "type": "pie",
            "data": {
                "labels": labels,
                "datasets": [{"label": metric, "data": data}],
            },
            "options": {"plugins": {"title": {"display": True, "text": spec.title or ""}}},
        }

    # --- HISTOGRAM (approximated as bar chart) ---
    elif spec.chart_type == "histogram":
        counts = df[spec.x].value_counts().sort_index()
        config = {
            "type": "bar",
            "data": {
                "labels": counts.index.astype(str).tolist(),
                "datasets": [{"label": "Count", "data": counts.values.tolist()}],
            },
            "options": {
                "plugins": {"title": {"display": True, "text": spec.title or ""}},
                "scales": {"x": {"title": {"display": True, "text": spec.x_label or spec.x}},
                           "y": {"title": {"display": True, "text": "Count"}}},
            },
        }

    # --- SCATTER ---
    elif spec.chart_type == "scatter":
        x = spec.x
        y = spec.y[0]
        data = [{"x": float(df.iloc[i][x]), "y": float(df.iloc[i][y])} for i in range(len(df))]
        config = {
            "type": "scatter",
            "data": {"datasets": [{"label": f"{y} vs {x}", "data": data}]},
            "options": {
                "plugins": {"title": {"display": True, "text": spec.title or ""}},
                "scales": {
                    "x": {"title": {"display": True, "text": x}},
                    "y": {"title": {"display": True, "text": y}},
                },
            },
        }

    else:  # TABLE fallback → no real chart
        config = {"type": "table", "data": {}}

    encoded = urllib.parse.quote(json.dumps(config))
    url = f"https://quickchart.io/chart?c={encoded}"

    return {
        "backend": "quickchart",
        "config": config,
        "url": url,
    }
