import requests
import os

# --- CONFIGURATION ---
# Your specific search URL parameters extracted
API_URL = "https://www.willhaben.at/iad/searchmarket/api/v1/search"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "x-wh-client": "api-v1-searchmarket" # Key header to access the API
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
    if os.path.exists("seen_ids.txt"):
        with open("seen_ids.txt", "r") as f:
            seen_ids = set(f.read().splitlines())
    else:
        seen_ids = set()

    # 2. Fetch data
    response = requests.get(API_URL, params=PARAMS, headers=HEADERS)
    data = response.json()
    
    new_ids = []
    
    for item in data.get("feedItems", []):
        ad_id = str(item.get("id"))
        
        if ad_id not in seen_ids:
            # Check description for keywords
            # Note: Willhaben API provides description in 'description' or 'attributes'
            description = item.get("description", "").lower()
            title = item.get("contentTitle", "").lower()
            
            if any(k in description for k in KEYWORDS) or any(k in title for k in KEYWORDS):
                price = item.get("price", {}).get("amount", "N/A")
                link = f"https://www.willhaben.at/iad/{item.get('seoUrl')}"
                
                msg = f"?? *New TV Bank Found!*\nPrice: €{price}\nMatch: {description[:100]}...\n\n[Open Item]({link})"
                send_telegram(msg)
                
            new_ids.append(ad_id)

    # 3. Save state (append only new ones to file)
    with open("seen_ids.txt", "a") as f:
        for ni in new_ids:
            f.write(ni + "\n")

if __name__ == "__main__":
    main()