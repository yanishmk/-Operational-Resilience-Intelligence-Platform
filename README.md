# Operational Resilience Intelligence Platform

Python and Supabase project that simulates a banking infrastructure, detects operational anomalies, manages incident lifecycle, estimates business impact, analyzes propagation, identifies root causes, ranks critical services, runs scenario simulations, and computes resilience KPIs.

## Features

- Synthetic banking service metrics generation
- Supabase upload pipeline
- Anomaly detection and incident creation
- Incident resolution lifecycle with duration tracking
- SLA, RTO, RPO target management
- Tolerance breach detection
- Business impact estimation
- Incident propagation analysis
- Critical service ranking
- Root cause analysis
- Resilience score calculation
- Recommendation generation
- Crisis scenario simulation
- Vendor and cloud concentration risk analysis
- Advanced resilience KPIs
- Streamlit dashboard

## Project Structure

```text
.
├── app.py
├── generate_metrics.py
├── upload_metrics.py
├── detect_anomalies.py
├── incident_resolution_engine.py
├── sla_rto_rpo_engine.py
├── tolerance_breach_engine.py
├── business_impact_engine.py
├── propagation_engine.py
├── critical_service_ranking.py
├── root_cause_engine.py
├── resilience_score_engine.py
├── recommendations_engine.py
├── scenario_simulation_engine.py
├── vendor_risk_engine.py
├── cloud_concentration_risk_engine.py
├── advanced_resilience_kpis.py
├── run_pipeline.py
├── operational_resilience_schema_updates.sql
├── requirements.txt
└── .env.example
```

## Setup

1. Create a Supabase project.
2. Run the SQL in `operational_resilience_schema_updates.sql` inside the Supabase SQL Editor.
3. Create a local `.env` file from `.env.example`:

```env
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your-supabase-anon-key
```

4. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Run The Pipeline

Run all processing engines in order:

```bash
python run_pipeline.py
```

Or run each stage manually:

```bash
python generate_metrics.py
python upload_metrics.py
python sla_rto_rpo_engine.py
python detect_anomalies.py
python incident_resolution_engine.py
python tolerance_breach_engine.py
python business_impact_engine.py
python propagation_engine.py
python critical_service_ranking.py
python root_cause_engine.py
python resilience_score_engine.py
python recommendations_engine.py
python scenario_simulation_engine.py
python vendor_risk_engine.py
python cloud_concentration_risk_engine.py
python advanced_resilience_kpis.py
```

## Run Dashboard

```bash
streamlit run app.py
```

For Streamlit Community Cloud, add these values in **App settings > Secrets**:

```toml
SUPABASE_URL = "https://your-project-ref.supabase.co"
SUPABASE_KEY = "your-supabase-anon-key"
```

In **Advanced settings**, select a stable Python version such as Python 3.11 or 3.12. If the app was already created with another Python version, delete the Streamlit app and redeploy it with the correct version selected.

## GitHub Notes

The `.env` file and generated CSV data are intentionally ignored by Git. Use `.env.example` to document required environment variables without exposing secrets.
