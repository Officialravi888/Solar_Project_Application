import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np

st.set_page_config(page_title="Solar Panel List", layout="wide")
st.markdown("<h1 style='text-align:center;color:#2E7D32;'>📋 Solar Panel Inventory</h1>", unsafe_allow_html=True)

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
        st.error(f"CSV file not found at {csv_path}")
        return pd.DataFrame(columns=["Panel_ID", "Brand", "Model", "Capacity_W", 
                                     "Efficiency_%", "Installation_Date", "Location", "Status"])

panels = load_panel_data()

if panels.empty:
    st.warning("No panel data found. Please add solar_panels.csv in data/ folder.")
    st.stop()

# ----------------------------- ENSURE REQUIRED COLUMNS -----------------------------
required_cols = ['Panel_ID', 'Brand', 'Model', 'Capacity_W', 'Efficiency_%', 
                 'Installation_Date', 'Location', 'Status']
for col in required_cols:
    if col not in panels.columns:
        panels[col] = 'Unknown' if col != 'Capacity_W' else 0

panels["Installation_Date"] = pd.to_datetime(panels["Installation_Date"], errors='coerce')

# ----------------------------- ADD EXTRA COLUMNS (if missing) -----------------------------
today = datetime.now()

if 'Last_Service_Date' not in panels.columns:
    panels['Last_Service_Date'] = [today - timedelta(days=np.random.randint(30, 180)) for _ in range(len(panels))]

if 'Next_Due_Date' not in panels.columns:
    panels['Next_Due_Date'] = panels['Last_Service_Date'] + timedelta(days=180)

if 'Today_Gen_kWh' not in panels.columns:
    panels['Today_Gen_kWh'] = (panels['Capacity_W'] / 1000) * 5 * (panels['Efficiency_%'] / 100) * np.random.uniform(0.7, 1.1, len(panels))
    panels['Today_Gen_kWh'] = panels['Today_Gen_kWh'].round(2)

if 'Health_Score_%' not in panels.columns:
    panels['Health_Score_%'] = np.random.randint(70, 101, len(panels))

if 'Lifetime_Gen_kWh' not in panels.columns:
    days_installed = (today - panels['Installation_Date']).dt.days
    panels['Lifetime_Gen_kWh'] = (panels['Capacity_W'] / 1000) * 4 * days_installed * np.random.uniform(0.8, 1.0, len(panels))
    panels['Lifetime_Gen_kWh'] = panels['Lifetime_Gen_kWh'].round(0)

if 'Performance_Ratio_%' not in panels.columns:
    panels['Performance_Ratio_%'] = np.random.randint(80, 106, len(panels))

# ---------- SUMMARY METRICS ----------
total_panels = len(panels)
total_capacity_kW = panels['Capacity_W'].sum() / 1000
active_panels = panels[panels['Status'].str.lower() == 'active'].shape[0]
maintenance_panels = panels[panels['Status'].str.lower() == 'maintenance'].shape[0]
avg_health = panels['Health_Score_%'].mean()
total_today_gen = panels['Today_Gen_kWh'].sum()

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Total Panels", total_panels)
col2.metric("Total Capacity", f"{total_capacity_kW:.1f} kW")
col3.metric("Active Panels", active_panels)
col4.metric("Maintenance", maintenance_panels)
col5.metric("Avg Health", f"{avg_health:.0f}%")
col6.metric("Today's Gen", f"{total_today_gen:.1f} kWh")

st.markdown("---")

# ---------- FILTERS ----------
st.subheader("🔍 Filter & Search")
all_statuses = panels['Status'].unique().tolist()
all_brands = panels['Brand'].unique().tolist()
all_locations = panels['Location'].unique().tolist()

col_search, col_status, col_brand, col_location = st.columns(4)
with col_search:
    search_term = st.text_input("🔎 Search (Panel ID / Brand / Model)", "")
with col_status:
    status_filter = st.multiselect("Status", options=all_statuses, default=all_statuses)
with col_brand:
    brand_filter = st.multiselect("Brand", options=all_brands, default=all_brands)
with col_location:
    location_filter = st.multiselect("Location", options=all_locations, default=all_locations)

filtered = panels[
    (panels['Status'].isin(status_filter)) &
    (panels['Brand'].isin(brand_filter)) &
    (panels['Location'].isin(location_filter))
]
if search_term:
    filtered = filtered[
        filtered['Panel_ID'].str.contains(search_term, case=False) |
        filtered['Brand'].str.contains(search_term, case=False) |
        filtered['Model'].str.contains(search_term, case=False)
    ]

st.caption(f"Showing {len(filtered)} of {len(panels)} panels")

