#!/bin/bash

# 1. Login
echo "=== 1. LOGIN ==="
LOGIN_RESP=$(curl -s -X POST http://localhost:8181/api/forklift/login \
-H "Content-Type: application/json" \
-d '{
  "barcode": "JkE4Ttgog6R3vpir",
  "deviceId": "CHECK_DOLLY_ORDER"
}')

echo "$LOGIN_RESP" | jq .

TOKEN=$(echo "$LOGIN_RESP" | jq -r '.token')
echo "Token: $TOKEN"

# 2. Scan dolly
echo -e "\n=== 2. SCAN DOLLY ==="
SCAN_RESP=$(curl -s -X POST http://localhost:8181/api/forklift/scan \
-H "Content-Type: application/json" \
-H "Authorization: Bearer $TOKEN" \
-d '{
  "loading_session_id": "CHECK_ORDER_NO",
  "dolly_barcode": "1070863",
  "forklift_user": "CheckTest"
}')

echo "$SCAN_RESP" | jq .

# 3. Check database for DollyOrderNo
echo -e "\n=== 3. DATABASE CHECK ==="
sqlcmd -S 10.25.1.174,1433 -U sa -P '$SqL$Rv24' -d ControlTower -C -Q "
SELECT TOP 1 
    DollyNo, 
    DollyOrderNo, 
    VinNo, 
    ScanOrder,
    Status,
    LoadingSessionId
FROM DollySubmissionHold 
WHERE LoadingSessionId = 'CHECK_ORDER_NO'
ORDER BY CreatedAt DESC
" -s "," -W
