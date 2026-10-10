from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# -------------------- PATHS --------------------

BASE_DIR = Path(__file__).resolve().parent.parent
SUMMARY_PATH = BASE_DIR / "data" / "dashboard" / "summaries"
LOGO_PATH = BASE_DIR / "assets" / "lapd_logo.png"


# -------------------- LOAD DATA --------------------

@st.cache_data
def load_data():
    files = [
        "yearly_crime",
        "monthly_crime",
        "crime_by_year",
        "area_by_year",
        "premise_by_year",
    ]

    return {
        name: pd.read_parquet(SUMMARY_PATH / f"{name}.parquet")
        for name in files
    }


data = load_data()

yearly_crime = data["yearly_crime"]
monthly_crime = data["monthly_crime"]
crime_by_year = data["crime_by_year"]
area_by_year = data["area_by_year"]
premise_by_year = data["premise_by_year"]


# -------------------- KPI CARD --------------------

def render_kpi_card(label, value):
    st.html(
        f"""
        <div style="
            border: 1px solid rgba(128,128,128,0.25);
            border-radius: 10px;
            padding: 16px;
            min-height: 115px;
            background: rgba(128,128,128,0.08);
            display: flex;
            flex-direction: column;
            justify-content: center;
            box-sizing: border-box;
        ">
            <div style="font-size: 14px; color: gray; margin-bottom: 8px;">
                {label}
            </div>
            <div style="
                font-size: 21px;
                font-weight: 650;
                overflow-wrap: anywhere;
            ">
                {value}
            </div>
        </div>
        """,
        width="stretch",
    )


# -------------------- SIDEBAR --------------------

with st.sidebar:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=120)

    st.markdown("## LA Crime Dashboard")
    st.caption("Los Angeles crime data • 2010–2024")
    st.divider()

    st.markdown("### Overview Filter")

    years = sorted(yearly_crime["year"].dropna().astype(int).unique())
    year_options = ["All Years"] + years

    selected_years = st.multiselect(
        "Year",
        options=year_options,
        default=["All Years"],
        help="Choose one or more years to explore.",
    )

    if "All Years" in selected_years and len(selected_years) > 1:
        selected_years = ["All Years"]
        st.warning("All Years cannot be combined with individual years.")

    if not selected_years:
        selected_years = ["All Years"]
        st.info("No year selected. Showing All Years.")


# -------------------- FILTER DATA --------------------

tables = {
    "yearly": yearly_crime,
    "monthly": monthly_crime,
    "crime": crime_by_year,
    "area": area_by_year,
    "premise": premise_by_year,
}

filtered = {
    name: (
        df.copy()
        if "All Years" in selected_years
        else df[df["year"].isin(selected_years)].copy()
    )
    for name, df in tables.items()
}

yearly = filtered["yearly"]
monthly = filtered["monthly"]
crime = filtered["crime"]
area = filtered["area"]
premise = filtered["premise"]


# -------------------- PAGE HEADER --------------------

st.title("LA Crime Dashboard")

st.markdown(
    """
    Explore crime patterns across Los Angeles using recorded incidents
    from **January 2010 through December 2024**.

    The Overview page summarizes incident volume, common crime types,
    peak periods, and LAPD areas. Use the navigation menu for detailed
    analysis.
    """
)

if yearly.empty:
    st.warning("No incidents match the selected years.")
    st.stop()


# -------------------- KPI CALCULATIONS --------------------

total_incidents = int(yearly["incident_count"].sum())


def get_top_category(df, column):
    totals = df.groupby(column)["incident_count"].sum()

    return totals.idxmax() if not totals.empty else "N/A"


most_common_crime = get_top_category(crime, "Crm Cd Desc")
most_common_premise = get_top_category(premise, "Premis Desc")


