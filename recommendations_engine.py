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
# DATA
# =========================================================

def get_table(table_name):
    response = supabase.table(table_name).select("*").execute()
    return response.data


def recommendation_already_exists(incident_id):
    response = (
        supabase.table("resilience_recommendations")
        .select("recommendation_id")
        .eq("incident_id", incident_id)
        .execute()
    )
    return len(response.data) > 0


# =========================================================
# RULES
# =========================================================

def priority_for(severity, impact_score, propagation_count):
    if severity == "CRITICAL" or impact_score >= 85 or propagation_count >= 5:
        return "CRITICAL"
    if severity == "HIGH" or impact_score >= 65 or propagation_count >= 3:
        return "HIGH"
    if severity == "MEDIUM" or impact_score >= 40:
        return "MEDIUM"
    return "LOW"


def build_recommendation(incident, service, impact, propagation_count):
    service_name = service.get("service_name", "Unknown Service")
    incident_type = incident["incident_type"]
    severity = incident["severity"]
    impact_score = impact.get("impact_score") if impact else 0

    if service_name == "Payment API" and incident_type == "LATENCY_SPIKE" and severity == "CRITICAL":
        return "Scale payment processing workers and activate fallback payment route."

    if service_name == "Cloud Provider" and severity == "CRITICAL":
        return "Trigger multi-region failover and validate critical service redundancy."

    if service_name == "Customer Database" and incident_type == "HIGH_ERROR_RATE":
        return "Check database connection pool, query latency and failover replica health."

    if incident_type == "LATENCY_SPIKE":
        return f"Investigate latency on {service_name}, scale capacity and review upstream dependency saturation."

    if incident_type == "HIGH_ERROR_RATE":
        return f"Review error logs for {service_name}, validate retries and inspect recent deployment changes."

    if incident_type == "AVAILABILITY_DROP":
        return f"Validate availability controls for {service_name}, check health probes and failover readiness."

    if incident_type == "CPU_OVERLOAD":
        return f"Scale compute for {service_name}, inspect hot processes and tune autoscaling thresholds."

    if incident_type == "MEMORY_OVERLOAD":
        return f"Inspect memory pressure on {service_name}, restart unhealthy workers and review memory leaks."

    if impact_score >= 80 or propagation_count >= 4:
        return f"Escalate {service_name} to incident command and validate dependent service containment."

    return f"Monitor {service_name}, validate recovery signals and document preventive actions."


# =========================================================
# INSERT
# =========================================================

def insert_recommendation(row):
    (
        supabase.table("resilience_recommendations")
        .insert(row, returning="minimal")
        .execute()
    )


# =========================================================
# MAIN ENGINE
# =========================================================

def run_recommendations_engine():
    incidents = get_table("incidents")
    services = get_table("services")
    impacts = get_table("business_impact")
    propagations = get_table("incident_propagation")

    service_by_id = {service["service_id"]: service for service in services}
    impact_by_incident_id = {
        impact["incident_id"]: impact
        for impact in impacts
    }

    created = 0
    skipped = 0

    for incident in incidents:
        incident_id = incident["incident_id"]

        if recommendation_already_exists(incident_id):
            skipped += 1
            continue

        service = service_by_id.get(incident["service_id"], {})
        impact = impact_by_incident_id.get(incident_id, {})
        propagation_count = sum(
            1 for prop in propagations
            if prop["incident_id"] == incident_id
        )

        priority = priority_for(
            incident["severity"],
            impact.get("impact_score") or 0,
            propagation_count
        )

        row = {
            "incident_id": incident_id,
            "service_id": incident["service_id"],
            "recommendation_text": build_recommendation(
                incident,
                service,
                impact,
                propagation_count
            ),
            "priority": priority,
        }

        insert_recommendation(row)
        created += 1

        print(
            f"[RECOMMENDATION] Incident {incident_id} | "
            f"service_id={incident['service_id']} | "
            f"priority={priority} | "
            f"{row['recommendation_text']}"
        )

    print("\n===================================")
    print(f"Nouvelles recommandations : {created}")
    print(f"Deja existantes           : {skipped}")
    print("Recommendations Engine termine.")
    print("===================================\n")


if __name__ == "__main__":
    run_recommendations_engine()
