import requests
import os
import time
import sys
import json

# --- CONFIGURATION ---
SEARCH_API_URL = "https://www.willhaben.at/webapi/iad/search/atz/seo/kaufen-und-verkaufen/marktplatz/a/farbe-schwarz-3201"
DETAIL_API_URL = "https://www.willhaben.at/webapi/iad/atdetail/"

HEADERS = {
    "accept": "application/json",
    "x-wh-client": "api@willhaben.at;responsive_web;server;1.0.0;phone",
    "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Mobile"
}

# Your strictly defined search criteria
KEYWORDS = ["150"]

TELEGRAM_TOKEN = os.getenv("TG_TOKEN")
CHAT_ID = os.getenv("TG_CHAT_ID")

def log(msg):
    """Force-flushed logging for GitHub Action visibility."""
    print(f">>> {msg}", flush=True)

def send_telegram(message):
    """Sends a notification to Telegram."""
    log("Sending Telegram notification...")
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        res = requests.post(url, json=payload, timeout=10)
        log(f"Telegram status: {res.status_code}")
    except Exception as e:
        log(f"Telegram failed: {e}")

def get_full_description(ad_id):
    """Fetches the detail JSON and scrapes all possible text fields."""
    try:
        url = f"{DETAIL_API_URL}{ad_id}"
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            log("DEBUG DATA FOR {ad_id}:")
            log(json.dumps(data, indent=2))
            # Start with standard description/heading fields
            all_text = [
                str(data.get("description", "")),
                str(data.get("heading", ""))
            ]
            
            # Extract all attribute values (where Willhaben hides dimensions)
            attrs = data.get("attributes", {}).get("attribute", [])
            for a in attrs:
                # Common names: BODY_DYN (description), HEADING (title)
                all_text.extend([str(v) for v in a.get("values", [])])
            
            combined_text = " ".join(all_text).lower()
            log(f"ID {ad_id}: Successfully scanned {len(combined_text)} characters.")
            return combined_text
    except Exception as e:
        log(f"Detail fetch error for {ad_id}: {e}")
    return ""

def main():
    log("Initializing Deep Search (4 Pages, 90 items/page)...")
    
    if not TELEGRAM_TOKEN or not CHAT_ID:
        log("CRITICAL: Secrets missing. Check TG_TOKEN and TG_CHAT_ID.")
        return

    # 1. Load seen IDs from history
    seen_ids = set()
    if os.path.exists("seen_ids.txt"):
        with open("seen_ids.txt", "r") as f:
            seen_ids = set(f.read().splitlines())
    log(f"Current items in memory: {len(seen_ids)}")

    new_matches = 0
    new_ids_discovered = []

    # 2. Iterate through 4 pages
    for page_num in range(1, 5):
        log(f"Fetching Page {page_num}...")
        params = {
            "areaId": "900",
            "keyword": "tv bank",
            "rows": "90",
            "page": str(page_num),
            "isNavigation": "true"
        }

        try:
            response = requests.get(SEARCH_API_URL, params=params, headers=HEADERS, timeout=15)
            if response.status_code != 200:
                log(f"Page {page_num} failed with status {response.status_code}")
                break

            data = response.json()
            ads = data.get("advertSummaryList", {}).get("advertSummary", [])
            
            for ad in ads:
                ad_id = str(ad.get("id"))
                
                if ad_id not in seen_ids:
                    # Check the full description for "150"
                    full_text = get_full_description(ad_id)
                    
                    if any(k in full_text for k in KEYWORDS):
                        # Extract SEO URL for the link
                        seo_url = ""
                        for attr in ad.get("attributes", {}).get("attribute", []):
                            if attr.get("name") == "SEO_URL":
                                seo_url = attr.get("values", [""])[0]
                        
                        link = f"https://www.willhaben.at/iad/{seo_url}"
                        send_telegram(f"📺 *Found '150' match!*\nID: {ad_id}\n[Open Item]({link})")
                        new_matches += 1
                    
                    new_ids_discovered.append(ad_id)
                    time.sleep(0.5) # Gentle rate limiting

        except Exception as e:
            log(f"Fatal error on Page {page_num}: {e}")

    # 3. Update the tracking file
    if new_ids_discovered:
        with open("seen_ids.txt", "a") as f:
            for nid in new_ids_discovered:
                f.write(nid + "\n")
        log(f"Saved {len(new_ids_discovered)} new IDs to seen_ids.txt")
    
    log(f"Process complete. Notifications sent: {new_matches}")

if __name__ == "__main__":
    main()
