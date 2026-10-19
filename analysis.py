import pandas as pd
import numpy as np

from data_cleaning import detect_identifier_columns


def get_column_groups(df):
    """Return numeric, categorical, date, and identifier column lists."""
    date_columns = [
        column for column in df.columns
        if pd.api.types.is_datetime64_any_dtype(df[column])
    ]
    identifiers = detect_identifier_columns(df)

    numeric_columns = [
        column for column in df.select_dtypes(include=np.number).columns
        if column not in identifiers
        and not pd.api.types.is_bool_dtype(df[column])
        and df[column].nunique(dropna=True) > 1
    ]

    categorical_columns = [
        column for column in df.select_dtypes(
            include=["object", "string", "category", "bool"]
        ).columns
        if column not in date_columns
    ]

    return {
        "numeric": numeric_columns,
        "categorical": categorical_columns,
        "date": date_columns,
        "identifiers": identifiers,
    }


def get_category_summary(df, category, metric, aggregation="SUM"):
    """Summarize a numeric metric by category."""
    if category not in df.columns or metric not in df.columns:
        return pd.DataFrame(columns=["Category", "Value", "Share %"])

    data = df[[category, metric]].copy()
    data[metric] = pd.to_numeric(data[metric], errors="coerce")
    data = data.dropna(subset=[metric])

    if data.empty:
        return pd.DataFrame(columns=["Category", "Value", "Share %"])

    if aggregation == "SUM":
        grouped = data.groupby(category, dropna=False)[metric].sum()
    elif aggregation == "MEAN":
        grouped = data.groupby(category, dropna=False)[metric].mean()
    else:
        grouped = data.groupby(category, dropna=False)[metric].count()

    grouped = grouped.sort_values(ascending=False).head(20)
    result = grouped.rename_axis("Category").reset_index(name="Value")

    # Share is meaningful for SUM and COUNT. A mean is an average, not a share.
    if aggregation in ("SUM", "COUNT"):
        total = float(grouped.sum())
        result["Share %"] = (result["Value"] / total * 100).round(1) if total else 0.0
    else:
        result["Share %"] = "—"

    result["Category"] = result["Category"].astype(str)
    result["Value"] = pd.to_numeric(result["Value"], errors="coerce").round(2)
    return result


def get_dataset_summary(raw_df, cleaned_df, cleaning_info):
    return {
        "original_rows": len(raw_df),
        "cleaned_rows": len(cleaned_df),
        "columns": len(cleaned_df.columns),
        "original_missing": int(raw_df.isna().sum().sum()),
        "missing_after": int(cleaned_df.isna().sum().sum()),
        "duplicates_removed": cleaning_info["duplicates_removed"],
    }


def generate_insights(df, metric=None, category=None, date_column=None, cleaning_info=None):
    """Create a small set of plain-language findings from the data."""
    insights = []
    cleaning_info = cleaning_info or {}

    duplicates = cleaning_info.get("duplicates_removed", 0)
    missing = cleaning_info.get("missing_before_fill", 0)

    if duplicates:
        insights.append(f"{duplicates:,} duplicate row(s) were removed.")
    if missing:
        insights.append(
            f"{missing:,} missing value(s) were found before filling missing data."
        )

    if metric and metric in df.columns:
        values = pd.to_numeric(df[metric], errors="coerce").dropna()
        if not values.empty:
            insights.append(f"Average {metric}: {values.mean():,.2f}.")
            insights.append(f"Highest {metric}: {values.max():,.2f}.")
            insights.append(f"Lowest {metric}: {values.min():,.2f}.")

    if category and metric and category in df.columns and metric in df.columns:
        summary = get_category_summary(df, category, metric, "SUM")
        if not summary.empty:
            top = summary.iloc[0]
            insights.append(
                f"{top['Category']} has the highest total {metric} "
                f"among the displayed categories."
            )

    if date_column and metric and date_column in df.columns and metric in df.columns:
        trend = df[[date_column, metric]].copy()
        trend[metric] = pd.to_numeric(trend[metric], errors="coerce")
        trend = trend.dropna().sort_values(date_column)
        if len(trend) >= 2:
            # Aggregate by date first so the comparison is not based on row order.
            trend = trend.groupby(date_column, as_index=False)[metric].sum()
            if len(trend) >= 2:
                first_value = float(trend[metric].iloc[0])
                last_value = float(trend[metric].iloc[-1])
                if first_value != 0:
                    change = (last_value - first_value) / abs(first_value) * 100
                    if change >= 0.1:
                        insights.append(f"{metric} is {change:.1f}% higher on the latest date than on the earliest date.")
                    elif change <= -0.1:
                        insights.append(f"{metric} is {abs(change):.1f}% lower on the latest date than on the earliest date.")

    return insights[:8]
