import streamlit as st

st.set_page_config(
    page_title="SolarGreen India",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("☀️ SolarGreen India")
st.markdown("### Welcome to your Solar Management Dashboard")

st.info("👈 Use the sidebar to navigate between pages")

# Display some quick stats or intro
st.markdown("""
### Features available:
- **Dashboard** – coming soon (you can add your own content here)
- **Panel List** – view, filter, and export all solar panels
- **Analytics** – charts and performance metrics
- **Maintenance** – track service history and alerts
- **Solar Forecast** – 7‑day generation prediction
- **Renewable Trends** – India’s renewable energy growth
- **Settings** – app configuration and contact

---

*All data is loaded from CSV files in the `data/` folder.*
""")