import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Analytics & Performance", layout="wide")
st.markdown("<h1 style='text-align:center;color:#2E7D32;'>📈 Performance Analytics</h1>", unsafe_allow_html=True)

# ----------------------------- DATA LOADING -----------------------------
@st.cache_data
def load_panel_data():
    csv_path = Path(__file__).parent.parent / "data" / "solar_panels.csv"
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        if "Installation_Date" in df.columns:
            df["Installation_Date"] = pd.to_datetime(df["Installation_Date"], errors='coerce')
        if "Status" not in df.columns:
            df["Status"] = "Active"
        return df
    else:
        st.warning("Panel data not found. Please add solar_panels.csv in data/ folder.")
        return pd.DataFrame()

@st.cache_data
def load_renewable_data():
    csv_path = Path(__file__).parent.parent / "data" / "india_renewable_energy.csv"
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        df.columns = df.columns.str.strip()
        numeric_cols = ['Installed - Solar Power', 'Installed - Wind Power', 
                        'Installed - Bio-Mass Power', 'Installed - Small Hydro Power',
                        'Installed - Waste to Energy']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        return df
    else:
        return pd.DataFrame()

panels = load_panel_data()
renewable = load_renewable_data()

if panels.empty:
    st.error("No panel data available. Cannot display analytics.")
    st.stop()

# ----------------------------- FILTERS SECTION -----------------------------
st.subheader("🔍 Filter Data for Analysis")
col1, col2, col3, col4 = st.columns(4)
with col1:
    brand_filter = st.multiselect("Brand", options=panels["Brand"].unique(), default=panels["Brand"].unique())
with col2:
    status_filter = st.multiselect("Status", options=panels["Status"].unique(), default=panels["Status"].unique())
with col3:
    location_filter = st.multiselect("Location", options=panels["Location"].unique(), default=panels["Location"].unique())
with col4:
    # Age range slider
    today = datetime.now()
    panels["Age (years)"] = (today - panels["Installation_Date"]).dt.days / 365.25
    min_age = 0
    max_age = max(panels["Age (years)"].max(), 1)
    age_range = st.slider("Age (years)", min_value=0.0, max_value=float(max_age), value=(0.0, float(max_age)), step=0.5)

# Search by Panel ID or Model
search_term = st.text_input("🔎 Search (Panel ID / Model)", "")

# Apply filters
filtered = panels[
    (panels["Brand"].isin(brand_filter)) &
    (panels["Status"].isin(status_filter)) &
    (panels["Location"].isin(location_filter)) &
    (panels["Age (years)"] >= age_range[0]) &
    (panels["Age (years)"] <= age_range[1])
]
if search_term:
    filtered = filtered[
        filtered["Panel_ID"].str.contains(search_term, case=False) |
        filtered["Model"].str.contains(search_term, case=False)
    ]

st.caption(f"Showing analytics for **{len(filtered)}** panels (out of {len(panels)} total)")

# If no data after filtering, show warning
if filtered.empty:
    st.warning("No panels match the selected filters. Adjust your filters.")
    st.stop()

# ----------------------------- PANEL ANALYTICS -----------------------------
st.subheader("📊 Panel Performance Metrics")

colA, colB = st.columns(2)
with colA:
    # Capacity distribution histogram
    fig_cap = px.histogram(
        filtered, x="Capacity_W", nbins=10,
        title="Capacity Distribution (Watts)",
        color_discrete_sequence=["green"],
        labels={"Capacity_W": "Capacity (W)"}
    )
    st.plotly_chart(fig_cap, use_container_width=True)

with colB:
    # Efficiency vs Capacity scatter
    fig_eff = px.scatter(
        filtered, x="Capacity_W", y="Efficiency_%", 
        text="Brand", title="Efficiency vs Capacity",
        size="Capacity_W", color="Brand",
        labels={"Capacity_W": "Capacity (W)", "Efficiency_%": "Efficiency (%)"}
    )
    st.plotly_chart(fig_eff, use_container_width=True)

