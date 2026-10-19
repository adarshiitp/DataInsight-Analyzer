
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

from data_cleaning import clean_dataset
from analysis import (
    get_column_groups,
    generate_insights,
    get_category_summary,
    get_dataset_summary,
)
from visualizations import (
    create_bar_chart,
    create_distribution_chart,
    create_trend_chart,
    create_correlation_chart,
)
from report_generator import (
    create_csv_download,
    create_excel_download,
    create_text_report,
)


# ---------------------------------------------------------
# DATA LOADING AND CACHING
# ---------------------------------------------------------

@st.cache_data(show_spinner=False, max_entries=3)
def load_and_clean_file(file_bytes, filename):
    """Read and clean a dataset, then reuse the cached result."""

    if filename.lower().endswith(".csv"):
        try:
            raw_df = pd.read_csv(BytesIO(file_bytes))
        except UnicodeDecodeError:
            raw_df = pd.read_csv(
                BytesIO(file_bytes),
                encoding="latin-1",
            )
    else:
        raw_df = pd.read_excel(
            BytesIO(file_bytes),
            engine="openpyxl",
        )

    cleaned_df, cleaning_info = clean_dataset(raw_df)

    return raw_df, cleaned_df, cleaning_info


# ---------------------------------------------------------
# PAGE SETTINGS
# ---------------------------------------------------------

st.set_page_config(
    page_title="DataInsight Analyzer",
    page_icon="📊",
    layout="wide",
)

