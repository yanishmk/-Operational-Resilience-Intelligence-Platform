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
# TARGETS
# =========================================================

TARGETS = {
    "Payment API": {"sla_target": 99.95, "rto_minutes": 15, "rpo_minutes": 5},
    "Core Banking System": {"sla_target": 99.99, "rto_minutes": 10, "rpo_minutes": 2},
    "Cloud Provider": {"sla_target": 99.90, "rto_minutes": 30, "rpo_minutes": 15},
    "Login Service": {"sla_target": 99.95, "rto_minutes": 20, "rpo_minutes": 5},
    "Customer Database": {"sla_target": 99.95, "rto_minutes": 20, "rpo_minutes": 5},
    "Transaction Database": {"sla_target": 99.95, "rto_minutes": 15, "rpo_minutes": 5},
}


def get_services():
    response = supabase.table("services").select("*").execute()
    return response.data


def target_exists(service_id):
    response = (
        supabase.table("service_resilience_targets")
        .select("target_id")
        .eq("service_id", service_id)
        .execute()
    )
    return len(response.data) > 0


def insert_target(service, target):
    row = {
        "service_id": service["service_id"],
        "sla_target": target["sla_target"],
        "rto_minutes": target["rto_minutes"],
        "rpo_minutes": target["rpo_minutes"],
    }

    (
        supabase.table("service_resilience_targets")
        .insert(row, returning="minimal")
        .execute()
    )

    return row


def run_sla_rto_rpo_engine():
    services = get_services()
    created = 0
    skipped = 0

    for service in services:
        service_name = service["service_name"]

        if service_name not in TARGETS:
            continue

        if target_exists(service["service_id"]):
            skipped += 1
            continue

        target = insert_target(service, TARGETS[service_name])
        created += 1

        print(
            f"[TARGET] {service_name} | "
            f"SLA={target['sla_target']} | "
            f"RTO={target['rto_minutes']} min | "
            f"RPO={target['rpo_minutes']} min"
        )

    print("\n===================================")
    print(f"Nouveaux targets : {created}")
    print(f"Deja existants   : {skipped}")
    print("SLA/RTO/RPO Engine termine.")
    print("===================================\n")


if __name__ == "__main__":
    run_sla_rto_rpo_engine()
