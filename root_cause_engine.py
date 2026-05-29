import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(override=True)

for proxy_var in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"):
    os.environ.pop(proxy_var, None)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_table(table_name):
    response = supabase.table(table_name).select("*").execute()
    return response.data


def clear_old_root_causes():
    supabase.table("root_cause_analysis").delete().neq("root_cause_id", 0).execute()


def get_service_name(service_id, services):
    for service in services:
        if service["service_id"] == service_id:
            return service["service_name"]
    return "Unknown Service"


def calculate_confidence(incident, propagations, impacts):
    severity_weight = {
        "LOW": 25,
        "MEDIUM": 45,
        "HIGH": 70,
        "CRITICAL": 90,
    }

    base = severity_weight.get(incident["severity"], 40)

    propagation_count = len([
        p for p in propagations
        if p["incident_id"] == incident["incident_id"]
    ])

    impact = next(
        (i for i in impacts if i["incident_id"] == incident["incident_id"]),
        None
    )

    impact_score = impact["impact_score"] if impact else 0

    confidence = (
        base * 0.5
        + min(propagation_count * 8, 30)
        + impact_score * 0.2
    )

    return min(100, round(confidence, 2))


def build_explanation(incident, service_name, propagations, impacts):
    incident_id = incident["incident_id"]

    propagation_count = len([
        p for p in propagations
        if p["incident_id"] == incident_id
    ])

    impact = next(
        (i for i in impacts if i["incident_id"] == incident_id),
        None
    )

    if impact:
        loss = impact["estimated_loss_usd"]
        customers = impact["affected_customers"]
    else:
        loss = 0
        customers = 0

    explanation = (
        f"The incident started on {service_name}. "
        f"It generated {propagation_count} impacted downstream services. "
        f"Estimated affected customers: {customers}. "
        f"Estimated financial loss: ${loss}. "
        f"The service is considered the suspected root cause because the incident "
        f"originated there and propagated through the dependency graph."
    )

    return explanation


def root_cause_already_exists(incident_id):
    response = (
        supabase.table("root_cause_analysis")
        .select("root_cause_id")
        .eq("incident_id", incident_id)
        .execute()
    )

    return len(response.data) > 0


def run_root_cause_engine():
    services = get_table("services")
    incidents = get_table("incidents")
    propagations = get_table("incident_propagation")
    impacts = get_table("business_impact")

    created = 0
    skipped = 0

    for incident in incidents:
        incident_id = incident["incident_id"]

        if root_cause_already_exists(incident_id):
            skipped += 1
            continue

        root_service_id = incident["service_id"]
        root_service_name = get_service_name(root_service_id, services)

        confidence = calculate_confidence(
            incident,
            propagations,
            impacts
        )

        explanation = build_explanation(
            incident,
            root_service_name,
            propagations,
            impacts
        )

        row = {
            "incident_id": incident_id,
            "suspected_root_service_id": root_service_id,
            "suspected_root_service_name": root_service_name,
            "confidence_score": confidence,
            "explanation": explanation,
        }

        supabase.table("root_cause_analysis").insert(row, returning="minimal").execute()

        created += 1

        print(
            f"Incident {incident_id} | "
            f"Root Cause={root_service_name} | "
            f"Confidence={confidence}"
        )

    print("\n===================================")
    print(f"Nouvelles root causes : {created}")
    print(f"Déjà existantes      : {skipped}")
    print("Root Cause Engine terminé.")
    print("===================================\n")


if __name__ == "__main__":
    run_root_cause_engine()
