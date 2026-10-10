from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# -------------------- PAGE SETUP --------------------

st.set_page_config(
    page_title="Crime Profile | LA Crime Dashboard",
    page_icon="🚔",
    layout="wide",
)

BASE_DIR = Path(__file__).resolve().parent.parent
SUMMARY_DIR = BASE_DIR / "data" / "dashboard" / "summaries"
DATA_PATH = SUMMARY_DIR / "crime_profile_detail.parquet"
LOGO_PATH = BASE_DIR / "assets" / "lapd_logo.png"


# -------------------- LOAD DATA --------------------

if not DATA_PATH.exists():
    st.error("Crime Profile summary data is missing.")
    st.write("Run 03_Dashboard_Detailed_Summaries.ipynb first.")
    st.code(str(DATA_PATH))
    st.stop()


@st.cache_data
def load_data():
    data = pd.read_parquet(DATA_PATH)

    required_columns = [
        "year",
        "Crm Cd Desc",
        "Crime Category (Analytical)",
        "Status Desc",
        "Weapon Category",
        "incident_count",
    ]

    missing = [col for col in required_columns if col not in data.columns]

    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    data["year"] = pd.to_numeric(data["year"], errors="coerce").astype("Int64")
    data["incident_count"] = (
        pd.to_numeric(data["incident_count"], errors="coerce")
        .fillna(0)
        .astype("int64")
    )

    return data


profile = load_data()


# -------------------- DISPLAY ORDERS --------------------

CATEGORY_ORDER = [
    "Part 1 - Violent",
    "Part 1 - Property",
    "Part 2 - Simple Assault",
    "Part 2 - Financial/White Collar",
    "Part 2 - Statutory/Quality of Life",
    "Part 2 - Other / Miscellaneous",
]

STATUS_ORDER = [
    "Open / Investigation Continued",
    "Cleared (Adult Arrest)",
    "Cleared (Adult Other)",
    "Cleared (Juvenile Arrest)",
    "Cleared (Juvenile Other)",
    "Unknown",
]

WEAPON_ORDER = [
    "Firearm",
    "Edged Weapon",
    "Blunt Object",
    "Bodily Force / Threat",
    "Chemical / Special Weapon",
    "Other / Unknown Weapon",
    "No Weapon Recorded / Missing",
]


def ordered_options(data, column, preferred_order):
    """Keep the preferred order and append unexpected labels."""
    values = set(data[column].dropna().unique())

    return (
        [item for item in preferred_order if item in values]
        + sorted(values - set(preferred_order))
    )


def aggregate(data, column):
    """Calculate incident totals for each category."""
    return (
        data.groupby(column, as_index=False)["incident_count"]
        .sum()
        .sort_values("incident_count", ascending=False)
    )


def render_kpi(label, value):
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


def draw_bar(data, x, y, title, labels, horizontal=False):
    """Create a consistent bar chart."""
    if horizontal:
        data = data.sort_values(x)

    fig = px.bar(
        data,
        x=x,
        y=y,
        orientation="h" if horizontal else "v",
        title=title,
        labels=labels,
        text="incident_count" if "incident_count" in data.columns else None,
    )

    if "incident_count" in data.columns:
        fig.update_traces(
            texttemplate="%{text:,}",
            textposition="outside",
        )

    fig.update_layout(
        margin={"l": 10, "r": 25, "t": 60, "b": 10},
        yaxis_title=None if horizontal else y,
    )

    st.plotly_chart(
        fig,
        width="stretch",
        theme="streamlit",
        config={"displaylogo": False, "responsive": True},
    )


# -------------------- SIDEBAR --------------------

