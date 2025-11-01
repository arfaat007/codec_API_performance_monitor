import requests
import time
import sqlite3
from datetime import datetime

# ✅ List of APIs to monitor
APIS_TO_MONITOR = [
    "https://api.github.com",
    "https://jsonplaceholder.typicode.com/posts",
    "https://dog.ceo/api/breeds/image/random",
    "https://catfact.ninja/fact",
    "https://api.coindesk.com/v1/bpi/currentprice.json",
    "https://api.ipify.org?format=json",
    "https://api.chucknorris.io/jokes/random",
    "https://www.boredapi.com/api/activity",
    "https://api.agify.io?name=michael",
    "https://api.open-meteo.com/v1/forecast?latitude=35&longitude=139&current_weather=true"
]

DB_PATH = "database.db"

def log_to_db(api_url, status_code, response_time):
    """Store metrics into SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS api_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_url TEXT,
            status_code TEXT,
            response_time REAL,
            checked_at TEXT
        )
    """)
    cur.execute("""
        INSERT INTO api_metrics (api_url, status_code, response_time, checked_at)
        VALUES (?, ?, ?, ?)
    """, (api_url, status_code, response_time, datetime.now()))
    conn.commit()
    conn.close()

def monitor_apis():
    """Check all APIs and log response times."""
    for api in APIS_TO_MONITOR:
        try:
            start = time.time()
            response = requests.get(api, timeout=5)
            elapsed = round((time.time() - start) * 1000, 2)  # milliseconds
            log_to_db(api, response.status_code, elapsed)
            print(f"[✅ OK] {api} → {response.status_code} in {elapsed} ms")
        except Exception as e:
            log_to_db(api, "ERROR", 0)
            print(f"[❌ FAIL] {api} → {e}")

if __name__ == "__main__":
    print("🌐 Starting API Performance Monitor...")
    while True:
        monitor_apis()
        print("Sleeping for 60 seconds...\n")
        time.sleep(60)
