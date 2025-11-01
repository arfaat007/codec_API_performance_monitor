from flask import Flask, render_template_string, jsonify
import sqlite3

app = Flask(__name__)
DB_PATH = "database.db"

# HTML template with Chart.js + Tailwind + Auto-refresh
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>API Performance Monitor</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body class="bg-gray-900 text-gray-100 min-h-screen">
    <div class="container mx-auto p-6">
        <h1 class="text-3xl font-bold mb-6 text-center">🌐 API Performance Monitor Dashboard</h1>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div class="bg-gray-800 p-4 rounded-lg shadow">
                <h2 class="text-xl font-semibold mb-4">📊 Response Time Chart</h2>
                <canvas id="responseChart" height="200"></canvas>
            </div>

            <div class="bg-gray-800 p-4 rounded-lg shadow overflow-x-auto">
                <h2 class="text-xl font-semibold mb-4">📋 Recent API Checks</h2>
                <table class="table-auto w-full text-sm border border-gray-700">
                    <thead class="bg-gray-700 text-gray-200">
                        <tr>
                            <th class="px-4 py-2 text-left">API URL</th>
                            <th class="px-4 py-2 text-left">Status</th>
                            <th class="px-4 py-2 text-left">Response Time (ms)</th>
                            <th class="px-4 py-2 text-left">Checked At</th>
                        </tr>
                    </thead>
                    <tbody id="metricsTable"></tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
    async function fetchMetrics() {
        const res = await fetch('/metrics');
        const data = await res.json();

        // Update Table
        const table = document.getElementById("metricsTable");
        table.innerHTML = "";
        data.forEach(row => {
            const tr = document.createElement("tr");
            tr.className = "border-t border-gray-700 hover:bg-gray-800";
            if (row.status_code === "ERROR") tr.classList.add("bg-red-900");
            tr.innerHTML = `
                <td class="px-4 py-2">${row.api_url}</td>
                <td class="px-4 py-2">${row.status_code}</td>
                <td class="px-4 py-2">${row.response_time}</td>
                <td class="px-4 py-2">${row.checked_at}</td>
            `;
            table.appendChild(tr);
        });

        // Prepare data for chart
        const chartLabels = [...new Set(data.map(d => d.api_url))];
        const datasets = chartLabels.map(api => {
            const apiData = data.filter(d => d.api_url === api).slice(-10);
            return {
                label: api,
                data: apiData.map(d => d.response_time),
                fill: false,
                borderColor: `hsl(${Math.random() * 360}, 70%, 60%)`,
                tension: 0.2
            };
        });

        // Render chart
        const ctx = document.getElementById("responseChart").getContext("2d");
        if (window.apiChart) window.apiChart.destroy();
        window.apiChart = new Chart(ctx, {
            type: "line",
            data: { labels: [...Array(10).keys()], datasets },
            options: {
                plugins: { legend: { labels: { color: "#fff" } } },
                scales: {
                    x: { ticks: { color: "#aaa" }, grid: { color: "#333" } },
                    y: { ticks: { color: "#aaa" }, grid: { color: "#333" } }
                }
            }
        });
    }

    // Initial load
    fetchMetrics();

    // Auto-refresh every 30 seconds
    setInterval(fetchMetrics, 30000);
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    """Serve dashboard page."""
    return render_template_string(HTML_TEMPLATE)

@app.route("/metrics")
def metrics():
    """Return JSON of recent metrics for JS chart/table."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
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
    cur.execute("SELECT * FROM api_metrics ORDER BY checked_at DESC LIMIT 100")
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jsonify(rows)

if __name__ == "__main__":
    app.run(debug=True)
