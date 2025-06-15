# 🌿 USDA-Plants-Web-Scraper

A web scraper for the [USDA PLANTS Database](https://plants.usda.gov/), focused on extracting detailed characteristics data for all listed species (excluding cultivars).

## 📁 Project Structure

```
overgrazed-scraper/
├── json/
│   ├── A/
│   ├── B/
│   └── ...      # JSON output organized by the first letter of the USDA symbol
├── initialize_progress.py  # Initializes progress.json using names.csv
├── names.csv               # Raw plant list from USDA Characteristics Search
├── progress.json           # Tracks scraping progress/status
├── README.md               # This file
└── scrape.py               # Main scraper script
```

## 🧪 Data Source

- The `names.csv` file should be downloaded from the [USDA Characteristics Search](https://plants.usda.gov/characteristics-search) with **no filters applied**. It contains the full list of plants in the database.

## 📦 Included Data

This repository includes both the scraped data (`json/`) and the raw plant list (`names.csv`) for convenience and transparency.

However, these files are not required to use the project. If preferred, you can generate all data yourself by downloading a fresh `names.csv` from the USDA Characteristics Search and running the provided scripts. The process is fully reproducible.

## ⚙️ Scripts

### `initialize_progress.py`

- Reads `names.csv`
- Creates `progress.json` to track scraping state

### `scrape.py`

- Scrapes plant data from the **main plant page** and its **characteristics page**
- Stores data as `json/<first-letter-of-USDA-symbol>/<USDA-symbol>.json`
- Uses `progress.json` to resume or continue scraping
- **Skips**:
  - Cultivars (entirely ignored)
  - Species with no characteristics data

## ✅ Output Example

Each JSON file contains structured information for one plant, stored in a subdirectory based on the first letter of its USDA symbol.

```
json/
└── E/
    └── EABR.json
```

## ❌ Exclusions

- Cultivars are **never** stored  
- Species without characteristics data are skipped

These cases were excluded by design, as they were not relevant to the intended use. The scraper can be easily modified to include them if needed.

## 🚀 Usage

1. Download `names.csv` from the USDA site using the Characteristics Search with no filters.
2. Run `initialize_progress.py` to generate `progress.json`:
   ```bash
   python initialize_progress.py
   ```
3. Run the scraper:
   ```bash
   python scrape.py
   ```

## 🔁 Resumability

- Scraping is tracked via `progress.json`. If interrupted, rerunning `scrape.py` will resume where it left off.

## 📄 Data Source and Licensing

This project uses public domain data from the [USDA PLANTS Database](https://plants.usda.gov/). The USDA is a United States federal agency, and as such, the data it produces is not subject to copyright under 17 U.S.C. § 105.

No copyright is claimed on the original source material.

If you use this project or redistribute its contents, it is good practice to acknowledge the USDA as the original data provider.
