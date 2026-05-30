# Operational Resilience Intelligence Platform

An end-to-end Python and Supabase platform that simulates the operational resilience workflow of a financial institution: infrastructure monitoring, anomaly detection, incident lifecycle management, business impact analysis, dependency propagation, root cause analysis, risk scoring, recommendations, scenario simulation, and executive reporting.

This project was built as a portfolio-grade data engineering and analytics application for banking operational resilience, inspired by concepts such as incident management, SLA/RTO/RPO monitoring, critical service mapping, third-party risk, and executive resilience dashboards.

## What The Project Does

The platform models a banking technology environment with services such as Payment API, Core Banking System, Login Service, Customer Database, Transaction Database, Cloud Provider, ATM Network, and Monitoring System.

It generates operational metrics, uploads them to Supabase PostgreSQL, detects abnormal service behavior, creates incidents, resolves incidents when metrics recover, calculates business impact, analyzes downstream propagation, ranks critical services, identifies suspected root causes, generates recommendations, simulates crisis scenarios, evaluates vendor/cloud concentration risk, and displays the results in a Streamlit dashboard.

## Key Capabilities

- Synthetic banking infrastructure metrics generation
- Supabase PostgreSQL ingestion pipeline
- Anomaly detection based on latency, error rate, uptime, CPU, and memory
- Incident creation with duplicate prevention
- Incident resolution lifecycle with `resolved_at` and `duration_minutes`
- SLA, RTO, and RPO target management
- RTO tolerance breach detection
- Business impact estimation using incident severity, duration, failed transactions, transaction volume, and service criticality
- Dependency propagation analysis across banking services
- Critical service ranking
- Root cause analysis
- Global bank resilience score
- Operational recommendations by incident type, service, severity, impact, and propagation
- Crisis scenario simulation for major service failures
- Vendor risk scoring
- Cloud concentration risk analysis
- Advanced KPIs: MTTR, MTTD, MTBF, SLA compliance, open incident rate, critical incident rate
- Streamlit executive dashboard

## Architecture

```text
Synthetic Metrics
      |
      v
service_metrics table
      |
      v
Anomaly Detection Engine
      |
      v
incidents + alerts
      |
      +--> Incident Resolution Engine
      +--> Business Impact Engine
      +--> Propagation Engine
      +--> Root Cause Engine
      +--> Critical Service Ranking
      +--> Resilience Score Engine
      +--> Recommendations Engine
      +--> Scenario Simulation Engine
      +--> Vendor / Cloud Risk Engines
      +--> Advanced KPI Engine
      |
      v
Streamlit Dashboard
```

## Tech Stack

- Python
- Supabase PostgreSQL
- Supabase Python client
- Streamlit
- Pandas
- Plotly
- python-dotenv

## Database Tables

Core operational tables:

- `services`
- `dependencies`
- `service_metrics`
- `incidents`
- `alerts`

Analysis and intelligence tables:

- `business_impact`
- `incident_propagation`
- `service_criticality_ranking`
- `root_cause_analysis`
- `resilience_score`
- `service_resilience_targets`
- `tolerance_breaches`
- `resilience_recommendations`
- `scenario_simulations`
- `vendors`
- `vendor_dependencies`
- `advanced_resilience_kpis`

## Processing Engines

| Script | Purpose |
| --- | --- |
| `generate_metrics.py` | Generates synthetic service metrics for the banking infrastructure |
| `upload_metrics.py` | Uploads generated metrics to Supabase |
| `sla_rto_rpo_engine.py` | Seeds SLA, RTO, and RPO targets for critical services |
| `detect_anomalies.py` | Detects anomalies and creates incidents and alerts |
| `incident_resolution_engine.py` | Resolves incidents when service metrics return to normal |
| `tolerance_breach_engine.py` | Detects RTO breaches |
| `business_impact_engine.py` | Calculates business impact for incidents |
| `propagation_engine.py` | Analyzes downstream service propagation |
| `critical_service_ranking.py` | Ranks services by operational criticality |
| `root_cause_engine.py` | Identifies suspected root causes |
| `resilience_score_engine.py` | Calculates the global resilience score |
| `recommendations_engine.py` | Generates resilience recommendations |
| `scenario_simulation_engine.py` | Simulates major crisis scenarios |
| `vendor_risk_engine.py` | Scores vendor and third-party risk |
| `cloud_concentration_risk_engine.py` | Measures cloud provider concentration risk |
| `advanced_resilience_kpis.py` | Calculates MTTR, MTTD, MTBF, SLA compliance, and incident rates |
| `run_pipeline.py` | Runs the full pipeline in order |

## Streamlit Dashboard

The dashboard includes:

- Executive Overview
- Incident Center
- Business Impact
- Propagation Analysis
- Critical Services
- Recommendations
- Scenario Simulations
- What-if Simulation
- Vendor and Cloud Risk
- Advanced KPIs

Run locally:

```bash
streamlit run app.py
```

## Setup

1. Clone the repository:

```bash
git clone https://github.com/yanishmk/-Operational-Resilience-Intelligence-Platform.git
cd -Operational-Resilience-Intelligence-Platform
```

2. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

3. Create a `.env` file:

```env
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your-supabase-anon-key
```

4. Create the database schema:

Open Supabase SQL Editor and run:

```text
operational_resilience_schema_updates.sql
```

5. Run the full pipeline:

```bash
python run_pipeline.py
```

6. Launch the dashboard:

```bash
streamlit run app.py
```

## Streamlit Cloud Deployment

In Streamlit Community Cloud:

1. Select `app.py` as the main file.
2. Use Python 3.11 or Python 3.12 in Advanced settings.
3. Add the following secrets:

```toml
SUPABASE_URL = "https://your-project-ref.supabase.co"
SUPABASE_KEY = "your-supabase-anon-key"
```

Important: `SUPABASE_URL` should be the project URL only. Do not include `/rest/v1`.

## Example Recommendation Rules

- Payment API + latency spike + critical severity:
  `Scale payment processing workers and activate fallback payment route.`

- Cloud Provider + critical severity:
  `Trigger multi-region failover and validate critical service redundancy.`

- Customer Database + high error rate:
  `Check database connection pool, query latency and failover replica health.`

## Skills Demonstrated

- Data engineering pipeline design
- PostgreSQL schema modeling
- Supabase integration
- Operational risk analytics
- Incident lifecycle automation
- SLA/RTO/RPO monitoring
- Business impact modeling
- Dependency graph analysis
- Dashboard design with Streamlit
- Modular Python application structure
- Cloud deployment readiness

## Security Notes

The `.env` file is intentionally ignored by Git. Use `.env.example` to document required variables without exposing credentials.

For production usage, apply stricter Row Level Security policies and avoid using broad demo policies.

## Project Status

This is a portfolio project designed to demonstrate how operational resilience workflows can be modeled with Python, PostgreSQL, and interactive analytics. It is ready for demonstration and can be extended with authentication, scheduled jobs, notification integrations, and more advanced statistical anomaly detection.
