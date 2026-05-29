import csv
from supabase import create_client
from dotenv import load_dotenv
import os

# Charger variables environnement
load_dotenv(override=True)

for proxy_var in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"):
    os.environ.pop(proxy_var, None)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Connexion Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Charger CSV
with open("service_metrics_generated.csv", newline="", encoding="utf-8") as file:
    records = list(csv.DictReader(file))

# Insertion par batch
BATCH_SIZE = 500

for i in range(0, len(records), BATCH_SIZE):
    batch = records[i:i+BATCH_SIZE]

    response = supabase.table("service_metrics").insert(batch, returning="minimal").execute()

    print(f"Batch {i // BATCH_SIZE + 1} inséré.")

print("Upload terminé.")
