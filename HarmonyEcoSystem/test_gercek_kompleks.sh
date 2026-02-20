#!/bin/bash
# GERÇEK OPERATÖR ile KARMAŞIK TOPLAMA TEST

BASE_URL="http://localhost:8181/api"
OPERATOR_BARCODE="JkE4Ttgog6R3vpir"

echo "=========================================="
echo "  KARMAŞIK GRUP TOPLAMA TEST"
echo "  Operatör: $OPERATOR_BARCODE"
echo "=========================================="
echo ""

# Login
echo "1️⃣  Login..."
LOGIN=$(curl -s -X POST "$BASE_URL/forklift/login" \
  -H "Content-Type: application/json" \
  -d "{\"operatorBarcode\":\"$OPERATOR_BARCODE\",\"operatorName\":\"Test Operatör\",\"deviceId\":\"test-kompleks\"}")

echo "$LOGIN" | python3 -m json.tool
TOKEN=$(echo "$LOGIN" | python3 -c "import sys, json; print(json.load(sys.stdin).get('sessionToken', ''))")
echo "✅ Token: ${TOKEN:0:30}..."
echo ""

# Grupları listele
echo "2️⃣  Grupları Listele..."
GROUPS=$(curl -s "$BASE_URL/manual-collection/groups" -H "Authorization: Bearer $TOKEN")
echo "$GROUPS" | python3 -m json.tool
echo ""

# Grup seç
GROUP_ID=$(echo "$GROUPS" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d[0]['group_id'])")
GROUP_NAME=$(echo "$GROUPS" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d[0]['group_name'])")
EOL1_ID=$(echo "$GROUPS" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d[0]['eols'][0]['eol_id'])")
EOL1_NAME=$(echo "$GROUPS" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d[0]['eols'][0]['eol_name'])")

echo "✅ Seçilen: $GROUP_NAME (ID: $GROUP_ID)"
echo "   İlk EOL: $EOL1_NAME (ID: $EOL1_ID)"
echo ""

# İlk EOL dolly'leri
echo "3️⃣  $EOL1_NAME dolly'lerini al..."
EOL1_DOLLYS=$(curl -s "$BASE_URL/manual-collection/groups/$GROUP_ID/eols/$EOL1_ID" -H "Authorization: Bearer $TOKEN")
echo "$EOL1_DOLLYS" | python3 -m json.tool | head -n 80
echo ""

# İlk 3 dolly seç
D1=$(echo "$EOL1_DOLLYS" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['dollys'][0]['dolly_no'] if len(d.get('dollys',[])) > 0 else '')")
D2=$(echo "$EOL1_DOLLYS" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['dollys'][1]['dolly_no'] if len(d.get('dollys',[])) > 1 else '')")
D3=$(echo "$EOL1_DOLLYS" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['dollys'][2]['dolly_no'] if len(d.get('dollys',[])) > 2 else '')")

echo "Seçilen Dolly'ler: $D1, $D2, $D3"
echo ""

# İkinci EOL var mı kontrol et
EOL2_ID=$(echo "$GROUPS" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d[0]['eols'][1]['eol_id']) if len(d[0]['eols']) > 1 else print('')" 2>/dev/null)
EOL2_NAME=$(echo "$GROUPS" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d[0]['eols'][1]['eol_name']) if len(d[0]['eols']) > 1 else print('')" 2>/dev/null)

D4=""
D5=""

if [ -n "$EOL2_ID" ]; then
  echo "4️⃣  $EOL2_NAME dolly'lerini al..."
  EOL2_DOLLYS=$(curl -s "$BASE_URL/manual-collection/groups/$GROUP_ID/eols/$EOL2_ID" -H "Authorization: Bearer $TOKEN")
  echo "$EOL2_DOLLYS" | python3 -m json.tool | head -n 60
  echo ""
  
  D4=$(echo "$EOL2_DOLLYS" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['dollys'][0]['dolly_no'] if len(d.get('dollys',[])) > 0 else '')")
  D5=$(echo "$EOL2_DOLLYS" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['dollys'][1]['dolly_no'] if len(d.get('dollys',[])) > 1 else '')")
  
  echo "Seçilen Dolly'ler: $D4, $D5"
  echo ""
