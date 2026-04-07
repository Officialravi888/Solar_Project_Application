import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np

st.set_page_config(page_title="Maintenance & Alerts", layout="wide")
st.markdown("<h1 style='text-align:center;color:#2E7D32;'>🔧 Maintenance & Service History</h1>", unsafe_allow_html=True)

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
        st.error("Panel data not found. Please add solar_panels.csv in data/ folder.")
        return pd.DataFrame()

@st.cache_data
def load_maintenance_logs():
    logs_path = Path(__file__).parent.parent / "data" / "maintenance_logs.csv"
    if logs_path.exists():
        df = pd.read_csv(logs_path)
        # Ensure date columns are datetime
        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"], errors='coerce')
        if "Next_Due_Date" in df.columns:
            df["Next_Due_Date"] = pd.to_datetime(df["Next_Due_Date"], errors='coerce')
        return df
    else:
        # Create sample logs if file missing
        return pd.DataFrame(columns=["Log_ID", "Panel_ID", "Date", "Issue", "Action", "Cost", "Next_Due_Date"])

def save_maintenance_logs(df):
    logs_path = Path(__file__).parent.parent / "data" / "maintenance_logs.csv"
    logs_path.parent.mkdir(exist_ok=True)
    df.to_csv(logs_path, index=False)
    st.cache_data.clear()

panels = load_panel_data()
if panels.empty:
    st.stop()

today = datetime.now()
panels["Age_Years"] = (today - panels["Installation_Date"]).dt.days / 365.25

# ----------------------------- TABS FOR ORGANIZATION -----------------------------
tab1, tab2, tab3, tab4 = st.tabs(["⚠️ Alerts & Due", "📋 Maintenance Logs", "➕ Add New Log", "📊 Analytics"])

# ========================= TAB 1: ALERTS & DUE =========================
with tab1:
    st.subheader("🔔 Current Alerts")
    
    # Alert 1: Panels with status "Maintenance"
    maint_panels = panels[panels["Status"].str.lower() == "maintenance"]
    if not maint_panels.empty:
        st.warning(f"⚠️ {len(maint_panels)} panel(s) require immediate maintenance")
        st.dataframe(maint_panels[["Panel_ID", "Brand", "Model", "Location", "Status"]], use_container_width=True)
    else:
        st.success("✅ No panels in 'Maintenance' status.")
    
    # Alert 2: Panels older than 1 year (recommend inspection)
    old_panels = panels[panels["Age_Years"] > 1]
    if not old_panels.empty:
        st.info(f"📅 {len(old_panels)} panel(s) are older than 1 year – recommend inspection")
        st.dataframe(old_panels[["Panel_ID", "Brand", "Installation_Date", "Age_Years"]], use_container_width=True)
    else:
        st.info("✅ All panels are less than 1 year old.")
    
    # Alert 3: Upcoming maintenance from logs (next due date within 30 days)
    logs = load_maintenance_logs()
    if not logs.empty and "Next_Due_Date" in logs.columns:
        upcoming = logs[logs["Next_Due_Date"] <= today + timedelta(days=30)]
        upcoming = upcoming[upcoming["Next_Due_Date"] >= today]  # not past due
        if not upcoming.empty:
            st.warning(f"🔧 {len(upcoming)} maintenance task(s) due in next 30 days")
            st.dataframe(upcoming[["Panel_ID", "Issue", "Next_Due_Date"]], use_container_width=True)
        else:
            st.success("✅ No upcoming maintenance tasks in next 30 days.")
    else:
        st.info("No maintenance logs found. Add logs to see due dates.")

