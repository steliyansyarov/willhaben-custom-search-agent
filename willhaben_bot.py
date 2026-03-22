import sys
import os

# --- 1. GLOBAL TEST ---
print(">>> SCRIPT LOADED SUCCESSFULLY", flush=True)

try:
    import requests
    import time
    import random
    print(">>> LIBRARIES IMPORTED", flush=True)
except Exception as e:
    print(f">>> IMPORT ERROR: {e}", flush=True)
    sys.exit(1)

# --- CONFIGURATION ---
SEARCH_API_URL = "https://www.willhaben.at/webapi/iad/search/atz/seo/kaufen-und-verkaufen/marktplatz/a/farbe-schwarz-3201"
DETAIL_API_URL = "https://www.willhaben.at/webapi/iad/atdetail/"

HEADERS = {
    "accept": "application/json",
    "x-wh-client": "api@willhaben.at;responsive_web;server;1.0.0;phone",
    "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Mobile"
}

KEYWORDS = ["160x", "160 cm", "breite 160"]
TELEGRAM_TOKEN = os.getenv("TG_TOKEN")
CHAT_ID = os.getenv("TG_CHAT_ID")

def send_telegram(message):
    print(f">>> Attempting to send Telegram message...", flush=True)
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    res = requests.post(url, json=payload, timeout=10)
    print(f">>> Telegram Response: {res.status_code} - {res.text[:50]}", flush=True)

def main():
    print(">>> ENTERING MAIN FUNCTION", flush=True)
    
    # 1. Secret Check (Don't print the actual token!)
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print(">>> ERROR: Telegram Secrets are missing!", flush=True)
        return

    # 2. Fetch Search
    print(f">>> Fetching search results from Willhaben...", flush=True)
    params = {"areaId": "900", "keyword": "tv bank", "rows": "30", "isNavigation": "true"}
    
    response = requests.get(SEARCH_API_URL, params=params, headers=HEADERS, timeout=15)
    print(f">>> Search API Status: {response.status_code}", flush=True)
    
    if response.status_code != 200:
        return

    data = response.json()
    ads = data.get("advertSummaryList", {}).get("advertSummary", [])
    print(f">>> Found {len(ads)} total ads in search.", flush=True)

    # 3. Seen IDs Logic
    seen_ids = set()
    if os.path.exists("seen_ids.txt"):
        with open("seen_ids.txt", "r") as f:
            seen_ids = set(f.read().splitlines())
    print(f">>> Known IDs in memory: {len(seen_ids)}", flush=True)

    # 4. Processing
    new_count = 0
    for ad in ads:
        ad_id = str(ad.get("id"))
        if ad_id not in seen_ids:
            print(f">>> New item discovered: {ad_id}. Checking details...", flush=True)
            # (Your detail-checking logic goes here)
            # For now, let's just mark it as seen
            with open("seen_ids.txt", "a") as f:
                f.write(ad_id + "\n")
            new_count += 1
    
    print(f">>> Script finished. Discovered {new_count} new items.", flush=True)

if _name_ == "_main_":
    try:
        main()
    except Exception as e:
        print(f">>> CRITICAL RUNTIME ERROR: {e}", flush=True)
        import traceback
        traceback.print_exc()