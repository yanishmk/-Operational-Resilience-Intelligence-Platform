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
# DATA RETRIEVAL
# =========================================================

def get_open_incidents():
    response = (
        supabase.table("incidents")
        .select("*")
        .eq("status", "OPEN")
        .execute()
    )
    return response.data


def get_latest_metrics(service_id):
    response = (
        supabase.table("service_metrics")
        .select("*")
        .eq("service_id", service_id)
        .order("timestamp", desc=True)
        .limit(1)
        .execute()
    )
    return response.data[0] if response.data else None


# =========================================================
# RESOLUTION RULES
# =========================================================

def is_service_recovered(metrics):
    return (
        metrics["latency_ms"] < 500
        and metrics["error_rate"] < 5
        and metrics["uptime_percentage"] > 98
        and metrics["cpu_usage"] < 80
        and metrics["memory_usage"] < 80
    )


def parse_timestamp(value):
    if not value:
        return datetime.now(timezone.utc)

    normalized = str(value).replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def calculate_duration(detected_at, resolved_at):
    duration = resolved_at - parse_timestamp(detected_at)
    return max(0, int(duration.total_seconds() // 60))


# =========================================================
# UPDATE
# =========================================================

def resolve_incident(incident_id, duration_minutes):
    update = {
        "status": "RESOLVED",
        "resolved_at": datetime.now(timezone.utc).isoformat(),
        "duration_minutes": duration_minutes,
    }

    (
        supabase.table("incidents")
        .update(update)
        .eq("incident_id", incident_id)
        .execute()
    )


# =========================================================
# MAIN ENGINE
# =========================================================

def run_incident_resolution_engine():
    incidents = get_open_incidents()

    if not incidents:
        print("Aucun incident OPEN trouve.")
        return

    analyzed = 0
    resolved = 0
    still_open = 0
    missing_metrics = 0

    for incident in incidents:
        analyzed += 1
        metrics = get_latest_metrics(incident["service_id"])

        if not metrics:
            missing_metrics += 1
            print(
                f"[SKIPPED] Incident {incident['incident_id']} | "
                f"service_id={incident['service_id']} | "
                f"no metrics found"
            )
            continue

        if is_service_recovered(metrics):
            resolved_at = datetime.now(timezone.utc)
            detected_at = (
                incident.get("detected_at")
                or incident.get("created_at")
                or resolved_at.isoformat()
            )
            duration_minutes = calculate_duration(detected_at, resolved_at)

            resolve_incident(incident["incident_id"], duration_minutes)
            resolved += 1

            print(
                f"[RESOLVED] Incident {incident['incident_id']} | "
                f"service_id={incident['service_id']} | "
                f"duration={duration_minutes} min | "
                f"latency={metrics['latency_ms']}ms | "
                f"error_rate={metrics['error_rate']}%"
            )
        else:
            still_open += 1
            print(
                f"[OPEN] Incident {incident['incident_id']} | "
                f"service_id={incident['service_id']} | "
                f"latest metrics still abnormal"
            )

    print("\n===================================")
    print(f"Incidents analyses     : {analyzed}")
    print(f"Incidents resolus       : {resolved}")
    print(f"Encore ouverts          : {still_open}")
    print(f"Metriques introuvables  : {missing_metrics}")
    print("Incident Resolution termine.")
    print("===================================\n")


if __name__ == "__main__":
    run_incident_resolution_engine()
