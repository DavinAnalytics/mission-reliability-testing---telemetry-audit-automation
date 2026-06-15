# UAV Mission Reliability Testing & Telemetry Audit Automation

**Author:** Davin Kim  
**Core Infrastructure:** DuckDB (SQL) · Python (pandas) · Conda · PowerShell  
**Frontend Stack:** Streamlit (Operations UI) · HTML5/CSS3/JS (GitHub Pages Executive Briefing)

---

## Why clean dashboards fail rugged robots

Most data analytics portfolios are built for the cloud, tracking clean consumer transactions, e-commerce clicks, or predictable SaaS metrics.

Physical robots don't live in the cloud. When an autonomous platform operates at the edge in unstructured, GPS-denied environments, a sensor failure isn't a database anomaly; it can take the vehicle offline mid-operation. If a drone or quadruped experiences thrust degradation, localized stabilization collapse, or structural impact mid-mission, a field operations team can't spend hours parsing a sub-second, multi-sensor fused telemetry log with hundreds of variables.

This project builds a local data pipeline that ingests 12,253 rows of high-frequency kinematic telemetry (`fusion_data_raw.csv`), isolates physical failure modes through time-series feature engineering, downsamples edge noise into human-scale windows, and ships an interactive Fleet Operations Portal that ops and support teams can actually use during triage.

---

## Local execution architecture

This system bypasses heavy cloud warehouses entirely. Everything runs locally, which matters when you're working against edge-collected data that doesn't belong in a managed service.

* **Ingestion & Processing:** DuckDB running an embedded, vectorized execution engine directly in-memory inside a local Python process. It processes complex analytical queries on raw CSV lines at native C++ speeds.
* **Environment Control:** Isolated Conda environment (`uav-env`) on Windows 10 managing dependencies without global package pollution.
* **Triage Presentation:** Streamlit reading directly from our engineered data layer, optimized with local function caching (`@st.cache_data`) to prevent redundant disk I/O during UI interactions.

---

## 📈 Technical Findings & Kinematic Insights

Our telemetry audit isolated **189 critical anomalous seconds** out of the active flight timeline. By querying sensor variances and vector limits across the dataset, the pipeline mapped out the exact physical "signatures" of four distinct system faults:

### 1. Flight Leg Failure Signatures
* **Label 1 (Attitude Drift):** Minor tracking deviations where actual orientation drifted slightly from commanded paths (`avg_rp_error: 0.0417`). This represents acceptable closed-loop adjustments under localized environmental loads (e.g., crosswinds).
* **Label 2 (Critical Oscillation & Structural Shock):** Major hardware instability. Autopilot tracking errors multiplied **10x** ($0.4292$), accompanied by an extreme peak mechanical shock vector spike of **89.42 Gs**. This mathematical signature flags a severe structural impact event or aerodynamic control loop breakdown.
* **Label 3 (Actuator Saturation):** Localized component strain. Autopilot tracking errors increased slightly ($0.0532$), but registered the lowest overall peak mechanical shock ($10.42$ Gs). This isolates an over-saturated motor working at maximum thermal limits to keep the platform airborne without causing immediate structural trauma.
* **Label 4 (Avionics Freeze / Dead State):** A critical software lockup. Autopilot tracking errors dropped to **exactly 0.0000**. Because a moving aerial vehicle navigating 3D physical space *never* experiences perfectly zero error against its desired target, this absolute mathematical zero exposes a frozen flight controller loop that locked the last known state.

### 2. Data Pipeline & Temporal Integrity
* **Double-Clipping Identified:** The pipeline exposed a minimum time step gap of `0.0 ms`, proving the hardware logger recorded duplicate sensor frames at identical millisecond marks. 
* **Packet-Loss Isolation:** The temporal audit caught a maximum consecutive time gap of **8,149,655.5 ms (~2.26 hours)**. This represents a non-flight workshop bench period. By setting our data sanitization boundary filter to `delta_ms < 500000`, the transformation layer cleanly severed this gap, preventing massive timeline distortion on downstream analytical visuals.

---

## 🛠️ Feature Engineering & SQL Optimizations

### Vector Magnitude Optimization (Kinetic Shock)
Calculating the 3D Euclidean Vector Magnitude ($\|v\| = \sqrt{x^2 + y^2 + z^2}$) to extract overall physical impact forces across all 12,253 rows is a slow CPU operation if square roots are executed row-by-row. 

To optimize execution velocity, the pipeline computes the *squared magnitude* ($x^2 + y^2 + z^2$) across the dataset inside a Common Table Expression (CTE) first. Because squaring preserves relative numeric ordering ($A > B \iff A^2 > B^2$), the database isolates the maximum squared winner at C++ speed and applies the computationally heavy `SQRT` function **only once** per grouped category.

### Dual Independent Axis Scale Design
When plotting telemetry variations, standard single-axis charts suffer from **axis scale dominance**. Because peak mechanical shock reaches **89.42 Gs**, plotting tracking errors (ranging between `0.0` and `0.43`) on the same axis flattens the error line into an unreadable 1-pixel baseline. 

The operations interface resolves this by splitting the time series into independent layout columns with distinct vertical scales. This exposes the **smoking gun of the mission failure**: a clean chronological correlation proving that the structural trauma (89G spike) and the tracking error explosion occurred at the exact same physical millisecond.

---

## User interfaces and deployment

The frontend is split into two distinct environments to target different organizational stakeholders:

### Operations tool (Streamlit)
An interactive utility for support and dispatch teams actively working a maintenance triage ticket.
* **Actionable Triage Sidebar:** Real-time metrics display flashing incident tallies. Interactive dropdown menus and text fields allow technicians to dynamically escalate ticket priority (`High`, `Medium`, `Low`) and commit review states directly from the workspace UI.
* **Optimized Human-Scale Interface:** Groups high-frequency data into 1-second chunks—calculating the mean of tracking errors to observe systematic drift, while preserving the maximum acceleration force to ensure critical impact spikes are never washed out.

### Executive summary (GitHub Pages)
A single-page web artifact designed for engineering managers and stakeholders who need to review vehicle flight health without running terminal environments.
* **Interactive Physics Motion:** Features CSS keyframe animations visually demonstrating vehicle pitch/roll drift and high-frequency structural vibration.
* **Conversion Funnel:** Provides an executive summary overview topped with a prominent call-to-action button driving traffic directly to the active operational dashboard interface.

---

## Quickstart

To run the pipeline and dashboard locally, execute these commands in PowerShell in order:

powershell
# 1. Clone the repository
git clone [https://github.com/DavinAnalytics/uav-telemetry-pipeline.git](https://github.com/DavinAnalytics/uav-telemetry-pipeline.git)
cd uav-telemetry-pipeline

# 2. Set up the Conda environment
conda create -n uav-env python=3.11 -y
conda activate uav-env

# 3. Install core dependencies
pip install pandas duckdb streamlit

# 4. Execute the rules engineering pipeline to generate sanitized data
python build_telemetry_rules.py

# 5. Launch the local triage interactive dashboard
streamlit run app.py