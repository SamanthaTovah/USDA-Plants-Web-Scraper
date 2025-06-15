import os
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
from collections import deque
from datetime import datetime

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

def save_plant_data(symbol, traits, scientific_name=None, common_name=None):
    letter = symbol[0].upper()
    folder = os.path.join(OUTPUT_DIR, letter)
    os.makedirs(folder, exist_ok=True)
    out_path = os.path.join(folder, f"{symbol}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "symbol": symbol,
            "scientific_name": scientific_name,
            "common_name": common_name,
            "traits": traits
        }, f, indent=2)

# === Scrape each plant ===
for symbol, info in progress.items():
    if info.get("done"):
        continue

    start_time = datetime.now()

    url = f"https://plants.usda.gov/plant-profile/{symbol}/characteristics"
    print(f"\n🌱 Scraping: {symbol} → {url}")
    driver.get(url)
    time.sleep(1.5)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    wrapper = soup.select_one("div#characteristics")

    traits = {}

    if wrapper:
        tables = wrapper.find_all("table")
        tables = [
            t for t in tables
            if not t.find("caption") or "cultivar" not in t.find("caption").get_text(strip=True).lower()
        ]
        for table in tables:
            for row in table.find_all("tr"):
                cells = row.find_all("td")
                if len(cells) == 2:
                    key = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    traits[key] = value

    if traits:
        print(f"✅ Found {len(traits)} traits for {symbol}")
        save_plant_data(symbol, traits)
        progress[symbol]["has_data"] = True
    else:
        print(f"⚠️ No data found for {symbol}")
        progress[symbol]["has_data"] = False

    progress[symbol]["done"] = True

    # Show progress bar
    total = len(progress)
    done = sum(1 for p in progress.values() if p.get("done"))
    percent = round((done / total) * 100, 1)
    print(f"📊 Progress: {done}/{total} plants scraped ({percent}%)")

    save_progress()

    # === Track time and estimate ETA
    SCRAPE_TIMES.append((datetime.now() - start_time).total_seconds())
    avg_time = sum(SCRAPE_TIMES) / len(SCRAPE_TIMES) if SCRAPE_TIMES else 0
    remaining = total - done
    eta_sec = int(avg_time * remaining)

    eta_hr, rem = divmod(eta_sec, 3600)
    eta_min, eta_sec = divmod(rem, 60)

    print(f"⏳ ETA: {eta_hr}h {eta_min}m {eta_sec}s remaining")

driver.quit()
print("✅ All done!")
