#!/bin/bash

# KARMAŞIK GRUP TOPLAMA TEST
# Manuel curl komutları ile API testi

BASE_URL="http://localhost:8181/api"

echo "=========================================="
echo "  GRUP TOPLAMA API TEST"
echo "=========================================="
echo ""

# STEP 1: Login
echo "[1] Login..."
LOGIN_DATA='{"operatorBarcode":"TESTUSER001","operatorName":"Test Operatör","deviceId":"test-device-001"}'
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/forklift/login" \
  -H "Content-Type: application/json" \
  -d "$LOGIN_DATA")

echo "$LOGIN_RESPONSE" | python3 -m json.tool
echo ""

TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('sessionToken', ''))" 2>/dev/null)

if [ -z "$TOKEN" ]; then
  echo "ERROR: Token alınamadı!"
  exit 1
fi

echo "✅ Token alındı: ${TOKEN:0:30}..."
echo ""

# STEP 2: Grupları listele
echo "[2] Manuel Toplama Gruplarını Listele..."
GROUPS=$(curl -s -X GET "$BASE_URL/manual-collection/groups" \
  -H "Authorization: Bearer $TOKEN")

echo "$GROUPS" | python3 -m json.tool | head -n 100
echo ""

GROUP_ID=$(echo "$GROUPS" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d[0]['group_id'] if len(d) > 0 else '')")
GROUP_NAME=$(echo "$GROUPS" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d[0]['group_name'] if len(d) > 0 else '')")

echo "✅ Seçilen Grup: $GROUP_NAME (ID: $GROUP_ID)"
echo ""

# STEP 3: İlk EOL dolly'lerini al
echo "[3] İlk EOL'deki Dolly'leri Listele..."
FIRST_EOL_ID=$(echo "$GROUPS" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d[0]['eols'][0]['eol_id'] if len(d) > 0 and len(d[0]['eols']) > 0 else '')")
FIRST_EOL_NAME=$(echo "$GROUPS" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d[0]['eols'][0]['eol_name'] if len(d) > 0 and len(d[0]['eols']) > 0 else '')")

EOL1_DOLLYS=$(curl -s -X GET "$BASE_URL/manual-collection/groups/$GROUP_ID/eols/$FIRST_EOL_ID" \
  -H "Authorization: Bearer $TOKEN")

echo "$EOL1_DOLLYS" | python3 -m json.tool | head -n 50
echo ""

DOLLY_1=$(echo "$EOL1_DOLLYS" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['dollys'][0]['dolly_no'] if len(d.get('dollys', [])) > 0 else '')")
DOLLY_2=$(echo "$EOL1_DOLLYS" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['dollys'][1]['dolly_no'] if len(d.get('dollys', [])) > 1 else '')")
DOLLY_3=$(echo "$EOL1_DOLLYS" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['dollys'][2]['dolly_no'] if len(d.get('dollys', [])) > 2 else '')")

echo "✅ İlk EOL: $FIRST_EOL_NAME - Seçilen: $DOLLY_1, $DOLLY_2, $DOLLY_3"
echo ""

# STEP 4: İkinci EOL dolly'lerini al (varsa)
SECOND_EOL_ID=$(echo "$GROUPS" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d[0]['eols'][1]['eol_id'] if len(d) > 0 and len(d[0]['eols']) > 1 else '')")
SECOND_EOL_NAME=$(echo "$GROUPS" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d[0]['eols'][1]['eol_name'] if len(d) > 0 and len(d[0]['eols']) > 1 else '')")

DOLLY_4=""
DOLLY_5=""

if [ -n "$SECOND_EOL_ID" ]; then
  echo "[4] İkinci EOL'deki Dolly'leri Listele..."
  
  EOL2_DOLLYS=$(curl -s -X GET "$BASE_URL/manual-collection/groups/$GROUP_ID/eols/$SECOND_EOL_ID" \
    -H "Authorization: Bearer $TOKEN")
  
  echo "$EOL2_DOLLYS" | python3 -m json.tool | head -n 50
  echo ""
  
  DOLLY_4=$(echo "$EOL2_DOLLYS" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['dollys'][0]['dolly_no'] if len(d.get('dollys', [])) > 0 else '')")
  DOLLY_5=$(echo "$EOL2_DOLLYS" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['dollys'][1]['dolly_no'] if len(d.get('dollys', [])) > 1 else '')")
  
  echo "✅ İkinci EOL: $SECOND_EOL_NAME - Seçilen: $DOLLY_4, $DOLLY_5"
  echo ""
