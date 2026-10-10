# LA Crime Analytics Dashboard

An exploratory data analysis (EDA) project for recorded Los Angeles Police Department (LAPD) crime incidents. The project combines a documented cleaning workflow, exploratory notebooks, precomputed Parquet assets, and a five-page interactive Streamlit dashboard.

> **Scope:** This is a descriptive analysis of a historical LAPD dataset snapshot, not an official LAPD product, a real-time crime monitor, a crime-rate study, a prediction system, or a causal analysis.

## Project snapshot

- **Occurrence-date coverage:** January 1, 2010–December 30, 2024, in the saved analytical dataset.
- **Cleaned master dataset:** 3,080,111 rows and 29 columns in the supplied notebook outputs.
- **Notebooks:** 3.
- **Streamlit pages:** 5.
- **Dashboard assets:** 21 precomputed Parquet summary/detail files are included under `data/dashboard/summaries/`.
- **Large inputs omitted:** the raw source CSVs and the generated master Parquet file are not included in this project package. The bundled dashboard summaries are sufficient to run the dashboard as supplied; the raw inputs are needed to rebuild the full pipeline.

Counts above describe the saved project snapshot. If the source data is refreshed or the cleaning rules change, rerun the pipeline and update the snapshot description as appropriate.

## What the project explores

The analysis investigates recorded incidents across:

- crime descriptions and yearly volume;
- annual and monthly patterns, weekday, hour, and time-of-day;
- LAPD geographic areas and premise descriptions;
- recorded victim age, sex, and descent fields;
- the elapsed time between occurrence and report dates;
- project-defined analytical crime and weapon groupings;
- cross-dimensional patterns, such as crime type by area or premise.

The notebooks provide the analytical workflow; the Streamlit app provides an interactive way to explore the prepared summaries.

## Dashboard pages

| Page | Purpose |
|---|---|
| **Main** | Overview KPIs, annual/monthly trends, leading crime descriptions, area and premise summaries. |
| **Crime & Time** | Filters and charts for crime, year, month, area, hour, weekday, and time-of-day patterns. |
| **Victims** | Recorded victim age, sex, descent, and age profiles across crime types. |
| **Location & Reporting** | Area and premise patterns, occurrence-to-reporting lag, and a sampled map of valid recorded coordinates. |
| **Crime Profile** | Project-defined crime categories, recorded status descriptions, and weapon-description groupings. |

The app reads the prepared Parquet files from `data/dashboard/summaries/`; it does not load the raw CSVs at page-render time.

## Project structure

```text
project EDA LAPD/
├── app.py
├── README.md
├── requirements.txt
├── environment.yml
├── .gitignore
├── .streamlit/
│   └── config.toml
├── assets/
│   └── lapd_logo.png
├── data/
│   ├── raw/                         # Put source CSVs here to rebuild the pipeline
│   ├── processed/                   # Generated cleaned master Parquet
│   └── dashboard/
│       ├── crime_data/              # Generated year-partitioned Parquet dataset
│       └── summaries/               # 21 bundled Parquet summary/detail assets
├── notebooks/
│   ├── 01_cleaning_phase.ipynb
│   ├── 02_data_visualizing.ipynb
│   └── 03_Data_Preparation.ipynb
└── pages/
    ├── 1_main.py
    ├── 2_crime_time.py
    ├── 3_victims.py
    ├── 4_location_reporting.py
    └── 5_crime_profile.py
```

### Notebook workflow

Run the notebooks in this order when rebuilding the analysis from source data:

1. **`01_cleaning_phase.ipynb`** — loads the two raw source CSVs, audits and cleans them, creates temporal features and the reporting-lag field, validates the resulting data, and writes `data/processed/crime_2010_2024.parquet`.
2. **`02_data_visualizing.ipynb`** — reads the cleaned master dataset and explores data quality, crime distributions, trends, area, time, victim fields, premises, weapons, geography, and reporting delay. It is an analysis notebook, not a required runtime dependency for the dashboard.
3. **`03_Data_Preparation.ipynb`** — reads the cleaned master file, creates year-partitioned Parquet data and dashboard summaries, derives dashboard-only analytical groupings, and validates generated outputs.

