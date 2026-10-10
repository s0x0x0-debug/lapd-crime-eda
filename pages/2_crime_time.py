from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# -------------------- PAGE CONFIGURATION --------------------

st.set_page_config(
    page_title="Crime & Time | LA Crime Dashboard",
    page_icon="🚔",
    layout="wide",
    initial_sidebar_state="expanded",
)


# -------------------- PATHS & DATA --------------------

BASE_DIR = Path(__file__).resolve().parent.parent
SUMMARY_PATH = BASE_DIR / "data" / "dashboard" / "summaries"
LOGO_PATH = BASE_DIR / "assets" / "lapd_logo.png"
DATA_PATH = SUMMARY_PATH / "crime_time_detail.parquet"

if not DATA_PATH.exists():
    st.error("Crime & Time summary data is missing.")
    st.info(
        "Run prepare_detailed_dashboard_summaries.py to generate "
        "crime_time_detail.parquet."
    )
    st.stop()


@st.cache_data
def load_data():
    return pd.read_parquet(DATA_PATH, engine="pyarrow")


crime_time = load_data()


# -------------------- CONSTANTS --------------------

MONTHS = [
    "January", "February", "March", "April",
    "May", "June", "July", "August",
    "September", "October", "November", "December",
]

TIME_PERIODS = ["Night", "Morning", "Afternoon", "Evening"]

DAYS = [
    "Monday", "Tuesday", "Wednesday", "Thursday",
    "Friday", "Saturday", "Sunday", "Missing",
]