# ========================= TAB 2: MAINTENANCE LOGS =========================
with tab2:
    st.subheader("📋 Service History Logs")
    logs = load_maintenance_logs()
    if not logs.empty:
        # Add panel brand for readability (join with panels)
        if not panels.empty:
            logs = logs.merge(panels[["Panel_ID", "Brand"]], on="Panel_ID", how="left")
        # Format dates for display
        logs["Date_str"] = logs["Date"].dt.strftime("%Y-%m-%d") if "Date" in logs.columns else ""
        logs["Next_Due_str"] = logs["Next_Due_Date"].dt.strftime("%Y-%m-%d") if "Next_Due_Date" in logs.columns else ""
        show_cols = ["Log_ID", "Panel_ID", "Brand", "Date_str", "Issue", "Action", "Cost", "Next_Due_str"]
        show_df = logs[[c for c in show_cols if c in logs.columns]]
        st.dataframe(show_df, use_container_width=True)
        
        # Download logs
        csv = logs.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Logs as CSV", csv, "maintenance_logs.csv", "text/csv")
    else:
        st.info("No maintenance logs recorded yet. Use 'Add New Log' tab to create one.")
        # Option to create sample log
        if st.button("Generate Sample Logs"):
            sample_logs = pd.DataFrame([
                {"Log_ID": "LOG001", "Panel_ID": "SP006", "Date": "2025-12-10", 
                 "Issue": "Inverter noise", "Action": "Replaced capacitor", "Cost": 2500, "Next_Due_Date": "2026-06-10"},
                {"Log_ID": "LOG002", "Panel_ID": "SP002", "Date": "2026-01-15", 
                 "Issue": "Cleaning", "Action": "Panel cleaning", "Cost": 800, "Next_Due_Date": "2026-07-15"}
            ])
            sample_logs["Date"] = pd.to_datetime(sample_logs["Date"])
            sample_logs["Next_Due_Date"] = pd.to_datetime(sample_logs["Next_Due_Date"])
            save_maintenance_logs(sample_logs)
            st.success("Sample logs created! Refresh the page.")
            st.rerun()

# ========================= TAB 3: ADD NEW LOG =========================
with tab3:
    st.subheader("➕ Record New Maintenance Activity")
    with st.form("add_log_form"):
        panel_id = st.selectbox("Select Panel", panels["Panel_ID"].tolist())
        issue = st.text_area("Issue Description", placeholder="e.g., Inverter error, Low output, Physical damage")
        action = st.text_area("Action Taken", placeholder="e.g., Replaced fuse, Cleaned panels, Firmware update")
        cost = st.number_input("Cost (INR)", min_value=0.0, step=100.0, value=0.0)
        next_due = st.date_input("Next Maintenance Due Date", value=today + timedelta(days=180))
        submitted = st.form_submit_button("Save Log")
        
        if submitted:
            if not issue or not action:
                st.error("Please fill both Issue and Action fields.")
            else:
                logs = load_maintenance_logs()
                new_id = f"LOG{datetime.now().strftime('%Y%m%d%H%M%S')}"
                new_row = pd.DataFrame([{
                    "Log_ID": new_id,
                    "Panel_ID": panel_id,
                    "Date": today,
                    "Issue": issue,
                    "Action": action,
                    "Cost": cost,
                    "Next_Due_Date": next_due
                }])
                logs = pd.concat([logs, new_row], ignore_index=True)
                save_maintenance_logs(logs)
                st.success(f"Log {new_id} added successfully!")
                st.rerun()

# ========================= TAB 4: ANALYTICS =========================
with tab4:
    st.subheader("📊 Maintenance Analytics")
    logs = load_maintenance_logs()
    if not logs.empty:
        # Most frequent issues
        issue_counts = logs["Issue"].value_counts().reset_index()
        issue_counts.columns = ["Issue", "Count"]
        fig1 = px.bar(issue_counts.head(10), x="Issue", y="Count", title="Top 10 Most Frequent Issues", color="Count")
        st.plotly_chart(fig1, use_container_width=True)
        
        # Maintenance cost per panel
        if "Cost" in logs.columns:
            cost_by_panel = logs.groupby("Panel_ID")["Cost"].sum().reset_index()
            cost_by_panel = cost_by_panel.merge(panels[["Panel_ID", "Brand"]], on="Panel_ID", how="left")
            fig2 = px.bar(cost_by_panel, x="Panel_ID", y="Cost", color="Brand", title="Total Maintenance Cost per Panel")
            st.plotly_chart(fig2, use_container_width=True)
        
        # Maintenance over time
        logs["YearMonth"] = logs["Date"].dt.strftime("%Y-%m")
        monthly = logs.groupby("YearMonth").size().reset_index(name="Count")
        fig3 = px.line(monthly, x="YearMonth", y="Count", markers=True, title="Maintenance Events Over Time")
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("No logs available for analytics. Add maintenance logs first.")

st.caption("💡 Tip: Use the 'Add New Log' tab to record service activities. The system will alert you when next due date approaches.")