There are **three notebooks in this repository**. References to a fourth notebook or to preparation scripts not present in the repository are outdated; use the filenames listed above.

## Quick start: run the dashboard

### Requirements

- Python **3.12** (the environment file specifies Python 3.12.13).
- The installed dependencies listed in `requirements.txt`.
- The Parquet assets under `data/dashboard/summaries/`.

### 1. Create and activate an environment

**Windows PowerShell:**

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**macOS / Linux:**

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Start Streamlit

From the project root—the folder containing `app.py`—run:

```bash
streamlit run app.py
```

Open the local URL printed by Streamlit in your browser.

**Important:** file paths are case-sensitive on Linux and many deployment platforms. The page definition in `app.py` must point to `pages/2_crime_time.py`, matching the actual filename exactly.

### If the dashboard reports missing data

The supplied project package includes Parquet summaries. Confirm that these files exist under `data/dashboard/summaries/`, especially the files loaded directly by the pages:

- `yearly_crime.parquet`, `monthly_crime.parquet`, `crime_by_year.parquet`, `area_by_year.parquet`, `premise_by_year.parquet` — Main;
- `crime_time_detail.parquet` — Crime & Time;
- `victim_profile.parquet` — Victims;
- `location_reporting_detail.parquet`, `geo_sample.parquet` — Location & Reporting;
- `crime_profile_detail.parquet` — Crime Profile.

If one of the required assets is missing or you want to regenerate the dashboard data, follow the full pipeline instructions below. The dashboard can run from the bundled summaries without the raw CSVs or the cleaned master Parquet file.

## Rebuild the complete pipeline

### 1. Obtain the matching historical CSV files

The cleaning notebook expects these exact filenames:

```text
data/raw/Crime_Data_from_2010_to_2019.csv
data/raw/Crime_Data_from_2020_to_2024.csv
```

Download the historical datasets from the official Los Angeles Open Data Portal:

