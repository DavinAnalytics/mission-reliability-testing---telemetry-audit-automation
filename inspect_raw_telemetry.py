# Inspect the structural validity of the raw CSV file to understand timestamp frequencies and row structural health

import duckdb
import pandas as pd

DATA_PATH = "data/fusion_data_raw.csv"

def inspect_telemetry_health(file_path):
    """
    Audits raw telemetry for fault label distribution and timestamp structural gaps.

    Runs two DuckDB queries:
      1. Fault label counts with kinematic error and peak shock statistics per class.
      2. Timestamp delta analysis to detect duplicate records and communication blackouts.
    """
    print('=== Initialize Telemetry Audit Pipeline ===')

    con = duckdb.connect(database=':memory:')

    print("\n[1/2] Auditing Fleet Label & Fault State Distribution...")
    optimized_query = f"""
        WITH label_counts AS (
            SELECT
                labels,
                COUNT(*) AS record_count,
                AVG(ErrRP) AS avg_roll_pitch_error,
                AVG(ErrYaw) AS avg_yaw_error,
                -- Squared form avoids repeated SQRT calls across all rows for performance
                MAX(abAccX * abAccX + abAccY * abAccY + abAccZ * abAccZ) AS max_squared_shock
            FROM '{file_path}'
            GROUP BY labels
        )
        SELECT
            labels,
            record_count,
            ROUND((record_count *100.0)/SUM(record_count) OVER (), 2) AS percentage,
            ROUND(avg_roll_pitch_error, 4) AS avg_rp_error,
            ROUND(avg_yaw_error, 4) AS avg_yaw_error,
            ROUND(SQRT(max_squared_shock), 4) AS max_total_shock_g
        FROM label_counts
        ORDER BY labels ASC;
    """
    kinematic_df = con.execute(optimized_query).df()
    print(kinematic_df.to_string(index=False))

    print("\n[2/2] Auditing Telemetry Frequency & Structural Time Gaps...")
    time_query = f"""
        WITH time_deltas AS (
            SELECT
                timestamp,
                -- LAG grabs the previous record's timestamp to compute the inter-sample gap
                timestamp - LAG(timestamp) OVER (ORDER BY timestamp) AS delta_ms
            FROM '{file_path}'
        )
        SELECT
            COUNT(*) AS total_sampled_records,
            MIN(delta_ms) AS min_time_gap_ms,   -- 0 = duplicate records (logging glitch)
            MAX(delta_ms) AS max_time_gap_ms,   -- large value = communication blackout
            ROUND(AVG(delta_ms), 2) AS avg_sensor_period_ms
        FROM time_deltas;
    """
    temporal_df = con.execute(time_query).df()
    print(temporal_df.to_string(index=False))

if __name__ == "__main__":
    inspect_telemetry_health(DATA_PATH)
