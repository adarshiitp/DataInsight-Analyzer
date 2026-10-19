import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def create_bar_chart(summary_df, metric, aggregation):
    if summary_df.empty or "Value" not in summary_df.columns:
        return None

    data = summary_df.head(15)
    figure, axis = plt.subplots(figsize=(7.2, 4), dpi=110)
    axis.bar(data["Category"].astype(str), data["Value"])
    axis.set_title(f"{aggregation} of {metric}", loc="left", fontsize=12, fontweight="bold")
    axis.set_ylabel(metric)
    axis.tick_params(axis="x", rotation=25, labelsize=8)
    axis.grid(axis="y", alpha=0.2)
    axis.set_axisbelow(True)
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    figure.tight_layout()
    return figure


def create_trend_chart(df, date_column, metric):
    data = df[[date_column, metric]].copy()
    data[date_column] = pd.to_datetime(data[date_column], errors="coerce")
    data[metric] = pd.to_numeric(data[metric], errors="coerce")
    data = data.dropna().sort_values(date_column)

    if len(data) < 2:
        return None

    data = data.groupby(date_column, as_index=False)[metric].sum().sort_values(date_column)
    if len(data) < 2:
        return None
    if len(data) > 40:
        data = data.tail(40)

    figure, axis = plt.subplots(figsize=(6.5, 3.8), dpi=110)
    axis.plot(data[date_column], data[metric], marker="o" if len(data) <= 20 else None, linewidth=2)
    axis.set_title(f"{metric} over time", loc="left", fontsize=12, fontweight="bold")
    axis.set_ylabel(metric)
    axis.tick_params(axis="x", rotation=30, labelsize=8)
    axis.grid(axis="y", alpha=0.2)
    axis.set_axisbelow(True)
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    figure.tight_layout()
    return figure


def create_distribution_chart(df, metric):
    values = pd.to_numeric(df[metric], errors="coerce").dropna()
    if len(values) < 3 or values.nunique() < 2:
        return None

    bins = min(30, max(5, int(np.sqrt(len(values)))))
    figure, axis = plt.subplots(figsize=(6.5, 3.8), dpi=110)
    axis.hist(values, bins=bins)
    axis.set_title(f"{metric} distribution", loc="left", fontsize=12, fontweight="bold")
    axis.set_xlabel(metric)
    axis.set_ylabel("Frequency")
    axis.grid(axis="y", alpha=0.2)
    axis.set_axisbelow(True)
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    figure.tight_layout()
    return figure


def create_correlation_chart(df, columns):
    if len(columns) < 2:
        return None

    numeric_data = df[columns].apply(pd.to_numeric, errors="coerce")
    # Skip constant columns because their correlations cannot be calculated.
    usable_columns = [
        column for column in numeric_data.columns
        if numeric_data[column].nunique(dropna=True) > 1
    ]
    if len(usable_columns) < 2:
        return None

    correlation = numeric_data[usable_columns].corr()
    size = min(10, max(5.5, len(usable_columns) * 0.7))
    figure, axis = plt.subplots(figsize=(size, size * 0.8), dpi=110)
    image = axis.imshow(correlation.values, vmin=-1, vmax=1, aspect="auto", cmap="viridis")
    axis.set_xticks(range(len(usable_columns)))
    axis.set_yticks(range(len(usable_columns)))
    axis.set_xticklabels(usable_columns, rotation=45, ha="right", fontsize=8)
    axis.set_yticklabels(usable_columns, fontsize=8)

    for row in range(len(usable_columns)):
        for column in range(len(usable_columns)):
            value = correlation.iloc[row, column]
            if pd.notna(value):
                axis.text(column, row, f"{value:.2f}", ha="center", va="center", fontsize=7, color="white")

    axis.set_title("Correlation between numeric columns", loc="left", fontsize=12, fontweight="bold")
    figure.colorbar(image, ax=axis, fraction=0.035, pad=0.04)
    figure.tight_layout()
    return figure
