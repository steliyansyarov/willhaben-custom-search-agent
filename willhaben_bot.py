import requests
import os
import time
import sys
import json
import math

# --- CONFIGURATION ---
# The exact Search API URL found in your browser network tab
SEARCH_API_URL = "https://www.willhaben.at/webapi/iad/search/atz/seo/kaufen-und-verkaufen/marktplatz/a/farbe-schwarz-3201"
# API for specific item details
DETAIL_API_URL = "https://www.willhaben.at/webapi/iad/atdetail/"

HEADERS = {
    "accept": "application/json",
    "x-wh-client": "api@willhaben.at;responsive_web;server;1.0.0;phone",
    "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Mobile"
}

# The keyword you are testing for
KEYWORDS = ["150"] 
ROWS_PER_PAGE = 90

# Secrets from GitHub Actions
TELEGRAM_TOKEN = os.getenv("TG_TOKEN")
CHAT_ID = os.getenv("TG_CHAT_ID")

def log(msg):
    """Force-flushed logging to ensure visibility in GitHub Action logs."""
    print(f">>> {msg}", flush=True)

def get_full_description_greedy(ad_id):
    """
    Fetches the detail JSON and performs a greedy string match on the raw text.
    This accounts for BODY_DYN and any other hidden attributes.
    """
    try:
        url = f"{DETAIL_API_URL}{ad_id}"
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            # Greedy Scan: Check the entire raw JSON string for the keyword
            raw_content = response.text.lower()
            if any(k in raw_content for k in KEYWORDS):
                return True
    except Exception as e:
        log(f"Detail fetch error for {ad_id}: {e}")
    return False

def main():
    log("Initializing Dynamic Deep Search...")
    
    if not TELEGRAM_TOKEN or not CHAT_ID:
        log("CRITICAL: Telegram secrets are missing!")
        return

    # 1. Load seen IDs from history
    seen_ids = set()
    if os.path.exists("seen_ids.txt"):
        with open("seen_ids.txt", "r") as f:
            seen_ids = set(f.read().splitlines())
    log(f"Current items in memory: {len(seen_ids)}")

    current_page = 1
    total_pages = 1 # Will be updated dynamically
    new_matches = 0
    new_ids_discovered = []

    # 2. Dynamic Pagination Loop
    while current_page <= total_pages:
        log(f"Processing Page {current_page} of {total_pages}...")
        
        params = {
            "areaId": "900",
            "keyword": "tv bank",
            "rows": str(ROWS_PER_PAGE),
            "page": str(current_page),
            "isNavigation": "true"
        }

        try:
            response = requests.get(SEARCH_API_URL, params=params, headers=HEADERS, timeout=15)
            if response.status_code != 200:
                log(f"Page {current_page} failed: {response.status_code}")
                break

            data = response.json()

            # Dynamic Page Calculation
            if current_page == 1:
                rows_found = data.get("rowsFound", 0)
                total_pages = math.ceil(rows_found / ROWS_PER_PAGE)
                # Safety cap: don't scrape more than 10 pages per run
                total_pages = min(total_pages, 10) 
                log(f"Total results: {rows_found}. Calculated {total_pages} pages.")

            ads = data.get("advertSummaryList", {}).get("advertSummary", [])
            for ad in ads:
                ad_id = str(ad.get("id"))
                
                if ad_id not in seen_ids:
                    # Deep check for "150" in raw JSON
                    if get_full_description_greedy(ad_id):
                        # Extract SEO URL for the Telegram link
                        seo_url = ""
                        for attr in ad.get("attributes", {}).get("attribute", []):
                            if attr.get("name") == "SEO_URL":
                                seo_url = attr.get("values", [""])[0]
                        
                        link = f"https://www.willhaben.at/iad/{seo_url}"
                        
                        # Send Telegram Notification
                        tg_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
                        requests.post(tg_url, json={
                            "chat_id": CHAT_ID, 
                            "text": f"🎯 *Match Found (150)*\nID: {ad_id}\n[View Item]({link})",
                            "parse_mode": "Markdown"
                        })
                        new_matches += 1
                        log(f"MATCH FOUND: {ad_id}")
                    
                    new_ids_discovered.append(ad_id)
                    time.sleep(0.5) # Throttling for safety

            current_page += 1

        except Exception as e:
            log(f"Error on page {current_page}: {e}")
            break

    # 3. Update seen_ids.txt
    if new_ids_discovered:
        with open("seen_ids.txt", "a") as f:
            for nid in new_ids_discovered:
                f.write(nid + "\n")
        log(f"Saved {len(new_ids_discovered)} new IDs.")

    log(f"Scan complete. Notifications sent: {new_matches}")

if __name__ == "__main__":
    main()
