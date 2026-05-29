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


def breach_already_exists(incident_id, breach_type):
    response = (
        supabase.table("tolerance_breaches")
        .select("breach_id")
        .eq("incident_id", incident_id)
        .eq("breach_type", breach_type)
        .execute()
    )
    return len(response.data) > 0


# =========================================================
# TIME
# =========================================================

def parse_timestamp(value):
    if not value:
        return datetime.now(timezone.utc)

    normalized = str(value).replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def incident_duration_minutes(incident):
    if incident.get("duration_minutes") is not None:
        return int(incident["duration_minutes"])

    started_at = incident.get("detected_at") or incident.get("created_at")
    ended_at = incident.get("resolved_at")

    if not ended_at and incident.get("status") == "OPEN":
        ended_at = datetime.now(timezone.utc).isoformat()

    duration = parse_timestamp(ended_at) - parse_timestamp(started_at)
    return max(0, int(duration.total_seconds() // 60))


# =========================================================
# INSERT
# =========================================================

def insert_breach(row):
    (
        supabase.table("tolerance_breaches")
        .insert(row, returning="minimal")
        .execute()
    )


# =========================================================
# MAIN ENGINE
# =========================================================

def run_tolerance_breach_engine():
    incidents = get_table("incidents")
    targets = get_table("service_resilience_targets")
    target_by_service = {target["service_id"]: target for target in targets}

    analyzed = 0
    created = 0
    skipped = 0

    for incident in incidents:
        if incident.get("status") not in ("OPEN", "RESOLVED"):
            continue

        analyzed += 1
        service_id = incident["service_id"]
        target = target_by_service.get(service_id)

        if not target:
            continue

        duration_minutes = incident_duration_minutes(incident)
        threshold_minutes = target["rto_minutes"]

        if duration_minutes <= threshold_minutes:
            continue

        if breach_already_exists(incident["incident_id"], "RTO_BREACH"):
            skipped += 1
            continue

        row = {
            "incident_id": incident["incident_id"],
            "service_id": service_id,
            "breach_type": "RTO_BREACH",
            "duration_minutes": duration_minutes,
            "threshold_minutes": threshold_minutes,
            "severity": incident["severity"],
        }

        insert_breach(row)
        created += 1

        print(
            f"[BREACH] Incident {incident['incident_id']} | "
            f"service_id={service_id} | "
            f"duration={duration_minutes} min | "
            f"RTO={threshold_minutes} min | "
            f"severity={incident['severity']}"
        )

    print("\n===================================")
    print(f"Incidents analyses : {analyzed}")
    print(f"Nouveaux breaches  : {created}")
    print(f"Deja existants     : {skipped}")
    print("Tolerance Breach Engine termine.")
    print("===================================\n")


if __name__ == "__main__":
    run_tolerance_breach_engine()
