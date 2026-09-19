<<<<<<< HEAD
# Debt Data Analysis Project



## Overview

This repository analyzes debt-related indicators across countries by cleaning raw CSV data, reshaping it into a usable format, and exploring trends through summary statistics and visualizations.

The project combines:

- raw debt data
- metadata about countries and indicators
- exploratory data analysis (EDA)
- chart generation and profile reports
- optional notebook-based investigation

## Why this project

Debt data often arrives in wide, messy tabular formats. This project demonstrates how to:

- normalize raw country/year data
- join metadata to core financial indicators
- clean inconsistent values and missing entries
- summarize large datasets with pandas
- generate quick visual insights for reporting and exploration

## Features

- data cleaning and preprocessing for debt tables
- metadata enrichment from country and series files
- long-format transformation for easier analysis
- summary statistics and missing-value checks
- automated plotting for histograms, boxplots, and correlations
- optional Plotly-based interactive visualizations
- dataset profiling with HTML reports

## Project structure

```text
mini_pro_two/
├── Country-Series - Metadata.csv
├── IDS_ALLCountries_Data.csv
├── IDS_CountryMetaData.csv
├── IDS_FootNoteMetaData.csv
├── IDS_SeriesMetaData.csv
├── debt.py
├── eda_tools.py
├── run_eda.py
├── remove_year_columns.py
├── requirements.txt
├── test_series_metadata.py
├── debt.ipynb
├── README.md
└── output_plots/   # generated when running EDA scripts
```

## Datasets

- `IDS_ALLCountries_Data.csv`: main dataset containing country-year-indicator values
- `IDS_CountryMetaData.csv`: country attributes such as region and income group
- `IDS_SeriesMetaData.csv`: details about each debt-related series or indicator
- `IDS_FootNoteMetaData.csv`: footnotes associated with selected records
- `Country-Series - Metadata.csv`: mapping between country metadata and related series

## Data workflow

1. Load the raw CSV files.
2. Standardize country names, codes, and formatting.
3. Clean missing or invalid values.
4. Convert wide year-based data into a long-form structure.
5. Merge metadata with the main debt observations.
6. Aggregate by country, year, or series for analysis.
7. Produce charts, summary reports, and deeper insights.

## Setup

Create a virtual environment and install the required packages:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Quick start

Run the EDA script on the main debt data:

```powershell
python run_eda.py IDS_ALLCountries_Data.csv --plots-dir output_plots --corr output_plots/corr.png --report
```

This command will:

- print a dataframe summary
- show the most important missing-value issues
- save charts to the output directory
- create a correlation matrix image
- generate a profile report in HTML format

To create interactive Plotly charts instead:

```powershell
python run_eda.py IDS_ALLCountries_Data.csv --plots-dir output_plots --use-plotly
```

## Example analyses

This project supports questions such as:

- Which countries have the highest total debt?
- How do debt values change across years?
- Which series contribute most strongly to total debt?
- Which countries or indicators have the most missing data?
- How do debt values compare across metadata groups like region or income level?

## Main Python files

### `debt.py`
Contains the core data-processing and visualization logic used for exploring debt trends and preparing analytical outputs.

### `eda_tools.py`
Provides reusable EDA helpers for:

- loading CSVs
- generating summaries
- checking missing values
- creating histograms and boxplots
- computing correlation matrices
- generating profile reports

### `run_eda.py`
CLI runner that makes analysis quick and reproducible from the command line.

### `test_series_metadata.py`
Basic validation checks for metadata consistency and series-level assumptions.

## Notes

- The raw dataset is not always perfectly clean, so the code includes several normalization steps.
- The project focuses on analytical exploration and reporting rather than deployment or API production.
- It is a strong foundation for building a dashboard, database-backed reports, or a more advanced data pipeline.

## Future improvements

- build a Streamlit dashboard for interactive exploration
- add more automated validation tests
- create SQL or database versions of the cleaned data
- add more advanced visual storytelling and KPI summaries
- improve documentation for each field in the metadata tables

## License

