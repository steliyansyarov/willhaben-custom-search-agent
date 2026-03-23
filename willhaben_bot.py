import requests
import os
import time
import math

# --- CONFIGURATION ---
SEARCH_API_URL = "https://www.willhaben.at/webapi/iad/search/atz/seo/kaufen-und-verkaufen/marktplatz/a/farbe-schwarz-3201"

HEADERS = {
    "accept": "application/json",
    "x-wh-client": "api@willhaben.at;responsive_web;server;1.0.0;phone",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "referer": "https://www.willhaben.at/",
    "origin": "https://www.willhaben.at"
}

KEYWORDS = ["150x", "150 x", "150 cm", "150cm", "x150", "x 150"]
ROWS_PER_PAGE = 90

TELEGRAM_TOKEN = os.getenv("TG_TOKEN")
CHAT_ID = os.getenv("TG_CHAT_ID")

def log(msg):
    """Prints with forced flush for GitHub Actions visibility."""
    print(f">>> {msg}", flush=True)

def load_seen_ids(file_path="seen_ids.txt"):
    """Loads previously processed IDs from the local file."""
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return set(f.read().splitlines())
    return set()

def save_new_ids(new_ids, file_path="seen_ids.txt"):
    """Appends newly discovered IDs to the local file."""
    if not new_ids:
        return
    with open(file_path, "a") as f:
        for ad_id in new_ids:
            f.write(f"{ad_id}\n")
    log(f"Saved {len(new_ids)} new IDs to history.")

def fetch_search_page(page_number):
    """Performs the network request for a specific search page."""
    params = {
        "areaId": "900",
        "keyword": "tv bank",
        "rows": str(ROWS_PER_PAGE),
        "page": str(page_number),
        "isNavigation": "true"
    }
    try:
        response = requests.get(SEARCH_API_URL, params=params, headers=HEADERS, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        log(f"Error fetching page {page_number}: {e}")
        return None

def parse_ad_data(ad):
    """Extracts relevant fields (text, price, link) from a raw ad JSON object."""
    attributes = ad.get("attributes", {}).get("attribute", [])
    
    # Initialize defaults
    content_to_search = str(ad.get("description", "")).lower()
    seo_url = ""
    price = "N/A"
    location = "Unknown"

    for attr in attributes:
        name = attr.get("name")
        values = attr.get("values", [])
        if not values: continue

        if name == "BODY_DYN":
            content_to_search += " " + " ".join(values).lower()
        elif name == "SEO_URL":
            seo_url = values[0]
        elif name == "PRICE_FOR_DISPLAY":
            price = values[0]
        elif name == "LOCATION":
            location = values[0]

    return {
        "id": str(ad.get("id")),
        "search_text": content_to_search,
        "url": f"https://www.willhaben.at/iad/{seo_url}",
        "price": price,
        "location": location
    }

def send_telegram_match(ad_details):
    """Formats and sends the Telegram notification."""
    message = (
        f"🎯 *Match Found*\n"
        f"💰 Price: {ad_details['price']}\n"
        f"📍 Location: {ad_details['location']}\n"
        f"🔗 [View Item]({ad_details['url']})"
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        log(f"Telegram notification failed: {e}")

def main():
    log("Initializing Willhaben Watcher...")
    if not TELEGRAM_TOKEN or not CHAT_ID:
        log("CRITICAL: Environment variables TG_TOKEN or TG_CHAT_ID are missing.")
        return

    seen_ids = load_seen_ids()
    current_page = 1
    total_pages = 1
    new_ids_for_history = []
    matches_count = 0

    while current_page <= total_pages:
        data = fetch_search_page(current_page)
        if not data: break

        # Calculate total pages on the first request
        if current_page == 1:
            rows_found = data.get("rowsFound", 0)
            total_pages = min(math.ceil(rows_found / ROWS_PER_PAGE), 15)
            log(f"Total items: {rows_found}. Scanning {total_pages} pages.")

        ads = data.get("advertSummaryList", {}).get("advertSummary", [])
        for raw_ad in ads:
            ad = parse_ad_data(raw_ad)
            
            if ad["id"] not in seen_ids:
                # Check if any keyword matches the combined text
                if any(k in ad["search_text"] for k in KEYWORDS):
                    log(f"Match found! ID: {ad['id']}")
                    send_telegram_match(ad)
                    matches_count += 1
                
                new_ids_for_history.append(ad["id"])

        current_page += 1
        time.sleep(1) # Polite delay between pages

    save_new_ids(new_ids_for_history)
    log(f"Scan finished. Notifications sent: {matches_count}")

if __name__ == "__main__":
    main()
