import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
LOG_FILE = "trade_log.csv"

def send_telegram(msg):
    if TG_TOKEN and TG_CHAT_ID:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        data = {"chat_id": TG_CHAT_ID, "text": msg}
        try:
            requests.post(url, data=data)
        except Exception as e:
            print("Telegram Error:", e)

def log_trade(action, side, symbol, price, amount):
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w') as f:
            f.write("timestamp,action,side,symbol,price,amount\n")
    with open(LOG_FILE, 'a') as f:
        f.write(f"{datetime.utcnow()},{action},{side},{symbol},{price},{amount}\n")