with st.sidebar:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=120)

    st.title("LA Crime Dashboard")
    st.caption("Crime Profile Analysis")
    st.divider()
    st.subheader("Crime Profile Filters")

    years = sorted(profile["year"].dropna().astype(int).unique().tolist())

    categories = ordered_options(
        profile, "Crime Category (Analytical)", CATEGORY_ORDER
    )
    crimes = sorted(profile["Crm Cd Desc"].dropna().unique().tolist())
    statuses = ordered_options(profile, "Status Desc", STATUS_ORDER)
    weapons = ordered_options(profile, "Weapon Category", WEAPON_ORDER)

    selected_years = st.multiselect(
        "Year",
        ["All Years"] + years,
        default=["All Years"],
    )

    if not selected_years or "All Years" in selected_years:
        selected_years = years

    selected_categories = st.multiselect(
        "Crime Category",
        ["All Crime Categories"] + categories,
        default=["All Crime Categories"],
    )

    if (
        not selected_categories
        or "All Crime Categories" in selected_categories
    ):
        selected_categories = categories

    selected_crimes = st.multiselect(
        "Crime Type",
        ["All Crime Types"] + crimes,
        default=["All Crime Types"],
    )

    if not selected_crimes or "All Crime Types" in selected_crimes:
        selected_crimes = crimes

    selected_statuses = st.multiselect(
        "Case Status",
        ["All Case Statuses"] + statuses,
        default=["All Case Statuses"],
    )

    if not selected_statuses or "All Case Statuses" in selected_statuses:
        selected_statuses = statuses

    selected_weapons = st.multiselect(
        "Weapon Category",
        ["All Weapon Categories"] + weapons,
        default=["All Weapon Categories"],
    )

    if (
        not selected_weapons
        or "All Weapon Categories" in selected_weapons
    ):
        selected_weapons = weapons


# -------------------- APPLY FILTERS --------------------

st.title("Crime Profile")
st.write(
    "Explore recorded crime categories, case status, weapon categories, "
    "and crime types across different years."
)

filters = {
    "year": selected_years,
    "Crime Category (Analytical)": selected_categories,
    "Crm Cd Desc": selected_crimes,
    "Status Desc": selected_statuses,
    "Weapon Category": selected_weapons,
}

filtered = profile.copy()

for column, values in filters.items():
    filtered = filtered[filtered[column].isin(values)]

if filtered.empty:
    st.warning("No incidents match the selected filters.")
    st.stop()


# -------------------- KPI SUMMARY --------------------

total = int(filtered["incident_count"].sum())

category_totals = aggregate(filtered, "Crime Category (Analytical)")
status_totals = aggregate(filtered, "Status Desc")
weapon_totals = aggregate(filtered, "Weapon Category")

kpi_values = [
    ("Total Incidents", f"{total:,}"),
    (
        "Most Common Crime Category",
        category_totals.iloc[0]["Crime Category (Analytical)"],
    ),
    ("Most Common Case Status", status_totals.iloc[0]["Status Desc"]),
    ("Most Common Weapon Category", weapon_totals.iloc[0]["Weapon Category"]),
]

st.subheader("Summary")
columns = st.columns(4)

for column, (label, value) in zip(columns, kpi_values):
    with column:
        render_kpi(label, value)


# -------------------- CRIME CATEGORY DISTRIBUTION --------------------

st.divider()
st.subheader("Crime Category Distribution")

draw_bar(
    category_totals,
    x="incident_count",
    y="Crime Category (Analytical)",
    title="Recorded Incidents by Crime Category",
    labels={
        "incident_count": "Number of Incidents",
        "Crime Category (Analytical)": "Crime Category",
    },
    horizontal=True,
)


# -------------------- CATEGORY TRENDS --------------------

st.subheader("Crime Category Trends by Year")

yearly_categories = (
    filtered.groupby(
        ["year", "Crime Category (Analytical)"],
        as_index=False,
    )["incident_count"]
    .sum()
)

fig = px.line(
    yearly_categories,
    x="year",
    y="incident_count",
    color="Crime Category (Analytical)",
    markers=True,
    title="Annual Incident Counts by Crime Category",
    labels={
        "year": "Year",
        "incident_count": "Number of Incidents",
        "Crime Category (Analytical)": "Crime Category",
    },
    category_orders={
        "Crime Category (Analytical)": categories,
    },
)