# Brand-wise total capacity (filtered)
brand_cap = filtered.groupby("Brand")["Capacity_W"].sum().reset_index()
brand_cap.columns = ["Brand", "Total Capacity (W)"]
fig_brand = px.bar(
    brand_cap, x="Brand", y="Total Capacity (W)",
    title="Total Capacity by Brand (Filtered)",
    color="Total Capacity (W)", color_continuous_scale="Greens"
)
st.plotly_chart(fig_brand, use_container_width=True)

# ---------- AGE ANALYSIS (Filtered) ----------
st.subheader("📅 Panel Age Distribution (Filtered)")
age_bins = [0, 1, 2, 3, 5, 10]
age_labels = ["<1 year", "1-2 years", "2-3 years", "3-5 years", ">5 years"]
filtered["Age Group"] = pd.cut(filtered["Age (years)"], bins=age_bins, labels=age_labels, right=False)
age_counts = filtered["Age Group"].value_counts().reset_index()
age_counts.columns = ["Age Group", "Count"]
fig_age = px.bar(age_counts, x="Age Group", y="Count", title="Panel Age Distribution", color_discrete_sequence=["orange"])
st.plotly_chart(fig_age, use_container_width=True)

# ---------- PERFORMANCE METRICS (Summaries for filtered data) ----------
st.subheader("📈 Performance Summary")
avg_efficiency = filtered["Efficiency_%"].mean()
avg_capacity = filtered["Capacity_W"].mean()
total_capacity_kw = filtered["Capacity_W"].sum() / 1000
active_ratio = (filtered["Status"].str.lower() == "active").mean() * 100

colM1, colM2, colM3, colM4 = st.columns(4)
colM1.metric("Avg Efficiency", f"{avg_efficiency:.1f}%")
colM2.metric("Avg Capacity", f"{avg_capacity:.0f} W")
colM3.metric("Total Capacity", f"{total_capacity_kw:.1f} kW")
colM4.metric("Active Ratio", f"{active_ratio:.0f}%")

# ---------- CORRELATION ----------
corr = filtered[["Capacity_W", "Efficiency_%"]].corr().iloc[0,1]
st.subheader("📊 Correlation Analysis")
st.metric("Correlation (Capacity vs Efficiency)", f"{corr:.2f}")
if corr > 0.5:
    st.write("✅ Moderate positive correlation – larger panels tend to have slightly higher efficiency.")
elif corr > 0:
    st.write("📈 Weak positive correlation – capacity and efficiency are somewhat related.")
else:
    st.write("📉 No significant correlation.")

# ---------- RENEWABLE ENERGY TRENDS (if data available) ----------
if not renewable.empty:
    st.subheader("🌍 India Renewable Energy Trends (National Data)")
    latest_year = renewable["Year"].max()
    latest_df = renewable[renewable["Year"] == latest_year].copy()
    latest_df["Total_RE_MW"] = (
        latest_df.get("Installed - Solar Power", 0) +
        latest_df.get("Installed - Wind Power", 0) +
        latest_df.get("Installed - Bio-Mass Power", 0) +
        latest_df.get("Installed - Small Hydro Power", 0) +
        latest_df.get("Installed - Waste to Energy", 0)
    )
    top_states = latest_df.nlargest(10, "Total_RE_MW")
    fig_re = px.bar(
        top_states, x="State", y="Total_RE_MW",
        title=f"Top 10 States by Total Renewable Capacity ({latest_year})",
        color="Total_RE_MW", color_continuous_scale="Greens"
    )
    st.plotly_chart(fig_re, use_container_width=True)

    st.subheader("📈 Solar Capacity Growth (Top 5 States)")
    top_solar_states = latest_df.nlargest(5, "Installed - Solar Power")["State"].tolist()
    solar_growth = renewable[renewable["State"].isin(top_solar_states)]
    fig_growth = px.line(
        solar_growth, x="Year", y="Installed - Solar Power",
        color="State", markers=True,
        title="Solar Capacity Growth (MW)",
        labels={"Installed - Solar Power": "Solar Capacity (MW)"}
    )
    st.plotly_chart(fig_growth, use_container_width=True)
else:
    st.info("Renewable energy data not available. Add india_renewable_energy.csv to see state-wise trends.")

st.caption("💡 Use the filters above to analyze specific subsets of panels (by brand, status, location, age). All charts and metrics update automatically.")