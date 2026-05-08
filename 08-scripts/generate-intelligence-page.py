#!/usr/bin/env python3
"""
generate-intelligence-page.py v1 — Pentahelix Intelligence Platform (PRD-002)
Generate landing page data.upshalter.com dengan 10 insights terbaru dari SKP
Dijalankan setiap 30 menit via cron
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path

# Config
SKP_DB = "/root/.hermes/shared_knowledge_pool.db"
OUTPUT_HTML = "/var/www/data.upshalter.com/index.html"
OUTPUT_JSON = "/var/www/data.upshalter.com/data.json"

def get_skp_insights(limit=10):
    """Ambil insights terbaru dari SKP database"""
    insights = []
    
    if not Path(SKP_DB).exists():
        print(f"SKP database not found: {SKP_DB}")
        return insights
    
    try:
        conn = sqlite3.connect(SKP_DB)
        cursor = conn.cursor()
        
        # Ambil 10 entries terbaru
        cursor.execute("""
            SELECT key, value, source_agent_name, created_at 
            FROM memory_notes 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        
        for row in rows:
            key, value, source, created_at = row
            # Parse JSON value jika memungkinkan
            try:
                val_json = json.loads(value)
                summary = val_json.get('summary', val_json.get('content', str(val_json)[:200]))
            except:
                summary = str(value)[:200]
            
            insights.append({
                'key': key,
                'summary': summary,
                'source': source or 'unknown',
                'timestamp': created_at
            })
        
        conn.close()
    except Exception as e:
        print(f"Error reading SKP: {e}")
    
    return insights

def get_senator_status():
    """Cek status Senator (last update)"""
    senators = ['akademisi', 'bisnis', 'komunitas', 'pemerintah', 'media']
    status = []
    
    if not Path(SKP_DB).exists():
        return status
    
    try:
        conn = sqlite3.connect(SKP_DB)
        cursor = conn.cursor()
        
        for senator in senators:
            cursor.execute("""
                SELECT created_at, key 
                FROM memory_notes 
                WHERE key LIKE ? 
                ORDER BY created_at DESC 
                LIMIT 1
            """, (f"{senator}/%",))
            
            row = cursor.fetchone()
            if row:
                last_update, key = row
                status.append({
                    'name': f'senator-{senator}',
                    'last_update': last_update,
                    'key': key,
                    'active': True
                })
            else:
                status.append({
                    'name': f'senator-{senator}',
                    'last_update': None,
                    'key': None,
                    'active': False
                })
        
        conn.close()
    except Exception as e:
        print(f"Error checking senator status: {e}")
    
    return status

