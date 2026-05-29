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
# SCENARIOS
# =========================================================

SCENARIOS = [
    "Cloud Provider failure",
    "Payment API failure",
    "Core Banking failure",
    "Customer Database failure",
    "Transaction Database failure",
]

SERVICE_NAME_BY_SCENARIO = {
    "Cloud Provider failure": "Cloud Provider",
    "Payment API failure": "Payment API",
    "Core Banking failure": "Core Banking System",
    "Customer Database failure": "Customer Database",
    "Transaction Database failure": "Transaction Database",
}

BASE_CUSTOMERS = {
    "Payment API": 40000,
    "Core Banking System": 50000,
    "Cloud Provider": 60000,
    "Customer Database": 30000,
    "Transaction Database": 35000,
}


# =========================================================
# DATA
# =========================================================

def get_table(table_name):
    response = supabase.table(table_name).select("*").execute()
    return response.data


def build_dependency_graph(dependencies):
    graph = {}

    for dep in dependencies:
        source = dep["target_service_id"]
        impacted = dep["source_service_id"]
        graph.setdefault(source, []).append(impacted)

    return graph


def find_impacted_services(graph, source_service_id, max_depth=4):
    impacted = set()
    queue = [(source_service_id, 0)]

    while queue:
        current_service, level = queue.pop(0)

        if level >= max_depth:
            continue

        for next_service in graph.get(current_service, []):
            if next_service not in impacted:
                impacted.add(next_service)
                queue.append((next_service, level + 1))

    return impacted


# =========================================================
# SIMULATION
# =========================================================

def calculate_scenario(scenario_name, service, impacted_services):
    service_name = service["service_name"]
    impacted_count = len(impacted_services)
    estimated_affected_customers = BASE_CUSTOMERS.get(service_name, 20000)
    estimated_affected_customers += impacted_count * 7000

    estimated_lost_transactions = int(estimated_affected_customers * 0.35)
    average_transaction_value = 85 if service_name == "Payment API" else 65
    estimated_loss_usd = round(estimated_lost_transactions * average_transaction_value, 2)

    risk_score = min(
        100,
        round(
            impacted_count * 8
            + estimated_affected_customers / 1200
            + estimated_loss_usd / 100000,
            2,
        ),
    )

    return {
        "scenario_name": scenario_name,
        "source_service_id": service["service_id"],
        "impacted_services_count": impacted_count,
        "estimated_affected_customers": estimated_affected_customers,
        "estimated_lost_transactions": estimated_lost_transactions,
        "estimated_loss_usd": estimated_loss_usd,
        "risk_score": risk_score,
    }


def insert_simulation(row):
    (
        supabase.table("scenario_simulations")
        .insert(row, returning="minimal")
        .execute()
    )


def run_scenario_simulation_engine():
    services = get_table("services")
    dependencies = get_table("dependencies")
    service_by_name = {service["service_name"]: service for service in services}
    graph = build_dependency_graph(dependencies)

    created = 0

    for scenario_name in SCENARIOS:
        service_name = SERVICE_NAME_BY_SCENARIO[scenario_name]
        service = service_by_name.get(service_name)

        if not service:
            print(f"[SKIPPED] {scenario_name} | source service not found")
            continue

        impacted_services = find_impacted_services(graph, service["service_id"])
        row = calculate_scenario(scenario_name, service, impacted_services)
        insert_simulation(row)
        created += 1

        print(
            f"[SCENARIO] {scenario_name} | "
            f"impacted={row['impacted_services_count']} | "
            f"customers={row['estimated_affected_customers']} | "
            f"loss=${row['estimated_loss_usd']} | "
            f"risk={row['risk_score']}"
        )

    print("\n===================================")
    print(f"Scenarios simules : {created}")
    print("Scenario Simulation Engine termine.")
    print("===================================\n")


if __name__ == "__main__":
    run_scenario_simulation_engine()
