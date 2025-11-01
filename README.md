# API Performance Monitor

A lightweight API performance monitor using:
- Python (Flask + requests)
- SQLite for storage
- Grafana for visualization (optional; see notes)

## Files
- `db.py` - DB setup and helper functions
- `app.py` - Flask admin API to manage monitors and view measurements
- `collector.py` - background probe worker to perform requests and write measurements
- `aggregator.py` - periodic aggregator computing avg/p95/error rate per-minute
- `requirements.txt` - Python dependencies
- `docker-compose.yml` - optional Grafana + Flask dev stack (read notes)

## Quick start (local)
1. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
