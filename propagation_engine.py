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
# DATA RETRIEVAL
# =========================================================

def get_open_incidents():
    response = (
        supabase.table("incidents")
        .select("*")
        .eq("status", "OPEN")
        .execute()
    )
    return response.data


def get_dependencies():
    response = (
        supabase.table("dependencies")
        .select("*")
        .execute()
    )

    print("Dependencies trouvées :", len(response.data))
    print("Exemple dependencies :", response.data[:3])

    return response.data


# =========================================================
# DUPLICATE CHECK
# =========================================================

def propagation_already_exists(incident_id):
    response = (
        supabase.table("incident_propagation")
        .select("propagation_id")
        .eq("incident_id", incident_id)
        .execute()
    )

    return len(response.data) > 0


# =========================================================
# GRAPH BUILDING
# =========================================================

def build_dependency_graph(dependencies):
    graph = {}

    for dep in dependencies:
        source = dep["target_service_id"]
        impacted = dep["source_service_id"]

        if source not in graph:
            graph[source] = []

        graph[source].append(impacted)

    return graph


def find_impacted_services(graph, source_service_id, max_depth=3):
    impacted = []
    visited = set()
    queue = [(source_service_id, 0)]

    while queue:
        current_service, level = queue.pop(0)

        if level >= max_depth:
            continue

        for next_service in graph.get(current_service, []):
            if next_service not in visited:
                visited.add(next_service)

                impacted.append({
                    "impacted_service_id": next_service,
                    "propagation_level": level + 1
                })

                queue.append((next_service, level + 1))

    return impacted


# =========================================================
# RISK SCORE
# =========================================================

def calculate_risk_score(severity, propagation_level):
    severity_base = {
        "LOW": 25,
        "MEDIUM": 50,
        "HIGH": 75,
        "CRITICAL": 95
    }

    base = severity_base.get(severity, 40)
    level_penalty = (propagation_level - 1) * 12

    return max(0, round(base - level_penalty, 2))


# =========================================================
# INSERT PROPAGATION
# =========================================================

def insert_propagation_rows(incident, impacted_services):
    rows = []

    for item in impacted_services:
        risk_score = calculate_risk_score(
            incident["severity"],
            item["propagation_level"]
        )

        rows.append({
            "incident_id": incident["incident_id"],
            "source_service_id": incident["service_id"],
            "impacted_service_id": item["impacted_service_id"],
            "propagation_level": item["propagation_level"],
            "risk_score": risk_score
        })

    if rows:
        supabase.table("incident_propagation").insert(rows, returning="minimal").execute()

    return rows


# =========================================================
# MAIN ENGINE
# =========================================================

def run_propagation_engine():
    incidents = get_open_incidents()
    dependencies = get_dependencies()

    if not incidents:
        print("Aucun incident OPEN trouvé.")
        return

    if not dependencies:
        print("Aucune dépendance trouvée.")
        return

    graph = build_dependency_graph(dependencies)

    created = 0
    skipped = 0

    for incident in incidents:
        incident_id = incident["incident_id"]
        source_service_id = incident["service_id"]

        if propagation_already_exists(incident_id):
            skipped += 1
            continue

        impacted_services = find_impacted_services(
            graph,
            source_service_id,
            max_depth=3
        )

        rows = insert_propagation_rows(incident, impacted_services)

        created += len(rows)

        print(
            f"Incident {incident_id} | "
            f"source_service={source_service_id} | "
            f"services impactés={len(rows)}"
        )

    print("\n===================================")
    print(f"Nouvelles propagations : {created}")
    print(f"Déjà existantes       : {skipped}")
    print("Propagation Engine terminé.")
    print("===================================\n")


if __name__ == "__main__":
    run_propagation_engine()
