import pandas as pd


def calculate_normal_behavior(
    dataframe: pd.DataFrame,
    axis_columns: list[str],
) -> pd.DataFrame:
    """Calculate active-current statistics used by anomaly detection."""

    numeric_axes = dataframe[axis_columns].apply(
        pd.to_numeric,
        errors="coerce"
    )

    active_current = numeric_axes.where(
        numeric_axes > 0
    )

    return pd.DataFrame(
        {
            "Active Records": active_current.count(),
            "Mean Current": active_current.mean(),
            "Median Current": active_current.median(),
            "Standard Deviation": active_current.std(),
            "P05": active_current.quantile(0.05),
            "P95": active_current.quantile(0.95),
            "P99": active_current.quantile(0.99),
        }
    ).round(2)