import re
import requests
import pandas as pd
from bs4 import BeautifulSoup

# Regular expression to identify days
DAY_RE = re.compile(r"\b(Lundi|Mardi|Mercredi|Jeudi|Vendredi|Samedi|Dimanche)\b", re.IGNORECASE)

def clean(txt: str) -> str:
    return re.sub(r"\s+", " ", txt or "").strip()

def extract_and_save(url, output_path):
    """
    Scrapes surf data and saves it to CSV using the required format.
    """
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, timeout=30, headers=headers)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    rows = []
    day_blocks = []
    seen = set()

    # --- 1) Extract blocks by day ---
    for node in soup.find_all(string=True):
        t = clean(node)
        if DAY_RE.search(t) and 10 <= len(t) <= 40:
            date_txt = t
            if date_txt in seen:
                continue
            seen.add(date_txt)
            
            # Move up to the table container
            container = node.parent
            for _ in range(7):
                if container and container.find("div", class_="content"):
                    break
                container = container.parent if container else None
            
            if container:
                content = container.find("div", class_="content")
                if content:
                    day_blocks.append((date_txt, content))

    # --- 2) Extract hourly rows ---
    for date_txt, content in day_blocks:
        lines = content.select("div.line")
        for idx, line in enumerate(lines):
            # Skip header rows
            if line.select_one(".entetes") or "tides" in (line.get("class") or []):
                continue

            time_cell = line.select_one("div.cell.date")
            waves_cell = line.select_one("div.cell.waves")
            wind_cell = line.select_one("div.cell.large-bis-bis.with-border")

            if not (time_cell and waves_cell and wind_cell):
                continue

            # 'day hour' formatting with index
            time_val = clean(time_cell.get_text())
            day_hour_str = f"{date_txt}\n\n{time_val}\n\n{idx}"

            # 'waves_size' formatting (e.g. 0.8-1.3)
            wave_val = clean(waves_cell.get_text()).replace("m", "").replace(" ", "")

            # 'wind_speed' formatting with line breaks
            speed_span = wind_cell.select_one("div.wind span")
            speed_val = f"\n{clean(speed_span.get_text())}\n\n" if speed_span else ""

            # 'wind direction' formatting without duplication
            img = wind_cell.select_one("div.wind.img img")
            raw_dir = clean(img["alt"]) if img else ""
            # Cleanup to avoid "Orientation vent Orientation vent"
            clean_dir = raw_dir.replace("Orientation vent", "").strip()
            direction_val = f"Orientation vent {clean_dir}"

            rows.append({
                "day\n\nhour": day_hour_str,
                "waves_size": wave_val,
                "wind_speed": speed_val,
                "wind direction": direction_val
            })

    # --- 3) Save to CSV ---
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=True, encoding="utf-8")
    print(f"Extraction completed. File '{output_path}' generated with {len(df)} rows.")

import sys

def cli():
    if len(sys.argv) != 3:
        print("Usage: surf-scrap <URL> <output_file>")
        sys.exit(1)

    url = sys.argv[1]
    output_path = sys.argv[2]

    extract_and_save(url, output_path)
