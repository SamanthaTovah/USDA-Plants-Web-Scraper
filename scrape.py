import os
import sys
import json
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

def scrape_characteristics(symbol):
    url = f"https://plants.usda.gov/plant-profile/{symbol}/characteristics"
    print(f"🌿 Scraping characteristics: {symbol} → {url}")
    driver.get(url)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#characteristics table"))
        )
    except:
        print(f"❌ Timed out waiting for tables on {symbol}")
        driver.quit()
        sys.exit(1)

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
                if len(cells) != 2:
                    continue
                key = cells[0].get_text(strip=True)
                value = cells[1].get_text(strip=True)
                traits[key] = value

    return traits

def scrape_general_info(symbol):
    url = f"https://plants.usda.gov/plant-profile/{symbol}"
    print(f"🔁 Scraping general info: {symbol} → {url}")
    driver.get(url)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table"))
        )
    except:
        print(f"❌ Timed out waiting for general info tables on {symbol}")
        driver.quit()
        sys.exit(1)

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

    return common_name, general_info, classification

# === Scrape loop ===
for symbol, info in progress.items():
    if info.get("done"):
        continue

    start_time = datetime.now()
    print(f"\n🌱 Scraping: {symbol}")

    traits = scrape_characteristics(symbol)

    if not traits:
        print(f"⚠️ Symbol {symbol} is a cultivar-only entry. Skipping JSON save.")
        progress[symbol]["done"] = True
        progress[symbol]["has_data"] = False
        save_progress()
        continue

    common_name, general_info, classification = scrape_general_info(symbol)

    # Save JSON
    letter = symbol[0].upper()
    folder = os.path.join(OUTPUT_DIR, letter)
    os.makedirs(folder, exist_ok=True)
    json_path = os.path.join(folder, f"{symbol}.json")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "symbol": symbol,
            "common_name": common_name,
            "traits": traits,
            "general_information": general_info,
            "classification": classification
        }, f, indent=2)

    progress[symbol]["done"] = True
    progress[symbol]["has_data"] = True
    save_progress()

    # ETA output
    done = sum(1 for p in progress.values() if p.get("done"))
    total = len(progress)
    percent = round((done / total) * 100, 1)
    print(f"📊 Progress: {done}/{total} plants scraped ({percent}%)")

    SCRAPE_TIMES.append((datetime.now() - start_time).total_seconds())
    avg_time = sum(SCRAPE_TIMES) / len(SCRAPE_TIMES)
    eta_sec = int(avg_time * (total - done))
    eta_hr, rem = divmod(eta_sec, 3600)
    eta_min, eta_sec = divmod(rem, 60)
    print(f"⏳ ETA: {eta_hr}h {eta_min}m {eta_sec}s remaining")
    print(f"🌱 Scraped: {common_name}!")

driver.quit()
print("✅ All scraping complete!")
