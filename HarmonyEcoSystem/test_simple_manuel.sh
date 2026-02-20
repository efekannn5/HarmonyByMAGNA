#!/bin/bash

# SİMPLE - Grup Toplama Manuel Test
# Adım adım manuel curl komutları

BASE_URL="http://localhost:8181/api"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  GRUP TOPLAMA TEST - Basit Manuel Komutlar${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}\n"

# STEP 1: Login
echo -e "${YELLOW}STEP 1: Login${NC}"
LOGIN_CMD="curl -s -X POST \"$BASE_URL/forklift/login\" \\
  -H \"Content-Type: application/json\" \\
  -d '{
    \"operatorBarcode\": \"TESTUSER001\",
    \"operatorName\": \"Test Operatör\",
    \"deviceId\": \"test-device-001\"
  }'"

echo -e "${CYAN}Komut:${NC}"
echo "$LOGIN_CMD"
echo ""

LOGIN_RESPONSE=$(eval $LOGIN_CMD)
echo -e "${GREEN}Response:${NC}"
echo "$LOGIN_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$LOGIN_RESPONSE"
echo ""

TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['sessionToken'])" 2>/dev/null)

if [ -z "$TOKEN" ]; then
  echo -e "${RED}❌ Token alınamadı!${NC}"
  exit 1
fi

echo -e "${GREEN}✅ Token: ${TOKEN:0:30}...${NC}\n"

# STEP 2: Grupları Listele
echo -e "${YELLOW}STEP 2: Manuel Toplama Gruplarını Listele${NC}"
GROUPS_CMD="curl -s -X GET \"$BASE_URL/manual-collection/groups\" \\
  -H \"Authorization: Bearer $TOKEN\""

echo -e "${CYAN}Komut:${NC}"
echo "$GROUPS_CMD"
echo ""

GROUPS_RESPONSE=$(eval $GROUPS_CMD)
echo -e "${GREEN}Response:${NC}"
echo "$GROUPS_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$GROUPS_RESPONSE"
echo ""

# Grup bilgilerini parse et
GROUP_ID=$(echo "$GROUPS_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data[0]['group_id'] if len(data) > 0 else '')" 2>/dev/null)
GROUP_NAME=$(echo "$GROUPS_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data[0]['group_name'] if len(data) > 0 else '')" 2>/dev/null)

if [ -z "$GROUP_ID" ]; then
  echo -e "${RED}❌ Grup bulunamadı!${NC}"
  exit 1
fi

echo -e "${GREEN}✅ Seçilen Grup: $GROUP_NAME (ID: $GROUP_ID)${NC}\n"

# STEP 3: İlk EOL'deki dolly'leri listele
echo -e "${YELLOW}STEP 3: İlk EOL'deki Dolly'leri Listele${NC}"

FIRST_EOL_ID=$(echo "$GROUPS_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data[0]['eols'][0]['eol_id'] if len(data) > 0 and len(data[0]['eols']) > 0 else '')" 2>/dev/null)
FIRST_EOL_NAME=$(echo "$GROUPS_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data[0]['eols'][0]['eol_name'] if len(data) > 0 and len(data[0]['eols']) > 0 else '')" 2>/dev/null)

EOL_DOLLYS_CMD="curl -s -X GET \"$BASE_URL/manual-collection/groups/$GROUP_ID/eols/$FIRST_EOL_ID\" \\
  -H \"Authorization: Bearer $TOKEN\""

echo -e "${CYAN}Komut:${NC}"
echo "$EOL_DOLLYS_CMD"
echo ""

EOL_DOLLYS_RESPONSE=$(eval $EOL_DOLLYS_CMD)
echo -e "${GREEN}Response (ilk 500 karakter):${NC}"
echo "$EOL_DOLLYS_RESPONSE" | head -c 500
echo "..."
echo ""

# İlk 3 dolly'yi al
DOLLY_1=$(echo "$EOL_DOLLYS_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['dollys'][0]['dolly_no'] if len(data.get('dollys', [])) > 0 else '')" 2>/dev/null)
DOLLY_2=$(echo "$EOL_DOLLYS_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['dollys'][1]['dolly_no'] if len(data.get('dollys', [])) > 1 else '')" 2>/dev/null)
DOLLY_3=$(echo "$EOL_DOLLYS_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['dollys'][2]['dolly_no'] if len(data.get('dollys', [])) > 2 else '')" 2>/dev/null)

echo -e "${GREEN}✅ İlk EOL: $FIRST_EOL_NAME (ID: $FIRST_EOL_ID)${NC}"
echo -e "${GREEN}   Seçilen Dolly'ler: $DOLLY_1, $DOLLY_2, $DOLLY_3${NC}\n"

