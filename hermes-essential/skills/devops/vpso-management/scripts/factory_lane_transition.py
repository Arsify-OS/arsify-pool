#!/usr/bin/env python3
"""
Factory Lane Transition Handler
Mengelola transisi otomatis: Builder -> Sandbox -> Flowforce -> Infrastructure
"""
import sys
import os
import json
import requests
from datetime import datetime

# Konfigurasi
ORCHESTRATOR_URL = "http://localhost:8000"
API_KEY = "hma_lAgtJf6YdFpjr4BQF3NwmJ1HjQ14a8tHvL-MT8t6Ktc"  # factory-lane-test

HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def get_tasks_by_tag(tag):
    """Ambil task berdasarkan tag"""
    try:
        resp = requests.get(f"{ORCHESTRATOR_URL}/tasks?tags={tag}", headers=HEADERS)
        if resp.status_code == 200:
            return resp.json().get('tasks', [])
    except Exception as e:
        print(f"❌ Error fetching tasks with tag #{tag}: {e}")
    return []

def update_task_status(task_id, new_status, new_tags=None, note=None):
    """Update status task dan tambahkan tag baru"""
    payload = {"status": new_status}
    if new_tags:
        payload["tags"] = new_tags
    if note:
        payload["note"] = note
    
    try:
        resp = requests.put(f"{ORCHESTRATOR_URL}/tasks/{task_id}", 
                           headers=HEADERS, json=payload)
        return resp.status_code == 200
    except Exception as e:
        print(f"❌ Error updating task {task_id}: {e}")
    return False

def process_build_to_test():
    """Builder selesai -> Pindah ke Sandbox (Testing)"""
    tasks = get_tasks_by_tag("build")
    for task in tasks:
        if task.get('status') == 'completed':
            task_id = task.get('task_id')
            if not task_id:
                continue
            new_tags = ["test", "sandbox"]
            if update_task_status(task_id, "pending", new_tags=new_tags, note="Auto-transition: Build -> Test"):
                print(f"✅ [{datetime.now()}] Task {task_id} dipindah ke Sandbox (Testing)")
            else:
                print(f"❌ Gagal memindah task {task_id}")

def process_test_to_deploy():
    """Sandbox selesai -> Pindah ke Flowforce (Deployment)"""
    tasks = get_tasks_by_tag("test")
    for task in tasks:
        if task.get('status') == 'completed':
            task_id = task.get('task_id')
            if not task_id:
                continue
            new_tags = ["deploy", "flowforce"]
            if update_task_status(task_id, "pending", new_tags=new_tags, note="Auto-transition: Test -> Deploy"):
                print(f"✅ [{datetime.now()}] Task {task_id} dipindah ke Flowforce (Deployment)")
            else:
                print(f"❌ Gagal memindah task {task_id}")

def process_deploy_to_infra():
    """Flowforce selesai -> Pindah ke Infrastructure (Production)"""
    tasks = get_tasks_by_tag("deploy")
    for task in tasks:
        if task.get('status') == 'completed':
            task_id = task.get('task_id')
            if not task_id:
                continue
            new_tags = ["infra", "production"]
            if update_task_status(task_id, "pending", new_tags=new_tags, note="Auto-transition: Deploy -> Infra"):
                print(f"✅ [{datetime.now()}] Task {task_id} dipindah ke Infrastructure (Production)")
            else:
                print(f"❌ Gagal memindah task {task_id}")

def main():
    print(f"🏭 Factory Lane Transition Check: {datetime.now()}")
    print("=" * 50)
    
    process_build_to_test()
    process_test_to_deploy()
    process_deploy_to_infra()
    
    print("=" * 50)
    print("✅ Selesai.")

if __name__ == "__main__":
    main()