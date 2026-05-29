import os
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
# DATA RETRIEVAL
# =========================================================

def get_service_metrics():
    response = (
        supabase.table("service_metrics")
        .select("*")
        .order("timestamp", desc=True)
        .limit(5000)
        .execute()
    )

    return response.data

# =========================================================
# ANOMALY RULES
# =========================================================

def detect_severity(row):

    if (
        row["latency_ms"] >= 1500
        or row["error_rate"] >= 25
        or row["uptime_percentage"] <= 93
    ):
        return "CRITICAL"

    elif (
        row["latency_ms"] >= 900
        or row["error_rate"] >= 12
        or row["uptime_percentage"] <= 96
    ):
        return "HIGH"

    elif (
        row["latency_ms"] >= 500
        or row["error_rate"] >= 5
        or row["uptime_percentage"] <= 98
    ):
        return "MEDIUM"

    return "LOW"


def detect_incident_type(row):

    if row["latency_ms"] >= 500:
        return "LATENCY_SPIKE"

    if row["error_rate"] >= 5:
        return "HIGH_ERROR_RATE"

    if row["uptime_percentage"] <= 98:
        return "AVAILABILITY_DROP"

    if row["cpu_usage"] >= 80:
        return "CPU_OVERLOAD"

    if row["memory_usage"] >= 80:
        return "MEMORY_OVERLOAD"

    return "NORMAL"


def is_anomaly(row):

    return (
        row["latency_ms"] >= 500
        or row["error_rate"] >= 5
        or row["uptime_percentage"] <= 98
        or row["cpu_usage"] >= 80
        or row["memory_usage"] >= 80
    )

# =========================================================
# DUPLICATE CHECK
# =========================================================

def incident_already_exists(row):

    incident_type = detect_incident_type(row)

    response = (
        supabase.table("incidents")
        .select("incident_id")
        .eq("service_id", int(row["service_id"]))
        .eq("incident_type", incident_type)
        .eq("status", "OPEN")
        .execute()
    )

    return len(response.data) > 0

# =========================================================
# INCIDENTS
# =========================================================

def create_incident(row):

    incident_type = detect_incident_type(row)
    severity = detect_severity(row)

    description = (
        f"Anomaly detected on service_id {row['service_id']}. "
        f"Latency={row['latency_ms']}ms | "
        f"Error Rate={row['error_rate']}% | "
        f"Uptime={row['uptime_percentage']}% | "
        f"CPU={row['cpu_usage']}% | "
        f"Memory={row['memory_usage']}%"
    )

    incident = {
        "service_id": int(row["service_id"]),
        "incident_type": incident_type,
        "severity": severity,
        "status": "OPEN",
        "description": description,
    }

    response = (
        supabase.table("incidents")
        .insert(incident)
        .execute()
    )

    return response.data[0]

# =========================================================
# ALERTS
# =========================================================

def create_alert(incident):

    alert = {
        "incident_id": incident["incident_id"],
        "alert_message":
            f"{incident['severity']} anomaly detected: "
            f"{incident['incident_type']}",
        "priority": incident["severity"],
    }

    supabase.table("alerts").insert(alert, returning="minimal").execute()

    return alert

# =========================================================
# MAIN ENGINE
# =========================================================

def run_detection():

    metrics = get_service_metrics()

    if not metrics:
        print("Aucune donnée trouvée.")
        return

    anomalies = [row for row in metrics if is_anomaly(row)]

    print(f"\nNombre d'anomalies détectées : {len(anomalies)}\n")

    created = 0
    skipped = 0

    for row in anomalies:

        if incident_already_exists(row):
            skipped += 1
            continue

        incident = create_incident(row)
        alert = create_alert(incident)

        created += 1

        print(
            f"[NEW] Incident {incident['incident_id']} | "
            f"Service={incident['service_id']} | "
            f"Type={incident['incident_type']} | "
            f"Severity={incident['severity']}"
        )

    print("\n===================================")
    print(f"Nouveaux incidents : {created}")
    print(f"Déjà existants   : {skipped}")
    print("Détection terminée.")
    print("===================================\n")


if __name__ == "__main__":
    run_detection()
