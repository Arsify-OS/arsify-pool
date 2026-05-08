#!/usr/bin/env python3
"""
Hermes Worker Pool Daemon Template
Role: Internal Worker Pool (Monolith)
Template untuk agent dengan 16 workers dalam 1 proses

Usage:
  - Copy file ini ke /root/hermes-<nama>/daemon.py
  - Edit konfigurasi AGENT_NAME, SOURCES, OUTPUT_TARGET
  - Jalankan via systemd service
"""

import threading
import time
import logging
import sqlite3
import queue
from datetime import datetime
from typing import List, Dict, Any

# === KONFIGURASI AGENT ===
AGENT_NAME = "template"  # Ganti dengan nama agent
AGENT_VERSION = "1.0"
WORKER_COUNT = 16  # Jumlah workers (Layer 0-4)

# Sources (ganti dengan sumber data agent Anda)
SOURCES = [
    "https://api.example.com/data1",
    "https://api.example.com/data2",
    "https://rss.example.com/feed",
]

# Output target
OUTPUT_TARGET = {
    "skp_db": "/root/.hermes/shared_knowledge_pool.db",
    "telegram": True,
    "telegram_token": "8673939697:AAEFPs2G-xhbTl8eJ7hnPk5ezc4PZeLhSrU",
    "telegram_chat_id": "5807834405",
}

# === SETUP LOGGING ===
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'/root/hermes-{AGENT_NAME}/data/daemon.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(f'Hermes{AGENT_NAME.capitalize()}')

# === WORKER CLASSES (Layer 0-4) ===

class GapDetectionWorker(threading.Thread):
    """Layer 0: Deteksi gap pengetahuan"""
    def __init__(self, task_queue: queue.Queue):
        super().__init__()
        self.task_queue = task_queue
        self.daemon = True
    
    def run(self):
        logger.info("Layer 0: Gap Detection started")
        while True:
            try:
                # TODO: Implement gap detection logic
                gaps = self.detect_gaps()
                for gap in gaps:
                    self.task_queue.put(("collect", gap))
                time.sleep(300)  # Poll every 5 minutes
            except Exception as e:
                logger.error(f"Gap Detection error: {e}")
                time.sleep(60)
    
    def detect_gaps(self) -> List[Dict]:
        # Template: Cek database untuk topik yang belum tercrawl
        return []

class CollectionWorker(threading.Thread):
    """Layer 1: Koleksi data dari sources"""
    def __init__(self, task_queue: queue.Queue, result_queue: queue.Queue, source: str):
        super().__init__()
        self.task_queue = task_queue
        self.result_queue = result_queue
        self.source = source
        self.daemon = True
    
    def run(self):
        logger.info(f"Layer 1: Collection started for {self.source}")
        while True:
            try:
                task = self.task_queue.get(timeout=10)
                if task[0] == "collect":
                    data = self.collect_data(task[1])
                    self.result_queue.put(("process", data))
                self.task_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Collection error ({self.source}): {e}")
    
    def collect_data(self, topic: Dict) -> Dict:
        # TODO: Implement collection logic per source
        return {"topic": topic, "content": "", "source": self.source}

class ProcessingWorker(threading.Thread):
    """Layer 2: Pemrosesan data"""
    def __init__(self, result_queue: queue.Queue, output_queue: queue.Queue):
        super().__init__()
        self.result_queue = result_queue
        self.output_queue = output_queue
        self.daemon = True
    
    def run(self):
        logger.info("Layer 2: Processing started")
        while True:
            try:
                task = self.result_queue.get(timeout=10)
                if task[0] == "process":
                    processed = self.process_data(task[1])
                    self.output_queue.put(("distribute", processed))
                self.result_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Processing error: {e}")
    
    def process_data(self, data: Dict) -> Dict:
        # TODO: Implement processing (clean, parse, extract)
        return data

