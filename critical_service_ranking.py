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


def risk_level(score):
    if score >= 85:
        return "CRITICAL"
    elif score >= 65:
        return "HIGH"
    elif score >= 40:
        return "MEDIUM"
    return "LOW"


def clear_old_ranking():
    supabase.table("service_criticality_ranking").delete().neq("ranking_id", 0).execute()


def run_critical_service_ranking():
    services = get_table("services")
    dependencies = get_table("dependencies")
    incidents = get_table("incidents")
    propagations = get_table("incident_propagation")
    impacts = get_table("business_impact")

    clear_old_ranking()

    rows = []

    for service in services:
        service_id = service["service_id"]
        service_name = service["service_name"]
        business_criticality = service.get("business_criticality") or 5

        dependency_count = sum(
            1 for dep in dependencies
            if dep["target_service_id"] == service_id
        )

        incident_count = sum(
            1 for inc in incidents
            if inc["service_id"] == service_id
        )

        propagation_count = sum(
            1 for prop in propagations
            if prop["source_service_id"] == service_id
        )

        service_incident_ids = [
            inc["incident_id"] for inc in incidents
            if inc["service_id"] == service_id
        ]

        related_impacts = [
            impact for impact in impacts
            if impact["incident_id"] in service_incident_ids
        ]

        total_loss = sum(
            impact.get("estimated_loss_usd") or 0
            for impact in related_impacts
        )

        if related_impacts:
            avg_impact = sum(
                impact.get("impact_score") or 0
                for impact in related_impacts
            ) / len(related_impacts)
        else:
            avg_impact = 0

        score = (
            business_criticality * 6
            + dependency_count * 4
            + incident_count * 3
            + propagation_count * 2
            + avg_impact * 0.4
            + min(total_loss / 10000, 20)
        )

        score = min(100, round(score, 2))

        rows.append({
            "service_id": service_id,
            "service_name": service_name,
            "dependency_count": dependency_count,
            "incident_count": incident_count,
            "propagation_count": propagation_count,
            "total_estimated_loss_usd": round(total_loss, 2),
            "avg_impact_score": round(avg_impact, 2),
            "criticality_score": score,
            "risk_level": risk_level(score),
        })

    rows = sorted(rows, key=lambda x: x["criticality_score"], reverse=True)

    if rows:
        supabase.table("service_criticality_ranking").insert(rows, returning="minimal").execute()

    print("\n===== Critical Service Ranking =====\n")

    for index, row in enumerate(rows, start=1):
        print(
            f"{index}. {row['service_name']} | "
            f"Score={row['criticality_score']} | "
            f"Risk={row['risk_level']} | "
            f"Incidents={row['incident_count']} | "
            f"Propagation={row['propagation_count']} | "
            f"Loss=${row['total_estimated_loss_usd']}"
        )

    print("\nRanking terminé.\n")


if __name__ == "__main__":
    run_critical_service_ranking()
