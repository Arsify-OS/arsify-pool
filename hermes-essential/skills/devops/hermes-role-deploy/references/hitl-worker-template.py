#!/usr/bin/env python3
"""
HITL Worker Template (Human-in-the-Loop)
Integrasi dengan Hermes Agent untuk approval workflow

Usage:
  - Gunakan sebagai worker di Worker Pool yang butuh human approval
  - Atau sebagai standalone script yang dipanggil Docker container
  
Dependencies:
  - requests (pip install requests)
  - Hermes Agent dengan send_message capability
"""

import requests
import json
import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime

# === KONFIGURASI HITL ===
HERMES_API = "http://localhost:8645"  # Hermes Agent gateway
TELEGRAM_TOKEN = "8673939697:AAEFPs2G-xhbTl8eJ7hnPk5ezc4PZeLhSrU"
TELEGRAM_CHAT_ID = "5807834405"

# Timeout menunggu approval (detik)
APPROVAL_TIMEOUT = 3600  # 1 jam

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - HITL - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HITLWorker:
    """Human-in-the-Loop Worker untuk approval workflow"""
    
    def __init__(self, task_name: str):
        self.task_name = task_name
        self.session = requests.Session()
    
    def request_approval(self, data: Dict[str, Any], context: str = "") -> Optional[Dict]:
        """
        Minta approval dari human via Telegram
        
        Returns:
            - Dict dengan hasil jika approved
            - None jika rejected/timeout
        """
        task_id = f"{self.task_name}_{int(time.time())}"
        
        # Format pesan approval
        message = self._format_approval_message(task_id, data, context)
        
        # Kirim ke Telegram via Hermes Agent atau langsung
        sent = self._send_telegram(message)
        
        if not sent:
            logger.error("Gagal mengirim approval request")
            return None
        
        logger.info(f"Approval request sent: {task_id}")
        logger.info(f"Menunggu approval (timeout: {APPROVAL_TIMEOUT}s)...")
        
        # Poll untuk response (dalam implementasi nyata: gunakan webhook/callback)
        # Template ini pakai polling sederhana
        return self._wait_for_approval(task_id)
    
    def _format_approval_message(self, task_id: str, data: Dict, context: str) -> str:
        """Format pesan approval untuk human"""
        lines = [
            f"🔔 **APPROVAL REQUEST**",
            f"",
            f"Task ID: `{task_id}`",
            f"Worker: `{self.task_name}`",
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        ]
        
        if context:
            lines.append(f"")
            lines.append(f"Context: {context}")
        
        lines.extend([
            f"",
            f"**Data to approve:**",
            f"```json",
            json.dumps(data, indent=2)[:500],  # Truncate if too long
            f"```",
            f"",
            f"Reply with: `/approve {task_id}` or `/reject {task_id}`"
        ])
        
        return "\n".join(lines)
    
    def _send_telegram(self, message: str) -> bool:
        """Kirim pesan ke Telegram (via Hermes send_message atau direct API)"""
        try:
            # Opsi 1: Via Hermes Agent API (jika ada endpoint)
            # response = self.session.post(
            #     f"{HERMES_API}/api/send_message",
            #     json={"target": f"telegram:{TELEGRAM_CHAT_ID}", "message": message}
            # )
            
            # Opsi 2: Direct Telegram API (uncomment jika perlu)
            # response = self.session.post(
            #     f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            #     json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
            # )
            # return response.status_code == 200
            
            # Opsi 3: Simpan ke file untuk diproses Hermes Agent manual
            with open(f"/tmp/hitl_{int(time.time())}.msg", "w") as f:
                f.write(message)
            
            logger.info("Message saved to /tmp/ for Hermes Agent to send")
            return True
            
        except Exception as e:
            logger.error(f"Send Telegram error: {e}")
            return False
    
    def _wait_for_approval(self, task_id: str) -> Optional[Dict]:
        """
        Poll untuk approval response
        
        NOTE: Ini implementasi sederhana. Di production, gunakan:
        - Webhook endpoint
        - Redis pub/sub
        - Database polling dengan status field
        """
        start_time = time.time()
        poll_interval = 10  # Cek setiap 10 detik
        
        while (time.time() - start_time) < APPROVAL_TIMEOUT:
            try:
                # Cek file status (implementasi sederhana)
                status_file = f"/tmp/hitl_{task_id}.status"
                try:
                    with open(status_file, "r") as f:
                        status = f.read().strip()
                    
                    if status == "approved":
                        logger.info(f"Task {task_id} APPROVED")
                        # Return processed data
                        return {"task_id": task_id, "status": "approved", "timestamp": time.time()}
                    
                    elif status == "rejected":
                        logger.info(f"Task {task_id} REJECTED")
                        return None
                        
                except FileNotFoundError:
                    pass  # Belum ada response
                
                time.sleep(poll_interval)
                
            except KeyboardInterrupt:
                logger.info("Polling interrupted")
                break
            except Exception as e:
                logger.error(f"Polling error: {e}")
                time.sleep(poll_interval)
        
        logger.warning(f"Approval timeout for task {task_id}")
        return None

# === CONTOH PENGGUNAAN ===

def example_usage():
    """Contoh penggunaan HITL Worker"""
    
    worker = HITLWorker("finance-transaction-validator")
    
    # Data yang butuh approval
    transaction_data = {
        "amount": 15000,
        "currency": "USD",
        "from": "account_A",
        "to": "account_B",
        "description": "Large fund transfer"
    }
    
    # Minta approval
    result = worker.request_approval(
        data=transaction_data,
        context="Large transaction exceeds threshold $10,000"
    )
    
    if result:
        print(f"✅ Transaction approved! Proceeding...")
        # Lanjutkan proses
    else:
        print(f"❌ Transaction rejected or timeout. Aborting...")
        # Batalkan proses

if __name__ == "__main__":
    logger.info("HITL Worker Template started")
    # example_usage()
    print("HITL Worker template loaded. See example_usage() for details.")
