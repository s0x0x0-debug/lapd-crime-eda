from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# -------------------- PAGE SETUP --------------------

st.set_page_config(
    page_title="Location & Reporting | LA Crime Dashboard",
    page_icon="🚔",
    layout="wide",
)

BASE_DIR = Path(__file__).resolve().parent.parent
SUMMARY_DIR = BASE_DIR / "data" / "dashboard" / "summaries"
LOGO_PATH = BASE_DIR / "assets" / "lapd_logo.png"

DETAIL_PATH = SUMMARY_DIR / "location_reporting_detail.parquet"
GEO_PATH = SUMMARY_DIR / "geo_sample.parquet"


# -------------------- LOAD DATA --------------------

missing_files = [
    path.name for path in [DETAIL_PATH, GEO_PATH]
    if not path.exists()
]

if missing_files:
    st.error("Location & Reporting summary data is missing.")
    st.write("Run prepare_detailed_dashboard_summaries.py first.")
    st.write(missing_files)
    st.stop()


@st.cache_data
def load_data():
    detail = pd.read_parquet(DETAIL_PATH)
    geo = pd.read_parquet(GEO_PATH)
    return detail, geo


detail, geo_sample = load_data()


# -------------------- KPI CARD FUNCTION --------------------


def render_kpi_card(label, value):

    st.html(
        f"""
        <div style="
            border: 1px solid rgba(128, 128, 128, 0.25);
            border-radius: 0.65rem;
            padding: 1rem 1.1rem;
            min-height: 115px;
            background-color: rgba(128, 128, 128, 0.08);
            display: flex;
            flex-direction: column;
            justify-content: center;
            box-sizing: border-box;
        ">
            <div style="
                font-size: 0.85rem;
                font-weight: 600;
                color: rgba(128, 128, 128, 1);
                margin-bottom: 0.5rem;
            ">
                {label}
            </div>
            <div style="
                font-size: 1.35rem;
                font-weight: 650;
                line-height: 1.3;
                word-wrap: break-word;
                overflow-wrap: anywhere;
            ">
                {value}
            </div>
        </div>
        """,
        width="stretch",
    )

# -------------------- HELPER FUNCTIONS --------------------

def get_options(data, column):
    """Return sorted, non-missing filter options."""
    return sorted(data[column].dropna().unique().tolist())


def render_kpi(label, value):
    st.metric(label, value)


def make_bar_chart(data, x, y, title, labels, horizontal=False):
    """Create a reusable bar chart."""
    if horizontal:
        data = data.sort_values(x)

    fig = px.bar(
        data,
        x=x,
        y=y,
        title=title,
        labels=labels,
        orientation="h" if horizontal else "v",
        text="incident_count" if "incident_count" in data.columns else None,
    )

    if "incident_count" in data.columns:
        fig.update_traces(
            texttemplate="%{text:,}",
            textposition="outside",
        )

    fig.update_layout(
        margin={"l": 10, "r": 20, "t": 60, "b": 10}
    )

    st.plotly_chart(
        fig,
        width="stretch",
        theme="streamlit",
        config={"displaylogo": False, "responsive": True},
    )


def weighted_median(data):
    """Calculate the median using incident counts as weights."""
    data = data[data["reporting_lag_days"] >= 0]

    if data.empty:
        return None

    distribution = (
        data.groupby("reporting_lag_days")["incident_count"]
        .sum()
        .sort_index()
    )

    total = distribution.sum()

    if total == 0:
        return None

    cumulative = distribution.cumsum()

    lower = distribution.index[
        cumulative >= (total + 1) // 2
    ][0]

    upper = distribution.index[
        cumulative >= (total + 2) // 2
    ][0]

    return (float(lower) + float(upper)) / 2


def aggregate(data, column):
    """Count incidents by a selected category."""
    return (
        data.groupby(column, as_index=False)["incident_count"]
        .sum()
        .sort_values("incident_count", ascending=False)
    )


# -------------------- SIDEBAR FILTERS --------------------