This project is intended for educational and analytical use. If a formal license is added later, it should be documented here.


        elif selected_query == "Identify countries contributing more than 5% of global debt.":
            total_global_debt = all_countries_data['Value'].sum()
            result_df = (
                all_countries_data.groupby('Country Name', as_index=False)['Value']
                .sum()
                .query(f'Value > {0.05 * total_global_debt}')
            )
            st.write("Countries Contributing More than 5% of Global Debt")
            st.dataframe(result_df) 

        elif selected_query == "Find the most dominant indicator (highest contribution) for each country.":
            result_df = (
                all_countries_data.groupby(['Country Name', 'Series Code'], as_index=False)['Value']
                .sum()
                .sort_values(['Country Name', 'Value'], ascending=[True, False])
                .groupby('Country Name')
                .head(1)
            )
            st.write("Most Dominant Indicator for Each Country")
            st.dataframe(result_df)
=======
# Debt Data Analysis Project

A simple data analysis project for exploring debt trends, country metadata, and key macroeconomic indicators across countries.

## Overview

This project processes debt-related datasets from multiple CSV files, cleans inconsistent values, reshapes the data for analysis, and produces summaries and visualizations for country-level comparisons.

It is designed to help answer questions like:

- Which countries carry the highest debt burden?
- How do debt indicators change over time?
- Which metadata fields are most useful for comparing countries?
- What patterns appear across regions and income groups?

## Features

- Clean and standardize raw country metadata
- Fill missing values and normalize inconsistent entries
- Convert wide year-based data into long-form analysis tables
- Merge debt values with country and series metadata
- Generate descriptive statistics and visual insights
- Support quick exploration through Python and notebook workflows

## Tech Stack

- Python
- Pandas
- NumPy
- Matplotlib
- Seaborn
- Plotly
- Streamlit

## Project Structure

```text
mini_pro_two/
├── Country-Series - Metadata.csv
├── IDS_ALLCountries_Data.csv
├── IDS_CountryMetaData.csv
├── IDS_FootNoteMetaData.csv
├── IDS_SeriesMetaData.csv
├── debt.py
├── debt.ipynb
├── requirements.txt
├── README.md
└── .venv-1/
```

## Workflow

1. Load raw CSV files
2. Clean country and series metadata
3. Standardize names, codes, and numeric values
4. Transform data into a long-form structure
5. Merge metadata with debt indicators
6. Explore trends and produce charts

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run

Open the notebook for exploratory analysis:

```bash
jupyter notebook debt.ipynb
```

Or run the Streamlit app:

```bash
streamlit run debt.ipynb
```

## Example Analysis Questions

- Total debt by country
- Debt trends over time
- Country comparison by region or income group
- Dominant indicators per country
- Missing-value and metadata quality checks

## Why This Project

This project is a practical example of cleaning and analyzing real-world macroeconomic data. It demonstrates how raw international datasets can be transformed into a cleaner, more useful structure for decision-making and reporting.

## Future Improvements

- Add a richer interactive dashboard
- Improve metadata validation and reporting
- Expand chart summaries and KPI views
- Build a more user-friendly presentation layer

## License

This project is intended for educational and analytical use. If a formal license is added later, it should be documented here.


        elif selected_query == "Identify countries contributing more than 5% of global debt.":
            total_global_debt = all_countries_data['Value'].sum()
            result_df = (
                all_countries_data.groupby('Country Name', as_index=False)['Value']
                .sum()
                .query(f'Value > {0.05 * total_global_debt}')
            )
            st.write("Countries Contributing More than 5% of Global Debt")
            st.dataframe(result_df) 

        elif selected_query == "Find the most dominant indicator (highest contribution) for each country.":
            result_df = (
                all_countries_data.groupby(['Country Name', 'Series Code'], as_index=False)['Value']
                .sum()
                .sort_values(['Country Name', 'Value'], ascending=[True, False])
                .groupby('Country Name')
                .head(1)
            )
            st.write("Most Dominant Indicator for Each Country")
            st.dataframe(result_df)
