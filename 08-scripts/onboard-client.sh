#!/bin/bash
# onboard-client.sh [CLIENT_NAME] [CLIENT_VPS_IP] [CLIENT_TELEGRAM_ID]
# Contoh: ./onboard-client.sh "PT ABC" "45.67.89.10" "123456789"

CLIENT_NAME="$1"
CLIENT_VPS="$2"
CLIENT_TG="$3"
LOG="/root/upshalter-logs/onboarding-${CLIENT_NAME// /-}-$(date +%Y%m%d).log"

echo "=== ONBOARDING: $CLIENT_NAME ===" | tee $LOG
echo "Tanggal: $(date)" | tee -a $LOG

# Day 1 Tasks
echo "--- DAY 1: Infrastructure Setup ---" | tee -a $LOG

# 1.1 Test SSH ke VPS klien
echo "[ ] 1.1 SSH connectivity to $CLIENT_VPS"
ssh root@$CLIENT_VPS "echo 'SSH OK'" 2>/dev/null && \
    echo "✅ SSH connected" | tee -a $LOG || \
    echo "❌ SSH failed — manual intervention needed" | tee -a $LOG

# 1.2 Install dependencies
echo "[ ] 1.2 Install Hermes Agent"
ssh root@$CLIENT_VPS << 'REMOTE'
# Install Hermes
curl -fsSL https://install.hermesagent.ai/install.sh | bash 2>/dev/null || \
  apt-get update && apt-get install -y hermes-agent 2>/dev/null || \
  echo "Manual install needed"

# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh 2>/dev/null || true
systemctl start ollama 2>/dev/null || true
REMOTE

# 1.3 Setup 3-zona security
echo "[ ] 1.3 Configure 3-zona security"
# ... implementation

# Day 2 Tasks
echo "--- DAY 2: Agent Configuration ---" | tee -a $LOG

# 2.1 Create SOUL.md for main agent
cat > /tmp/client-soul.md << SOUL
# SOUL — AI Assistant untuk $CLIENT_NAME

## Identitas
Kamu adalah AI assistant untuk $CLIENT_NAME.
Kamu membantu tim mereka dengan riset, analisa, dan eksekusi tugas sehari-hari.

## Aturan Utama
- SELALU lapor ke manusia sebelum mengeksekusi task berisiko tinggi
- TIDAK PERNAH bagikan informasi sensitif bisnis ke luar
- JIKA ragu, tanya user untuk klarifikasi

## Konteks Bisnis
[DI-FILL saat onboarding oleh tim Upshalter]
SOUL

echo "[ ] 2.2 Seed SKP with client context"
echo "[ ] 2.3 Setup Telegram bot"
echo "[ ] 2.4 Test automation"

# Day 3 Tasks
echo "--- DAY 3: Training & Handover ---" | tee -a $LOG
echo "[ ] 3.1 2-hour training session"
echo "[ ] 3.2 Test daily brief delivery"
echo "[ ] 3.3 Handover documentation"

echo "=== ONBOARDING CHECKLIST READY ===" | tee -a $LOG