with st.sidebar:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=120)

    st.title("LA Crime Dashboard")
    st.caption("Location Analysis")
    st.divider()
    st.subheader("Location Filters")

    years = sorted(detail["year"].dropna().astype(int).unique())
    year_options = ["All Years"] + years

    selected_years = st.multiselect(
        "Year",
        year_options,
        default=["All Years"],
    )

    if not selected_years or "All Years" in selected_years:
        selected_years = ["All Years"]

    crimes = get_options(detail, "Crm Cd Desc")
    selected_crimes = st.multiselect(
        "Crime Type", crimes, placeholder="All Crime Types"
    )

    areas = get_options(detail, "AREA NAME")
    selected_areas = st.multiselect(
        "LAPD Area", areas, placeholder="All Areas"
    )

    premises = get_options(detail, "Premis Desc")
    selected_premises = st.multiselect(
        "Premise", premises, placeholder="All Premises"
    )


# -------------------- APPLY FILTERS --------------------

filtered = detail.copy()

filters = {
    "year": None if "All Years" in selected_years
            else selected_years,
    "Crm Cd Desc": selected_crimes,
    "AREA NAME": selected_areas,
    "Premis Desc": selected_premises,
}

for column, selection in filters.items():
    if selection:
        filtered = filtered[filtered[column].isin(selection)]

if filtered.empty:
    st.warning("No records match your selected filters.")
    st.stop()


# -------------------- PAGE HEADER --------------------

st.title("Location & Reporting")
st.caption(
    "Explore crime locations, common premises, and reporting delays "
    "using the selected filters."
)


# -------------------- KPI CARDS --------------------

total_incidents = int(filtered["incident_count"].sum())

area_totals = aggregate(filtered, "AREA NAME")
premise_totals = aggregate(filtered, "Premis Desc")

median_lag = weighted_median(filtered)

kpis = st.columns(4)

with kpis[0]:
    render_kpi_card("Total Incidents", f"{total_incidents:,}")

with kpis[1]:
    render_kpi_card("Most Common LAPD Area", area_totals.iloc[0]["AREA NAME"])

with kpis[2]:
    render_kpi_card("Most Common Premise", premise_totals.iloc[0]["Premis Desc"])

with kpis[3]:
    render_kpi_card(
        "Median Reporting Lag",
        "N/A" if median_lag is None else f"{median_lag:,.1f} days",
    )


# -------------------- TOP 10 AREAS --------------------

st.divider()
st.subheader("Top 10 LAPD Areas")

top_areas = area_totals.head(10)

make_bar_chart(
    top_areas,
    x="incident_count",
    y="AREA NAME",
    title="Top 10 LAPD Areas by Recorded Incidents",
    labels={
        "incident_count": "Number of Incidents",
        "AREA NAME": "LAPD Area",
    },
    horizontal=True,
)


# -------------------- TOP 10 PREMISES --------------------

st.divider()
st.subheader("Top 10 Premises")

top_premises = premise_totals.head(10)

make_bar_chart(
    top_premises,
    x="incident_count",
    y="Premis Desc",
    title="Top 10 Premise Types by Recorded Incidents",
    labels={
        "incident_count": "Number of Incidents",
        "Premis Desc": "Premise",
    },
    horizontal=True,
)


# -------------------- CRIME COMPARISON --------------------

st.divider()
st.subheader("Crime Composition Across LAPD Areas")

comparison_areas = st.multiselect(
    "Select LAPD areas to compare",
    area_totals["AREA NAME"].tolist(),
    default=area_totals["AREA NAME"].head(5).tolist(),
    key="location_area_comparison",
)

comparison = filtered[
    filtered["AREA NAME"].isin(comparison_areas)
].copy()

if comparison.empty:
    st.info("Select at least one LAPD area.")
else:
    top_crimes = (
        comparison.groupby("Crm Cd Desc")["incident_count"]
        .sum()
        .nlargest(5)
        .index
    )

    comparison = comparison[
        comparison["Crm Cd Desc"].isin(top_crimes)
    ]

    fig = px.bar(
        comparison,
        x="AREA NAME",
        y="incident_count",
        color="Crm Cd Desc",
        barmode="group",
        title="Top Crime Types Across Selected LAPD Areas",
        labels={
            "AREA NAME": "LAPD Area",
            "incident_count": "Number of Incidents",
            "Crm Cd Desc": "Crime Type",
        },
    )

    st.plotly_chart(fig, width="stretch", theme="streamlit")


