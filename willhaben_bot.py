import requests
import os
import sys

# --- CONFIGURATION ---
API_URL = "https://www.willhaben.at/iad/searchmarket/api/v1/search"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "de-AT,de;q=0.9,en-US;q=0.8,en;q=0.7",
    "x-wh-client": "api-v1-searchmarket",
    "Origin": "https://www.willhaben.at",
    "Referer": "https://www.willhaben.at/"
}

# The parameters from your URL
PARAMS = {
    "rows": 30,
    "areaId": 900,         # Vienna
    "keyword": "tv bank",
    "attribute": ["farbe:schwarz"],
    "isNavigation": "true"
}

KEYWORDS = ["160x", "160 cm", "breite 160", "x160"] # Add more as needed
TELEGRAM_TOKEN = os.getenv("TG_TOKEN")
CHAT_ID = os.getenv("TG_CHAT_ID")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, json=payload)


def main():
    # 1. Load seen IDs
    seen_ids = set()
    if os.path.exists("seen_ids.txt"):
        with open("seen_ids.txt", "r") as f:
            seen_ids = set(f.read().splitlines())

    # 2. Fetch data with error handling
    try:
        response = requests.get(API_URL, params=PARAMS, headers=HEADERS, timeout=15)
        
        # Check if the request was successful
        if response.status_code != 200:
            print(f"Error: Willhaben returned status {response.status_code}")
            # Optional: send_telegram(f"⚠️ Bot Alert: Willhaben blocked the request (Status {response.status_code})")
            return

        data = response.json()
    except Exception as e:
        print(f"Failed to parse JSON: {e}")
        return
    
    # 3. Process items
    new_ids = []
    feed_items = data.get("feedItems", [])
    
    if not feed_items:
        print("No items found in the feed.")
        return

    for item in feed_items:
        ad_id = str(item.get("id"))
        if ad_id not in seen_ids:
            # Check title and description
            description = item.get("description", "").lower()
            title = item.get("contentTitle", "").lower()
            
            if any(k in description for k in KEYWORDS) or any(k in title for k in KEYWORDS):
                price = item.get("price", {}).get("amount", "N/A")
                # Build the URL correctly
                seo_url = item.get('seoUrl', '')
                link = f"https://www.willhaben.at/iad/{seo_url}"
                
                msg = f"📺 New TV Bank Found!\nPrice: €{price}\n\n[Open Item]({link})"
                send_telegram(msg)
                
            new_ids.append(ad_id)

    # 4. Save state
    if new_ids:
        with open("seen_ids.txt", "a") as f:
            for ni in new_ids:
                f.write(ni + "\n")
        print(f"Success: Processed {len(new_ids)} new items.")

if __name__ == "__main__":
    main()