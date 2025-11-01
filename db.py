


# `db.py`

"""
db.py - shared DB helpers and schema for API Performance Monitor

This module is used by app.py, collector.py and aggregator.py.
It ensures schema creation and provides helper functions for per-thread connections.

Tables:
- monitors: the endpoints configuration
- measurements: raw probe results
- aggregates: per-minute aggregated stats (avg, p95, error_rate, request_count)
"""

import sqlite3
import json
from pathlib import Path

DB_PATH = Path("apimon.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS monitors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    method TEXT NOT NULL DEFAULT 'GET',
    headers TEXT,
    body TEXT,
    interval_sec INTEGER NOT NULL DEFAULT 60,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS measurements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    monitor_id INTEGER NOT NULL,
    ts DATETIME DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
    status_code INTEGER,
    latency_ms REAL,
    error TEXT,
    response_size INTEGER,
    response_headers TEXT,
    response_body_snippet TEXT,
    FOREIGN KEY(monitor_id) REFERENCES monitors(id)
);

CREATE TABLE IF NOT EXISTS aggregates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    monitor_id INTEGER NOT NULL,
    window_start DATETIME,
    window_end DATETIME,
    avg_latency_ms REAL,
    p95_latency_ms REAL,
    error_rate REAL,
    requests INTEGER
);
"""

def init_db(db_path: str | None = None):
    path = DB_PATH if db_path is None else Path(db_path)
    path_parent = path.parent
    if not path_parent.exists():
        path_parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()

def get_connection(db_path: str | None = None):
    """Return a new sqlite3 connection configured for use in a thread."""
    path = DB_PATH if db_path is None else Path(db_path)
    conn = sqlite3.connect(str(path), timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def row_to_dict(row):
    if row is None:
        return None
    return {k: row[k] for k in row.keys()}

# Sample SQL queries (for Grafana panels)
# 1) avg latency per minute for the last hour:
# SELECT strftime('%Y-%m-%dT%H:%M:00', ts) AS time, avg(latency_ms) AS value, monitor_id as metric
# FROM measurements
# WHERE latency_ms IS NOT NULL AND ts >= datetime('now','-1 hour')
# GROUP BY metric, time ORDER BY time;
#
# 2) error rate per minute:
# SELECT strftime('%Y-%m-%dT%H:%M:00', ts) as time,
#   sum(CASE WHEN error IS NOT NULL OR (status_code IS NOT NULL AND status_code >= 500) THEN 1 ELSE 0 END)*1.0/count(*) as value,
#   monitor_id as metric
# FROM measurements
# WHERE ts >= datetime('now','-1 hour')
# GROUP BY metric, time ORDER BY time;
#
# 3) use aggregates table (recommended) for p95:
# SELECT window_start AS time, p95_latency_ms AS value, monitor_id as metric FROM aggregates
# WHERE window_start >= datetime('now','-1 hour');

if __name__ == "__main__":
    init_db()
    print("Database initialized at", DB_PATH.resolve())
