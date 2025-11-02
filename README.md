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

## Features

🔹 Monitor multiple APIs automatically at defined intervals
🔹 Store metrics (response time, status code, timestamp) in a local SQLite database
🔹 Expose collected data via a /metrics endpoint
🔹 Aggregate and analyze API performance data
🔹 Modular design with separate scripts for monitoring, collection, and aggregation
🔹 Optional Docker support for containerized deployment


| Component                | Technology              |
| ------------------------ | ----------------------- |
| Backend                  | Python (Flask)          |
| Monitoring               | Requests, schedulers    |
| Database                 | SQLite                  |
| Visualization (optional) | Grafana / JSON endpoint |
| Containerization         | Docker & Docker Compose |


How to Run
 1.Install dependencies
pip install -r requirements.txt

2. Initialize database
python db.py

3. Start the Flask API
python app.py

4.Run the monitor to start tracking APIs
python monitor.py

5. View collected metrics
Open your browser and visit:
http://127.0.0.1:5000/metrics

6.(Optional) Run in Docker:
docker compose up --build


💡 Use Cases

-API uptime and latency tracking
-Detecting slow or failing endpoints
-Demonstrating API monitoring for DevOps / backend engineering projects
=Building real-world Python + Flask applications

🧑‍💻 Author
Mohammed Shoaib Arfaat Nayyer
🎓 CSE Student (VTU) | Passionate about backend, APIs & performance engineering
