import os
import json
import csv
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup

# === CONFIG ===
CHROMEDRIVER_PATH = "E:/ChromeDriver/chromedriver-win64/chromedriver.exe"
PROGRESS_FILE = "progress.json"
OUTPUT_DIR = "json"

# === Setup Selenium ===
options = Options()
options.add_argument("--headless")
service = Service(CHROMEDRIVER_PATH)
driver = webdriver.Chrome(service=service, options=options)

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

    url = f"https://plants.usda.gov/plant-profile/{symbol}/characteristics"
    print(f"\n🌱 Scraping: {symbol} → {url}")
    driver.get(url)
    time.sleep(1.5)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    wrapper = soup.select_one("div#characteristics")

    if not wrapper:
        print("❌ No characteristics container found")
        progress[symbol]["done"] = True
        progress[symbol]["has_data"] = False
        save_progress()
        continue

    tables = wrapper.find_all("table")

    # Filter out cultivar tables
    tables = [
        t for t in tables
        if not t.find("caption") or "cultivar" not in t.find("caption").get_text(strip=True).lower()
    ]

    traits = {}
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
        progress[symbol]["done"] = True
        progress[symbol]["has_data"] = True
    else:
        print(f"⚠️ No data found for {symbol}")
        progress[symbol]["done"] = True
        progress[symbol]["has_data"] = False

    save_progress()
    time.sleep(0.2)

driver.quit()
print("✅ All done!")