fi

# KARMAŞIK TOPLAMA BAŞLAT
SESSION_ID="KOMPLEKS_TEST_$(date +%Y%m%d_%H%M%S)"
echo "=========================================="
echo "  KARMAŞIK TOPLAMA BAŞLAT"
echo "  Session: $SESSION_ID"
echo "=========================================="
echo ""

# Scan 1
if [ -n "$D1" ]; then
  echo "🔵 SCAN #1: $EOL1_NAME - Dolly $D1"
  S1=$(curl -s -X POST "$BASE_URL/forklift/scan" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d "{\"dollyNo\":\"$D1\",\"loadingSessionId\":\"$SESSION_ID\"}")
  echo "$S1" | python3 -m json.tool
  echo ""
fi

# Scan 2
if [ -n "$D2" ]; then
  echo "🔵 SCAN #2: $EOL1_NAME - Dolly $D2"
  S2=$(curl -s -X POST "$BASE_URL/forklift/scan" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d "{\"dollyNo\":\"$D2\",\"loadingSessionId\":\"$SESSION_ID\"}")
  echo "$S2" | python3 -m json.tool
  echo ""
fi

# Scan 3
if [ -n "$D3" ]; then
  echo "🔵 SCAN #3: $EOL1_NAME - Dolly $D3"
  S3=$(curl -s -X POST "$BASE_URL/forklift/scan" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d "{\"dollyNo\":\"$D3\",\"loadingSessionId\":\"$SESSION_ID\"}")
  echo "$S3" | python3 -m json.tool
  echo ""
fi

# Submit ETMEDEN ikinci EOL'den scan
if [ -n "$D4" ] && [ -n "$D5" ]; then
  echo "⚠️  ÖNEMLİ: Submit etmeden İKİNCİ EOL'e geçiliyor!"
  echo ""
  
  echo "🟢 SCAN #4: $EOL2_NAME - Dolly $D4"
  S4=$(curl -s -X POST "$BASE_URL/forklift/scan" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d "{\"dollyNo\":\"$D4\",\"loadingSessionId\":\"$SESSION_ID\"}")
  echo "$S4" | python3 -m json.tool
  echo ""
  
  echo "🟢 SCAN #5: $EOL2_NAME - Dolly $D5"
  S5=$(curl -s -X POST "$BASE_URL/forklift/scan" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d "{\"dollyNo\":\"$D5\",\"loadingSessionId\":\"$SESSION_ID\"}")
  echo "$S5" | python3 -m json.tool
  echo ""
fi

# Session durumu
echo "📊 Session Durumu Kontrol..."
SESSIONS=$(curl -s "$BASE_URL/forklift/sessions?status=scanned" -H "Authorization: Bearer $TOKEN")
echo "$SESSIONS" | python3 -m json.tool
echo ""

# Complete Loading
echo "✅ Complete Loading..."
COMPLETE=$(curl -s -X POST "$BASE_URL/forklift/complete-loading" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d "{\"loadingSessionId\":\"$SESSION_ID\"}")
echo "$COMPLETE" | python3 -m json.tool
echo ""

echo "=========================================="
echo "✅ TEST TAMAMLANDI"
echo "=========================================="
echo ""
echo "Özet:"
echo "  - Grup: $GROUP_NAME"
echo "  - Session: $SESSION_ID"
echo "  - $EOL1_NAME: 3 dolly"
if [ -n "$EOL2_NAME" ]; then
  echo "  - $EOL2_NAME: 2 dolly"
  echo "  - TOPLAM: 5 dolly (2 FARKLI EOL ✅)"
else
  echo "  - TOPLAM: 3 dolly"
fi
echo ""
