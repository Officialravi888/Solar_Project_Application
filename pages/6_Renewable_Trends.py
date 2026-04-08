import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="Renewable Trends", layout="wide")
st.markdown("<h1 style='text-align:center;color:#2E7D32;'>🌍 India Renewable Energy Trends (2006-2024)</h1>", unsafe_allow_html=True)

# ----------------------------- LOAD OR CREATE DATA -----------------------------
@st.cache_data
def load_renewable_data():
    csv_path = Path(__file__).parent.parent / "data" / "india_renewable_energy.csv"
    csv_path.parent.mkdir(exist_ok=True)  # ensure data folder exists

    if not csv_path.exists():
        # Create sample CSV automatically
        sample_data = pd.DataFrame({
            "State": ["Rajasthan", "Gujarat", "Karnataka", "Tamil Nadu", "Maharashtra", "Uttar Pradesh"],
            "Year": [2024, 2024, 2024, 2024, 2024, 2024],
            "Installed - Solar Power": [12564, 25471, 17752, 5067, 14483, 2244],
            "Installed - Wind Power": [4326, 11722, 6019, 9866, 5207, 0],
            "Installed - Bio-Mass Power": [121, 112, 1907, 1012, 2643, 2117],
            "Installed - Small Hydro Power": [23, 91, 1280, 123, 382, 49],
            "Installed - Waste to Energy": [3, 7, 19, 30, 46, 72]
        })
        sample_data.to_csv(csv_path, index=False)
        st.info("📄 Sample renewable data created. Replace with full dataset for complete analysis.")
        return sample_data

    df = pd.read_csv(csv_path)
    # Clean column names
    df.columns = df.columns.str.strip()
    # Ensure numeric columns
    source_cols = ['Installed - Solar Power', 'Installed - Wind Power', 
                   'Installed - Bio-Mass Power', 'Installed - Small Hydro Power',
                   'Installed - Waste to Energy']
    for col in source_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

df = load_renewable_data()
if df.empty:
    st.error("Could not load or create renewable data.")
    st.stop()

# ----------------------------- FILTERS -----------------------------
st.subheader("🔍 Select Data to Visualize")

all_states = sorted(df["State"].unique())
col1, col2 = st.columns(2)
with col1:
    selected_state = st.selectbox("Select State", ["All India"] + all_states)
with col2:
    source_options = ["Solar Power", "Wind Power", "Bio-Mass Power", "Small Hydro Power", "Waste to Energy"]
    selected_source = st.selectbox("Select Energy Source", source_options)

source_map = {
    "Solar Power": "Installed - Solar Power",
    "Wind Power": "Installed - Wind Power",
    "Bio-Mass Power": "Installed - Bio-Mass Power",
    "Small Hydro Power": "Installed - Small Hydro Power",
    "Waste to Energy": "Installed - Waste to Energy"
}
selected_col = source_map[selected_source]

# ----------------------------- FILTER DATA -----------------------------
if selected_state == "All India":
    plot_df = df.groupby("Year")[selected_col].sum().reset_index()
    plot_df["State"] = "India"
    title = f"{selected_source} Capacity Growth - All India"
else:
    plot_df = df[df["State"] == selected_state][["Year", selected_col]].copy()
    plot_df["State"] = selected_state
    title = f"{selected_source} Capacity Growth - {selected_state}"

plot_df = plot_df.dropna(subset=[selected_col])

# ----------------------------- LINE CHART -----------------------------
st.subheader("📈 Growth Over Years")
if not plot_df.empty:
    fig = px.line(plot_df, x="Year", y=selected_col, 
                  title=title, markers=True,
                  labels={selected_col: f"{selected_source} Capacity (MW)", "Year": "Year"},
                  color_discrete_sequence=["green"])
    fig.update_traces(line=dict(width=3), marker=dict(size=8))
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📋 Data Table")
    st.dataframe(plot_df, use_container_width=True)
else:
    st.warning("No data available for the selected filters.")

# ----------------------------- TOP STATES (Latest Year) -----------------------------
st.subheader("🏆 Top States by Total Renewable Capacity (Latest Year)")
if "Year" in df.columns:
    latest_year = df["Year"].max()
    latest_df = df[df["Year"] == latest_year].copy()
    latest_df["Total_RE_MW"] = (
        latest_df.get("Installed - Solar Power", 0) +
        latest_df.get("Installed - Wind Power", 0) +
        latest_df.get("Installed - Bio-Mass Power", 0) +
        latest_df.get("Installed - Small Hydro Power", 0) +
        latest_df.get("Installed - Waste to Energy", 0)
    )
    top_states = latest_df.nlargest(10, "Total_RE_MW")
    if not top_states.empty:
        fig_bar = px.bar(top_states, x="State", y="Total_RE_MW", 
                         title=f"Top 10 States - Total Renewable Capacity ({latest_year})",
                         color="Total_RE_MW", color_continuous_scale="Greens")
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("No state data available.")
else:
    st.info("Year column missing – cannot compute latest year.")

st.caption("💡 Data source: Ministry of New and Renewable Energy (MNRE), Government of India.")