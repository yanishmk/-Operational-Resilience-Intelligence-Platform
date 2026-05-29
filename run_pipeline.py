import subprocess
import sys

PIPELINE_STEPS = [
    "generate_metrics.py",
    "upload_metrics.py",
    "sla_rto_rpo_engine.py",
    "detect_anomalies.py",
    "incident_resolution_engine.py",
    "tolerance_breach_engine.py",
    "business_impact_engine.py",
    "propagation_engine.py",
    "critical_service_ranking.py",
    "root_cause_engine.py",
    "resilience_score_engine.py",
    "recommendations_engine.py",
    "scenario_simulation_engine.py",
    "vendor_risk_engine.py",
    "cloud_concentration_risk_engine.py",
    "advanced_resilience_kpis.py",
]


def run_step(script_name):
    print("\n===================================")
    print(f"Running {script_name}")
    print("===================================\n")

    subprocess.run([sys.executable, script_name], check=True)


def run_pipeline():
    for script_name in PIPELINE_STEPS:
        run_step(script_name)

    print("\nPipeline completed successfully.\n")


if __name__ == "__main__":
    run_pipeline()
