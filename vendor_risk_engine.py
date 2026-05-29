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


def risk_level(score):
    if score >= 85:
        return "CRITICAL"
    if score >= 65:
        return "HIGH"
    if score >= 40:
        return "MEDIUM"
    return "LOW"


# =========================================================
# SCORING
# =========================================================

def calculate_vendor_scores():
    vendors = get_table("vendors")
    vendor_dependencies = get_table("vendor_dependencies")
    services = get_table("services")
    ranking = get_table("service_criticality_ranking")

    service_by_id = {service["service_id"]: service for service in services}
    ranking_by_service_id = {
        row["service_id"]: row
        for row in ranking
    }

    rows = []

    for vendor in vendors:
        dependencies = [
            dep for dep in vendor_dependencies
            if dep["vendor_id"] == vendor["vendor_id"]
        ]

        service_count = len(dependencies)
        critical_services = 0
        criticality_total = 0

        for dependency in dependencies:
            service_id = dependency["service_id"]
            service = service_by_id.get(service_id, {})
            service_criticality = service.get("business_criticality") or 5
            ranking_score = ranking_by_service_id.get(service_id, {}).get("criticality_score") or 0

            criticality_total += service_criticality * 7 + ranking_score * 0.3

            if service_criticality >= 8 or ranking_score >= 85:
                critical_services += 1

        score = min(
            100,
            round(service_count * 12 + critical_services * 15 + criticality_total / 4, 2)
        )

        rows.append({
            "vendor": vendor,
            "service_count": service_count,
            "critical_services": critical_services,
            "score": score,
            "risk_level": risk_level(score),
        })

    return rows


def update_vendor(vendor_id, score, level):
    (
        supabase.table("vendors")
        .update({"criticality_score": score, "risk_level": level})
        .eq("vendor_id", vendor_id)
        .execute()
    )


def run_vendor_risk_engine():
    scores = calculate_vendor_scores()

    for item in scores:
        vendor = item["vendor"]
        update_vendor(vendor["vendor_id"], item["score"], item["risk_level"])

        print(
            f"[VENDOR] {vendor['vendor_name']} | "
            f"type={vendor['vendor_type']} | "
            f"services={item['service_count']} | "
            f"critical_services={item['critical_services']} | "
            f"score={item['score']} | "
            f"risk={item['risk_level']}"
        )

    print("\n===================================")
    print(f"Vendors analyses : {len(scores)}")
    print("Vendor Risk Engine termine.")
    print("===================================\n")


if __name__ == "__main__":
    run_vendor_risk_engine()
