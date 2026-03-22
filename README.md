# 📺 Willhaben Search Item Watcher

This project is a Python-based automation tool designed to monitor **Willhaben** for specific products (currently configured for **black TV banks in Vienna**). It filters new listings based on specific strings in the description (e.g., **"160x"**) and sends instant notifications via **Telegram**.

## 🚀 Features
* **Deep Filtering:** Goes beyond standard app filters by scanning the item description for specific dimensions or keywords.
* **Zero Hosting Costs:** Runs entirely on **GitHub Actions**—no local server or Raspberry Pi required.
* **Smart Notifications:** Sends a direct Telegram message with a clickable link and price info.
* **Memory Persistent:** Tracks "seen" ads in a local file to ensure you never get notified about the same item twice.

## 🛠 Setup

### 1. Telegram Configuration
1.  Message [@BotFather](https://t.me/botfather) on Telegram to create a bot and get your **API Token**.
2.  Get your **Chat ID** (the unique ID for your private chat with the bot).

### 2. GitHub Secrets
To keep your credentials safe, add the following as **Actions Secrets** in your GitHub repository settings:
* `TG_TOKEN`: Your Telegram Bot API Token.
* `TG_CHAT_ID`: Your personal Telegram Chat ID.

### 3. Repository Permissions
Ensure your GitHub Action has permission to save data back to the repo:
* Go to **Settings > Actions > General**.
* Under **Workflow permissions**, select **Read and write permissions**.

## 📂 File Structure
* `willhaben_bot.py`: The core logic that fetches JSON data from Willhaben and filters results.
* `.github/workflows/check.yml`: The automation schedule (currently set to run every **20 minutes**).
* `seen_ids.txt`: A database of already notified ads (automatically updated).

---