- [Crime Data from 2010 to 2019](https://data.lacity.org/Public-Safety/Crime-Data-from-2010-to-2019/63jg-8b9z)
- [Crime Data from 2020 to 2024 — legacy historical dataset](https://data.lacity.org/Public-Safety/Crime-Data-from-2020-to-2024/2nrs-mtv8)

The original CSVs are not bundled because they are large. Make sure you obtain compatible historical snapshots whose columns match the fields expected by `01_cleaning_phase.ipynb`; do not substitute a newer NIBRS export without adapting and validating the pipeline, because its schema and reporting unit differ.

### 2. Install dependencies

Use the environment setup above. `requirements.txt` pins the package versions used for this project, including Pandas, NumPy, Plotly, Streamlit, PyArrow, and Jupyter.

Alternatively, create the Conda environment from the supplied file:

```bash
conda env create -f environment.yml
conda activate EDA
```

### 3. Run the notebooks in order

The notebook paths use `../data/...` relative to the `notebooks/` directory. To keep those relative paths valid, start Jupyter from that directory:

```bash
cd notebooks
jupyter lab
```

Then open and run every cell from top to bottom in:

1. `01_cleaning_phase.ipynb`
2. `02_data_visualizing.ipynb`
3. `03_Data_Preparation.ipynb`

The expected outputs are:

- `data/processed/crime_2010_2024.parquet` — cleaned 29-column master dataset;
- `data/dashboard/crime_data/` — year-partitioned Parquet dataset;
- `data/dashboard/summaries/` — generated dashboard summary/detail Parquet files.

After rebuilding, return to the project root and run `streamlit run app.py`. Notebook outputs and the README snapshot counts should be refreshed if the input data or cleaning rules changed.

## Dashboard Parquet asset inventory

The supplied snapshot includes these 21 files in `data/dashboard/summaries/`:

```text
area_by_year.parquet
area_crime_by_year.parquet
crime_area_day_hour.parquet
crime_area_hour.parquet
crime_area_month.parquet
crime_area_time_of_day.parquet
crime_by_year.parquet
crime_profile_detail.parquet
crime_time_detail.parquet
geo_sample.parquet
location_reporting_detail.parquet
monthly_crime.parquet
premise_by_year.parquet
premise_crime_by_year.parquet
reporting_lag_by_year.parquet
reporting_lag_distribution.parquet
victim_age_by_year.parquet
victim_descent_by_year.parquet
victim_profile.parquet
victim_sex_by_year.parquet
yearly_crime.parquet
```

The dashboard primarily consumes the files listed under **“If the dashboard reports missing data”** above. Some additional summary files are generated for analysis and future dashboard extensions.

## Data cleaning and feature engineering

The cleaning notebook documents and implements decisions including:

- combining the historical 2010–2019 and 2020–2024 sources;
- parsing and validating occurrence and report dates;
- removing exact duplicate source rows while auditing duplicate incident identifiers;
- removing source columns not required by the analysis;
- treating invalid victim ages as missing rather than dropping the entire incident;
- turning invalid `(0, 0)` coordinate placeholders into missing values;
- preserving unknown or missing fields when there is no defensible value to impute;
- creating `year`, `month`, `month_name`, `day_of_week`, `day_name`, `hour`, `minute`, and `reporting_lag_days`;
- validating the final schema and exporting it to Parquet.

The engineered fields are derived from the occurrence date and recorded occurrence time. Negative occurrence-to-reporting lags are treated as missing for lag analysis.

## Cleaned master dataset schema

The cleaned master dataset contains 29 columns: 21 retained source fields plus 8 engineered fields. Types can be nullable after cleaning; inspect the Parquet schema rather than assuming every field is non-null.

| Column | Meaning |
|---|---|
| `DR_NO` | Incident/file identifier used for integrity checks. |
| `Date Rptd` | Date the incident was reported/recorded in the source system. |
| `DATE OCC` | Recorded occurrence date; defines the analysis time window. |
| `TIME OCC` | Recorded occurrence time in HHMM-style 24-hour form. |
| `AREA` | LAPD geographic-area code. |
| `AREA NAME` | LAPD geographic-area name. |
| `Rpt Dist No` | Reporting-district code within an area. |
| `Crm Cd` | Recorded crime code. |
| `Crm Cd Desc` | Human-readable crime description. |
| `Vict Age` | Recorded victim age; invalid values are treated as missing. |
| `Vict Sex` | Recorded victim sex code. |
| `Vict Descent` | Recorded victim descent code. |
| `Premis Cd` | Code for the premise/location type. |
| `Premis Desc` | Human-readable premise description. |
| `Weapon Used Cd` | Recorded weapon code, when available. |
| `Weapon Desc` | Recorded weapon description, when available. |
| `Status` | Source case-status code. |
| `Status Desc` | Human-readable source case-status description. |
| `LOCATION` | Source location text; the source may generalize addresses for privacy. |
| `LAT` | Recorded latitude; invalid zero placeholders are treated as missing. |
| `LON` | Recorded longitude; invalid zero placeholders are treated as missing. |
| `year` | Occurrence year derived from `DATE OCC`. |
| `month` | Occurrence month number, 1–12. |
| `month_name` | Occurrence month name. |
| `day_of_week` | Monday-based weekday index, 0–6. |
| `day_name` | Weekday name. |
| `hour` | Hour extracted from `TIME OCC`, 0–23 when valid. |
| `minute` | Minute extracted from `TIME OCC`, 0–59 when valid. |
| `reporting_lag_days` | Difference in days between `Date Rptd` and `DATE OCC`; negative values are treated as missing. |

The two dashboard-only groupings below are derived during dashboard preparation and are **not** part of the 29-column cleaned master schema.

## Analytical groupings used by the dashboard

`03_Data_Preparation.ipynb` creates two **project-defined heuristic groupings** for the dashboard:

- **`Crime Category (Analytical)`** — broad groupings based on text rules applied to source crime descriptions. These are not official LAPD, UCR, or FBI classifications.
- **`Weapon Category`** — readable groupings of the recorded weapon-description field.

These groupings are for exploratory summarization only. Text-based rules can misclassify edge cases and should not be treated as authoritative offence classifications.

## Data sources and currency

The source data is provided by the **Los Angeles Police Department (LAPD)** through the [Los Angeles Open Data Portal](https://data.lacity.org/). The project uses the legacy historical snapshots linked above.

LAPD's documentation states that the legacy `Crime Data from 2020 to 2024` dataset is no longer updated and is retained for historical reference. LAPD now publishes separate NIBRS datasets from its newer Records Management System; see the [LAPD NIBRS Offenses Dataset](https://data.lacity.org/Public-Safety/LAPD-NIBRS-Offenses-Dataset/k7nn-b2ep). The new reporting system can represent multiple offenses within an incident, so its counts may not be directly comparable to older records. This project does not merge the new NIBRS dataset into its historical snapshot.

For source terms and metadata, see the [Los Angeles Open Data Terms of Use](https://data.lacity.org/terms-of-use) and the dataset pages. The repository does not include a separate project-specific license file; check the applicable source terms before redistributing datasets or code.

## Interpretation and limitations

- **Incident counts are not crime rates.** The dashboard does not adjust counts for population, exposure, visitor activity, land use, or reporting patterns. A higher count does not by itself mean an area is more dangerous.
- **Treat the 2024 trend break cautiously.** The supplied occurrence-date series ends on December 30, 2024, and the LAPD reporting-system transition in March 2024 affects comparability. Do not interpret the visible decline as proof of an equivalent reduction in real-world crime.
- **Missing fields are not negative findings.** A missing weapon description does not prove no weapon was involved; missing demographic values should not be interpreted as a demographic category.
- **Recorded status is not a final case outcome.** A label such as `Open / Investigation Continued` should not automatically be described as “unsolved.”
- **The map is a sample.** `geo_sample.parquet` contains a deterministic sample of records with usable coordinates (15,000 points in the saved notebook output). It provides spatial context, not a complete point-level inventory. Locations are also subject to source privacy/generalization practices.
- **Associations are not causes.** This project is descriptive EDA; explaining why observed patterns occurred requires additional data and an appropriate study design.
- **The dashboard is historical, not live.** The bundled Parquet files are a fixed snapshot until they are regenerated.

## Troubleshooting

**`FileNotFoundError` for a Parquet file**

Confirm the expected file exists at the path named in the error. To rebuild the summaries, supply the raw CSV inputs and run notebooks 01 and 03 in order (Notebook 02 is the EDA stage between them).

**A notebook cannot find `data/raw` or `data/processed`**

Check the notebook's working directory. The notebooks use relative paths from `notebooks/`, so start Jupyter with `cd notebooks` as shown above, or update the code paths consistently for your preferred workspace convention.

**The Crime & Time page does not load on Linux/deployment**

Check that `app.py` references `pages/2_crime_time.py` with the same lower-case spelling as the file on disk.

**A chart or summary disagrees with another output**

Regenerate the cleaned dataset and all dashboard summaries from the same raw snapshot. Do not combine summary files generated from different versions of the master dataset.

## Acknowledgment

Recorded data is supplied by the Los Angeles Police Department through the Los Angeles Open Data Portal. The dashboard is an independent educational/analytical project and is not affiliated with or endorsed by LAPD or the City of Los Angeles.