# ---------- DISPLAY TABLE WITH ALL DETAILS ----------
display_df = filtered.copy()
display_df['Capacity (kW)'] = (display_df['Capacity_W'] / 1000).round(2)
display_df['Efficiency (%)'] = display_df['Efficiency_%'].astype(str) + '%'
display_df['Installation Date'] = display_df['Installation_Date'].dt.strftime('%Y-%m-%d')
display_df['Age (years)'] = display_df['Installation_Date'].apply(
    lambda x: round((today - x).days / 365.25, 1) if pd.notnull(x) else 'N/A'
)
display_df['Last Service'] = pd.to_datetime(display_df['Last_Service_Date']).dt.strftime('%Y-%m-%d')
display_df['Next Due'] = pd.to_datetime(display_df['Next_Due_Date']).dt.strftime('%Y-%m-%d')
display_df['Today (kWh)'] = display_df['Today_Gen_kWh']
display_df['Health (%)'] = display_df['Health_Score_%']
display_df['Lifetime (kWh)'] = display_df['Lifetime_Gen_kWh'].apply(lambda x: f"{x:,.0f}")
display_df['PR (%)'] = display_df['Performance_Ratio_%']
display_df['Status'] = display_df['Status'].apply(lambda x: '✅ Active' if str(x).lower() == 'active' else '⚠️ Maintenance')

col_order = [
    'Panel_ID', 'Brand', 'Model', 'Capacity (kW)', 'Efficiency (%)',
    'Installation Date', 'Age (years)', 'Location', 'Status',
    'Last Service', 'Next Due', 'Today (kWh)', 'Health (%)',
    'Lifetime (kWh)', 'PR (%)'
]
display_df = display_df[col_order]

# Conditional formatting using `map` (replaces deprecated `applymap`)
def highlight_status(val):
    if isinstance(val, str):
        if 'Maintenance' in val:
            return 'background-color: #ffcccc; color: #b30000'
        elif 'Active' in val:
            return 'background-color: #d4edda; color: #155724'
    return ''

def health_bar(val):
    if isinstance(val, (int, float)):
        return f'background: linear-gradient(90deg, #2e7d32 {val}%, #e0e0e0 {val}%); color: black;'
    return ''

# Apply styling
styled_df = display_df.style.map(highlight_status, subset=['Status'])
styled_df = styled_df.map(health_bar, subset=['Health (%)'])

st.dataframe(styled_df, use_container_width=True, height=500)

# ---------- EXPORT ----------
csv = filtered.to_csv(index=False).encode('utf-8')
st.download_button("📥 Download Filtered Data as CSV", csv, "solar_panels_advanced.csv", "text/csv")

# ---------- QUICK ANALYTICS ----------
st.markdown("---")
st.subheader("📊 Quick Analytics")
col_a, col_b = st.columns(2)
with col_a:
    fig = px.histogram(filtered, x="Capacity_W", nbins=10, title="Capacity Distribution (W)", color_discrete_sequence=["green"])
    st.plotly_chart(fig, use_container_width=True)
with col_b:
    status_counts = filtered['Status'].value_counts().reset_index()
    status_counts.columns = ['Status', 'Count']
    status_counts['Status'] = status_counts['Status'].apply(lambda x: 'Active' if str(x).lower()=='active' else 'Maintenance')
    fig2 = px.pie(status_counts, names='Status', values='Count', title="Status Breakdown", color='Status',
                  color_discrete_map={'Active':'#2e7d32','Maintenance':'#d32f2f'})
    st.plotly_chart(fig2, use_container_width=True)

col_c, col_d = st.columns(2)
with col_c:
    fig3 = px.bar(filtered, x='Panel_ID', y='Health_Score_%', title="Panel Health Score (%)", color='Health_Score_%', color_continuous_scale='RdYlGn')
    st.plotly_chart(fig3, use_container_width=True)
with col_d:
    fig4 = px.scatter(filtered, x='Capacity_W', y='Performance_Ratio_%', text='Brand', title="Performance Ratio vs Capacity", color='Health_Score_%')
    st.plotly_chart(fig4, use_container_width=True)

# Maintenance reminders
if 'Next_Due_Date' in filtered.columns:
    filtered['Next_Due_Date'] = pd.to_datetime(filtered['Next_Due_Date'])
    upcoming = filtered[filtered['Next_Due_Date'] <= today + timedelta(days=30)]
    if not upcoming.empty:
        st.warning(f"⚠️ {len(upcoming)} panels have maintenance due in next 30 days")
        st.dataframe(upcoming[['Panel_ID', 'Brand', 'Next Due', 'Health_Score_%']], use_container_width=True)
    else:
        st.success("✅ No upcoming maintenance in next 30 days")

st.caption("💡 Tip: Hover over 'Health (%)' to see the bar; click column headers to sort.")