# Peak period depends on the selected years.
if "All Years" in selected_years or len(selected_years) > 1:
    peak_year = yearly.loc[yearly["incident_count"].idxmax()]
    peak_period = int(peak_year["year"])
    peak_label = "Peak Crime Year"

else:
    if monthly.empty:
        peak_period = "N/A"
    else:
        peak_month = monthly.loc[monthly["incident_count"].idxmax()]
        peak_period = peak_month["month_name"]

    peak_label = "Peak Month"


# -------------------- DISPLAY KPIs --------------------

st.markdown("### Summary")

for col, label, value in zip(
    st.columns(4),
    [
        "Total Incidents",
        "Most Common Crime",
        peak_label,
        "Most Common Premise",
    ],
    [
        f"{total_incidents:,}",
        most_common_crime,
        peak_period,
        most_common_premise,
    ],
):
    with col:
        render_kpi_card(label, value)


# -------------------- CRIME TREND --------------------

st.markdown("### Crime Trend")

if "All Years" in selected_years:
    trend_data = yearly.sort_values("year")

    fig = px.line(
        trend_data,
        x="year",
        y="incident_count",
        markers=True,
        title="Crime Incidents by Year",
        labels={
            "year": "Year",
            "incident_count": "Number of Incidents",
        },
    )

elif len(selected_years) == 1:
    month_order = [
        "January", "February", "March", "April",
        "May", "June", "July", "August",
        "September", "October", "November", "December",
    ]

    trend_data = monthly.sort_values("month")

    fig = px.line(
        trend_data,
        x="month_name",
        y="incident_count",
        markers=True,
        title=f"Monthly Crime Incidents — {selected_years[0]}",
        labels={
            "month_name": "Month",
            "incident_count": "Number of Incidents",
        },
        category_orders={"month_name": month_order},
    )

else:
    trend_data = yearly.sort_values("year")

    fig = px.bar(
        trend_data,
        x="year",
        y="incident_count",
        text="incident_count",
        title="Crime Incidents for Selected Years",
        labels={
            "year": "Year",
            "incident_count": "Number of Incidents",
        },
    )

    fig.update_traces(
        texttemplate="%{text:,}",
        textposition="outside",
    )

fig.update_layout(hovermode="x unified")

st.plotly_chart(fig, width='stretch')


# -------------------- TOP 10 CHARTS --------------------

def render_top10_chart(df, column, title, x_label):
    top10 = (
        df.groupby(column)["incident_count"]
        .sum()
        .nlargest(10)
        .sort_values()
        .reset_index()
    )

    fig = px.bar(
        top10,
        x="incident_count",
        y=column,
        orientation="h",
        text="incident_count",
        title=title,
        labels={
            column: x_label,
            "incident_count": "Number of Incidents",
        },
    )

    fig.update_traces(
        texttemplate="%{text:,}",
        textposition="outside",
    )

    fig.update_layout(yaxis_title=None)

    st.plotly_chart(fig, width='stretch')


col1, col2 = st.columns(2)

with col1:
    st.markdown("### Top 10 Crime Types")
    render_top10_chart(
        crime,
        "Crm Cd Desc",
        "Top 10 Crime Types",
        "Crime Type",
    )

with col2:
    st.markdown("### Top 10 LAPD Areas")
    render_top10_chart(
        area,
        "AREA NAME",
        "Top 10 LAPD Areas by Incident Count",
        "LAPD Area",
    )


# -------------------- ABOUT THE DATASET --------------------

st.divider()
st.markdown("### About the Dataset")

dataset_info = [
    ("Coverage", "2010–2024"),
    ("Total Records", f"{int(yearly_crime['incident_count'].sum()):,}"),
    ("Source", "LAPD"),
    ("Primary Date", "DATE OCC"),
]

for col, (label, value) in zip(st.columns(4), dataset_info):
    with col:
        render_kpi_card(label, value)

st.caption(
    "The dashboard uses the cleaned and validated Parquet dataset "
    "produced by the data-cleaning workflow."
)