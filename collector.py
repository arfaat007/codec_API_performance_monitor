"""
collector.py - probe worker that periodically sends requests to configured monitors
and writes results to the measurements table.

Behavior:
- Reads all monitors on startup and spawns a thread per monitor that polls at monitor.interval_sec
- Each probe writes one measurement row; failures populate 'error'
- Uses per-thread DB connections (sqlite + check_same_thread=False)
- Safe shutdown via KeyboardInterrupt

Run:
    python collector.py
"""

import threading
import time
import json
from db import get_connection, init_db, row_to_dict
from datetime import datetime
import requests
import traceback

STOP_EVENT = threading.Event()

def load_monitors():
    conn = get_connection()
    try:
        cur = conn.execute("SELECT * FROM monitors")
        rows = [row_to_dict(r) for r in cur.fetchall()]
        # decode headers to dict (if stored as json string)
        for r in rows:
            if r.get("headers"):
                try:
                    r["headers"] = json.loads(r["headers"])
                except Exception:
                    pass
        return rows
    finally:
        conn.close()

def record_measure(measure):
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO measurements
            (monitor_id, ts, status_code, latency_ms, error, response_size, response_headers, response_body_snippet)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                measure["monitor_id"],
                measure["ts"],
                measure.get("status_code"),
                measure.get("latency_ms"),
                measure.get("error"),
                measure.get("response_size"),
                json.dumps(measure.get("response_headers") or {}),
                (measure.get("response_body_snippet") or "")[:2000]
            )
        )
        conn.commit()
    finally:
        conn.close()

def probe_once(monitor):
    mid = monitor["id"]
    method = (monitor.get("method") or "GET").upper()
    headers = monitor.get("headers") or {}
    body = monitor.get("body")
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    try:
        start = time.time()
        r = requests.request(method, monitor["url"], headers=headers, data=body, timeout=20)
        latency_ms = (time.time() - start) * 1000.0
        m = {
            "monitor_id": mid,
            "ts": ts,
            "status_code": r.status_code,
            "latency_ms": latency_ms,
            "error": None,
            "response_size": len(r.content or b""),
            "response_headers": dict(r.headers),
            "response_body_snippet": (r.text or "")[:2000]
        }
    except Exception as e:
        m = {
            "monitor_id": mid,
            "ts": ts,
            "status_code": None,
            "latency_ms": None,
            "error": str(e),
            "response_size": None,
            "response_headers": None,
            "response_body_snippet": None
        }
    record_measure(m)

def monitor_loop(monitor):
    interval = max(5, int(monitor.get("interval_sec") or 60))
    # perform an immediate probe on start
    while not STOP_EVENT.is_set():
        try:
            probe_once(monitor)
        except Exception:
            # defensive: log to console but don't kill loop
            traceback.print_exc()
        # wait with early exit
        if STOP_EVENT.wait(interval):
            break

def run():
    init_db()
    monitors = load_monitors()
    if not monitors:
        print("No monitors found. Add monitors via app.py (/monitors). Exiting.")
        return
    threads = []
    for m in monitors:
        t = threading.Thread(target=monitor_loop, args=(m,), daemon=True)
        t.start()
        threads.append(t)
        print(f"Started monitor thread: id={m['id']} url={m['url']} interval={m['interval_sec']}s")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down collector...")
        STOP_EVENT.set()
        for t in threads:
            t.join(timeout=2)
        print("Collector stopped.")

if __name__ == "__main__":
    run()
