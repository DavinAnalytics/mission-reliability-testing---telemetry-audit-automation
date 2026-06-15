# Actionable Triage Diagnostics App for Fleet Operations & Service Teams
import streamlit as st
import pandas as pd
import numpy as np

# Set dashboard layout configuration
st.set_page_config(layout="wide", page_title="Field AI Flight Telemetry Audit")

DATA_PATH = "data/fusion_data_sanitized.csv"

@st.cache_data
def load_and_downsample_telemetry(file_path):
    df = pd.read_csv(file_path)
    
    # Create a 1-second human-scale grouping key by converting timestamps to nearest whole second
    # Assuming timestamps increment roughly by 50,000 units (microseconds or scaled steps)
    df['second_bucket'] = (df['timestamp'] // 1000000).astype(int)
    
    # Aggregate data to human scale
    downsampled = df.groupby('second_bucket').agg({
        'timestamp': 'first',
        'operational_status': 'first',
        'labels': 'first',
        'ErrRP': 'mean',         # Average attitude control tracking error
        'ErrYaw': 'mean',        # Average compass heading tracking error
        'total_kinetic_shock_g': 'max' # Capture peak mechanical shock event per second
    }).reset_index(drop=True)
    
    return downsampled

# Initialize our human-scale flight dataset
flight_df = load_and_downsample_telemetry(DATA_PATH)

st.title("🛸 UAV Mission Reliability Testing & Telemetry Audit")
st.caption("Field AI Service Organization — High-Frequency Sensor Stream Triage Utility")

# --- SIDEBAR: ACTIONABLE TRIAGE INPUTS ---
st.sidebar.header("🚨 Incident Triage Control Room")

# Calculate global flight metrics for operator situational awareness
total_anomalies = int((flight_df['labels'] > 0).sum())
st.sidebar.metric(label="Flagged Anomaly Ticks", value=total_anomalies)

st.sidebar.markdown("---")
st.sidebar.subheader("Configure Triage Ticket")

# Actionable Input 1: Change ticket operational priority
ticket_priority = st.sidebar.selectbox(
    "Set Operational Priority:",
    options=["High (Immediate Physical Teardown)", "Medium (Field Inspection Required)", "Low (Software Drift Monitoring)"]
)

# Actionable Input 2: State engine checkbox to acknowledge review status
ops_reviewed = st.sidebar.checkbox("Mark Flight Leg as Reviewed by Ops")

# Actionable Input 3: Log internal technician notes
tech_notes = st.sidebar.text_area("Technician Maintenance Notes:", placeholder="Enter localized structural or component notes here...")

# Submission button to print active triage state
if st.sidebar.button("Commit Triage Actions to Fleet Log"):
    st.sidebar.success("Triage Status Successfully Dispatched!")
    st.sidebar.info(f"Priority: {ticket_priority}\n\nReviewed: {ops_reviewed}\n\nNotes: {tech_notes}")

# --- MAIN LAYOUT: ANALYTICAL INSPECTION LAYER ---
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Operational Metrics Summary")
    st.dataframe(
        flight_df[['operational_status', 'ErrRP', 'total_kinetic_shock_g']]
        .groupby('operational_status')
        .agg({'ErrRP': 'mean', 'total_kinetic_shock_g': 'max'})
        .rename(columns={'ErrRP': 'Avg RP Error', 'total_kinetic_shock_g': 'Peak Shock (G)'}),
        use_container_width=True
    )

with col2:
    st.subheader("Kinematic Mission Timeline")
    # Plotting physical vector variations and errors over time
    chart_data = flight_df[['timestamp', 'total_kinetic_shock_g', 'ErrRP']].set_index('timestamp')
    st.line_chart(chart_data)

st.markdown("---")
st.subheader("Detailed Human-Scale Telemetry Log")
st.dataframe(flight_df, use_container_width=True)