class DistributionWorker(threading.Thread):
    """Layer 3: Distribusi ke target (SKP, Telegram)"""
    def __init__(self, output_queue: queue.Queue, feedback_queue: queue.Queue):
        super().__init__()
        self.output_queue = output_queue
        self.feedback_queue = feedback_queue
        self.daemon = True
    
    def run(self):
        logger.info("Layer 3: Distribution started")
        while True:
            try:
                task = self.output_queue.get(timeout=10)
                if task[0] == "distribute":
                    self.distribute(task[1])
                    self.feedback_queue.put(("feedback", task[1]))
                self.output_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Distribution error: {e}")
    
    def distribute(self, data: Dict):
        # TODO: Save to SKP DB, send Telegram alert
        logger.info(f"Distributing: {data.get('topic', {}).get('title', 'Unknown')}")
        
        # Save to SKP
        if OUTPUT_TARGET.get("skp_db"):
            self.save_to_skp(data)
        
        # Send Telegram
        if OUTPUT_TARGET.get("telegram"):
            self.send_telegram(data)
    
    def save_to_skp(self, data: Dict):
        # Template: Save to Shared Knowledge Pool
        try:
            conn = sqlite3.connect(OUTPUT_TARGET["skp_db"])
            cursor = conn.cursor()
            # TODO: Insert to fact_checks or relevant table
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"SKP save error: {e}")
    
    def send_telegram(self, data: Dict):
        # Template: Send Telegram notification
        # TODO: Implement via requests or subprocess
        pass

class FeedbackWorker(threading.Thread):
    """Layer 4: Feedback loop"""
    def __init__(self, feedback_queue: queue.Queue):
        super().__init__()
        self.feedback_queue = feedback_queue
        self.daemon = True
    
    def run(self):
        logger.info("Layer 4: Feedback started")
        while True:
            try:
                task = self.feedback_queue.get(timeout=10)
                if task[0] == "feedback":
                    self.process_feedback(task[1])
                self.feedback_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Feedback error: {e}")
    
    def process_feedback(self, data: Dict):
        # TODO: Update crawl_cache, adjust priorities
        logger.info(f"Feedback processed for: {data}")

# === MAIN DAEMON ===

class WorkerPoolDaemon:
    def __init__(self):
        self.task_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.output_queue = queue.Queue()
        self.feedback_queue = queue.Queue()
        self.workers = []
    
    def start(self):
        logger.info(f"╔══════════════════════════════════════════════╗")
        logger.info(f"║  HERMES {AGENT_NAME.upper()} RESEARCH AGENT v{AGENT_VERSION}  ║")
        logger.info(f"║  Worker Pool Mode - {WORKER_COUNT} Workers         ║")
        logger.info(f"╚══════════════════════════════════════════════╝")
        
        # Layer 0: Gap Detection (1 worker)
        gap_worker = GapDetectionWorker(self.task_queue)
        gap_worker.start()
        self.workers.append(gap_worker)
        
        # Layer 1: Collection (4 workers, satu per source)
        for i, source in enumerate(SOURCES[:4]):
            worker = CollectionWorker(self.task_queue, self.result_queue, source)
            worker.start()
            self.workers.append(worker)
        
        # Layer 2: Processing (5 workers)
        for i in range(5):
            worker = ProcessingWorker(self.result_queue, self.output_queue)
            worker.start()
            self.workers.append(worker)
        
        # Layer 3: Distribution (3 workers)
        for i in range(3):
            worker = DistributionWorker(self.output_queue, self.feedback_queue)
            worker.start()
            self.workers.append(worker)
        
        # Layer 4: Feedback (3 workers)
        for i in range(3):
            worker = FeedbackWorker(self.feedback_queue)
            worker.start()
            self.workers.append(worker)
        
        logger.info(f"✅ All {len(self.workers)} workers started")
        
        # Keep main thread alive
        try:
            while True:
                time.sleep(60)
                self.health_check()
        except KeyboardInterrupt:
            logger.info("Daemon stopped by user")
    
    def health_check(self):
        alive = sum(1 for w in self.workers if w.is_alive())
        logger.info(f"Health check: {alive}/{len(self.workers)} workers alive")

if __name__ == "__main__":
    # Create data directory if not exists
    import os
    os.makedirs(f'/root/hermes-{AGENT_NAME}/data', exist_ok=True)
    
    daemon = WorkerPoolDaemon()
    daemon.start()