# -------------------- REPORTING LAG DISTRIBUTION --------------------

st.divider()
st.subheader("Reporting Lag Distribution")

lag_data = filtered[
    filtered["reporting_lag_days"] >= 0
].copy()

if lag_data.empty:
    st.info("No valid reporting-lag data is available.")
else:
    lag_data["Lag Range"] = pd.cut(
        lag_data["reporting_lag_days"],
        bins=[-1, 1, 7, 30, 90, 180, 365, float("inf")],
        labels=[
            "0–1 days", "2–7 days", "8–30 days",
            "31–90 days", "91–180 days",
            "181–365 days", ">365 days",
        ],
    )

    lag_summary = (
        lag_data.groupby("Lag Range", observed=False, as_index=False)
        ["incident_count"].sum()
    )

    make_bar_chart(
        lag_summary,
        x="Lag Range",
        y="incident_count",
        title="Reporting Lag Distribution",
        labels={
            "Lag Range": "Reporting Lag",
            "incident_count": "Number of Incidents",
        },
    )

    st.caption(
        "Records without valid reporting delays are excluded."
    )


# -------------------- MEDIAN LAG BY YEAR --------------------

st.divider()
st.subheader("Median Reporting Lag by Year")

yearly_rows = []

for year, group in filtered.groupby("year"):
    median = weighted_median(group)

    if median is not None:
        yearly_rows.append({
            "year": int(year),
            "median_lag_days": median,
            "incident_count": int(
                group.loc[
                    group["reporting_lag_days"] >= 0,
                    "incident_count",
                ].sum()
            ),
        })

yearly = pd.DataFrame(yearly_rows)

if yearly.empty:
    st.info("No yearly reporting-lag data is available.")
else:
    fig = px.line(
        yearly,
        x="year",
        y="median_lag_days",
        markers=True,
        title="Median Reporting Lag by Occurrence Year",
        labels={
            "year": "Occurrence Year",
            "median_lag_days": "Median Lag (Days)",
        },
        hover_data={"incident_count": ":,"},
    )

    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, width="stretch", theme="streamlit")


# -------------------- GEOGRAPHIC MAP --------------------

st.divider()
st.subheader("Recorded Crime Locations")

map_filters = {
    "year": None if "All Years" in selected_years else selected_years,
    "Crm Cd Desc": selected_crimes,
    "AREA NAME": selected_areas,
    "Premis Desc": selected_premises,
}

map_data = geo_sample.copy()

for column, selection in map_filters.items():
    if selection:
        map_data = map_data[map_data[column].isin(selection)]

if map_data.empty:
    st.info("No sampled locations match your filters.")
else:
    fig = px.scatter_map(
        map_data,
        lat="LAT",
        lon="LON",
        color="AREA NAME",
        hover_data=[
            "Crm Cd Desc",
            "Premis Desc",
            "year",
        ],
        zoom=9,
        center={"lat": 34.05, "lon": -118.25},
        map_style="carto-positron",
        title="Sampled Incident Locations by LAPD Area",
        height=620,
    )

    fig.update_layout(margin={"l": 0, "r": 0, "t": 60, "b": 0})
    st.plotly_chart(fig, width="stretch", theme="streamlit")

    st.caption(
        "The map uses sampled records with valid coordinates, "
        "so it does not represent every incident."
    )


# -------------------- CURRENT SELECTION --------------------

st.divider()
st.subheader("Current Selection")

year_display = (
    "All Years"
    if "All Years" in selected_years
    else ", ".join(map(str, selected_years))
)

selection_col1, selection_col2 = st.columns(2)

with selection_col1:
    st.write(f"**Years:** {year_display}")
    st.write(
        "**Crime Types:** "
        + (f"{len(selected_crimes)} selected" if selected_crimes else "All")
    )
    st.write(
        "**LAPD Areas:** "
        + (f"{len(selected_areas)} selected" if selected_areas else "All")
    )

with selection_col2:
    st.write(
        "**Premises:** "
        + (f"{len(selected_premises)} selected" if selected_premises else "All")
    )
    st.write(f"**Filtered Incidents:** {total_incidents:,}")
    st.write(f"**Map Records:** {len(map_data):,}")


