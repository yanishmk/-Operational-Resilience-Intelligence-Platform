import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(override=True)

for proxy_var in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"):
    os.environ.pop(proxy_var, None)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_open_incidents():
    response = (
        supabase.table("incidents")
        .select("*")
        .execute()
    )
    return response.data


def get_service(service_id):
    response = (
        supabase.table("services")
        .select("*")
        .eq("service_id", service_id)
        .limit(1)
        .execute()
    )
    return response.data[0] if response.data else {}


def parse_timestamp(value):
    if not value:
        return datetime.now(timezone.utc)

    normalized = str(value).replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def get_incident_metrics(incident):
    started_at = parse_timestamp(incident.get("created_at"))
    ended_at = parse_timestamp(incident.get("resolved_at")) if incident.get("resolved_at") else datetime.now(timezone.utc)

    response = (
        supabase.table("service_metrics")
        .select("*")
        .eq("service_id", incident["service_id"])
        .gte("timestamp", started_at.isoformat())
        .lte("timestamp", ended_at.isoformat())
        .execute()
    )

    return response.data


def impact_already_exists(incident_id):
    response = (
        supabase.table("business_impact")
        .select("impact_id")
        .eq("incident_id", incident_id)
        .execute()
    )
    return len(response.data) > 0


def calculate_business_impact(incident):
    service_id = incident["service_id"]
    severity = incident["severity"]
    service = get_service(service_id)
    metrics = get_incident_metrics(incident)

    base_customers = {
        1: 18000,
        2: 12000,
        3: 25000,
        4: 30000,
        5: 40000,
        6: 22000,
        7: 50000,
        8: 35000,
        9: 8000,
        10: 15000,
        11: 60000,
        12: 5000,
    }

    severity_multiplier = {
        "LOW": 0.10,
        "MEDIUM": 0.30,
        "HIGH": 0.60,
        "CRITICAL": 0.90,
    }

    average_transaction_value = {
        5: 85.0,
        7: 120.0,
        8: 95.0,
        10: 60.0,
        11: 75.0,
    }.get(service_id, 45.0)

    duration_minutes = incident.get("duration_minutes")
    if duration_minutes is None:
        started_at = parse_timestamp(incident.get("created_at"))
        ended_at = parse_timestamp(incident.get("resolved_at")) if incident.get("resolved_at") else datetime.now(timezone.utc)
        duration_minutes = max(1, int((ended_at - started_at).total_seconds() // 60))

    transaction_volume = sum(metric.get("transaction_volume") or 0 for metric in metrics)
    metric_failed_transactions = sum(metric.get("failed_transactions") or 0 for metric in metrics)
    business_criticality = service.get("business_criticality") or 5
    criticality_multiplier = 1 + (business_criticality / 20)

    lost_transactions = int(metric_failed_transactions * criticality_multiplier)

    if lost_transactions == 0 and transaction_volume > 0:
        lost_transactions = int(
            transaction_volume
            * severity_multiplier.get(severity, 0.20)
            * 0.02
            * criticality_multiplier
        )

    affected_customers = int(
        base_customers.get(service_id, 10000)
        * severity_multiplier.get(severity, 0.20)
        * min(max(duration_minutes / 30, 0.5), 4)
    )

    estimated_loss_usd = round(lost_transactions * average_transaction_value, 2)

    impact_score = min(
        100,
        round(
            affected_customers / 600
            + lost_transactions / 100
            + estimated_loss_usd / 5000
            + duration_minutes / 10,
            2,
        ),
    )

    return {
        "incident_id": incident["incident_id"],
        "affected_customers": affected_customers,
        "lost_transactions": lost_transactions,
        "estimated_loss_usd": estimated_loss_usd,
        "impact_score": impact_score,
    }


def insert_business_impact(impact):
    (
        supabase.table("business_impact")
        .insert(impact, returning="minimal")
        .execute()
    )
    return impact


def run_business_impact_engine():
    incidents = get_open_incidents()

    if not incidents:
        print("Aucun incident OPEN trouvé.")
        return

    created = 0
    skipped = 0

    for incident in incidents:
        incident_id = incident["incident_id"]

        if impact_already_exists(incident_id):
            skipped += 1
            continue

        impact = calculate_business_impact(incident)
        inserted = insert_business_impact(impact)

        created += 1

        print(
            f"[IMPACT] Incident {incident_id} | "
            f"Customers={inserted['affected_customers']} | "
            f"Lost Tx={inserted['lost_transactions']} | "
            f"Loss=${inserted['estimated_loss_usd']} | "
            f"Score={inserted['impact_score']}"
        )

    print("\n===================================")
    print(f"Nouveaux impacts : {created}")
    print(f"Déjà existants  : {skipped}")
    print("Business Impact terminé.")
    print("===================================\n")


if __name__ == "__main__":
    run_business_impact_engine()
