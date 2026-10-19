from io import BytesIO
import pandas as pd


def _format_dates_for_export(df, date_columns):
    export_df = df.copy()
    for column in date_columns:
        if column in export_df.columns:
            export_df[column] = pd.to_datetime(
                export_df[column], errors="coerce"
            ).dt.strftime("%Y-%m-%d")
    return export_df


def create_csv_download(df, date_columns):
    """Prepare the data for download as a CSV file."""
    export_df = _format_dates_for_export(df, date_columns)
    return export_df.to_csv(index=False).encode("utf-8-sig")


def create_excel_download(df, summary, insights, column_groups):
    """Create an Excel workbook for download, or return None if Excel support is unavailable."""
    try:
        buffer = BytesIO()
        summary_rows = [
            ("Original rows", summary["original_rows"]),
            ("Cleaned rows", summary["cleaned_rows"]),
            ("Columns", summary["columns"]),
            ("Original missing values", summary["original_missing"]),
            ("Missing values after cleaning", summary["missing_after"]),
            ("Duplicate rows removed", summary["duplicates_removed"]),
            ("Numeric fields", len(column_groups["numeric"])),
            ("Categorical fields", len(column_groups["categorical"])),
            ("Date fields", len(column_groups["date"])),
        ]

        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            _format_dates_for_export(df, column_groups["date"]).to_excel(
                writer, index=False, sheet_name="Cleaned Data"
            )
            pd.DataFrame(summary_rows, columns=["Metric", "Value"]).to_excel(
                writer, index=False, sheet_name="Summary"
            )
            pd.DataFrame({"Insight": insights}).to_excel(
                writer, index=False, sheet_name="Insights"
            )

            missing = df.isna().sum()
            missing = missing[missing > 0]
            quality_df = pd.DataFrame({
                "Column": missing.index,
                "Missing values": missing.values,
            })
            if quality_df.empty:
                quality_df = pd.DataFrame({"Status": ["No missing values remain"]})
            quality_df.to_excel(writer, index=False, sheet_name="Data Quality")

        return buffer.getvalue()
    except (ImportError, ModuleNotFoundError):
        return None


def create_text_report(filename, summary, cleaning_info, column_groups, insights):
    """Create a text report with the analysis results."""
    lines = [
        "DataInsight Analyzer",
        "=" * 24,
        f"Source file: {filename}",
        "",
        "DATASET SUMMARY",
        f"Original rows: {summary['original_rows']:,}",
        f"Cleaned rows: {summary['cleaned_rows']:,}",
        f"Columns: {summary['columns']:,}",
        f"Original missing values: {summary['original_missing']:,}",
        f"Missing values after cleaning: {summary['missing_after']:,}",
        f"Duplicate rows removed: {summary['duplicates_removed']:,}",
        "",
        "COLUMN TYPES",
        "Numeric: " + (", ".join(column_groups["numeric"]) or "None"),
        "Categorical: " + (", ".join(column_groups["categorical"]) or "None"),
        "Date: " + (", ".join(column_groups["date"]) or "None"),
        "",
        "CLEANING DETAILS",
    ]

    if cleaning_info["changes"]:
        lines.extend(f"- {change}" for change in cleaning_info["changes"])
    else:
        lines.append("- No common cleaning changes were needed.")

    lines.extend(["", "KEY INSIGHTS"])
    if insights:
        lines.extend(f"- {insight}" for insight in insights)
    else:
        lines.append("- No automatic insights were available for this dataset.")

    lines.extend([
        "",
        "Note: Automatically generated findings are descriptive and should be checked in context.",
    ])
    return "\n".join(lines)
