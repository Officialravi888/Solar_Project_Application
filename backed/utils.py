import streamlit as st
import pandas as pd
from pathlib import Path

@st.cache_data
def load_panel_data():
    csv_path = Path(__file__).parent / "data" / "solar_panels.csv"
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        if "Installation_Date" in df.columns:
            df["Installation_Date"] = pd.to_datetime(df["Installation_Date"])
        return df
    else:
        st.error(f"CSV not found at {csv_path}")
        return pd.DataFrame()