import requests
import os
import time
import sys

# --- CONFIGURATION ---
SEARCH_API_URL = "https://www.willhaben.at/webapi/iad/search/atz/seo/kaufen-und-verkaufen/marktplatz/a/farbe-schwarz-3201"
DETAIL_API_URL = "https://www.willhaben.at/webapi/iad/atdetail/"

HEADERS = {
    "accept": "application/json",
    "x-wh-client": "api@willhaben.at;responsive_web;server;1.0.0;phone",
    "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Mobile"
}

KEYWORDS = ["150"]
TELEGRAM_TOKEN = os.getenv("TG_TOKEN")
CHAT_ID = os.getenv("TG_CHAT_ID")

def log(msg):
    print(f">>> {msg}", flush=True)

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        log(f"Telegram failed: {e}")

def get_full_description(ad_id):
    try:
        url = f"{DETAIL_API_URL}{ad_id}"
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            all_text = [data.get("description", "")]
            attrs = data.get("attributes", {}).get("attribute", [])
            for a in attrs:
                if a.get("name") in ["BODY_DYN", "HEADING"]:
                    all_text.extend(a.get("values", []))
            return " ".join(all_text).lower()
    except:
        pass
    return ""

def main():
    log("Starting Deep Search (90 items per page)...")
    
    seen_ids = set()
    if os.path.exists("seen_ids.txt"):
        with open("seen_ids.txt", "r") as f:
            seen_ids = set(f.read().splitlines())

    new_matches = 0
    new_ids_discovered = []

    # Check first 2 pages with 90 items each = 180 total items
    for page_num in range(1, 3):
        log(f"Fetching Page {page_num}...")
        params = {
            "areaId": "900",
            "keyword": "tv bank",
            "rows": "90",  # Maximize items per request
            "page": str(page_num),
            "isNavigation": "true"
        }

        try:
            response = requests.get(SEARCH_API_URL, params=params, headers=HEADERS, timeout=15)
            if response.status_code != 200:
                break

            data = response.json()
            ads = data.get("advertSummaryList", {}).get("advertSummary", [])
            
            for ad in ads:
                ad_id = str(ad.get("id"))
                if ad_id not in seen_ids:
                    full_text = get_full_description(ad_id)
                    if any(k in full_text for k in KEYWORDS):
                        # Extract SEO URL for the link
                        seo_url = next((a['values'][0] for a in ad['attributes']['attribute'] if a['name'] == 'SEO_URL'), "")
                        link = f"https://www.willhaben.at/iad/{seo_url}"
                        send_telegram(f"📺 *TV Bank Found (Page {page_num})*\n[View on Willhaben]({link})")
                        new_matches += 1
                    
                    new_ids_discovered.append(ad_id)
                    time.sleep(0.5) # Gentle throttle
        except Exception as e:
            log(f"Error on page {page_num}: {e}")

    if new_ids_discovered:
        with open("seen_ids.txt", "a") as f:
            for nid in new_ids_discovered:
                f.write(nid + "\n")
    
    log(f"Deep Search finished. New IDs stored: {len(new_ids_discovered)}")

if __name__ == "__main__":
    main()
