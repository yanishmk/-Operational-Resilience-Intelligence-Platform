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


def clear_old_scores():
    supabase.table("resilience_score").delete().neq("score_id", 0).execute()


# =========================================================
# SCORING LOGIC
# =========================================================

def risk_level(score):
    if score >= 85:
        return "LOW"
    elif score >= 65:
        return "MEDIUM"
    elif score >= 40:
        return "HIGH"
    return "CRITICAL"


def calculate_resilience_score():
    incidents = get_table("incidents")
    impacts = get_table("business_impact")
    root_causes = get_table("root_cause_analysis")
    propagations = get_table("incident_propagation")
    services = get_table("services")

    total_incidents = len(incidents)

    critical_incidents = sum(
        1 for inc in incidents
        if inc["severity"] == "CRITICAL"
    )

    high_incidents = sum(
        1 for inc in incidents
        if inc["severity"] == "HIGH"
    )

    total_loss = sum(
        impact.get("estimated_loss_usd") or 0
        for impact in impacts
    )

    unresolved_incidents = sum(
        1 for inc in incidents
        if inc.get("status") == "OPEN"
    )

    durations = [
        inc.get("duration_minutes") or 0
        for inc in incidents
        if inc.get("duration_minutes") is not None
    ]

    avg_incident_duration = (
        sum(durations) / len(durations)
        if durations else 0
    )

    avg_impact_score = (
        sum((impact.get("impact_score") or 0) for impact in impacts) / len(impacts)
        if impacts else 0
    )

    avg_root_confidence = (
        sum((root.get("confidence_score") or 0) for root in root_causes) / len(root_causes)
        if root_causes else 0
    )

    propagation_count = len(propagations)
    service_by_id = {service["service_id"]: service for service in services}

    sla_breaches = 0
    rto_breaches = 0

    for incident in incidents:
        service = service_by_id.get(incident["service_id"], {})
        duration_minutes = incident.get("duration_minutes") or 0
        rto_minutes = service.get("rto_minutes")

        if incident.get("status") == "OPEN":
            sla_breaches += 1

        if rto_minutes and duration_minutes > rto_minutes:
            rto_breaches += 1

    # Formule plus réaliste pour un projet portfolio
    incident_penalty = min(total_incidents * 0.6, 20)
    critical_penalty = min(critical_incidents * 1.4, 28)
    high_penalty = min(high_incidents * 0.8, 12)
    unresolved_penalty = min(unresolved_incidents * 2.0, 20)
    duration_penalty = min(avg_incident_duration / 10, 15)
    sla_penalty = min(sla_breaches * 1.5, 15)
    rto_penalty = min(rto_breaches * 2.0, 12)
    impact_penalty = min(avg_impact_score * 0.22, 22)
    loss_penalty = min(total_loss / 500000, 15)
    propagation_penalty = min(propagation_count * 0.08, 12)

    total_penalty = (
        incident_penalty
        + critical_penalty
        + high_penalty
        + unresolved_penalty
        + duration_penalty
        + sla_penalty
        + rto_penalty
        + impact_penalty
        + loss_penalty
        + propagation_penalty
    )

    resilience_score = max(0, round(100 - total_penalty, 2))

    return {
        "total_incidents": total_incidents,
        "critical_incidents": critical_incidents,
        "unresolved_incidents": unresolved_incidents,
        "avg_incident_duration_minutes": round(avg_incident_duration, 2),
        "total_estimated_loss_usd": round(total_loss, 2),
        "sla_breaches": sla_breaches,
        "rto_breaches": rto_breaches,
        "propagation_count": propagation_count,
        "avg_impact_score": round(avg_impact_score, 2),
        "avg_root_cause_confidence": round(avg_root_confidence, 2),
        "resilience_score": resilience_score,
        "risk_level": risk_level(resilience_score),
    }


# =========================================================
# INSERT
# =========================================================

def insert_resilience_score(score):
    clear_old_scores()
    supabase.table("resilience_score").insert(score, returning="minimal").execute()


# =========================================================
# MAIN
# =========================================================

def run_resilience_score_engine():
    score = calculate_resilience_score()
    insert_resilience_score(score)

    print("\n===== Bank Resilience Score =====")
    print(f"Total incidents        : {score['total_incidents']}")
    print(f"Critical incidents     : {score['critical_incidents']}")
    print(f"Unresolved incidents   : {score['unresolved_incidents']}")
    print(f"Avg duration minutes   : {score['avg_incident_duration_minutes']}")
    print(f"Estimated total loss   : ${score['total_estimated_loss_usd']}")
    print(f"SLA breaches           : {score['sla_breaches']}")
    print(f"RTO breaches           : {score['rto_breaches']}")
    print(f"Propagation count      : {score['propagation_count']}")
    print(f"Average impact score   : {score['avg_impact_score']}")
    print(f"Root cause confidence  : {score['avg_root_cause_confidence']}")
    print("--------------------------------")
    print(f"Resilience Score       : {score['resilience_score']} / 100")
    print(f"Risk Level             : {score['risk_level']}")
    print("================================\n")


if __name__ == "__main__":
    run_resilience_score_engine()