# -------------------- REUSABLE FUNCTIONS --------------------

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
            <div style="font-size:14px;color:gray;margin-bottom:8px">
                {label}
            </div>
            <div style="
                font-size:21px;
                font-weight:650;
                overflow-wrap:anywhere;
            ">
                {value}
            </div>
        </div>
        """,
        width="stretch",
    )


def show_chart(fig):
    fig.update_layout(hovermode="x unified")

    st.plotly_chart(
        fig,
        width="stretch",
        theme="streamlit",
        config={"displaylogo": False, "responsive": True},
    )


def group_counts(df, columns):
    return (
        df.groupby(columns, as_index=False)["incident_count"]
        .sum()
    )


def get_peak(df, value_column, label_column, valid=None):
    if valid is not None:
        df = df[valid]

    # Avoid duplicate group columns, e.g. hour/hour.
    group_columns = list(dict.fromkeys([
        value_column,
        label_column,
    ]))

    totals = group_counts(df, group_columns)

    if totals.empty:
        return "N/A"

    return totals.loc[
        totals["incident_count"].idxmax(),
        label_column,
    ]


def render_bar_chart(df, category, title, horizontal=False):
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


# -------------------- SIDEBAR FILTERS --------------------

with st.sidebar:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=120)

    st.markdown("## LA Crime Dashboard")
    st.caption("Crime & Time Analysis")
    st.divider()
    st.markdown("### Crime & Time Filters")

    years = sorted(crime_time["year"].dropna().astype(int).unique())

    selected_years = st.multiselect(
        "Year",
        ["All Years"] + years,
        default=["All Years"],
    )

    if "All Years" in selected_years and len(selected_years) > 1:
        selected_years = ["All Years"]
        st.warning("All Years cannot be combined with individual years.")

    if not selected_years:
        selected_years = ["All Years"]

    selected_months = st.multiselect(
        "Month",
        MONTHS,
        placeholder="All Months",
    )

    selected_crimes = st.multiselect(
        "Crime Type",
        sorted(crime_time["Crm Cd Desc"].dropna().unique()),
        placeholder="All Crime Types",
    )

    selected_areas = st.multiselect(
        "LAPD Area",
        sorted(crime_time["AREA NAME"].dropna().unique()),
        placeholder="All Areas",
    )

    selected_times = st.multiselect(
        "Time of Day",
        TIME_PERIODS,
        placeholder="All Time Periods",
    )


# -------------------- PAGE HEADER --------------------

st.title("Crime & Time Analysis")

st.markdown(
    """
    Explore when crime incidents occur across **years, months, days of
    the week, hours, crime types, and LAPD areas**.

    All sidebar filters apply to the KPIs and visualizations.
    """
)


# -------------------- APPLY FILTERS --------------------

filtered = crime_time.copy()

filters = {
    "year": selected_years if "All Years" not in selected_years else [],
    "month_name": selected_months,
    "Crm Cd Desc": selected_crimes,
    "AREA NAME": selected_areas,
    "time_of_day": selected_times,
}

for column, selections in filters.items():
    if selections:
        filtered = filtered[filtered[column].isin(selections)]

if filtered.empty:
    st.warning("No incidents match your filters. Try changing your selections.")
    st.stop()


# -------------------- KPI CALCULATIONS --------------------

total_incidents = int(filtered["incident_count"].sum())

peak_hour = get_peak(
    filtered[filtered["hour"] >= 0],
    "hour",
    "hour",
)

if peak_hour != "N/A":
    peak_hour = f"{int(peak_hour):02d}:00"

peak_day = get_peak(
    filtered[filtered["day_of_week"] >= 0],
    "day_of_week",
    "day_name",
)

# Display the day name rather than its numeric index.
if peak_day != "N/A":
    peak_day = get_peak(
        filtered[filtered["day_of_week"] >= 0],
        "day_of_week",
        "day_name",
    )

peak_month = get_peak(
    filtered[filtered["month"] >= 1],
    "month",
    "month_name",
)


# -------------------- KPI DISPLAY --------------------

st.markdown("### Summary")

kpi_values = [
    ("Total Incidents", f"{total_incidents:,}"),
    ("Peak Hour", peak_hour),
    ("Peak Day", peak_day),
    ("Peak Month", peak_month),
]

for col, (label, value) in zip(st.columns(4), kpi_values):
    with col:
        render_kpi_card(label, value)


# -------------------- CRIME TREND --------------------


# -------------------- CRIME TREND --------------------

st.markdown("### Crime Trend")

# "All Years" is a special option, not an actual year.
all_years_selected = "All Years" in selected_years

# Keep only rows with valid calendar months for monthly charts.
valid_month_data = filtered.loc[
    filtered["month"].between(1, 12)
].copy()

fig = None

# CASE 1: All years + all months.
# Show the annual total for each year.
if all_years_selected and not selected_months:

    trend = (
        group_counts(filtered, ["year"])
        .sort_values("year")
    )

    if not trend.empty:
        fig = px.line(
            trend,
            x="year",
            y="incident_count",
            markers=True,
            title="Crime Incidents by Year",
            labels={
                "year": "Year",
                "incident_count": "Number of Incidents",
            },
        )

# CASE 2: Exactly one actual year is selected.
# Show a monthly trend for that year.
elif not all_years_selected and len(selected_years) == 1:

    trend = (
        group_counts(
            valid_month_data,
            ["month", "month_name"],
        )
        .sort_values("month")
    )

    if not trend.empty:
        fig = px.line(
            trend,
            x="month_name",
            y="incident_count",
            markers=True,
            title=f"Monthly Crime Incidents — {selected_years[0]}",
            category_orders={"month_name": MONTHS},
            labels={
                "month_name": "Month",
                "incident_count": "Number of Incidents",
            },
        )

# CASE 3: Multiple years (or All Years) + specific month selection.
# Compare selected months across years instead of treating
# All Years as if it were one actual year.
elif selected_months:

    monthly_trend = group_counts(
        valid_month_data,
        ["year", "month", "month_name"],
    ).sort_values(["year", "month"])

    if len(selected_months) == 1:
        # One selected month: compare its total across years.
        trend = (
            monthly_trend
            .groupby("year", as_index=False)["incident_count"]
            .sum()
            .sort_values("year")
        )

        if not trend.empty:
            fig = px.line(
                trend,
                x="year",
                y="incident_count",
                markers=True,
                title=f"Crime Incidents by Year — {selected_months[0]}",
                labels={
                    "year": "Year",
                    "incident_count": "Number of Incidents",
                },
            )

    else:
        # Multiple selected months: show a separate line
        # for each month across the selected years.
        if not monthly_trend.empty:
            fig = px.line(
                monthly_trend,
                x="year",
                y="incident_count",
                color="month_name",
                markers=True,
                title="Crime Incidents by Year for Selected Months",
                category_orders={"month_name": MONTHS},
                labels={
                    "year": "Year",
                    "month_name": "Month",
                    "incident_count": "Number of Incidents",
                },
            )

# CASE 4: Multiple actual years + all months.
# Show the monthly pattern for each selected year.
else:

    trend = group_counts(
        valid_month_data,
        ["year", "month", "month_name"],
    ).sort_values(["year", "month"])

    if not trend.empty:
        fig = px.line(
            trend,
            x="month_name",
            y="incident_count",
            color="year",
            markers=True,
            title="Monthly Crime Incidents by Selected Years",
            category_orders={"month_name": MONTHS},
            labels={
                "month_name": "Month",
                "incident_count": "Number of Incidents",
                "year": "Year",
            },
        )

# Display the chart or a helpful message.
if fig is None:
    st.info(
        "No valid year/month data is available for the selected filters."
    )
else:
    show_chart(fig)



# -------------------- TOP CRIMES & TIME OF DAY --------------------

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Top 10 Crime Types")

    top_crimes = (
        group_counts(filtered, ["Crm Cd Desc"])
        .nlargest(10, "incident_count")
        .sort_values("incident_count")
    )

    render_bar_chart(
        top_crimes,
        "Crm Cd Desc",
        "Top 10 Crime Types",
        horizontal=True,
    )

with col2:
    st.markdown("### Incidents by Time of Day")

    time_data = group_counts(filtered, ["time_of_day"])

    time_data["time_of_day"] = pd.Categorical(
        time_data["time_of_day"],
        categories=TIME_PERIODS + ["Missing"],
        ordered=True,
    )

    time_data = time_data.sort_values("time_of_day")

    render_bar_chart(
        time_data,
        "time_of_day",
        "Crime Incidents by Time of Day",
    )


# -------------------- INCIDENTS BY HOUR --------------------

st.markdown("### Incidents by Hour")

hour_data = group_counts(
    filtered[filtered["hour"] >= 0],
    ["hour"],
).sort_values("hour")

if hour_data.empty:
    st.info("No valid hour values match the selected filters.")
else:
    render_bar_chart(
        hour_data,
        "hour",
        "Crime Incidents by Hour of Day",
    )


# -------------------- DAY × HOUR HEATMAP --------------------


# -------------------- DAY × HOUR HEATMAP --------------------

st.markdown("### Crime Incidents by Day and Hour")

# Define the exact order of weekdays and hours.
DAY_ORDER = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

HOUR_ORDER = list(range(24))

# Keep valid weekday/hour records only.
valid_heatmap_rows = filtered.loc[
    filtered["day_of_week"].between(0, 6)
    & filtered["hour"].between(0, 23)
    & filtered["day_name"].isin(DAY_ORDER),
    ["day_of_week", "day_name", "hour", "incident_count"],
].copy()

if valid_heatmap_rows.empty:
    st.info("No valid day/hour values match the selected filters.")

else:
    # Aggregate incident counts for each weekday and hour.
    # incident_count is already aggregated in the source data,
    # so sum it rather than counting DataFrame rows.
    heatmap_matrix = (
        valid_heatmap_rows
        .groupby(["day_name", "hour"], observed=True)["incident_count"]
        .sum()
        .unstack("hour", fill_value=0)
        .reindex(
            index=DAY_ORDER,
            columns=HOUR_ORDER,
            fill_value=0,
        )
    )

    # Use readable labels while preserving all 24 hourly columns.
    hour_labels = [f"{hour:02d}:00" for hour in HOUR_ORDER]
    heatmap_matrix.columns = hour_labels

    # Render the matrix directly.
    # Unlike density_heatmap, imshow does not bin the hour values.
    fig = px.imshow(
        heatmap_matrix,
        x=hour_labels,
        y=DAY_ORDER,
        aspect="auto",
        color_continuous_scale="Blues",
        title="Crime Incidents by Day of Week and Hour",
        labels={
            "x": "Hour of Day",
            "y": "Day of Week",
            "color": "Incidents",
        },
    )

    fig.update_layout(
        xaxis_title="Hour of Day",
        yaxis_title="Day of Week",
        coloraxis_colorbar_title="Incidents",
    )

    # Show every hour as a separate cell and label.
    fig.update_xaxes(
        side="bottom",
        tickmode="array",
        tickvals=hour_labels,
        ticktext=hour_labels,
        tickangle=-45,
    )

    # Show the exact values when the user hovers over a cell.
    fig.update_traces(
        hovertemplate=(
            "Day: %{y}<br>"
            "Hour: %{x}<br>"
            "Incidents: %{z:,.0f}"
            "<extra></extra>"
        )
    )

    show_chart(fig)



# -------------------- CRIME-SPECIFIC HOURLY PATTERN --------------------

st.markdown("### Crime-Specific Hourly Pattern")

available_crimes = (
    filtered[filtered["hour"] >= 0]
    .groupby("Crm Cd Desc")["incident_count"]
    .sum()
    .sort_values(ascending=False)
    .index.tolist()
)

if available_crimes:
    focus_crime = st.selectbox(
        "Select a crime type",
        available_crimes,
        help="Examine the hourly pattern for a selected crime type.",
    )

    focus_data = group_counts(
        filtered[
            (filtered["Crm Cd Desc"] == focus_crime)
            & (filtered["hour"] >= 0)
        ],
        ["hour"],
    ).sort_values("hour")

    fig = px.line(
        focus_data,
        x="hour",
        y="incident_count",
        markers=True,
        title=f"Hourly Incident Pattern — {focus_crime}",
        labels={
            "hour": "Hour of Day",
            "incident_count": "Number of Incidents",
        },
    )

    fig.update_xaxes(dtick=1)
    show_chart(fig)


# -------------------- CURRENT FILTER SUMMARY --------------------

st.divider()
st.markdown("### Current Selection")

year_summary = (
    "All Years"
    if "All Years" in selected_years
    else ", ".join(map(str, selected_years))
)

summaries = [
    ("Years", year_summary),
    ("Months", ", ".join(selected_months) if selected_months else "All Months"),
    (
        "Crime Types",
        f"{len(selected_crimes)} selected"
        if selected_crimes else "All Crime Types",
    ),
    (
        "LAPD Areas",
        f"{len(selected_areas)} selected"
        if selected_areas else "All LAPD Areas",
    ),
    (
        "Time of Day",
        ", ".join(selected_times) if selected_times else "All Time Periods",
    ),
    ("Filtered Incidents", f"{total_incidents:,}"),
]

summary_col1, summary_col2 = st.columns(2)

for index, (label, value) in enumerate(summaries):
    with (summary_col1 if index % 2 == 0 else summary_col2):
        st.markdown(f"**{label}:** {value}")