# STEP 4: İkinci EOL'deki dolly'leri listele (varsa)
SECOND_EOL_ID=$(echo "$GROUPS_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data[0]['eols'][1]['eol_id'] if len(data) > 0 and len(data[0]['eols']) > 1 else '')" 2>/dev/null)
SECOND_EOL_NAME=$(echo "$GROUPS_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data[0]['eols'][1]['eol_name'] if len(data) > 0 and len(data[0]['eols']) > 1 else '')" 2>/dev/null)

DOLLY_4=""
DOLLY_5=""

if [ -n "$SECOND_EOL_ID" ]; then
  echo -e "${YELLOW}STEP 4: İkinci EOL'deki Dolly'leri Listele${NC}"
  
  EOL2_DOLLYS_CMD="curl -s -X GET \"$BASE_URL/manual-collection/groups/$GROUP_ID/eols/$SECOND_EOL_ID\" \\
    -H \"Authorization: Bearer $TOKEN\""
  
  echo -e "${CYAN}Komut:${NC}"
  echo "$EOL2_DOLLYS_CMD"
  echo ""
  
  EOL2_DOLLYS_RESPONSE=$(eval $EOL2_DOLLYS_CMD)
  echo -e "${GREEN}Response (ilk 500 karakter):${NC}"
  echo "$EOL2_DOLLYS_RESPONSE" | head -c 500
  echo "..."
  echo ""
  
  DOLLY_4=$(echo "$EOL2_DOLLYS_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['dollys'][0]['dolly_no'] if len(data.get('dollys', [])) > 0 else '')" 2>/dev/null)
  DOLLY_5=$(echo "$EOL2_DOLLYS_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['dollys'][1]['dolly_no'] if len(data.get('dollys', [])) > 1 else '')" 2>/dev/null)
  
  echo -e "${GREEN}✅ İkinci EOL: $SECOND_EOL_NAME (ID: $SECOND_EOL_ID)${NC}"
  echo -e "${GREEN}   Seçilen Dolly'ler: $DOLLY_4, $DOLLY_5${NC}\n"
fi

# STEP 5: KARMAŞIK TOPLAMA - Scan işlemleri
SESSION_ID="MANUAL_TEST_$(date +%Y%m%d_%H%M%S)"

echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  KARMAŞIK TOPLAMA - Farklı EOL'lerden Scan${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}\n"
echo -e "${GREEN}Session ID: $SESSION_ID${NC}\n"

# Scan 1
echo -e "${YELLOW}SCAN #1: $FIRST_EOL_NAME - Dolly $DOLLY_1${NC}"
SCAN1_CMD="curl -s -X POST \"$BASE_URL/forklift/scan\" \\
  -H \"Authorization: Bearer $TOKEN\" \\
  -H \"Content-Type: application/json\" \\
  -d '{
    \"dollyNo\": \"$DOLLY_1\",
    \"loadingSessionId\": \"$SESSION_ID\"
  }'"

echo -e "${CYAN}Komut:${NC}"
echo "$SCAN1_CMD"
echo ""

SCAN1_RESPONSE=$(eval $SCAN1_CMD)
echo -e "${GREEN}Response:${NC}"
echo "$SCAN1_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$SCAN1_RESPONSE"
echo ""

# Scan 2
echo -e "${YELLOW}SCAN #2: $FIRST_EOL_NAME - Dolly $DOLLY_2${NC}"
SCAN2_CMD="curl -s -X POST \"$BASE_URL/forklift/scan\" \\
  -H \"Authorization: Bearer $TOKEN\" \\
  -H \"Content-Type: application/json\" \\
  -d '{
    \"dollyNo\": \"$DOLLY_2\",
    \"loadingSessionId\": \"$SESSION_ID\"
  }'"

echo -e "${CYAN}Komut:${NC}"
echo "$SCAN2_CMD"
echo ""

SCAN2_RESPONSE=$(eval $SCAN2_CMD)
echo -e "${GREEN}Response:${NC}"
echo "$SCAN2_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$SCAN2_RESPONSE"
echo ""

# Scan 3
echo -e "${YELLOW}SCAN #3: $FIRST_EOL_NAME - Dolly $DOLLY_3${NC}"
SCAN3_CMD="curl -s -X POST \"$BASE_URL/forklift/scan\" \\
  -H \"Authorization: Bearer $TOKEN\" \\
  -H \"Content-Type: application/json\" \\
  -d '{
    \"dollyNo\": \"$DOLLY_3\",
    \"loadingSessionId\": \"$SESSION_ID\"
  }'"