fig.update_layout(hovermode="x unified")
st.plotly_chart(fig, width="stretch", theme="streamlit")


# -------------------- CASE STATUS AND WEAPONS --------------------

col1, col2 = st.columns(2)

with col1:
    st.subheader("Case Status")

    draw_bar(
        status_totals,
        x="incident_count",
        y="Status Desc",
        title="Incidents by Case Status",
        labels={
            "incident_count": "Number of Incidents",
            "Status Desc": "Case Status",
        },
        horizontal=True,
    )

with col2:
    st.subheader("Weapon Category")

    draw_bar(
        weapon_totals,
        x="incident_count",
        y="Weapon Category",
        title="Incidents by Weapon Category",
        labels={
            "incident_count": "Number of Incidents",
            "Weapon Category": "Weapon Category",
        },
        horizontal=True,
    )


# -------------------- CROSS-DIMENSIONAL ANALYSIS --------------------

st.divider()
st.subheader("Case Status Across Crime Categories")

status_category = (
    filtered.groupby(
        ["Crime Category (Analytical)", "Status Desc"],
        as_index=False,
    )["incident_count"]
    .sum()
)

fig = px.bar(
    status_category,
    x="Crime Category (Analytical)",
    y="incident_count",
    color="Status Desc",
    barmode="stack",
    title="Case Status by Crime Category",
    labels={
        "Crime Category (Analytical)": "Crime Category",
        "incident_count": "Number of Incidents",
        "Status Desc": "Case Status",
    },
    category_orders={
        "Crime Category (Analytical)": categories,
        "Status Desc": statuses,
    },
)

st.plotly_chart(fig, width="stretch", theme="streamlit")


st.subheader("Weapon Patterns Across Crime Categories")

weapon_category = (
    filtered.groupby(
        ["Crime Category (Analytical)", "Weapon Category"],
        as_index=False,
    )["incident_count"]
    .sum()
)

fig = px.bar(
    weapon_category,
    x="Crime Category (Analytical)",
    y="incident_count",
    color="Weapon Category",
    barmode="stack",
    title="Weapon Category by Crime Category",
    labels={
        "Crime Category (Analytical)": "Crime Category",
        "incident_count": "Number of Incidents",
        "Weapon Category": "Weapon Category",
    },
    category_orders={
        "Crime Category (Analytical)": categories,
        "Weapon Category": weapons,
    },
)

st.plotly_chart(fig, width="stretch", theme="streamlit")


# -------------------- TOP 10 CRIME TYPES --------------------

st.divider()
st.subheader("Top 10 Crime Types")

top_crimes = aggregate(filtered, "Crm Cd Desc").head(10)

draw_bar(
    top_crimes,
    x="incident_count",
    y="Crm Cd Desc",
    title="Top 10 Crime Types",
    labels={
        "incident_count": "Number of Incidents",
        "Crm Cd Desc": "Crime Type",
    },
    horizontal=True,
)


# -------------------- CURRENT SELECTION --------------------

st.divider()
st.subheader("Current Selection")

selection = [
    ("Years", len(selected_years), len(years), "All Years"),
    (
        "Crime Categories",
        len(selected_categories),
        len(categories),
        "All Categories",
    ),
    ("Crime Types", len(selected_crimes), len(crimes), "All Crime Types"),
    ("Case Statuses", len(selected_statuses), len(statuses), "All Statuses"),
    (
        "Weapon Categories",
        len(selected_weapons),
        len(weapons),
        "All Weapon Categories",
    ),
]

for start in range(0, len(selection), 3):
    cols = st.columns(min(3, len(selection) - start))

    for col, (label, count, total_options, all_label) in zip(
        cols, selection[start:start + 3]
    ):
        with col:
            value = all_label if count == total_options else f"{count} selected"
            st.metric(label, value)


