#!/bin/bash

# HarmonyEcoSystem - Grup Bazlı Karmaşık Toplama Test Senaryoları
# Test: Bir gruptan birden fazla EOL'den sıralı toplama (X EOL'den 5, Y EOL'den 3, vs.)

BASE_URL="http://localhost:8181/api"
TOKEN=""

# Renkli output için
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  GRUP TOPLAMA TEST SENARYOLARI${NC}"
echo -e "${BLUE}========================================${NC}"

# STEP 1: Login
echo -e "\n${YELLOW}[1] Forklift Login - Barkod ile giriş...${NC}"
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/forklift/login" \
  -H "Content-Type: application/json" \
  -d '{
    "operatorBarcode": "TESTUSER001",
    "operatorName": "Test Operatör",
    "deviceId": "test-device-001"
  }')

echo "$LOGIN_RESPONSE" | jq '.'

# Extract token
TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.sessionToken')

if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
  echo -e "${RED}❌ Login BAŞARISIZ! Token alınamadı.${NC}"
  exit 1
fi

echo -e "${GREEN}✅ Login BAŞARILI! Token alındı: ${TOKEN:0:20}...${NC}"

# STEP 2: Grupları listele
echo -e "\n${YELLOW}[2] Tüm Grupları Listele (EOL detaylarıyla)...${NC}"
GROUPS_RESPONSE=$(curl -s -X GET "$BASE_URL/manual-collection/groups" \
  -H "Authorization: Bearer $TOKEN")

echo "$GROUPS_RESPONSE" | jq '.'

# İlk grubu seç
GROUP_ID=$(echo "$GROUPS_RESPONSE" | jq -r '.[0].group_id')
GROUP_NAME=$(echo "$GROUPS_RESPONSE" | jq -r '.[0].group_name')
TOTAL_EOLS=$(echo "$GROUPS_RESPONSE" | jq -r '.[0].eols | length')

echo -e "${GREEN}✅ Test için seçilen grup: ID=$GROUP_ID, Name=$GROUP_NAME, EOL Sayısı=$TOTAL_EOLS${NC}"

# STEP 3: İlk EOL'deki dolly'leri getir
echo -e "\n${YELLOW}[3] İlk EOL'deki Dolly'leri Listele...${NC}"
FIRST_EOL_ID=$(echo "$GROUPS_RESPONSE" | jq -r '.[0].eols[0].eol_id')
FIRST_EOL_NAME=$(echo "$GROUPS_RESPONSE" | jq -r '.[0].eols[0].eol_name')
FIRST_EOL_DOLLY_COUNT=$(echo "$GROUPS_RESPONSE" | jq -r '.[0].eols[0].dolly_count')

echo -e "${BLUE}İlk EOL: ID=$FIRST_EOL_ID, Name=$FIRST_EOL_NAME, Dolly Count=$FIRST_EOL_DOLLY_COUNT${NC}"

FIRST_EOL_DOLLYS=$(curl -s -X GET "$BASE_URL/manual-collection/groups/$GROUP_ID/eols/$FIRST_EOL_ID" \
  -H "Authorization: Bearer $TOKEN")

echo "$FIRST_EOL_DOLLYS" | jq '.'

# İlk EOL'den 3 dolly seç
FIRST_EOL_DOLLY_1=$(echo "$FIRST_EOL_DOLLYS" | jq -r '.dollys[0].dolly_no')
FIRST_EOL_DOLLY_2=$(echo "$FIRST_EOL_DOLLYS" | jq -r '.dollys[1].dolly_no')
FIRST_EOL_DOLLY_3=$(echo "$FIRST_EOL_DOLLYS" | jq -r '.dollys[2].dolly_no')

# STEP 4: İkinci EOL'deki dolly'leri getir (varsa)
if [ "$TOTAL_EOLS" -gt 1 ]; then
  echo -e "\n${YELLOW}[4] İkinci EOL'deki Dolly'leri Listele...${NC}"
  SECOND_EOL_ID=$(echo "$GROUPS_RESPONSE" | jq -r '.[0].eols[1].eol_id')
  SECOND_EOL_NAME=$(echo "$GROUPS_RESPONSE" | jq -r '.[0].eols[1].eol_name')
  SECOND_EOL_DOLLY_COUNT=$(echo "$GROUPS_RESPONSE" | jq -r '.[0].eols[1].dolly_count')
  
  echo -e "${BLUE}İkinci EOL: ID=$SECOND_EOL_ID, Name=$SECOND_EOL_NAME, Dolly Count=$SECOND_EOL_DOLLY_COUNT${NC}"
  
  SECOND_EOL_DOLLYS=$(curl -s -X GET "$BASE_URL/manual-collection/groups/$GROUP_ID/eols/$SECOND_EOL_ID" \
    -H "Authorization: Bearer $TOKEN")
  
  echo "$SECOND_EOL_DOLLYS" | jq '.'
  
  # İkinci EOL'den 2 dolly seç
  SECOND_EOL_DOLLY_1=$(echo "$SECOND_EOL_DOLLYS" | jq -r '.dollys[0].dolly_no')
  SECOND_EOL_DOLLY_2=$(echo "$SECOND_EOL_DOLLYS" | jq -r '.dollys[1].dolly_no')