def generate_html(insights, senator_status):
    """Generate HTML page"""
    
    # Convert insights to JSON for JavaScript
    data = {
        'insights': insights,
        'senators': senator_status,
        'generated_at': datetime.now().isoformat()
    }
    
    # Save JSON data
    with open(OUTPUT_JSON, 'w') as f:
        json.dump(data, f, indent=2)
    
    # Generate HTML
    html = f"""<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pentahelix Intelligence Platform - Upshalter</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #0a0e27 0%, #1a1a2e 100%);
            color: #e0e0e0; 
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ 
            text-align: center; 
            padding: 40px 20px; 
            background: linear-gradient(135deg, #1a1a2e, #16213e); 
            border-radius: 15px; 
            margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(0, 212, 255, 0.1);
        }}
        .header h1 {{ 
            color: #00d4ff; 
            margin: 0; 
            font-size: 3em;
            text-shadow: 0 0 20px rgba(0, 212, 255, 0.5);
        }}
        .header p {{ color: #a0a0a0; margin: 10px 0; font-size: 1.2em; }}
        .section {{ 
            background: #1a1a2e; 
            border-radius: 12px; 
            padding: 30px; 
            margin-bottom: 25px;
            border-left: 5px solid #00d4ff;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
        }}
        .section h2 {{ 
            color: #00d4ff; 
            margin-bottom: 20px;
            font-size: 1.8em;
        }}
        .insight-card {{ 
            background: #16213e; 
            border-radius: 10px; 
            padding: 20px; 
            margin-bottom: 15px;
            border-left: 4px solid #00d4ff;
        }}
        .insight-meta {{ 
            color: #888; 
            font-size: 0.85em; 
            margin-bottom: 10px;
        }}
        .insight-summary {{ 
            line-height: 1.6;
        }}
        .senator-grid {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 15px; 
            margin-top: 20px;
        }}
        .senator-card {{ 
            background: #16213e; 
            border-radius: 8px; 
            padding: 15px;
            border: 1px solid #2a2a4e;
        }}
        .senator-active {{ border-color: #00ff88; }}
        .senator-inactive {{ border-color: #ff4444; }}
        .status-dot {{ 
            display: inline-block; 
            width: 10px; 
            height: 10px; 
            border-radius: 50%; 
            margin-right: 8px;
        }}
        .status-active {{ background: #00ff88; }}
        .status-inactive {{ background: #ff4444; }}
        .cta-section {{ 
            text-align: center; 
            padding: 40px;
            background: linear-gradient(135deg, #16213e, #1a1a2e);
            border-radius: 12px;
            margin: 30px 0;
        }}
        .cta-button {{ 
            display: inline-block;
            background: #00d4ff;
            color: #000;
            padding: 15px 40px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: bold;
            font-size: 1.1em;
            margin: 10px;
            transition: background 0.3s;
        }}
        .cta-button:hover {{ background: #00b8e6; }}
        .form-group {{ margin: 15px 0; }}
        .form-group input {{ 
            padding: 12px;
            border-radius: 6px;
            border: 1px solid #2a2a4e;
            background: #0a0e27;
            color: #e0e0e0;
            width: 300px;
            max-width: 100%;
        }}
        .loading {{ text-align: center; padding: 40px; color: #00d4ff; }}
        .timestamp {{ color: #888; font-size: 0.9em; text-align: center; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏛️ Pentahelix Intelligence</h1>
            <p>Real-time Market Intelligence dari 5 Senator</p>
            <p id="last-update">Terakhir diupdate: Loading...</p>
        </div>

        <div class="section">
            <h2>💡 10 Insights Terbaru</h2>
            <div id="insights-list">
                <div class="loading">Loading insights...</div>
            </div>
        </div>

        <div class="section">
            <h2>🤖 Status Senator</h2>
            <div id="senator-status" class="senator-grid">
                <div class="loading">Loading senator status...</div>
            </div>
        </div>

        <div class="cta-section">
            <h2>📊 Dapatkan Laporan Lengkap</h2>
            <p style="margin: 20px 0; font-size: 1.1em;">Berlangganan untuk mendapatkan analisis mendalam setiap hari</p>
            
            <form id="subscribe-form" onsubmit="subscribe(event)">
                <div class="form-group">
                    <input type="text" name="name" placeholder="Nama Lengkap" required>
                </div>
                <div class="form-group">
                    <input type="email" name="email" placeholder="Email" required>
                </div>
                <div class="form-group">
                    <input type="text" name="telegram" placeholder="Telegram Username (opsional)">
                </div>
                <button type="submit" class="cta-button">Daftar Sekarang</button>
            </form>
            
            <div style="margin-top: 30px;">
                <a href="#" class="cta-button">Starter - Rp 2jt/bln</a>
                <a href="#" class="cta-button">Pro - Rp 5jt/bln</a>
                <a href="#" class="cta-button">Enterprise - Rp 15jt/bln</a>
            </div>
        </div>
    </div>

    <script>
        const DATA_URL = 'data.json';
        
        async function loadData() {{
            try {{
                const response = await fetch(DATA_URL);
                const data = await response.json();
                updatePage(data);
            }} catch (error) {{
                console.error('Error loading data:', error);
            }}
        }}
        
        function updatePage(data) {{
            // Update timestamp
            document.getElementById('last-update').textContent = 
                'Terakhir diupdate: ' + new Date(data.generated_at).toLocaleString('id-ID');
            
            // Update insights
            const insightsList = document.getElementById('insights-list');
            if (data.insights && data.insights.length > 0) {{
                let html = '';
                data.insights.forEach(insight => {{
                    html += `
                        <div class="insight-card">
                            <div class="insight-meta">
                                📅 ${{insight.timestamp}} | 🤖 ${{insight.source}}
                            </div>
                            <div class="insight-summary">${{insight.summary}}</div>
                        </div>
                    `;
                }});
                insightsList.innerHTML = html;
            }} else {{
                insightsList.innerHTML = '<div class="loading">Belum ada insights tersedia</div>';
            }}
            
            // Update senator status
            const senatorDiv = document.getElementById('senator-status');
            if (data.senators && data.senators.length > 0) {{
                let html = '';
                data.senators.forEach(senator => {{
                    const statusClass = senator.active ? 'senator-active' : 'senator-inactive';
                    const statusDot = senator.active ? 'status-active' : 'status-inactive';
                    const statusText = senator.active ? 'Active' : 'Inactive';
                    const lastUpdate = senator.last_update ? new Date(senator.last_update).toLocaleString('id-ID') : 'Never';
                    
                    html += `
                        <div class="senator-card ${{statusClass}}">
                            <div>
                                <span class="status-dot ${{statusDot}}"></span>
                                <strong>${{senator.name}}</strong>
                            </div>
                            <div style="font-size: 0.85em; margin-top: 8px; color: #888;">
                                ${{lastUpdate}}
                            </div>
                        </div>
                    `;
                }});
                senatorDiv.innerHTML = html;
            }}
        }}
        
        async function subscribe(event) {{
            event.preventDefault();
            const formData = new FormData(event.target);
            const data = Object.fromEntries(formData.entries());
            
            alert('Terima kasih! Tim kami akan menghubungi Anda segera.\\n\\nData: ' + JSON.stringify(data, null, 2));
            event.target.reset();
        }}
        
        // Initial load
        loadData();
        // Auto refresh every 30 seconds
        setInterval(loadData, 30000);
    </script>
</body>
</html>
"""
    
    with open(OUTPUT_HTML, 'w') as f:
        f.write(html)
    
    return data

if __name__ == "__main__":
    print(f"[{datetime.now()}] Generating intelligence page...")
    
    # Get data from SKP
    insights = get_skp_insights(limit=10)
    senator_status = get_senator_status()
    
    print(f"Found {len(insights)} insights")
    print(f"Senator status: {len(senator_status)} checked")
    
    # Generate page
    data = generate_html(insights, senator_status)
    
    print(f"✅ Page generated: {OUTPUT_HTML}")
    print(f"✅ Data saved: {OUTPUT_JSON}")
    print(f"📊 Insights: {len(data['insights'])}")
    print(f"🤖 Senators: {len(data['senators'])}")
