"""
aggregator.py - compute per-minute aggregates (avg, p95, error_rate, request_count)

This script is optional but recommended for fast Grafana queries. It:
- Runs a loop once per minute (aligned to minute boundary)
- For each monitor, reads measurements in the last minute and computes:
    - avg_latency_ms
    - p95_latency_ms
    - error_rate (fraction of requests that had error or status >= 500)
    - requests (count)
- Inserts a row into aggregates table

Run:
    python aggregator.py
"""

import time
from datetime import datetime, timedelta
from db import get_connection, init_db, row_to_dict
import statistics
import math
import threading

STOP = threading.Event()

def percentile(values, p):
    """Compute percentile p (0-100) of list of numeric values using linear interpolation.
    This is a small pure-Python replacement for numpy.percentile."""
    if not values:
        return None
    vals = sorted(values)
    k = (len(vals)-1) * (p/100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return vals[int(k)]
    d0 = vals[int(f)] * (c - k)
    d1 = vals[int(c)] * (k - f)
    return d0 + d1

def get_monitors():
    conn = get_connection()
    try:
        cur = conn.execute("SELECT * FROM monitors")
        return [row_to_dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

def aggregate_minute(window_start, window_end):
    monitors = get_monitors()
    conn = get_connection()
    try:
        for m in monitors:
            mid = m["id"]
            cur = conn.execute(
                "SELECT status_code, latency_ms, error FROM measurements WHERE monitor_id = ? AND ts >= ? AND ts < ?",
                (mid, window_start.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3], window_end.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3])
            )
            rows = cur.fetchall()
            latencies = [r["latency_ms"] for r in rows if r["latency_ms"] is not None]
            total = len(rows)
            errors = 0
            for r in rows:
                if r["error"] is not None:
                    errors += 1
                elif r["status_code"] is not None and r["status_code"] >= 500:
                    errors += 1
            avg_latency = statistics.mean(latencies) if latencies else None
            p95_latency = percentile(latencies, 95) if latencies else None
            error_rate = (errors/total) if total > 0 else None

            # insert aggregate row
            conn.execute(
                """INSERT INTO aggregates (monitor_id, window_start, window_end, avg_latency_ms, p95_latency_ms, error_rate, requests)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    mid,
                    window_start.strftime("%Y-%m-%d %H:%M:%S"),
                    window_end.strftime("%Y-%m-%d %H:%M:%S"),
                    avg_latency,
                    p95_latency,
                    error_rate,
                    total
                )
            )
        conn.commit()
    finally:
        conn.close()

def align_to_next_minute():
    now = datetime.utcnow()
    next_min = (now.replace(second=0, microsecond=0) + timedelta(minutes=1))
    return (next_min - now).total_seconds()

def run_loop():
    init_db()
    print("Aggregator started. Waiting to align to minute boundary...")
    time.sleep(align_to_next_minute())
    print("Aligned. Beginning per-minute aggregation.")
    try:
        while not STOP.is_set():
            # aggregate previous minute
            end = datetime.utcnow().replace(second=0, microsecond=0)
            start = end - timedelta(minutes=1)
            print(f"Aggregating from {start} to {end} (UTC)")
            aggregate_minute(start, end)
            # wait until next minute (sleep ~60s)
            for _ in range(60):
                if STOP.is_set():
                    break
                time.sleep(1)
    except KeyboardInterrupt:
        print("Aggregator interrupted; exiting.")
    finally:
        print("Aggregator stopped.")

if __name__ == "__main__":
    run_loop()
