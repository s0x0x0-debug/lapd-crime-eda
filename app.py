import streamlit as st


st.set_page_config(
    page_title="LA Crime Dashboard",
    page_icon="🚔",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Define the pages and explicitly control their sidebar labels/icons.
pages = [
    st.Page(
        "pages/1_main.py",
        title="Main",
        icon=":material/home:",
        default=True,
    ),
    st.Page(
        "pages/2_crime_time.py",
        title="Crime & Time",
        icon=":material/schedule:",
    ),
    st.Page(
            "pages/3_victims.py",
            title="Victims",
            icon=":material/person:",
    ),st.Page(
        "pages/4_location_reporting.py",
        title="Location & Reporting",
        icon=":material/location_on:",
    ),
    st.Page(
    "pages/5_crime_profile.py",
    title="Crime Profile",
    icon=":material/analytics:",
),
]


# Create the sidebar navigation.
# The displayed names now come from the `title` values above,
# rather than from the filenames.
pg = st.navigation(
    pages,
    position="sidebar",
)


# Run the currently selected page.
pg.run()