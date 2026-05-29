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


def concentration_level(percentage):
    if percentage >= 60:
        return "CRITICAL"
    if percentage >= 40:
        return "HIGH"
    if percentage >= 25:
        return "MEDIUM"
    return "LOW"


def run_cloud_concentration_risk_engine():
    services = get_table("services")
    vendors = get_table("vendors")
    dependencies = get_table("vendor_dependencies")

    cloud_vendors = [
        vendor for vendor in vendors
        if vendor["vendor_type"] == "CLOUD"
    ]

    total_services = len(services) or 1
    highest_percentage = 0
    highest_vendor = None

    for vendor in cloud_vendors:
        dependent_services = {
            dep["service_id"] for dep in dependencies
            if dep["vendor_id"] == vendor["vendor_id"]
        }

        percentage = round((len(dependent_services) / total_services) * 100, 2)
        level = concentration_level(percentage)

        if percentage > highest_percentage:
            highest_percentage = percentage
            highest_vendor = vendor["vendor_name"]

        print(
            f"[CLOUD] {vendor['vendor_name']} | "
            f"dependent_services={len(dependent_services)} | "
            f"concentration={percentage}% | "
            f"risk={level}"
        )

    overall_level = concentration_level(highest_percentage)

    print("\n===================================")
    print(f"Highest cloud vendor : {highest_vendor}")
    print(f"Highest concentration: {highest_percentage}%")
    print(f"Overall risk level   : {overall_level}")
    print("Cloud Concentration Risk Engine termine.")
    print("===================================\n")


if __name__ == "__main__":
    run_cloud_concentration_risk_engine()
