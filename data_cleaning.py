import re
import pandas as pd
import numpy as np


MISSING_TEXT_VALUES = {
    "", "nan", "none", "null", "n/a", "na", "nil"
}

DATE_NAME_HINTS = (
    "date", "time", "created", "updated", "dob", "birth_date",
)


def clean_column_names(df):
    """Make column names consistent and unique."""
    cleaned = df.copy()
    names = []
    seen = {}

    for index, column in enumerate(cleaned.columns, start=1):
        name = str(column).strip()
        name = re.sub(r"\s+", "_", name)
        name = re.sub(r"[^\w]+", "_", name)
        name = re.sub(r"_+", "_", name).strip("_")

        if not name:
            name = f"Column_{index}"

        base_name = name
        count = 1
        while name in seen:
            count += 1
            name = f"{base_name}_{count}"

        seen[name] = True
        names.append(name)

    cleaned.columns = names
    return cleaned


def clean_text_values(df):
    """Trim text and convert common text placeholders to missing values."""
    cleaned = df.copy()
    text_columns = cleaned.select_dtypes(include=["object", "string"]).columns

    for column in text_columns:
        values = cleaned[column].astype("string").str.strip()
        lower_values = values.str.lower()
        values = values.mask(lower_values.isin(MISSING_TEXT_VALUES), pd.NA)
        cleaned[column] = values

    return cleaned


def detect_date_columns(df):
    """Detect date columns only when the name and values both look date-like."""
    date_columns = []

    for column in df.columns:
        series = df[column]

        if pd.api.types.is_datetime64_any_dtype(series):
            date_columns.append(column)
            continue

        if not (
            pd.api.types.is_object_dtype(series)
            or pd.api.types.is_string_dtype(series)
        ):
            continue

        name = str(column).lower()
        if not any(hint in name for hint in DATE_NAME_HINTS):
            continue

        values = series.dropna()
        if len(values) < 3:
            continue

        try:
            parsed = pd.to_datetime(values, errors="coerce", format="mixed")
        except (TypeError, ValueError):
            parsed = pd.to_datetime(values, errors="coerce")

        if parsed.notna().mean() >= 0.90:
            date_columns.append(column)

    return date_columns


def convert_numeric_like_columns(df, date_columns):
    """Convert text columns to numbers when almost all non-missing values are numeric."""
    cleaned = df.copy()
    converted_columns = []

    for column in cleaned.columns:
        if column in date_columns:
            continue

        if not (
            pd.api.types.is_object_dtype(cleaned[column])
            or pd.api.types.is_string_dtype(cleaned[column])
        ):
            continue

        values = cleaned[column].dropna()
        if len(values) < 3:
            continue

        numeric_values = pd.to_numeric(values, errors="coerce")
        if numeric_values.notna().mean() >= 0.95:
            cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")
            converted_columns.append(column)

    return cleaned, converted_columns


def detect_identifier_columns(df):
    """Find likely ID/code fields so they are not treated as measurements."""
    patterns = (
        r"^id$", r".*_id$", r"^id_.*", r".*uuid.*",
        r".*identifier.*", r".*roll[_-]?no.*",
        r".*student[_-]?no.*", r".*employee[_-]?no.*",
        r".*order[_-]?no.*", r".*customer[_-]?no.*",
        r".*account[_-]?no.*", r".*serial.*",
        r".*index$", r"^code$", r".*_code$",
    )

    identifiers = []
    for column in df.columns:
        name = str(column).lower().strip()
        if any(re.match(pattern, name) for pattern in patterns):
            identifiers.append(column)

    return identifiers


def fill_missing_values(df, numeric_columns, categorical_columns):
    """Fill numeric gaps with the median and text gaps with the most common value."""
    cleaned = df.copy()
    filled_numeric = {}
    filled_categorical = {}

    for column in numeric_columns:
        missing_count = int(cleaned[column].isna().sum())
        if missing_count == 0:
            continue

        median_value = cleaned[column].median()
        if pd.notna(median_value):
            cleaned[column] = cleaned[column].fillna(median_value)
            filled_numeric[column] = missing_count

    for column in categorical_columns:
        missing_count = int(cleaned[column].isna().sum())
        if missing_count == 0:
            continue

        common_values = cleaned[column].mode(dropna=True)
        if not common_values.empty:
            cleaned[column] = cleaned[column].fillna(common_values.iloc[0])
            filled_categorical[column] = missing_count

    return cleaned, filled_numeric, filled_categorical


def clean_dataset(raw_df):
    """Run the cleaning steps and return the cleaned data plus a change log."""
    original_rows = len(raw_df)
    cleaned = clean_column_names(raw_df)
    cleaned = clean_text_values(cleaned)

    duplicates_removed = int(cleaned.duplicated().sum())
    cleaned = cleaned.drop_duplicates().reset_index(drop=True)

    date_columns = detect_date_columns(cleaned)
    cleaned, converted_columns = convert_numeric_like_columns(cleaned, date_columns)

    for column in date_columns:
        try:
            cleaned[column] = pd.to_datetime(
                cleaned[column], errors="coerce", format="mixed"
            )
        except (TypeError, ValueError):
            cleaned[column] = pd.to_datetime(cleaned[column], errors="coerce")

    identifier_columns = detect_identifier_columns(cleaned)
    numeric_columns = [
        column for column in cleaned.select_dtypes(include=np.number).columns
        if column not in identifier_columns
        and not pd.api.types.is_bool_dtype(cleaned[column])
        and cleaned[column].nunique(dropna=True) > 1
    ]
    categorical_columns = [
        column for column in cleaned.select_dtypes(
            include=["object", "string", "category"]
        ).columns
        if column not in date_columns
    ]

    missing_before_fill = int(cleaned.isna().sum().sum())
    cleaned, filled_numeric, filled_categorical = fill_missing_values(
        cleaned, numeric_columns, categorical_columns
    )
    missing_after_fill = int(cleaned.isna().sum().sum())

    changes = []
    if duplicates_removed:
        changes.append(f"Removed {duplicates_removed:,} duplicate row(s).")
    if converted_columns:
        changes.append(f"Converted {len(converted_columns)} text column(s) to numeric values.")
    if date_columns:
        changes.append(f"Detected {len(date_columns)} date column(s).")
    if filled_numeric:
        changes.append(
            f"Filled {sum(filled_numeric.values()):,} numeric missing value(s) using column medians."
        )
    if filled_categorical:
        changes.append(
            f"Filled {sum(filled_categorical.values()):,} categorical missing value(s) using the most common value."
        )
    if missing_after_fill:
        changes.append(f"Left {missing_after_fill:,} value(s) missing because they could not be filled safely.")

    info = {
        "original_rows": original_rows,
        "duplicates_removed": duplicates_removed,
        "date_columns": date_columns,
        "converted_numeric_columns": converted_columns,
        "filled_numeric": filled_numeric,
        "filled_categorical": filled_categorical,
        "missing_before_fill": missing_before_fill,
        "missing_after_fill": missing_after_fill,
        "changes": changes,
    }
    return cleaned, info
