from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# ============================================================
# CONFIGURATION & PATHS
# ============================================================

st.set_page_config(
    page_title="Victims | LA Crime Dashboard",
    page_icon="🚔",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).resolve().parent.parent
SUMMARY_PATH = BASE_DIR / "data" / "dashboard" / "summaries"
DATA_PATH = SUMMARY_PATH / "victim_profile.parquet"
LOGO_PATH = BASE_DIR / "assets" / "lapd_logo.png"


# ============================================================
# LOAD DATA
# ============================================================

if not DATA_PATH.exists():
    st.error("Victims summary data is missing.")
    st.info(
        "Run 03_Dashboard_Data_Preparation.ipynb to generate "
        "victim_profile.parquet."
    )
    st.stop()


@st.cache_data
def load_data():
    df = pd.read_parquet(DATA_PATH, engine="pyarrow")
    df.columns = df.columns.str.strip()

    required = [
        "year",
        "Crm Cd Desc",
        "Vict Age",
        "Vict Sex",
        "Vict Descent",
        "incident_count",
    ]

    missing = [col for col in required if col not in df.columns]

    if missing:
        raise ValueError(
            f"Missing columns: {missing}. "
            "Regenerate victim_profile.parquet from the preparation notebook."
        )

    for col in ["year", "Vict Age", "incident_count"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["incident_count"] = df["incident_count"].fillna(0).astype("int64")

    return df


try:
    victim_profile = load_data()
except (ValueError, OSError) as error:
    st.error(str(error))
    st.stop()


# ============================================================
# CONSTANTS & HELPER FUNCTIONS
# ============================================================

DESCENT_MAP = {
    "A": "Other Asian",
    "B": "Black",
    "C": "Chinese",
    "D": "Cambodian",
    "F": "Filipino",
    "G": "Guamanian",
    "H": "Hispanic/Latin/Mexican",
    "I": "American Indian/Alaskan Native",
    "J": "Japanese",
    "K": "Korean",
    "L": "Laotian",
    "O": "Other",
    "P": "Pacific Islander",
    "S": "Samoan",
    "U": "Hawaiian",
    "V": "Vietnamese",
    "W": "White",
    "X": "Unknown",
    "Z": "Asian Indian",
    "Missing": "Missing",
}

DESCENT_REVERSE = {v: k for k, v in DESCENT_MAP.items()}

AGE_BINS = [0, 17, 24, 34, 44, 54, 64, 74, 84, 100]
AGE_LABELS = [
    "1–17", "18–24", "25–34", "35–44",
    "45–54", "55–64", "65–74", "75–84", "85–100",
]


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


def group_counts(df, columns):
    return df.groupby(
        columns, as_index=False, observed=True
    )["incident_count"].sum()


def show_chart(fig):
    st.plotly_chart(
        fig,
        width="stretch",
        theme="streamlit",
        config={"displaylogo": False, "responsive": True},
    )


def weighted_median(df):
    """Calculate the exact median from age values and aggregated counts."""
    ages = (
        df.dropna(subset=["Vict Age"])
        .groupby("Vict Age")["incident_count"]
        .sum()
        .sort_index()
    )

    total = int(ages.sum())

    if total == 0:
        return None

    cumulative = ages.cumsum()
    lower = ages.index[(cumulative >= (total + 1) // 2)][0]
    upper = ages.index[(cumulative >= (total + 2) // 2)][0]

    return (float(lower) + float(upper)) / 2


def format_number(value):
    if value is None:
        return "N/A"
    return f"{value:,.0f}" if value.is_integer() else f"{value:,.1f}"


def bar_chart(df, category, title, horizontal=False):
    fig = px.bar(
        df,
        x="incident_count" if horizontal else category,
        y=category if horizontal else "incident_count",
        orientation="h" if horizontal else "v",
        text="incident_count",
        title=title,
        labels={
            category: category,
            "incident_count": "Number of Incidents",
        },
    )

    fig.update_traces(
        texttemplate="%{text:,}",
        textposition="outside",
    )

    if horizontal:
        fig.update_layout(yaxis_title=None)

    show_chart(fig)


# ============================================================
# SIDEBAR FILTERS
# ============================================================

with st.sidebar:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=120)

    st.markdown("## LA Crime Dashboard")
    st.caption("Victim Analysis")
    st.divider()
    st.markdown("### Victim Filters")

    years = sorted(victim_profile["year"].dropna().astype(int).unique())

    selected_years = st.multiselect(
        "Year",
        ["All Years"] + years,
        default=["All Years"],
    )

    if not selected_years:
        selected_years = ["All Years"]
    elif "All Years" in selected_years and len(selected_years) > 1:
        selected_years = ["All Years"]

    crimes = sorted(victim_profile["Crm Cd Desc"].dropna().unique())

    selected_crimes = st.multiselect(
        "Crime Type", crimes, placeholder="All Crime Types"
    )

    sexes = sorted(victim_profile["Vict Sex"].dropna().unique())

    selected_sex = st.multiselect(
        "Victim Sex", sexes, placeholder="All Sex Categories"
    )

    descent_codes = sorted(victim_profile["Vict Descent"].dropna().unique())
    descent_labels = [DESCENT_MAP.get(code, code) for code in descent_codes]

    selected_descent_labels = st.multiselect(
        "Victim Descent",
        descent_labels,
        placeholder="All Descent Categories",
    )

    selected_descent = [
        DESCENT_REVERSE.get(label, label)
        for label in selected_descent_labels
    ]

    age_range = st.slider(
        "Victim Age Range",
        min_value=1,
        max_value=100,
        value=(1, 100),
        help="Missing victim ages remain in the total incident count.",
    )


# ============================================================
# HEADER & FILTER DATA
# ============================================================

st.title("Victim Analysis")

st.markdown(
    """
    Explore victim characteristics across **age, sex, descent, and crime type**.
    Use the sidebar to compare victim profiles across years and crime types.
    """
)

filtered = victim_profile.copy()

filters = {
    "year": [] if "All Years" in selected_years else selected_years,
    "Crm Cd Desc": selected_crimes,
    "Vict Sex": selected_sex,
    "Vict Descent": selected_descent,
}

for column, values in filters.items():
    if values:
        filtered = filtered[filtered[column].isin(values)]

# Retain missing ages in totals; exclude out-of-range known ages.
filtered = filtered[
    filtered["Vict Age"].isna()
    | filtered["Vict Age"].between(*age_range)
].copy()

if filtered.empty:
    st.warning("No records match your filters. Try widening your selections.")
    st.stop()


# ============================================================
# SUMMARY CALCULATIONS
# ============================================================

total_incidents = int(filtered["incident_count"].sum())

age_data = (
    filtered.dropna(subset=["Vict Age"])
    .groupby("Vict Age", as_index=False)["incident_count"]
    .sum()
    .sort_values("Vict Age")
)

median_age = weighted_median(filtered)

sex_totals = group_counts(filtered, ["Vict Sex"]).sort_values(
    "incident_count", ascending=False
)

descent_totals = group_counts(filtered, ["Vict Descent"]).sort_values(
    "incident_count", ascending=False
)

most_common_sex = (
    str(sex_totals.iloc[0]["Vict Sex"])
    if not sex_totals.empty else "N/A"
)

most_common_descent = (
    DESCENT_MAP.get(descent_totals.iloc[0]["Vict Descent"],
                    descent_totals.iloc[0]["Vict Descent"])
    if not descent_totals.empty else "N/A"
)


# ============================================================
# KPI CARDS
# ============================================================

st.markdown("### Summary")

kpis = [
    ("Total Incidents", f"{total_incidents:,}"),
    ("Median Victim Age", format_number(median_age)),
    ("Most Common Sex", most_common_sex),
    ("Most Common Descent", most_common_descent),
]

for col, (label, value) in zip(st.columns(4), kpis):
    with col:
        render_kpi_card(label, value)


# ============================================================
# VICTIM AGE DISTRIBUTION
# ============================================================

st.markdown("### Victim Age Distribution")

if age_data.empty:
    st.info("No valid victim-age records match your filters.")
else:
    fig = px.bar(
        age_data,
        x="Vict Age",
        y="incident_count",
        title="Victim Age Distribution",
        labels={
            "Vict Age": "Victim Age",
            "incident_count": "Number of Incidents",
        },
    )
    fig.update_xaxes(dtick=5)
    show_chart(fig)

st.caption(
    "Age-specific charts exclude missing ages; overall incident totals retain them."
)


# ============================================================
# SEX & DESCENT
# ============================================================

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Victim Sex")
    fig = px.pie(
        sex_totals,
        names="Vict Sex",
        values="incident_count",
        hole=0.45,
        title="Incidents by Victim Sex",
    )
    show_chart(fig)

with col2:
    st.markdown("### Victim Descent")
    descent_display = descent_totals.head(10).copy()
    descent_display["Vict Descent"] = descent_display["Vict Descent"].map(
        lambda code: DESCENT_MAP.get(code, code)
    )
    descent_display = descent_display.sort_values("incident_count")

    bar_chart(
        descent_display,
        "Vict Descent",
        "Top 10 Victim Descent Categories",
        horizontal=True,
    )


# ============================================================
# AGE GROUPS BY SEX
# ============================================================

st.markdown("### Victim Age Groups by Sex")

age_group_data = filtered.dropna(subset=["Vict Age"]).copy()

age_group_data["Age Group"] = pd.cut(
    age_group_data["Vict Age"],
    bins=AGE_BINS,
    labels=AGE_LABELS,
)

age_sex = group_counts(age_group_data, ["Age Group", "Vict Sex"])
age_sex["Age Group"] = pd.Categorical(
    age_sex["Age Group"],
    categories=AGE_LABELS,
    ordered=True,
)
age_sex = age_sex.sort_values("Age Group")

fig = px.bar(
    age_sex,
    x="Age Group",
    y="incident_count",
    color="Vict Sex",
    barmode="group",
    title="Victim Age Groups by Sex",
    labels={
        "Age Group": "Victim Age Group",
        "incident_count": "Number of Incidents",
        "Vict Sex": "Victim Sex",
    },
    category_orders={"Age Group": AGE_LABELS},
)
show_chart(fig)


# ============================================================
# AGE DISTRIBUTION BY CRIME TYPE
# ============================================================

st.markdown("### Victim Age Pattern by Crime Type")

crime_totals = group_counts(filtered, ["Crm Cd Desc"]).sort_values(
    "incident_count", ascending=False
)

top_crimes = crime_totals.head(5)["Crm Cd Desc"].tolist()

age_crime = (
    filtered[filtered["Crm Cd Desc"].isin(top_crimes)]
    .dropna(subset=["Vict Age"])
    .groupby(["Crm Cd Desc", "Vict Age"], as_index=False)["incident_count"]
    .sum()
)

if age_crime.empty:
    st.info("No valid victim ages are available for this comparison.")
else:
    fig = px.line(
        age_crime,
        x="Vict Age",
        y="incident_count",
        color="Crm Cd Desc",
        title="Victim Age Distribution for the Five Most Common Crime Types",
        labels={
            "Vict Age": "Victim Age",
            "incident_count": "Number of Incidents",
            "Crm Cd Desc": "Crime Type",
        },
    )
    fig.update_xaxes(range=[1, 100], dtick=5)
    show_chart(fig)


# ============================================================
# CURRENT SELECTION
# ============================================================

st.divider()
st.markdown("### Current Selection")

year_summary = (
    "All Years" if "All Years" in selected_years
    else ", ".join(map(str, selected_years))
)

summary_items = [
    ("Years", year_summary),
    ("Crime Types", ", ".join(selected_crimes) if selected_crimes else "All Crime Types"),
    ("Victim Sex", ", ".join(selected_sex) if selected_sex else "All Sex Categories"),
    (
        "Victim Descent",
        ", ".join(selected_descent_labels)
        if selected_descent_labels else "All Descent Categories",
    ),
    ("Victim Age Range", f"{age_range[0]}–{age_range[1]}"),
    ("Filtered Incidents", f"{total_incidents:,}"),
]

col1, col2 = st.columns(2)

for i, (label, value) in enumerate(summary_items):
    with (col1 if i % 2 == 0 else col2):
        st.markdown(f"**{label}:** {value}")