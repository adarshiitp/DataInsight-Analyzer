# 📊 DataInsight Analyzer

A Python and Streamlit application that helps you **clean, analyze, and visualize datasets** with ease. Upload a CSV or Excel file to explore data quality, discover patterns, generate insights, and download reports.

## 🚀 Live Demo

🔗 **Live Project:** [Add your deployed app URL here](YOUR_STREAMLIT_APP_URL)


## ✨ Features

- 📂 **Upload Data** — Supports CSV and Excel (`.xlsx`) files.
- 👀 **Dataset Preview** — Explore your data and view row and column counts.
- 🧹 **Data Cleaning** — Standardizes column names, trims common text placeholders, and removes exact duplicate rows.
- 🔍 **Data Type Detection** — Identifies likely date and numeric columns.
- 🩹 **Missing Value Handling** — Fills numeric missing values with the median and categorical missing values with the most common value when available.
- 📈 **Data Visualization** — Explore distributions, category comparisons, date trends, and correlations.
- 💡 **Automated Insights** — Generates rule-based insights from the dataset.
- 📥 **Download Reports** — Export the cleaned dataset as CSV and download an Excel workbook and text summary report.

## 🛠️ Tech Stack

- **Language:** Python
- **App Framework:** Streamlit
- **Data Processing:** Pandas, NumPy
- **Visualization:** Matplotlib
- **Excel Support:** OpenPyXL

## ⚙️ Installation and Setup

### Requirements

- Python 3.10 or newer recommended
- pip

### 1. Clone the repository

```bash
git clone https://github.com/adarshhitp/DataInsight_Analyzer.git
cd DataInsight_Analyzer
```

### 2. Create a virtual environment

**Windows (PowerShell):**

```powershell
py -m venv .venv
.venv\Scripts\activate
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Run the application

```bash
streamlit run app.py
```

The application will open in your browser. Upload a CSV or Excel file to get started.

## 📁 Project Structure

```text
DataInsight_Analyzer/
├── app.py
├── data_cleaning.py
├── analysis.py
├── visualizations.py
├── report_generator.py
├── requirements.txt
├── README.md
├── .gitignore
└── sample_data/
    └── sample_sales.csv
```

## ⚠️ Notes and Limitations

- Data cleaning is rule-based. Review the cleaning summary before using the results.
- Numeric missing values are filled with the median; categorical missing values use the most common value when available.
- Automatic date detection may not identify every date column correctly.
- Correlation indicates association, not causation.
- Very large datasets may take longer to process and visualize.
- This application is intended for exploratory data analysis, not high-stakes decision-making.

## 👨‍💻 Author

**Adarsh**

- [GitHub Profile](https://github.com/adarshhitp)
- [Live Project](#idhar dal de dena bhai)

---

*Built with Python and Streamlit.*