fi

# STEP 5: KARMAŞIK TOPLAMA - İlk EOL'den scan
echo -e "\n${YELLOW}[5] SCAN #1 - İlk EOL'den 1. Dolly Scan...${NC}"
SCAN_1=$(curl -s -X POST "$BASE_URL/forklift/scan" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"dollyNo\": \"$FIRST_EOL_DOLLY_1\",
    \"loadingSessionId\": \"TEST_SESSION_001\"
  }")

echo "$SCAN_1" | jq '.'

# STEP 6: İlk EOL'den 2. dolly scan
echo -e "\n${YELLOW}[6] SCAN #2 - İlk EOL'den 2. Dolly Scan...${NC}"
SCAN_2=$(curl -s -X POST "$BASE_URL/forklift/scan" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"dollyNo\": \"$FIRST_EOL_DOLLY_2\",
    \"loadingSessionId\": \"TEST_SESSION_001\"
  }")

echo "$SCAN_2" | jq '.'

# STEP 7: İlk EOL'den 3. dolly scan
echo -e "\n${YELLOW}[7] SCAN #3 - İlk EOL'den 3. Dolly Scan...${NC}"
SCAN_3=$(curl -s -X POST "$BASE_URL/forklift/scan" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"dollyNo\": \"$FIRST_EOL_DOLLY_3\",
    \"loadingSessionId\": \"TEST_SESSION_001\"
  }")

echo "$SCAN_3" | jq '.'

# STEP 8: KARMAŞIK TOPLAMA - Submit etmeden İKİNCİ EOL'e geç
if [ "$TOTAL_EOLS" -gt 1 ]; then
  echo -e "\n${YELLOW}[8] SCAN #4 - İkinci EOL'den 1. Dolly Scan (Submit ETMEDEN!)...${NC}"
  SCAN_4=$(curl -s -X POST "$BASE_URL/forklift/scan" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"dollyNo\": \"$SECOND_EOL_DOLLY_1\",
      \"loadingSessionId\": \"TEST_SESSION_001\"
    }")
  
  echo "$SCAN_4" | jq '.'
  
  echo -e "\n${YELLOW}[9] SCAN #5 - İkinci EOL'den 2. Dolly Scan...${NC}"
  SCAN_5=$(curl -s -X POST "$BASE_URL/forklift/scan" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"dollyNo\": \"$SECOND_EOL_DOLLY_2\",
      \"loadingSessionId\": \"TEST_SESSION_001\"
    }")
  
  echo "$SCAN_5" | jq '.'
fi

# STEP 9: Session durumunu kontrol et
echo -e "\n${YELLOW}[10] Loading Session Durumunu Kontrol Et...${NC}"
SESSION_STATUS=$(curl -s -X GET "$BASE_URL/forklift/sessions?status=scanned" \
  -H "Authorization: Bearer $TOKEN")

echo "$SESSION_STATUS" | jq '.'

# STEP 10: Complete Loading
echo -e "\n${YELLOW}[11] COMPLETE LOADING - Yükleme Tamamla...${NC}"
COMPLETE_RESPONSE=$(curl -s -X POST "$BASE_URL/forklift/complete-loading" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "loadingSessionId": "TEST_SESSION_001"
  }')

echo "$COMPLETE_RESPONSE" | jq '.'

# Final Durum
echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}✅ TEST TAMAMLANDI!${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${YELLOW}Özet:${NC}"
echo -e "  - Grup: $GROUP_NAME (ID: $GROUP_ID)"
echo -e "  - İlk EOL: $FIRST_EOL_NAME - 3 dolly scan edildi"
if [ "$TOTAL_EOLS" -gt 1 ]; then
  echo -e "  - İkinci EOL: $SECOND_EOL_NAME - 2 dolly scan edildi"
fi
echo -e "  - Toplam: 5 dolly yükleme tamamlandı"
echo -e "${BLUE}========================================${NC}"
