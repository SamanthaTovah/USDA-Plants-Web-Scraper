import os
import json
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from datetime import datetime
from collections import deque

# === CONFIG ===
CHROMEDRIVER_PATH = "E:/ChromeDriver/chromedriver-win64/chromedriver.exe"
PROGRESS_FILE = "progress.json"
OUTPUT_DIR = "json"

# === Setup Selenium ===
options = Options()
options.add_argument("--headless")
service = Service(CHROMEDRIVER_PATH)
driver = webdriver.Chrome(service=service, options=options)

SCRAPE_TIMES = deque(maxlen=100)

# === Load progress.json ===
with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
    progress = json.load(f)

def save_progress():
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, indent=2)

# === Scrape loop ===
for symbol, info in progress.items():
    if not (info.get("done") and info.get("has_data")):
        continue

    if info.get("done_secondary"):
        continue

    url = f"https://plants.usda.gov/plant-profile/{symbol}"
    print(f"\n🔁 Scraping secondary data: {symbol} → {url}")
    start_time = datetime.now()


    driver.get(url)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table"))
        )
    except:
        print(f"❌ Timed out waiting for tables on {symbol}")
        continue

    soup = BeautifulSoup(driver.page_source, "html.parser")
    tables = soup.find_all("table")

    general_info = {}
    classification = {}
    common_name = None

    for table in tables:
        caption = table.find("caption")
        caption_text = caption.get_text(strip=True) if caption else ""
        rows = table.find_all("tr")
        for row in rows:
            th = row.find_all("th")
            td = row.find_all("td")

            if len(th) < 1 or len(td) < 1:
                continue
            key = th[0].get_text(strip=True)
            value = td[0].get_text(strip=True)

            if "general information" in caption_text.lower():
                if key in ("Symbol", "Native Status", "Plant Guide"):
                    continue
                general_info[key] = value

            elif "classification" in caption_text.lower():
                classification[key] = value

        if "general information" in caption_text.lower():
            caption_parts = caption.contents
            if caption_parts and isinstance(caption_parts[0], str):
                common_name = caption_parts[0].strip(' "\n')

    # === Check if all critical data exists ===
    if not common_name:
        print(f"❌ ERROR: No common name found for {symbol}. Halting.")
        driver.quit()
        sys.exit(1)

    if not general_info:
        print(f"❌ ERROR: No general info found for {symbol}. Halting.")
        driver.quit()
        sys.exit(1)

    if not classification:
        print(f"❌ ERROR: No classification found for {symbol}. Halting.")
        driver.quit()
        sys.exit(1)

    # === Load and update existing JSON
    json_path = os.path.join(OUTPUT_DIR, symbol[0].upper(), f"{symbol}.json")
    if not os.path.exists(json_path):
        print(f"❌ JSON file for {symbol} not found, skipping")
        continue

    with open(json_path, "r", encoding="utf-8") as f:
        plant_data = json.load(f)

    if "common_name" in plant_data and plant_data["common_name"]:
        print(f"⚠️ Symbol {symbol} already has a common_name, skipping update")
        continue

    # === Save updated plant data
    plant_data["common_name"] = common_name
    plant_data["general_information"] = general_info
    plant_data["classification"] = classification
    plant_data.pop("scientific_name", None)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(plant_data, f, indent=2)

    progress[symbol]["has_data_secondary"] = True
    progress[symbol]["done_secondary"] = True
    save_progress()

    # === Show progress and ETA
    done = sum(1 for p in progress.values() if p.get("done_secondary"))
    total = sum(1 for p in progress.values() if p.get("done") and p.get("has_data"))
    percent = round((done / total) * 100, 1)
    print(f"📊 Secondary progress: {done}/{total} ({percent}%)")

    SCRAPE_TIMES.append((datetime.now() - start_time).total_seconds())
    avg_time = sum(SCRAPE_TIMES) / len(SCRAPE_TIMES)
    eta_sec = int(avg_time * (total - done))
    eta_hr, rem = divmod(eta_sec, 3600)
    eta_min, eta_sec = divmod(rem, 60)
    print(f"⏳ ETA: {eta_hr}h {eta_min}m {eta_sec}s remaining")
    print(f"🌱 Fully scraped {common_name}!")

driver.quit()
print("✅ Secondary scrape complete!")
