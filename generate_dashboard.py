import csv
import os
from datetime import datetime, timedelta
from collections import defaultdict

DATA_DIR = "data"
STOCKS_FILE = os.path.join(DATA_DIR, "stocks_data.csv")
INDUSTRY_FILE = os.path.join(DATA_DIR, "industry_data.csv")
DOCS_DIR = "docs"
OUTPUT_FILE = os.path.join(DOCS_DIR, "index.html")


def load_stocks_data():
    stocks = []
    if os.path.isfile(STOCKS_FILE):
        with open(STOCKS_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                stocks.append(row)
    return stocks


def load_industry_data():
    industries = []
    if os.path.isfile(INDUSTRY_FILE):
        with open(INDUSTRY_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                industries.append(row)
    return industries


def filter_by_timeframe(data, days=None, start_date=None, end_date=None):
    if not data:
        return data
    
    today = datetime.now().date()
    
    if days is not None:
        start = today - timedelta(days=days)
        end = today
    elif start_date and end_date:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
    else:
        return data
    
    filtered = []
    for row in data:
        if "date" not in row or not row["date"]:
            continue
        try:
            row_date = datetime.strptime(row["date"], "%Y-%m-%d").date()
            if start <= row_date <= end:
                filtered.append(row)
        except ValueError:
            continue
    return filtered


def get_stock_counts(stocks_data):
    counts = defaultdict(lambda: {"count": 0, "industries": set(), "dates": []})
    for row in stocks_data:
        stock = row.get("stock", "")
        if not stock:
            continue
        counts[stock]["count"] += 1
        if row.get("industry"):
            counts[stock]["industries"].add(row["industry"])
        if row.get("date"):
            counts[stock]["dates"].append(row["date"])
    
    result = []
    for stock, data in counts.items():
        result.append({
            "stock": stock,
            "count": data["count"],
            "industry": ", ".join(sorted(data["industries"])) if data["industries"] else "N/A",
            "last_seen": max(data["dates"]) if data["dates"] else "N/A"
        })
    return sorted(result, key=lambda x: x["count"], reverse=True)


def get_industry_totals(industry_data):
    counts = defaultdict(int)
    for row in industry_data:
        industry = row.get("industry", "Unknown")
        count = int(row.get("count", 0))
        if industry:
            counts[industry] += count
    return sorted(counts.items(), key=lambda x: x[1], reverse=True)


def get_date_range(data):
    if not data:
        return None, None
    dates = []
    for row in data:
        if "date" in row and row["date"]:
            dates.append(row["date"])
    if not dates:
        return None, None
    return min(dates), max(dates)


def generate_dashboard():
    stocks_data = load_stocks_data()
    industry_data = load_industry_data()
    
    min_date, max_date = get_date_range(stocks_data)
    if min_date is None:
        min_date, max_date = get_date_range(industry_data)
    
    all_stock_counts = get_stock_counts(stocks_data)
    all_industry_totals = get_industry_totals(industry_data)
    
    timeframes = {
        "7d": filter_by_timeframe(stocks_data, days=7),
        "30d": filter_by_timeframe(stocks_data, days=30),
        "90d": filter_by_timeframe(stocks_data, days=90),
        "all": stocks_data
    }
    
    industry_timeframes = {
        "7d": filter_by_timeframe(industry_data, days=7),
        "30d": filter_by_timeframe(industry_data, days=30),
        "90d": filter_by_timeframe(industry_data, days=90),
        "all": industry_data
    }
    
    stocks_json = {}
    industries_json = {}
    for key, data in timeframes.items():
        stocks_json[key] = get_stock_counts(data)
    for key, data in industry_timeframes.items():
        industries_json[key] = get_industry_totals(data)
    
    html = generate_html(stocks_json, industries_json, min_date, max_date, len(stocks_data))
    
    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"Dashboard generated: {OUTPUT_FILE}")
    return OUTPUT_FILE


def generate_html(stocks_json, industries_json, min_date, max_date, total_records):
    import json
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Top Gainers Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-primary: #0a0a0f;
            --bg-secondary: #12121a;
            --bg-card: #1a1a24;
            --bg-hover: #22222e;
            --accent-green: #00ff88;
            --accent-green-dim: rgba(0, 255, 136, 0.15);
            --accent-blue: #00d4ff;
            --accent-orange: #ff8800;
            --text-primary: #ffffff;
            --text-secondary: #8888aa;
            --text-muted: #555566;
            --border: #2a2a3a;
            --gradient-1: linear-gradient(135deg, #00ff88 0%, #00d4ff 100%);
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Space Grotesk', sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            overflow-x: hidden;
        }}
        
        .noise {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            opacity: 0.03;
            z-index: 1000;
            background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 40px 24px;
            position: relative;
            z-index: 1;
        }}
        
        header {{
            margin-bottom: 48px;
        }}
        
        .logo {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 8px;
        }}
        
        .logo-icon {{
            width: 48px;
            height: 48px;
            background: var(--gradient-1);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            font-weight: 700;
            color: var(--bg-primary);
        }}
        
        h1 {{
            font-size: 32px;
            font-weight: 700;
            background: var(--gradient-1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        .subtitle {{
            color: var(--text-secondary);
            font-size: 14px;
            margin-top: 4px;
        }}
        
        .stats-bar {{
            display: flex;
            gap: 24px;
            margin-bottom: 32px;
            flex-wrap: wrap;
        }}
        
        .stat-item {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 16px 24px;
            min-width: 160px;
        }}
        
        .stat-label {{
            font-size: 12px;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 4px;
        }}
        
        .stat-value {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 24px;
            font-weight: 600;
            color: var(--accent-green);
        }}
        
        .timeframe-selector {{
            display: flex;
            gap: 8px;
            margin-bottom: 32px;
            background: var(--bg-secondary);
            padding: 6px;
            border-radius: 12px;
            width: fit-content;
        }}
        
        .timeframe-btn {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 13px;
            font-weight: 500;
            padding: 10px 20px;
            border: none;
            background: transparent;
            color: var(--text-secondary);
            cursor: pointer;
            border-radius: 8px;
            transition: all 0.2s ease;
        }}
        
        .timeframe-btn:hover {{
            color: var(--text-primary);
            background: var(--bg-hover);
        }}
        
        .timeframe-btn.active {{
            background: var(--accent-green);
            color: var(--bg-primary);
        }}
        
        .grid {{
            display: grid;
            grid-template-columns: 1fr 400px;
            gap: 24px;
        }}
        
        @media (max-width: 1024px) {{
            .grid {{
                grid-template-columns: 1fr;
            }}
        }}
        
        .card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            overflow: hidden;
        }}
        
        .card-header {{
            padding: 20px 24px;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .card-title {{
            font-size: 16px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .card-title::before {{
            content: '';
            width: 8px;
            height: 8px;
            background: var(--accent-green);
            border-radius: 50%;
            box-shadow: 0 0 12px var(--accent-green);
        }}
        
        .search-box {{
            display: flex;
            align-items: center;
            gap: 8px;
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 8px 12px;
        }}
        
        .search-box input {{
            font-family: 'Space Grotesk', sans-serif;
            font-size: 13px;
            background: transparent;
            border: none;
            outline: none;
            color: var(--text-primary);
            width: 180px;
        }}
        
        .search-box input::placeholder {{
            color: var(--text-muted);
        }}
        
        .table-container {{
            max-height: 600px;
            overflow-y: auto;
        }}
        
        .table-container::-webkit-scrollbar {{
            width: 6px;
        }}
        
        .table-container::-webkit-scrollbar-track {{
            background: var(--bg-secondary);
        }}
        
        .table-container::-webkit-scrollbar-thumb {{
            background: var(--border);
            border-radius: 3px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        th {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-muted);
            text-align: left;
            padding: 12px 24px;
            background: var(--bg-secondary);
            position: sticky;
            top: 0;
            z-index: 10;
        }}
        
        td {{
            padding: 14px 24px;
            border-bottom: 1px solid var(--border);
            font-size: 14px;
        }}
        
        tr:hover td {{
            background: var(--bg-hover);
        }}
        
        .stock-name {{
            font-weight: 600;
            color: var(--text-primary);
        }}
        
        .stock-industry {{
            font-size: 12px;
            color: var(--text-muted);
            margin-top: 2px;
        }}
        
        .count-badge {{
            font-family: 'JetBrains Mono', monospace;
            font-weight: 600;
            color: var(--accent-green);
            background: var(--accent-green-dim);
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 13px;
        }}
        
        .date-cell {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            color: var(--text-secondary);
        }}
        
        .industry-list {{
            padding: 8px;
        }}
        
        .industry-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 14px 16px;
            border-radius: 10px;
            margin-bottom: 4px;
            transition: background 0.2s ease;
        }}
        
        .industry-item:hover {{
            background: var(--bg-hover);
        }}
        
        .industry-name {{
            font-size: 14px;
            font-weight: 500;
        }}
        
        .industry-count {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 14px;
            font-weight: 600;
            color: var(--accent-blue);
        }}
        
        .industry-bar {{
            height: 4px;
            background: var(--bg-secondary);
            border-radius: 2px;
            margin-top: 8px;
            overflow: hidden;
        }}
        
        .industry-bar-fill {{
            height: 100%;
            background: var(--gradient-1);
            border-radius: 2px;
            transition: width 0.5s ease;
        }}
        
        .empty-state {{
            text-align: center;
            padding: 60px 24px;
            color: var(--text-muted);
        }}
        
        .empty-state svg {{
            width: 48px;
            height: 48px;
            margin-bottom: 16px;
            opacity: 0.5;
        }}
        
        .rank {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            color: var(--text-muted);
            width: 32px;
        }}
        
        .rank-1 {{ color: #ffd700; }}
        .rank-2 {{ color: #c0c0c0; }}
        .rank-3 {{ color: #cd7f32; }}
    </style>
</head>
<body>
    <div class="noise"></div>
    <div class="container">
        <header>
            <div class="logo">
                <div class="logo-icon">▲</div>
                <div>
                    <h1>Top Gainers Dashboard</h1>
                    <p class="subtitle">Track stocks appearing on the daily top gainers list</p>
                </div>
            </div>
        </header>
        
        <div class="stats-bar">
            <div class="stat-item">
                <div class="stat-label">Total Records</div>
                <div class="stat-value" id="total-records">{total_records}</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">Date Range</div>
                <div class="stat-value" style="font-size: 16px;" id="date-range">{min_date or 'N/A'} → {max_date or 'N/A'}</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">Unique Stocks</div>
                <div class="stat-value" id="unique-stocks">{len(stocks_json.get('all', []))}</div>
            </div>
        </div>
        
        <div class="timeframe-selector">
            <button class="timeframe-btn" data-tf="7d">7 Days</button>
            <button class="timeframe-btn" data-tf="30d">30 Days</button>
            <button class="timeframe-btn" data-tf="90d">90 Days</button>
            <button class="timeframe-btn active" data-tf="all">All Time</button>
        </div>
        
        <div class="grid">
            <div class="card">
                <div class="card-header">
                    <div class="card-title">Stock Appearances</div>
                    <div class="search-box">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="11" cy="11" r="8"></circle>
                            <path d="m21 21-4.35-4.35"></path>
                        </svg>
                        <input type="text" id="stock-search" placeholder="Search stocks...">
                    </div>
                </div>
                <div class="table-container" id="stocks-table">
                    <!-- Populated by JS -->
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <div class="card-title">Top Industries</div>
                </div>
                <div class="industry-list" id="industry-list">
                    <!-- Populated by JS -->
                </div>
            </div>
        </div>
    </div>
    
    <script>
        const stocksData = {json.dumps(stocks_json)};
        const industriesData = {json.dumps(industries_json)};
        
        let currentTimeframe = 'all';
        let searchQuery = '';
        
        function renderStocks() {{
            const container = document.getElementById('stocks-table');
            let data = stocksData[currentTimeframe] || [];
            
            if (searchQuery) {{
                data = data.filter(s => 
                    s.stock.toLowerCase().includes(searchQuery.toLowerCase()) ||
                    (s.industry && s.industry.toLowerCase().includes(searchQuery.toLowerCase()))
                );
            }}
            
            if (data.length === 0) {{
                container.innerHTML = `
                    <div class="empty-state">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M3 3v18h18"></path>
                            <path d="m19 9-5 5-4-4-3 3"></path>
                        </svg>
                        <p>No stock data available for this timeframe</p>
                    </div>
                `;
                return;
            }}
            
            let html = `
                <table>
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Stock</th>
                            <th>Count</th>
                            <th>Last Seen</th>
                        </tr>
                    </thead>
                    <tbody>
            `;
            
            data.forEach((stock, idx) => {{
                const rankClass = idx < 3 ? `rank-${{idx + 1}}` : '';
                html += `
                    <tr>
                        <td class="rank ${{rankClass}}">${{idx + 1}}</td>
                        <td>
                            <div class="stock-name">${{stock.stock}}</div>
                            <div class="stock-industry">${{stock.industry || 'N/A'}}</div>
                        </td>
                        <td><span class="count-badge">${{stock.count}}</span></td>
                        <td class="date-cell">${{stock.last_seen}}</td>
                    </tr>
                `;
            }});
            
            html += '</tbody></table>';
            container.innerHTML = html;
        }}
        
        function renderIndustries() {{
            const container = document.getElementById('industry-list');
            const data = industriesData[currentTimeframe] || [];
            
            if (data.length === 0) {{
                container.innerHTML = `
                    <div class="empty-state">
                        <p>No industry data available</p>
                    </div>
                `;
                return;
            }}
            
            const maxCount = Math.max(...data.map(d => d[1]));
            
            let html = '';
            data.slice(0, 15).forEach(([industry, count]) => {{
                const pct = (count / maxCount) * 100;
                html += `
                    <div class="industry-item">
                        <div style="flex: 1;">
                            <div class="industry-name">${{industry}}</div>
                            <div class="industry-bar">
                                <div class="industry-bar-fill" style="width: ${{pct}}%;"></div>
                            </div>
                        </div>
                        <div class="industry-count">${{count}}</div>
                    </div>
                `;
            }});
            
            container.innerHTML = html;
        }}
        
        document.querySelectorAll('.timeframe-btn').forEach(btn => {{
            btn.addEventListener('click', () => {{
                document.querySelectorAll('.timeframe-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentTimeframe = btn.dataset.tf;
                renderStocks();
                renderIndustries();
            }});
        }});
        
        document.getElementById('stock-search').addEventListener('input', (e) => {{
            searchQuery = e.target.value;
            renderStocks();
        }});
        
        renderStocks();
        renderIndustries();
    </script>
</body>
</html>
'''
    return html


if __name__ == "__main__":
    generate_dashboard()