echo -e "${CYAN}Komut:${NC}"
echo "$SCAN3_CMD"
echo ""

SCAN3_RESPONSE=$(eval $SCAN3_CMD)
echo -e "${GREEN}Response:${NC}"
echo "$SCAN3_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$SCAN3_RESPONSE"
echo ""

# İkinci EOL'den scan (varsa)
if [ -n "$DOLLY_4" ] && [ -n "$DOLLY_5" ]; then
  echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${YELLOW}⚠️  ÖNEMLİ: Submit etmeden İKİNCİ EOL'e geçiliyor!${NC}"
  echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
  
  # Scan 4
  echo -e "${YELLOW}SCAN #4: $SECOND_EOL_NAME - Dolly $DOLLY_4${NC}"
  SCAN4_CMD="curl -s -X POST \"$BASE_URL/forklift/scan\" \\
    -H \"Authorization: Bearer $TOKEN\" \\
    -H \"Content-Type: application/json\" \\
    -d '{
      \"dollyNo\": \"$DOLLY_4\",
      \"loadingSessionId\": \"$SESSION_ID\"
    }'"
  
  echo -e "${CYAN}Komut:${NC}"
  echo "$SCAN4_CMD"
  echo ""
  
  SCAN4_RESPONSE=$(eval $SCAN4_CMD)
  echo -e "${GREEN}Response:${NC}"
  echo "$SCAN4_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$SCAN4_RESPONSE"
  echo ""
  
  # Scan 5
  echo -e "${YELLOW}SCAN #5: $SECOND_EOL_NAME - Dolly $DOLLY_5${NC}"
  SCAN5_CMD="curl -s -X POST \"$BASE_URL/forklift/scan\" \\
    -H \"Authorization: Bearer $TOKEN\" \\
    -H \"Content-Type: application/json\" \\
    -d '{
      \"dollyNo\": \"$DOLLY_5\",
      \"loadingSessionId\": \"$SESSION_ID\"
    }'"
  
  echo -e "${CYAN}Komut:${NC}"
  echo "$SCAN5_CMD"
  echo ""
  
  SCAN5_RESPONSE=$(eval $SCAN5_CMD)
  echo -e "${GREEN}Response:${NC}"
  echo "$SCAN5_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$SCAN5_RESPONSE"
  echo ""
fi

# STEP 6: Session durumunu kontrol et
echo -e "${YELLOW}STEP 6: Session Durumunu Kontrol Et${NC}"
SESSION_CMD="curl -s -X GET \"$BASE_URL/forklift/sessions?status=scanned\" \\
  -H \"Authorization: Bearer $TOKEN\""

echo -e "${CYAN}Komut:${NC}"
echo "$SESSION_CMD"
echo ""

SESSION_RESPONSE=$(eval $SESSION_CMD)
echo -e "${GREEN}Response:${NC}"
echo "$SESSION_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$SESSION_RESPONSE"
echo ""

# STEP 7: Complete Loading
echo -e "${YELLOW}STEP 7: Complete Loading - Yükleme Tamamla${NC}"
COMPLETE_CMD="curl -s -X POST \"$BASE_URL/forklift/complete-loading\" \\
  -H \"Authorization: Bearer $TOKEN\" \\
  -H \"Content-Type: application/json\" \\
  -d '{
    \"loadingSessionId\": \"$SESSION_ID\"
  }'"

echo -e "${CYAN}Komut:${NC}"
echo "$COMPLETE_CMD"
echo ""

COMPLETE_RESPONSE=$(eval $COMPLETE_CMD)
echo -e "${GREEN}Response:${NC}"
echo "$COMPLETE_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$COMPLETE_RESPONSE"
echo ""

# SONUÇ
echo -e "\n${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ TEST TAMAMLANDI!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}\n"

echo -e "${YELLOW}Test Özeti:${NC}"
echo -e "  ├─ Grup: $GROUP_NAME (ID: $GROUP_ID)"
echo -e "  ├─ Session: $SESSION_ID"
echo -e "  ├─ $FIRST_EOL_NAME: 3 dolly scan edildi"
if [ -n "$SECOND_EOL_NAME" ]; then
  echo -e "  ├─ $SECOND_EOL_NAME: 2 dolly scan edildi"
  echo -e "  └─ Toplam: 5 dolly KARMAŞIK TOPLAMA ile yüklendi ✅"
else
  echo -e "  └─ Toplam: 3 dolly yüklendi"
fi
echo ""
