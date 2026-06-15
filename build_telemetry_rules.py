# Rule engineering pipeline to clean timing gaps and translate raw algorithmic labels into operational profiles
import duckdb
import pandas as pd

DATA_PATH = "data/fusion_data_raw.csv"
OUTPUT_PATH = "data/fusion_data_sanitized.csv"

def generate_operational_rules(input_path, output_path):
    print("=== Constructing Field AI Telemetry Rules Layer ===")
    
    con = duckdb.connect(database=':memory:')
    
    # Advanced SQL transformation query
    rules_query = f"""
        WITH chronological_telemetry AS (
            SELECT 
                timestamp,
                timestamp - LAG(timestamp) OVER (ORDER BY timestamp) AS delta_ms,
                DesRoll, Roll, DesPitch, Pitch, DesYaw, Yaw,
                ErrRP, ErrYaw,
                abAccX, abAccY, abAccZ,
                abGyrX, abGyrY, abGyrZ,
                labels,
                -- 1. Human-readable translation layer for Fleet Operations mapping
                CASE 
                    WHEN labels = 0 THEN '0_NORMAL_FLIGHT'
                    WHEN labels = 1 THEN '1_ATTITUDE_DRIFT'
                    WHEN labels = 2 THEN '2_CRITICAL_OSCILLATION'
                    WHEN labels = 3 THEN '3_ACTUATOR_SATURATION'
                    WHEN labels = 4 THEN '4_AVIONICS_FREEZE'
                    ELSE 'UNKNOWN_ANOMALY'
                END AS operational_status
            FROM '{input_path}'
        )
        SELECT 
            timestamp,
            DesRoll, Roll, DesPitch, Pitch, DesYaw, Yaw,
            ErrRP, ErrYaw,
            abAccX, abAccY, abAccZ,
            abGyrX, abGyrY, abGyrZ,
            labels,
            operational_status,
            -- 2. Kinematic Feature Engineering: Total Kinetic Shock Vector Magnitude
            ROUND(SQRT(abAccX * abAccX + abAccY * abAccY + abAccZ * abAccZ), 4) AS total_kinetic_shock_g
        FROM chronological_telemetry
        -- 3. Data Sanitization: Filter out exact duplicates (0) and drop the massive 2.2-hour gap (8.1M ms)
        WHERE delta_ms IS NULL OR (delta_ms > 0 AND delta_ms < 500000);
    """
    
    print("[Processing] Sanitizing time-series gaps and executing CASE conversions...")
    sanitized_df = con.execute(rules_query).df()
    
    # Print sample validation layout
    print("\n[Validation] Previewing Sanitized Fleet Operational Profiles:")
    print(sanitized_df[['timestamp', 'operational_status', 'total_kinetic_shock_g']].head(10).to_string(index=False))
    
    # Export sanitized dataset locally for downstream Streamlit app ingestion
    sanitized_df.to_csv(output_path, index=False)
    print(f"\n[Success] Sanitized data exported with {len(sanitized_df)} clean records to: {output_path}")

if __name__ == "__main__":
    generate_operational_rules(DATA_PATH, OUTPUT_PATH)