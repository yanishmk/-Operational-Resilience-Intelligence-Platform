import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from supabase import create_client

# =========================================================
# CONFIG
# =========================================================

load_dotenv(override=True)

for proxy_var in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"):
    os.environ.pop(proxy_var, None)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# =========================================================
# DATA
# =========================================================

def get_table(table_name):
    response = supabase.table(table_name).select("*").execute()
    return response.data


def parse_timestamp(value):
    if not value:
        return None

    normalized = str(value).replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


# =========================================================
# KPI CALCULATIONS
# =========================================================

def calculate_mttr(incidents):
    durations = [
        incident.get("duration_minutes") or 0
        for incident in incidents
        if incident.get("status") == "RESOLVED"
        and incident.get("duration_minutes") is not None
    ]

    return round(sum(durations) / len(durations), 2) if durations else 0


def calculate_mttd():
    # Metrics are simulated minute-by-minute and incidents are created immediately
    # by the detection engine, so MTTD is treated as near-real-time.
    return 1.0


def calculate_mtbf(incidents):
    sorted_incidents = sorted(
        [
            incident for incident in incidents
            if incident.get("created_at")
        ],
        key=lambda incident: incident["created_at"]
    )

    if len(sorted_incidents) < 2:
        return 0

    gaps = []

    for index in range(1, len(sorted_incidents)):
        previous = parse_timestamp(sorted_incidents[index - 1]["created_at"])
        current = parse_timestamp(sorted_incidents[index]["created_at"])

        if previous and current:
            gaps.append(max(0, (current - previous).total_seconds() / 60))

    return round(sum(gaps) / len(gaps), 2) if gaps else 0


def calculate_rates(incidents, breaches):
    total_incidents = len(incidents) or 1
    open_incidents = sum(1 for incident in incidents if incident.get("status") == "OPEN")
    critical_incidents = sum(1 for incident in incidents if incident.get("severity") == "CRITICAL")
    breached_incidents = {breach["incident_id"] for breach in breaches}

    sla_compliance_rate = round(((total_incidents - len(breached_incidents)) / total_incidents) * 100, 2)
    open_incident_rate = round((open_incidents / total_incidents) * 100, 2)
    critical_incident_rate = round((critical_incidents / total_incidents) * 100, 2)

    return sla_compliance_rate, open_incident_rate, critical_incident_rate


def calculate_kpis():
    incidents = get_table("incidents")
    breaches = get_table("tolerance_breaches")

    sla_compliance_rate, open_incident_rate, critical_incident_rate = calculate_rates(
        incidents,
        breaches
    )

    return {
        "mttr_minutes": calculate_mttr(incidents),
        "mttd_minutes": calculate_mttd(),
        "mtbf_minutes": calculate_mtbf(incidents),
        "sla_compliance_rate": sla_compliance_rate,
        "open_incident_rate": open_incident_rate,
        "critical_incident_rate": critical_incident_rate,
    }


# =========================================================
# INSERT
# =========================================================

def insert_kpis(row):
    (
        supabase.table("advanced_resilience_kpis")
        .insert(row, returning="minimal")
        .execute()
    )


def run_advanced_resilience_kpis():
    kpis = calculate_kpis()
    insert_kpis(kpis)

    print("\n===== Advanced Resilience KPIs =====")
    print(f"MTTR minutes           : {kpis['mttr_minutes']}")
    print(f"MTTD minutes           : {kpis['mttd_minutes']}")
    print(f"MTBF minutes           : {kpis['mtbf_minutes']}")
    print(f"SLA compliance rate    : {kpis['sla_compliance_rate']}%")
    print(f"Open incident rate     : {kpis['open_incident_rate']}%")
    print(f"Critical incident rate : {kpis['critical_incident_rate']}%")
    print("====================================\n")


if __name__ == "__main__":
    run_advanced_resilience_kpis()
