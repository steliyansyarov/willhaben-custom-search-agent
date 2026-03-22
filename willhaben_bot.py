import requests
import os
import time

# --- CONFIGURATION ---
# Use the exact base URL from your successful fetch
SEARCH_API_URL = "https://www.willhaben.at/webapi/iad/search/atz/seo/kaufen-und-verkaufen/marktplatz/a/farbe-schwarz-3201"
# API for item details
DETAIL_API_URL = "https://publicapi.willhaben.at/atdetail/v1/"

HEADERS = {
    "accept": "application/json",
    "x-wh-client": "api@willhaben.at;responsive_web;server;1.0.0;phone",
    "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Mobile Safari/537.36"
}

PARAMS = {
    "areaId": "900",
    "keyword": "tv bank",
    "rows": "30",
    "isNavigation": "true"
}

KEYWORDS = ["160x", "160 cm", "breite 160"]
TELEGRAM_TOKEN = os.getenv("TG_TOKEN")
CHAT_ID = os.getenv("TG_CHAT_ID")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, json=payload, timeout=10)

def get_full_description(ad_id):
    """Fetches the full description for a specific ad ID."""
    try:
        response = requests.get(f"{DETAIL_API_URL}{ad_id}", headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Extract description from attributes or description field
            return data.get("description", "").lower()
    except:
        return ""
    return ""

def main():
    # 1. Load seen IDs
    if os.path.exists("seen_ids.txt"):
        with open("seen_ids.txt", "r") as f:
            seen_ids = set(f.read().splitlines())
    else:
        seen_ids = set()

    # 2. Fetch Search Results
    response = requests.get(SEARCH_API_URL, params=PARAMS, headers=HEADERS)
    if response.status_code != 200:
        print(f"Search failed with status {response.status_code}")
        return

    data = response.json()
    ads = data.get("advertSummaryList", {}).get("advertSummary", [])
    
    new_ids_to_save = []

    for ad in ads:
        ad_id = str(ad.get("id"))
        
        if ad_id not in seen_ids:
            # Step 3: Get full description for the keyword check
            full_desc = get_full_description(ad_id)
            title = ad.get("description", "").lower() # In search results, 'description' is often the title
            
            if any(k in full_desc for k in KEYWORDS) or any(k in title for k in KEYWORDS):
                price = "N/A"
                # Find price in attributes
                for attr in ad.get("attributes", {}).get("attribute", []):
                    if attr.get("name") == "PRICE_FOR_DISPLAY":
                        price = attr.get("values", ["N/A"])[0]
                
                seo_path = ""
                for attr in ad.get("attributes", {}).get("attribute", []):
                    if attr.get("name") == "SEO_URL":
                        seo_path = attr.get("values", [""])[0]
                
                link = f"https://www.willhaben.at/iad/{seo_path}"
                msg = f"📺 Found matching TV Bank!\nPrice: {price}\n\n[Open Item]({link})"
                send_telegram(msg)
            
            new_ids_to_save.append(ad_id)
            time.sleep(1) # Small delay to be nice to the API

    # 4. Update memory
    if new_ids_to_save:
        with open("seen_ids.txt", "a") as f:
            for nid in new_ids_to_save:
                f.write(nid + "\n")

if __name__ == "__main__":
    main()