st.markdown(
    """
    <style>
    .stApp {
        background: #f7f8fa;
        color: #172033;
    }

    .block-container {
        max-width: 1200px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3 {
        color: #172033;
    }

    [data-testid="stMetric"] {
        background: white;
        border: 1px solid #e4e7ec;
        border-radius: 12px;
        padding: 14px 16px;
    }

    [data-testid="stFileUploader"] {
        background: white;
        border: 1px solid #e4e7ec;
        border-radius: 12px;
        padding: 8px;
    }

    .stDownloadButton > button {
        width: 100%;
        min-height: 42px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# HEADER AND FILE UPLOAD
# ---------------------------------------------------------

st.title("DataInsight Analyzer")

st.caption(
    "Clean raw data, explore patterns, visualize results, "
    "and generate a report from CSV or Excel files."
)

uploaded_file = st.file_uploader(
    "Upload a CSV or Excel file",
    type=["csv", "xlsx"],
    help="Supported formats: .csv and .xlsx",
)

if uploaded_file is None:
    st.info(
        "Upload a dataset to begin. "
        "Your file is processed in this app session."
    )
    st.stop()


# ---------------------------------------------------------
# LOAD AND CLEAN DATA
# ---------------------------------------------------------

try:
    file_bytes = uploaded_file.getvalue()

    with st.spinner("Reading and preparing your dataset..."):
        raw_df, cleaned_df, cleaning_info = load_and_clean_file(
            file_bytes,
            uploaded_file.name,
        )

except Exception as error:
    st.error(
        "We couldn't process this file. "
        f"Please check the file format and try again. Details: {error}"
    )
    st.stop()


if raw_df.empty or len(raw_df.columns) == 0:
    st.warning(
        "This file does not contain any usable rows or columns."
    )
    st.stop()


# ---------------------------------------------------------
# COLUMN INFORMATION AND DATASET SUMMARY
# ---------------------------------------------------------

column_groups = get_column_groups(cleaned_df)

numeric_columns = column_groups["numeric"]
categorical_columns = column_groups["categorical"]
date_columns = column_groups["date"]
identifier_columns = column_groups["identifiers"]

summary = get_dataset_summary(
    raw_df,
    cleaned_df,
    cleaning_info,
)


# ---------------------------------------------------------
# DATASET OVERVIEW
# ---------------------------------------------------------

st.subheader("Dataset Overview")

metric_columns = st.columns(4)

row_difference = (
    summary["cleaned_rows"] - summary["original_rows"]
)

metric_columns[0].metric(
    "Rows",
    f"{summary['cleaned_rows']:,}",
    delta=(
        f"{row_difference:,}"
        if row_difference != 0
        else None
    ),
)

metric_columns[1].metric(
    "Columns",
    f"{summary['columns']:,}",
)

metric_columns[2].metric(
    "Missing values left",
    f"{summary['missing_after']:,}",
)

metric_columns[3].metric(
    "Numeric fields",
    f"{len(numeric_columns):,}",
)


# ---------------------------------------------------------
# DATA CLEANING DETAILS
# ---------------------------------------------------------

st.subheader("Data Cleaning")

if cleaning_info["changes"]:
    st.success(
        "Dataset prepared. Review the changes below "
        "before using the results."
    )

    with st.expander("View cleaning details"):
        for change in cleaning_info["changes"]:
            st.write(f"• {change}")

        st.caption(
            "The original uploaded data is not modified on disk. "
            "Cleaning is applied to an in-memory copy."
        )
else:
    st.info("No common cleaning changes were needed.")


# ---------------------------------------------------------
# DATA HEALTH
# ---------------------------------------------------------

st.subheader("Data Health")

if summary["missing_after"] == 0:
    st.success(
        "The cleaned dataset has no missing values."
    )
else:
    st.warning(
        f"{summary['missing_after']:,} missing value(s) remain "
        "and could not be filled safely."
    )

    missing_by_column = cleaned_df.isna().sum()
    missing_by_column = missing_by_column[
        missing_by_column > 0
    ].sort_values(ascending=False)

    st.dataframe(
        pd.DataFrame(
            {
                "Column": missing_by_column.index,
                "Missing values": missing_by_column.values,
            }
        ),
        use_container_width=True,
        hide_index=True,
    )


# ---------------------------------------------------------
# DETECTED COLUMN TYPES
# ---------------------------------------------------------

with st.expander("View detected column types"):

    type_col1, type_col2, type_col3 = st.columns(3)

    with type_col1:
        st.markdown("**Numeric columns**")
        st.write(
            ", ".join(numeric_columns)
            if numeric_columns
            else "None detected"
        )

    with type_col2:
        st.markdown("**Categorical columns**")
        st.write(
            ", ".join(categorical_columns)
            if categorical_columns
            else "None detected"
        )

    with type_col3:
        st.markdown("**Date columns**")
        st.write(
            ", ".join(date_columns)
            if date_columns
            else "None detected"
        )

    if identifier_columns:
        st.markdown("**Columns treated as identifiers**")
        st.write(", ".join(identifier_columns))


# ---------------------------------------------------------
# CHOOSE DEFAULT COLUMNS
# ---------------------------------------------------------

default_metric = (
    numeric_columns[0]
    if numeric_columns
    else None
)

for preferred_word in (
    "sales",
    "revenue",
    "amount",
    "profit",
    "income",
    "price",
    "score",
    "quantity",
):
    matching = [
        column
        for column in numeric_columns
        if preferred_word in column.lower()
    ]

    if matching:
        default_metric = matching[0]
        break


default_category = None

for column in categorical_columns:
    unique_count = cleaned_df[column].nunique(dropna=True)

    if 2 <= unique_count <= 15:
        default_category = column
        break

if default_category is None and categorical_columns:
    default_category = categorical_columns[0]


default_date = None

for column in date_columns:
    if not any(
        word in column.lower()
        for word in ("birth", "dob")
    ):
        default_date = column
        break


# ---------------------------------------------------------
# KEY INSIGHTS
# ---------------------------------------------------------

insights = generate_insights(
    cleaned_df,
    metric=default_metric,
    category=default_category,
    date_column=default_date,
    cleaning_info=cleaning_info,
)

st.subheader("Key Insights")

if insights:
    insight_columns = st.columns(2)

    for index, insight in enumerate(insights):
        with insight_columns[index % 2]:
            st.info(insight)
else:
    st.caption(
        "There is not enough suitable data to generate "
        "automatic insights."
    )


# ---------------------------------------------------------
# VISUAL ANALYSIS
# ---------------------------------------------------------

st.subheader("Visual Analysis")

if not numeric_columns:
    st.info(
        "No suitable numeric columns were detected, "
        "so numeric charts are unavailable."
    )

else:
    control1, control2, control3 = st.columns(3)

    with control1:
        if categorical_columns:
            selected_category = st.selectbox(
                "Category",
                options=categorical_columns,
                index=(
                    categorical_columns.index(default_category)
                    if default_category in categorical_columns
                    else 0
                ),
            )
        else:
            selected_category = None
            st.selectbox(
                "Category",
                options=["No category available"],
                disabled=True,
            )

    with control2:
        selected_metric = st.selectbox(
            "Numeric metric",
            options=numeric_columns,
            index=(
                numeric_columns.index(default_metric)
                if default_metric in numeric_columns
                else 0
            ),
        )

    with control3:
        aggregation = st.selectbox(
            "Calculation",
            ["SUM", "MEAN", "COUNT"],
        )

    if selected_category:
        grouped = get_category_summary(
            cleaned_df,
            selected_category,
            selected_metric,
            aggregation,
        )

        if not grouped.empty:
            chart_col, table_col = st.columns([1.6, 1])

            with chart_col:
                figure = create_bar_chart(
                    grouped,
                    selected_metric,
                    aggregation,
                )

                if figure is not None:
                    st.pyplot(
                        figure,
                        use_container_width=True,
                    )
                    plt.close(figure)

            with table_col:
                st.markdown("**Category Summary**")
                st.dataframe(
                    grouped,
                    use_container_width=True,
                    hide_index=True,
                )
        else:
            st.caption(
                "There are no valid values for this category "
                "and metric combination."
            )

    trend_col, distribution_col = st.columns(2)

    with trend_col:
        st.markdown("**Trend over time**")

        useful_dates = [
            column
            for column in date_columns
            if not any(
                word in column.lower()
                for word in ("birth", "dob")
            )
        ]

        if useful_dates:
            selected_date = st.selectbox(
                "Date column",
                useful_dates,
            )

            trend_figure = create_trend_chart(
                cleaned_df,
                selected_date,
                selected_metric,
            )

            if trend_figure is not None:
                st.pyplot(
                    trend_figure,
                    use_container_width=True,
                )
                plt.close(trend_figure)
            else:
                st.caption(
                    "Not enough valid date values to draw a trend."
                )
        else:
            st.caption(
                "No likely event-date column was detected. "
                "Birth dates are not used as default trends."
            )

    with distribution_col:
        st.markdown(
            f"**{selected_metric} distribution**"
        )

        distribution_figure = create_distribution_chart(
            cleaned_df,
            selected_metric,
        )

        if distribution_figure is not None:
            st.pyplot(
                distribution_figure,
                use_container_width=True,
            )
            plt.close(distribution_figure)
        else:
            st.caption(
                "Not enough numeric values to draw a distribution."
            )


# ---------------------------------------------------------
# CORRELATION ANALYSIS
# ---------------------------------------------------------

if len(numeric_columns) >= 2:
    st.subheader("Relationships")

    correlation_columns = numeric_columns[:10]

    correlation_figure = create_correlation_chart(
        cleaned_df,
        correlation_columns,
    )

    if correlation_figure is not None:
        st.caption(
            "Correlation shows relationships between numeric "
            "columns; it does not prove cause and effect."
        )

        st.pyplot(
            correlation_figure,
            use_container_width=True,
        )
        plt.close(correlation_figure)


# ---------------------------------------------------------
# CLEANED DATA PREVIEW
# ---------------------------------------------------------

st.subheader("Cleaned Data Preview")

st.caption(
    f"Showing the first {min(15, len(cleaned_df)):,} rows."
)

st.dataframe(
    cleaned_df.head(15),
    use_container_width=True,
    hide_index=True,
)


# ---------------------------------------------------------
# DOWNLOAD RESULTS
# ---------------------------------------------------------

st.subheader("Download Results")

st.caption(
    "Export the cleaned data, analysis workbook, "
    "or readable insights report."
)

try:
    csv_data = create_csv_download(
        cleaned_df,
        date_columns,
    )

    excel_data = create_excel_download(
        cleaned_df,
        summary,
        insights,
        column_groups,
    )

    report_text = create_text_report(
        uploaded_file.name,
        summary,
        cleaning_info,
        column_groups,
        insights,
    )

except Exception as error:
    st.error(
        f"We couldn't prepare the downloads. Details: {error}"
    )
    st.stop()


download1, download2, download3 = st.columns(3)

with download1:
    st.markdown("**Cleaned data**")
    st.caption("CSV file")

    st.download_button(
        "Download CSV",
        data=csv_data,
        file_name="datainsight_cleaned_data.csv",
        mime="text/csv",
        use_container_width=True,
        key="download_csv",
    )

with download2:
    st.markdown("**Analysis workbook**")
    st.caption("Excel file with summary and insights")

    if excel_data is not None:
        st.download_button(
            "Download Excel",
            data=excel_data,
            file_name="datainsight_analysis.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            use_container_width=True,
            key="download_excel",
        )
    else:
        st.warning(
            "Excel export is unavailable. "
            "Install openpyxl to enable it."
        )

with download3:
    st.markdown("**Insights report**")
    st.caption("Readable text report")

    st.download_button(
        "Download Report",
        data=report_text,
        file_name="datainsight_report.txt",
        mime="text/plain",
        use_container_width=True,
        key="download_report",
    )


# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------



st.divider()

st.markdown("### 📊 Thanks for using DataInsight Analyzer")
col1, col2, col3 = st.columns(3)

with col1:
    st.link_button("Developer GitHub", "https://github.com/adarshiitp")

with col2:
    st.link_button(
        "Source Code",
        "https://github.com/adarshiitp/DataInsight_Analyzer"
    )


