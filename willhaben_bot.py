import requests
import os
import time
import sys

# --- CONFIGURATION ---
# Base Search URL from your successful browser fetch
SEARCH_API_URL = "https://www.willhaben.at/webapi/iad/search/atz/seo/kaufen-und-verkaufen/marktplatz/a/farbe-schwarz-3201"
# Internal API for fetching full ad details
DETAIL_API_URL = "https://www.willhaben.at/webapi/iad/atdetail/"

HEADERS = {
    "accept": "application/json",
    "x-wh-client": "api@willhaben.at;responsive_web;server;1.0.0;phone",
    "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Mobile"
}

# Search parameters based on your criteria (Vienna, Black, TV Bank)
PARAMS = {
    "areaId": "900",
    "keyword": "tv bank",
    "rows": "30",
    "isNavigation": "true"
}

# Keywords to look for in the description
KEYWORDS = ["160x", "160 cm", "breite 160"]

# Secrets loaded from GitHub Actions
TELEGRAM_TOKEN = os.getenv("TG_TOKEN")
CHAT_ID = os.getenv("TG_CHAT_ID")

def log(msg):
    """Prints message immediately to GitHub logs."""
    print(f">>> {msg}", flush=True)

def send_telegram(message):
    """Sends a notification to your Telegram bot."""
    log("Sending Telegram notification...")
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        res = requests.post(url, json=payload, timeout=10)
        log(f"Telegram status: {res.status_code}")
    except Exception as e:
        log(f"Telegram failed: {e}")

def get_full_description(ad_id):
    """Fetches the detailed ad data to scan the full description."""
    try:
        url = f"{DETAIL_API_URL}{ad_id}"
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Combine title and full body text for scanning
            all_text = [data.get("description", "")]
            attrs = data.get("attributes", {}).get("attribute", [])
            for a in attrs:
                if a.get("name") in ["BODY_DYN", "HEADING"]:
                    all_text.extend(a.get("values", []))
            return " ".join(all_text).lower()
    except Exception as e:
        log(f"Detail fetch failed for {ad_id}: {e}")
    return ""

def main():
    log("Starting Willhaben Agent...")
    
    if not TELEGRAM_TOKEN or not CHAT_ID:
        log("CRITICAL: Telegram secrets are missing!")
        return

    # 1. Load database of already seen items
    seen_ids = set()
    if os.path.exists("seen_ids.txt"):
        with open("seen_ids.txt", "r") as f:
            seen_ids = set(f.read().splitlines())
    log(f"Items in memory: {len(seen_ids)}")

    # 2. Fetch latest search results
    response = requests.get(SEARCH_API_URL, params=PARAMS, headers=HEADERS, timeout=15)
    if response.status_code != 200:
        log(f"Search failed: {response.status_code}")
        return

    data = response.json()
    ads = data.get("advertSummaryList", {}).get("advertSummary", [])
    log(f"Found {len(ads)} ads in search results.")

    new_matches = 0
    new_ids_discovered = []

    # 3. Process new ads
    for ad in ads:
        ad_id = str(ad.get("id"))
        
        if ad_id not in seen_ids:
            log(f"New item: {ad_id}. Checking description...")
            full_text = get_full_description(ad_id)
            
            # Check if any keyword matches
            if any(k in full_text for k in KEYWORDS):
                price = "N/A"
                seo_url = ""
                # Extract price and link from attributes
                for attr in ad.get("attributes", {}).get("attribute", []):
                    if attr.get("name") == "PRICE_FOR_DISPLAY":
                        price = attr.get("values", ["N/A"])[0]
                    if attr.get("name") == "SEO_URL":
                        seo_url = attr.get("values", [""])[0]
                
                link = f"https://www.willhaben.at/iad/{seo_url}"
                send_telegram(f"📺 *TV Bank Match Found!*\nPrice: {price}\n\n[View on Willhaben]({link})")
                new_matches += 1
            
            new_ids_discovered.append(ad_id)
            time.sleep(1) # Be gentle with the API

    # 4. Save new IDs to memory
    if new_ids_discovered:
        with open("seen_ids.txt", "a") as f:
            for nid in new_ids_discovered:
                f.write(nid + "\n")
        log(f"Added {len(new_ids_discovered)} items to seen_ids.txt")

    log(f"Finished. Notifications sent: {new_matches}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"Runtime error: {e}")