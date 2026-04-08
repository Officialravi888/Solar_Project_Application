import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import requests
import numpy as np

st.set_page_config(page_title="Solar Forecast", layout="wide")
st.markdown("<h1 style='text-align:center;color:#2E7D32;'>🌞 7‑Day Solar Generation Forecast</h1>", unsafe_allow_html=True)

# ----------------------------- LOAD PANEL DATA -----------------------------
@st.cache_data
def load_panel_data():
    csv_path = Path(__file__).parent.parent / "data" / "solar_panels.csv"
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        return df
    else:
        st.error("Panel data not found. Please add solar_panels.csv in data/ folder.")
        return pd.DataFrame()

# ----------------------------- GET WEATHER FORECAST (REAL API) -----------------------------
@st.cache_data(ttl=3600)  # refresh every hour
def get_solar_forecast(lat=25.5, lon=81.875):
    """Fetch real irradiance forecast from Open-Meteo API"""
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=global_tilted_irradiance&timezone=auto&forecast_days=7"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            hourly_irradiance = data["hourly"]["global_tilted_irradiance"]
            times = data["hourly"]["time"]
            # Convert hourly to daily total (Wh/m² per day)
            daily_irradiance_wh = []
            for day_start in range(0, len(hourly_irradiance), 24):
                day_wh = sum(hourly_irradiance[day_start:day_start+24])
                daily_irradiance_wh.append(day_wh)
            # Convert to kWh/m² per day
            daily_kwh_per_m2 = [x/1000 for x in daily_irradiance_wh]
            dates = [times[i][:10] for i in range(0, len(times), 24)]
            return {"dates": dates, "irradiance_kwh_per_m2": daily_kwh_per_m2}
        else:
            return None
    except:
        return None

# ----------------------------- CALCULATE GENERATION -----------------------------
def calculate_generation(irradiance_kwh_per_m2, total_capacity_kw, panel_area_m2=1.6, efficiency_pct=20):
    """
    Energy (kWh) = Irradiance (kWh/m²) * Panel Area (m²) * Efficiency * Number of panels
    Simplified: Energy = Total capacity (kW) * Irradiance (kWh/m²) * 0.8 (derating)
    """
    derating = 0.85  # system losses (inverter, temperature, dust)
    daily_kwh = [round(total_capacity_kw * irr * derating, 1) for irr in irradiance_kwh_per_m2]
    return daily_kwh

# ----------------------------- MAIN APP -----------------------------
panels = load_panel_data()
if panels.empty:
    st.stop()

# Calculate total system capacity
total_capacity_kw = panels["Capacity_W"].sum() / 1000

# User inputs for location
st.subheader("📍 Location Settings")
col1, col2 = st.columns(2)
with col1:
    lat = st.number_input("Latitude", value=25.5, format="%.2f", help="Default: Prayagraj, UP")
with col2:
    lon = st.number_input("Longitude", value=81.875, format="%.2f")

if st.button("🔄 Get Live Forecast", type="primary"):
    with st.spinner("Fetching real-time solar irradiance data..."):
        forecast_data = get_solar_forecast(lat, lon)
        if forecast_data:
            dates = forecast_data["dates"]
            irradiance = forecast_data["irradiance_kwh_per_m2"]
            generation = calculate_generation(irradiance, total_capacity_kw)
            df_forecast = pd.DataFrame({"Date": dates, "Expected Generation (kWh)": generation})
            st.success(f"Forecast based on real weather data. Total system capacity: {total_capacity_kw:.1f} kWp")
        else:
            st.warning("Could not fetch live data. Using demo forecast.")
            # Demo data (fallback)
            dates = [(datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
            np.random.seed(42)
            generation = [round(total_capacity_kw * 4.5 * (0.7 + 0.6*np.random.random()), 1) for _ in range(7)]
            df_forecast = pd.DataFrame({"Date": dates, "Expected Generation (kWh)": generation})
else:
    # Show demo forecast initially
    dates = [(datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    np.random.seed(42)
    generation = [round(total_capacity_kw * 4.5 * (0.7 + 0.6*np.random.random()), 1) for _ in range(7)]
    df_forecast = pd.DataFrame({"Date": dates, "Expected Generation (kWh)": generation})
    st.info("👆 Click 'Get Live Forecast' to fetch real weather data from Open-Meteo API. Below is a demo forecast.")

# ----------------------------- DISPLAY CHARTS & TABLE -----------------------------
st.subheader("📈 Forecast Chart")
fig = px.line(df_forecast, x="Date", y="Expected Generation (kWh)", 
              markers=True, title="7‑Day Solar Generation Forecast",
              labels={"Expected Generation (kWh)": "Energy (kWh)"},
              color_discrete_sequence=["orange"])
fig.update_traces(line=dict(width=3), marker=dict(size=8))
st.plotly_chart(fig, use_container_width=True)

st.subheader("📋 Daily Breakdown")
st.dataframe(df_forecast, use_container_width=True)

# Add total energy for the week
total_week_kwh = df_forecast["Expected Generation (kWh)"].sum()
st.metric("Total Energy Next 7 Days", f"{total_week_kwh:.1f} kWh")

st.caption("💡 Forecast uses global tilted irradiance from Open-Meteo API. Generation calculated as: Total Capacity (kW) × Irradiance (kWh/m²) × 0.85 (system losses).")