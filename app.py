import streamlit as st
import pandas as pd
import altair as alt

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Fleet Telemetry Triage Room",
    page_icon="🛸",
    layout="wide",
)

DATA_PATH = "data/fusion_data_sanitized.csv"

@st.cache_data
def load_data():
    """Loads sanitized time-series flight telemetry and engineers initial bucket partitions."""
    df = pd.read_csv(DATA_PATH)
    # Group raw high-frequency 20Hz ticks into discrete 1-second buckets
    df["second_bucket"] = (df["timestamp"] // 1000000).astype(int)
    # Format algorithmic labels into clean presentation titles
    df["fault_label"] = (
        df["operational_status"]
        .str.replace(r"^\d+_", "", regex=True)
        .str.replace("_", " ")
        .str.title()
    )
    return df

# Initialize Data Cache
df = load_data()


# ==============================================================================
# PHASE 1: STEP-AHEAD STATE ENGINE & DATA AGGREGATION
# ==============================================================================

# Extract unique fault categories available for structural filtering
fault_options = sorted(df["fault_label"].unique())

# Setup persistent session states for filter memory
if "selected_faults" not in st.session_state:
    st.session_state.selected_faults = fault_options

# Apply active sidebar filter to the raw data frame
filtered = df[df["fault_label"].isin(st.session_state.selected_faults)] if st.session_state.selected_faults else df.iloc[:0]

if not filtered.empty:
    # Kinematic Downsampling Layer: Aggregate to 1-second chunks
    # CRITICAL: ErrRP uses mean to catch drift; total_kinetic_shock_g MUST use max to preserve impact trauma
    agg_df = (
        filtered.groupby("second_bucket")
        .agg(
            {
                "ErrRP": "mean",
                "total_kinetic_shock_g": "max",  
                "fault_label": "first",
            }
        )
        .reset_index()
    )
else:
    agg_df = pd.DataFrame(columns=["second_bucket", "ErrRP", "total_kinetic_shock_g", "fault_label"])


# ==============================================================================
# PHASE 2: SIDEBAR CONTROL ROOM INTERFACE
# ==============================================================================
with st.sidebar:
    st.subheader("🚨 Incident Triage Control Room")
    
    # Synchronized Triage Metric: Counts unique consolidated seconds where a failure mode was active
    total_anomalous_seconds = int((agg_df["fault_label"] != "Normal Flight").sum())
    st.metric(label="Flagged Anomaly Ticks (Seconds)", value=f"{total_anomalous_seconds}")
    
    st.markdown("---")
    st.subheader("Configure Triage Ticket")
    
    ticket_priority = st.selectbox(
        "Set Operational Priority:",
        options=[
            "High (Immediate Physical Teardown)", 
            "Medium (Field Inspection Required)", 
            "Low (Software Drift Monitoring)"
        ]
    )
    
    ops_reviewed = st.checkbox("Mark Flight Leg as Reviewed by Ops")
    tech_notes = st.text_area("Technician Maintenance Notes:", placeholder="Enter localized structural or component notes here...")
    
    if st.button("Commit Triage Actions to Fleet Log", use_container_width=True):
        st.success("Triage Status Successfully Dispatched!")
        st.info(f"**Priority:** {ticket_priority}\n\n**Ops Status:** {'Reviewed' if ops_reviewed else 'Pending'}\n\n**Notes:** {tech_notes}")
    st.caption("Demo mode: triage actions are displayed above but not persisted.")

    st.markdown("---")
    
    st.multiselect("Active Fault Class Filter", fault_options, key="selected_faults")
    
    st.link_button(
        "View Source Code on GitHub",
        "https://github.com/DavinAnalytics/uav-telemetry-audit-pipeline",
    )


# ==============================================================================
# PHASE 3: MAIN ANALYTICAL APPLICATION DISPLAY LAYER
# ==============================================================================
st.title("🛸 UAV Mission Reliability Testing & Telemetry Audit")
st.caption("AI Service Organization — High-Frequency Sensor Stream Triage Utility")

if filtered.empty:
    st.warning("No fault classes selected. Adjust the sidebar filter options to load views.")
else:
    # --- KPI METRICS GRID ---
    kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
    
    with kpi_col1:
        with st.container(border=True):
            avg_err = filtered["ErrRP"].mean()
            st.metric("Avg Tracking Error (ErrRP)", f"{avg_err:.4f}", 
                      delta="Elevated Drift" if avg_err > 0.05 else None, delta_color="inverse")
            
    with kpi_col2:
        with st.container(border=True):
            max_shock = filtered["total_kinetic_shock_g"].max()
            st.metric("Peak Impact Force", f"{max_shock:.2f} G", 
                      delta="Critical Trauma" if max_shock > 50 else None, delta_color="inverse")
            
    with kpi_col3:
        with st.container(border=True):
            st.metric("Anomalous Flight Legs", f"{total_anomalous_seconds} secs")

    # --- INDEPENDENT DUAL-AXIS TIMELINE LAYER ---
    with st.container(border=True):
        st.subheader("Kinematic Mission Timeline (Independent Scales)")
        
        # Instantiate uniform baseline chart space
        base = alt.Chart(agg_df).encode(
            x=alt.X("second_bucket:Q", title="Timeline (Seconds Bucket)", scale=alt.Scale(zero=False))
        )
        
        # High-G Kinetic Shock Line Specification
        shock_line = base.mark_line(color="#58a6ff").encode(
            y=alt.Y("total_kinetic_shock_g:Q", title="Peak Shock (G)", scale=alt.Scale(domain=[0, 100])),
            tooltip=["second_bucket", "total_kinetic_shock_g", "fault_label"]
        )
        
        # Sub-Degree Closed-Loop Attitude Tracking Error Line Specification
        err_line = base.mark_line(color="#ff7b72").encode(
            y=alt.Y("ErrRP:Q", title="Avg Tracking Error (ErrRP)", scale=alt.Scale(zero=True)),
            tooltip=["second_bucket", "ErrRP", "fault_label"]
        )
        
        # Vertical Concatenation Layer - Forces independent axes and fills container boundaries width-wise
        final_timeline = alt.vconcat(
            shock_line.properties(height=180, width="container", title="💥 Peak Mechanical Shock Profile"),
            err_line.properties(height=180, width="container", title="🎯 Attitude Tracking Error Profile")
        ).configure_title(fontSize=14, anchor="start", color="white").resolve_scale(y="independent")
        
        st.altair_chart(final_timeline, use_container_width=True)

    # --- SENSOR STATISTICS SUMMARY PROFILE ---
    profile = (
        filtered.groupby("fault_label")
        .agg(
            {
                "ErrRP": ["mean", "max"],
                "total_kinetic_shock_g": ["mean", "max"],
                "timestamp": "count",
            }
        )
        .reset_index()
    )
    profile.columns = [
        "Fault class",
        "Avg RP error",
        "Max RP error",
        "Avg shock (G)",
        "Peak shock (G)",
        "Record count",
    ]

    with st.container(border=True):
        st.subheader("Sensor Statistics by Fault Profile Class")
        st.dataframe(profile, hide_index=True, use_container_width=True)

    # --- DISTRIBUTION PLOTS ---
    dist_col1, dist_col2 = st.columns(2)

    with dist_col1:
        with st.container(border=True):
            st.subheader("Avg RP Error Variance")
            err_chart = (
                alt.Chart(profile)
                .mark_bar()
                .encode(
                    x=alt.X("Avg RP error:Q", title="Avg RP error"),
                    y=alt.Y("Fault class:N", sort="-x", title=None),
                    color=alt.Color("Fault class:N", legend=None, scale=alt.Scale(scheme="redblue")),
                    tooltip=["Fault class", "Avg RP error", "Max RP error"],
                )
            )
            st.altair_chart(err_chart, use_container_width=True)

    with dist_col2:
        with st.container(border=True):
            st.subheader("Peak Vector Shock Isolation")
            shock_chart = (
                alt.Chart(profile)
                .mark_bar()
                .encode(
                    x=alt.X("Peak shock (G):Q", title="Peak shock (G)"),
                    y=alt.Y("Fault class:N", sort="-x", title=None),
                    color=alt.Color("Fault class:N", legend=None, scale=alt.Scale(scheme="redblue")),
                    tooltip=["Fault class", "Avg shock (G)", "Peak shock (G)"],
                )
            )
            st.altair_chart(shock_chart, use_container_width=True)