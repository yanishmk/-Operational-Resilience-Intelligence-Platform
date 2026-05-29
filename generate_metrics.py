import random
import csv
from datetime import datetime, timedelta

SERVICES = [
    {"service_id": 1, "name": "Mobile Banking App"},
    {"service_id": 2, "name": "Web Banking Portal"},
    {"service_id": 3, "name": "Login Service"},
    {"service_id": 4, "name": "Customer Database"},
    {"service_id": 5, "name": "Payment API"},
    {"service_id": 6, "name": "Fraud Detection API"},
    {"service_id": 7, "name": "Core Banking System"},
    {"service_id": 8, "name": "Transaction Database"},
    {"service_id": 9, "name": "Notification Service"},
    {"service_id": 10, "name": "ATM Network"},
    {"service_id": 11, "name": "Cloud Provider"},
    {"service_id": 12, "name": "Monitoring System"},
]

def normal_metrics(service_id, timestamp):
    latency = random.randint(50, 250)
    error_rate = round(random.uniform(0.1, 1.5), 2)
    uptime = round(random.uniform(99.5, 99.99), 2)
    volume = random.randint(3000, 20000)
    failed = int(volume * error_rate / 100)

    return {
        "service_id": service_id,
        "timestamp": timestamp,
        "latency_ms": latency,
        "error_rate": error_rate,
        "uptime_percentage": uptime,
        "transaction_volume": volume,
        "failed_transactions": failed,
        "cpu_usage": round(random.uniform(25, 65), 2),
        "memory_usage": round(random.uniform(30, 70), 2),
    }

def incident_metrics(service_id, timestamp):
    latency = random.randint(700, 2500)
    error_rate = round(random.uniform(8, 35), 2)
    uptime = round(random.uniform(90, 97), 2)
    volume = random.randint(8000, 30000)
    failed = int(volume * error_rate / 100)

    return {
        "service_id": service_id,
        "timestamp": timestamp,
        "latency_ms": latency,
        "error_rate": error_rate,
        "uptime_percentage": uptime,
        "transaction_volume": volume,
        "failed_transactions": failed,
        "cpu_usage": round(random.uniform(75, 98), 2),
        "memory_usage": round(random.uniform(78, 99), 2),
    }

def generate_data(hours=24):
    rows = []
    start_time = datetime.now() - timedelta(hours=hours)

    incident_services = [5, 7, 11]  # Payment API, Core Banking, Cloud Provider

    for minute in range(hours * 60):
        timestamp = start_time + timedelta(minutes=minute)

        for service in SERVICES:
            service_id = service["service_id"]

            # 3% chance of incident on critical services
            if service_id in incident_services and random.random() < 0.03:
                rows.append(incident_metrics(service_id, timestamp))
            else:
                rows.append(normal_metrics(service_id, timestamp))

    return rows

if __name__ == "__main__":
    rows = generate_data(hours=48)

    with open("service_metrics_generated.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print("Metrics generated successfully.")
    for row in rows[:5]:
        print(row)
    print(f"Total rows: {len(rows)}")
