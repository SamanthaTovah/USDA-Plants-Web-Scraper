import csv
import json
from collections import OrderedDict

input_csv = "names.csv"
output_json = "progress.json"

progress = OrderedDict()

# Step 1: Read symbols from CSV
with open(input_csv, newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        symbol = row["AcceptedSymbol"].strip()
        if symbol and symbol not in progress:
            progress[symbol] = {
                "done": False,
                "has_data": None  # will be True/False after scraping
            }

# Step 2: Save to JSON
with open(output_json, "w", encoding="utf-8") as jsonfile:
    json.dump(progress, jsonfile, indent=2)

print(f"Initialized progress.json with {len(progress)} symbols.")