fi

# STEP 5: KARMAŞIK TOPLAMA - Scan başlat
SESSION_ID="KOMPLEKS_$(date +%Y%m%d_%H%M%S)"

echo "=========================================="
echo "  KARMAŞIK TOPLAMA BAŞLIYOR"
echo "  Session: $SESSION_ID"
echo "=========================================="
echo ""

# Scan 1
echo "[SCAN-1] $FIRST_EOL_NAME - Dolly: $DOLLY_1"
SCAN_DATA='{"dollyNo":"'$DOLLY_1'","loadingSessionId":"'$SESSION_ID'"}'
SCAN1=$(curl -s -X POST "$BASE_URL/forklift/scan" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$SCAN_DATA")
echo "$SCAN1" | python3 -m json.tool
echo ""

# Scan 2
echo "[SCAN-2] $FIRST_EOL_NAME - Dolly: $DOLLY_2"
SCAN_DATA='{"dollyNo":"'$DOLLY_2'","loadingSessionId":"'$SESSION_ID'"}'
SCAN2=$(curl -s -X POST "$BASE_URL/forklift/scan" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$SCAN_DATA")
echo "$SCAN2" | python3 -m json.tool
echo ""

# Scan 3
echo "[SCAN-3] $FIRST_EOL_NAME - Dolly: $DOLLY_3"
SCAN_DATA='{"dollyNo":"'$DOLLY_3'","loadingSessionId":"'$SESSION_ID'"}'
SCAN3=$(curl -s -X POST "$BASE_URL/forklift/scan" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$SCAN_DATA")
echo "$SCAN3" | python3 -m json.tool
echo ""

# İkinci EOL'den scan (varsa)
if [ -n "$DOLLY_4" ] && [ -n "$DOLLY_5" ]; then
  echo "==========================================  "
  echo "⚠️  ÖNEMLİ: Submit etmeden FARKLI EOL'e geçiliyor!"
  echo "=========================================="
  echo ""
  
  # Scan 4
  echo "[SCAN-4] $SECOND_EOL_NAME - Dolly: $DOLLY_4"
  SCAN_DATA='{"dollyNo":"'$DOLLY_4'","loadingSessionId":"'$SESSION_ID'"}'
  SCAN4=$(curl -s -X POST "$BASE_URL/forklift/scan" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$SCAN_DATA")
  echo "$SCAN4" | python3 -m json.tool
  echo ""
  
  # Scan 5
  echo "[SCAN-5] $SECOND_EOL_NAME - Dolly: $DOLLY_5"
  SCAN_DATA='{"dollyNo":"'$DOLLY_5'","loadingSessionId":"'$SESSION_ID'"}'
  SCAN5=$(curl -s -X POST "$BASE_URL/forklift/scan" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$SCAN_DATA")
  echo "$SCAN5" | python3 -m json.tool
  echo ""
fi

# STEP 6: Session durumu
echo "[6] Session Durumunu Kontrol Et..."
SESSIONS=$(curl -s -X GET "$BASE_URL/forklift/sessions?status=scanned" \
  -H "Authorization: Bearer $TOKEN")
echo "$SESSIONS" | python3 -m json.tool
echo ""

# STEP 7: Complete Loading
echo "[7] Complete Loading - Yükleme Tamamla..."
COMPLETE_DATA='{"loadingSessionId":"'$SESSION_ID'"}'
COMPLETE=$(curl -s -X POST "$BASE_URL/forklift/complete-loading" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$COMPLETE_DATA")
echo "$COMPLETE" | python3 -m json.tool
echo ""

# Sonuç
echo "=========================================="
echo "✅ TEST TAMAMLANDI"
echo "=========================================="
echo ""
echo "Özet:"
echo "  - Grup: $GROUP_NAME"
echo "  - Session: $SESSION_ID"
echo "  - $FIRST_EOL_NAME: 3 dolly"
if [ -n "$SECOND_EOL_NAME" ]; then
  echo "  - $SECOND_EOL_NAME: 2 dolly"
  echo "  - TOPLAM: 5 dolly (KARMAŞIK TOPLAMA ✅)"
else
  echo "  - TOPLAM: 3 dolly"
fi
echo ""
