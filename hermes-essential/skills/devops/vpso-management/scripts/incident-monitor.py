#!/usr/bin/env python3
"""
Incident Monitor for VPSO - File-based reporting
Auto-detects incidents and saves to log file for dashboard
"""
import requests
import json
from datetime import datetime
import os

API_BASE = "http://localhost:8000"
API_KEY = "hermes-orchestrator-key-2026"
INCIDENT_LOG = "/usr/local/lib/hermes-orchestrator/incidents.json"
MAX_INCIDENTS = 100

def load_incidents():
    """Load existing incidents from file"""
    if os.path.exists(INCIDENT_LOG):
        try:
            with open(INCIDENT_LOG, 'r') as f:
                return json.load(f)
        except:
            pass
    return []

def save_incidents(incidents):
    """Save incidents to file (keep only last MAX_INCIDENTS)"""
    with open(INCIDENT_LOG, 'w') as f:
        json.dump(incidents[-MAX_INCIDENTS:], f, indent=2)

def get_health_status():
    """Get health status from API"""
    try:
        resp = requests.get(f"{API_BASE}/health", timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        print(f"Error getting health: {e}")
    return None

def report_incident(incident_data):
    """Save incident to log file"""
    incidents = load_incidents()
    
    incident = {
        "id": len(incidents) + 1,
        "timestamp": datetime.now().isoformat(),
        "title": incident_data["title"],
        "description": incident_data["description"],
        "severity": incident_data["severity"],
        "tags": incident_data.get("tags", ["#incident"]),
        "status": "open",
        "reported_by": "incident-monitor"
    }
    
    incidents.append(incident)
    save_incidents(incidents)
    print(f"✅ Incident #{incident['id']} saved: {incident['title']}")
    return True

def check_incidents(health_data):
    """Check for incidents based on health data"""
    incidents = []
    
    if not health_data:
        incidents.append({
            "title": "SKP API is UNREACHABLE",
            "description": "The SKP API at localhost:8000 is not responding.",
            "severity": "CRITICAL",
            "tags": ["#incident", "#alert", "#api-down"]
        })
        return incidents
    
    # Check overall status
    if health_data.get("status") != "running":
        incidents.append({
            "title": "API Status NOT RUNNING",
            "description": f"Status: {health_data.get('status')}",
            "severity": "HIGH",
            "tags": ["#incident", "#alert", "#api-unhealthy"]
        })
    
    # Check Redis
    redis = health_data.get("checks", {}).get("redis", {})
    if redis.get("status") != "healthy":
        incidents.append({
            "title": "Redis is UNHEALTHY",
            "description": redis.get("message", "N/A"),
            "severity": "CRITICAL",
            "tags": ["#incident", "#alert", "#redis"]
        })
    
    # Check Database
    db = health_data.get("checks", {}).get("database", {})
    if db.get("status") != "healthy":
        incidents.append({
            "title": "Database is UNHEALTHY",
            "description": db.get("message", "N/A"),
            "severity": "CRITICAL",
            "tags": ["#incident", "#alert", "#database"]
        })
    
    # Check Agents
    agents = health_data.get("checks", {}).get("agents", {})
    offline = agents.get("details", {}).get("offline_agents", 0)
    if offline > 0:
        incidents.append({
            "title": f"{offline} Agent(s) OFFLINE",
            "description": f"Total offline agents: {offline}. This may impact operations.",
            "severity": "HIGH",
            "tags": ["#incident", "#alert", "#agents-offline"]
        })
    
    # Check Queue
    queue = health_data.get("checks", {}).get("queue", {})
    pending = queue.get("details", {}).get("pending_tasks", 0)
    if pending > 50:
        incidents.append({
            "title": f"Queue Backup: {pending} pending tasks",
            "description": "Queue has too many pending tasks. This may indicate processing issues.",
            "severity": "MEDIUM",
            "tags": ["#incident", "#alert", "#queue"]
        })
    
    return incidents

def main():
    print(f"🔍 Incident Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    health = get_health_status()
    incidents = check_incidents(health)
    
    if incidents:
        print(f"\n🚨 Found {len(incidents)} incident(s):")
        for inc in incidents:
            print(f"  [{inc['severity']}] {inc['title']}")
            report_incident(inc)
        
        # Also try to POST to API (best effort)
        try:
            headers = {"X-API-Key": API_KEY}
            for inc in incidents:
                resp = requests.post(f"{API_BASE}/tasks", 
                    headers=headers,
                    json={
                        "task_type": "incident_report",
                        "description": f"[{inc['severity']}] {inc['title']}",
                        "tags": inc.get("tags", [])
                    },
                    timeout=2
                )
                if resp.status_code in [200, 201]:
                    print(f"  ✅ Also reported via API")
        except:
            pass  # Ignore API errors
    else:
        print("\n✅ No incidents detected. System healthy.")
    
    print("=" * 50)
    print(f"Done. Incident log: {INCIDENT_LOG}")

if __name__ == "__main__":
    main()
