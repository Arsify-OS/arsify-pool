#!/bin/bash
# Incident Detector for Hermes Orchestrator
# Auto-detects incidents and POSTs to SKP with #incident #alert tags

API_URL="http://localhost:8000"
API_KEY="key_49723cd1877dacb5"  # dashboard key
HEALTH_ENDPOINT="/health"
TASK_ENDPOINT="/tasks"

# Get health status
HEALTH_RESPONSE=$(curl -s "${API_URL}${HEALTH_ENDPOINT}")
HEALTH_STATUS=$(echo "$HEALTH_RESPONSE" | grep -o '"healthy":[^,}]*' | cut -d: -f2 | tr -d ' ')

# Check if any component is unhealthy
if [[ "$HEALTH_RESPONSE" == *"\"status\":\"unhealthy\""* ]]; then
    # Extract unhealthy components
    UNHEALTHY=$(echo "$HEALTH_RESPONSE" | grep -o '"status":"unhealthy"' -B 2 | grep '"[^"]*"' | head -1 | tr -d '"')
    
    # Post incident to SKP
    INCIDENT_DESC="Incident detected: $UNHEALTHY is unhealthy"
    
    curl -s -X POST "${API_URL}${TASK_ENDPOINT}" \
        -H "X-API-Key: ${API_KEY}" \
        -H "Content-Type: application/json" \
        -d "{
            \"task_type\": \"incident\",
            \"description\": \"${INCIDENT_DESC}\",
            \"priority\": \"critical\",
            \"tags\": [\"incident\", \"alert\", \"auto-detected\"],
            \"metadata\": {
                \"source\": \"incident-detector\",
                \"health_check\": ${HEALTH_RESPONSE}
            }
        }" > /dev/null
    
    echo "[$(date)] Incident posted: $INCIDENT_DESC"
else
    echo "[$(date)] All systems healthy"
fi
