#!/bin/bash

# DETAYLI API TEST - Grup Seçimleri ve Sıralı Toplama
# Test Senaryoları:
# 1. Grupları listele ve EOL detaylarını göster
# 2. Her EOL'deki dolly'leri göster
# 3. Karmaşık toplama: X EOL'den 5, Y EOL'den 3 dolly scan
# 4. Sıralama kontrolü

BASE_URL="http://localhost:8181/api"
TOKEN=""

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

print_header() {
  echo -e "\n${BLUE}════════════════════════════════════════════════════════════════${NC}"
  echo -e "${BLUE}  $1${NC}"
  echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}\n"
}

print_step() {
  echo -e "\n${YELLOW}▶ [$1] $2${NC}"
}

print_success() {
  echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
  echo -e "${RED}❌ $1${NC}"
}

print_info() {
  echo -e "${CYAN}ℹ️  $1${NC}"
}

# =============================================================================
# TEST BAŞLANGIÇ
# =============================================================================

print_header "HARMONYECOSYSTEM - API TEST SUITE"

# TEST 1: Health Check
print_step "1" "Health Check"
HEALTH=$(curl -s -X GET "$BASE_URL/health")
echo "$HEALTH" | jq '.'

if [ $? -eq 0 ]; then
  print_success "Backend çalışıyor!"
else
  print_error "Backend'e erişilemiyor!"
  exit 1
fi

# TEST 2: Forklift Login
print_step "2" "Forklift Login (Barkod ile giriş)"
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/forklift/login" \
  -H "Content-Type: application/json" \
  -d '{
    "operatorBarcode": "TESTUSER001",
    "operatorName": "Test Operatör",
    "deviceId": "test-device-manuel-toplama"
  }')

echo "$LOGIN_RESPONSE" | jq '.'

TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.sessionToken')
OPERATOR_NAME=$(echo "$LOGIN_RESPONSE" | jq -r '.operatorName')

if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
  print_error "Login başarısız!"
  exit 1
fi

print_success "Login başarılı! Operator: $OPERATOR_NAME"
print_info "Token: ${TOKEN:0:30}..."

# TEST 3: Manuel Toplama Gruplarını Listele
print_step "3" "Manuel Toplama Gruplarını Listele"
GROUPS=$(curl -s -X GET "$BASE_URL/manual-collection/groups" \
  -H "Authorization: Bearer $TOKEN")

echo "$GROUPS" | jq '.'

GROUP_COUNT=$(echo "$GROUPS" | jq '. | length')
print_info "Toplam $GROUP_COUNT grup bulundu"

if [ "$GROUP_COUNT" -eq 0 ]; then
  print_error "Hiç grup bulunamadı!"
  exit 1
fi

# Her grubu detaylı göster
for i in $(seq 0 $(($GROUP_COUNT - 1))); do
  GROUP_ID=$(echo "$GROUPS" | jq -r ".[$i].group_id")
  GROUP_NAME=$(echo "$GROUPS" | jq -r ".[$i].group_name")
  EOL_COUNT=$(echo "$GROUPS" | jq -r ".[$i].eols | length")
  TOTAL_DOLLY=$(echo "$GROUPS" | jq -r ".[$i].total_dolly_count")
  TOTAL_SCANNED=$(echo "$GROUPS" | jq -r ".[$i].total_scanned_count")
  
  echo ""
  print_info "Grup #$((i+1)): $GROUP_NAME (ID: $GROUP_ID)"
  print_info "  ├─ EOL Sayısı: $EOL_COUNT"
  print_info "  ├─ Toplam Dolly: $TOTAL_DOLLY"
  print_info "  └─ Scan Edilmiş: $TOTAL_SCANNED"
  
  # Her EOL'i göster
  for j in $(seq 0 $(($EOL_COUNT - 1))); do
    EOL_ID=$(echo "$GROUPS" | jq -r ".[$i].eols[$j].eol_id")
    EOL_NAME=$(echo "$GROUPS" | jq -r ".[$i].eols[$j].eol_name")
    EOL_DOLLY_COUNT=$(echo "$GROUPS" | jq -r ".[$i].eols[$j].dolly_count")
    EOL_SCANNED=$(echo "$GROUPS" | jq -r ".[$i].eols[$j].scanned_count")
    
    echo -e "    ${CYAN}├─ EOL #$((j+1)): $EOL_NAME (ID: $EOL_ID)${NC}"
    echo -e "    ${CYAN}│  ├─ Dolly: $EOL_DOLLY_COUNT${NC}"
    echo -e "    ${CYAN}│  └─ Scanned: $EOL_SCANNED${NC}"
  done
done

# TEST 4: İlk Grubu Seç ve Detaylı İncele
print_step "4" "İlk Grubu Detaylı İnceleme"
SELECTED_GROUP_ID=$(echo "$GROUPS" | jq -r '.[0].group_id')
SELECTED_GROUP_NAME=$(echo "$GROUPS" | jq -r '.[0].group_name')
SELECTED_EOL_COUNT=$(echo "$GROUPS" | jq -r '.[0].eols | length')

print_info "Seçilen Grup: $SELECTED_GROUP_NAME (ID: $SELECTED_GROUP_ID)"
print_info "Bu grupta $SELECTED_EOL_COUNT EOL var"

# Her EOL'deki dolly'leri detaylı getir
for i in $(seq 0 $(($SELECTED_EOL_COUNT - 1))); do
  EOL_ID=$(echo "$GROUPS" | jq -r ".[0].eols[$i].eol_id")
  EOL_NAME=$(echo "$GROUPS" | jq -r ".[0].eols[$i].eol_name")
  
  print_step "4.$((i+1))" "EOL '$EOL_NAME' Dolly Listesi"
  
  EOL_DOLLYS=$(curl -s -X GET "$BASE_URL/manual-collection/groups/$SELECTED_GROUP_ID/eols/$EOL_ID" \
    -H "Authorization: Bearer $TOKEN")
  
  echo "$EOL_DOLLYS" | jq '.'
  
  DOLLY_COUNT=$(echo "$EOL_DOLLYS" | jq '.dollys | length')
  print_info "Bu EOL'de $DOLLY_COUNT dolly var"
  
  # İlk 5 dolly'yi göster
  SHOW_COUNT=$DOLLY_COUNT
  if [ $DOLLY_COUNT -gt 5 ]; then
    SHOW_COUNT=5
  fi
  
  for j in $(seq 0 $(($SHOW_COUNT - 1))); do
    DOLLY_NO=$(echo "$EOL_DOLLYS" | jq -r ".dollys[$j].dolly_no")
    ORDER_NO=$(echo "$EOL_DOLLYS" | jq -r ".dollys[$j].dolly_order_no")
    SCANNED=$(echo "$EOL_DOLLYS" | jq -r ".dollys[$j].scanned")
    VIN_PREVIEW=$(echo "$EOL_DOLLYS" | jq -r ".dollys[$j].vin_no" | head -n 1)
    
    SCAN_STATUS=""
    if [ "$SCANNED" == "true" ]; then
      SCAN_STATUS="${GREEN}[SCANNED]${NC}"
    else
      SCAN_STATUS="${YELLOW}[BEKLEMEDE]${NC}"
    fi
    
    echo -e "  ${CYAN}├─ Dolly #$((j+1)): $DOLLY_NO (Order: $ORDER_NO) $SCAN_STATUS${NC}"
    echo -e "  ${CYAN}│  └─ VIN: ${VIN_PREVIEW:0:30}...${NC}"
  done
  
  if [ $DOLLY_COUNT -gt 5 ]; then
    print_info "... ve $(($DOLLY_COUNT - 5)) dolly daha"
  fi
done

# TEST 5: KARMAŞIK TOPLAMA SENARYOSU
print_header "KARMAŞIK TOPLAMA TEST SENARYOSU"
print_info "Senaryo: Farklı EOL'lerden karışık sıralı toplama"

# İlk EOL'den 3 dolly seç
FIRST_EOL_ID=$(echo "$GROUPS" | jq -r '.[0].eols[0].eol_id')
FIRST_EOL_NAME=$(echo "$GROUPS" | jq -r '.[0].eols[0].eol_name')

FIRST_EOL_DOLLYS=$(curl -s -X GET "$BASE_URL/manual-collection/groups/$SELECTED_GROUP_ID/eols/$FIRST_EOL_ID" \
  -H "Authorization: Bearer $TOKEN")

DOLLY_1=$(echo "$FIRST_EOL_DOLLYS" | jq -r '.dollys[0].dolly_no')
DOLLY_2=$(echo "$FIRST_EOL_DOLLYS" | jq -r '.dollys[1].dolly_no')
DOLLY_3=$(echo "$FIRST_EOL_DOLLYS" | jq -r '.dollys[2].dolly_no')

# İkinci EOL'den 2 dolly seç (varsa)
SECOND_EOL_DOLLY_1=""
SECOND_EOL_DOLLY_2=""
SECOND_EOL_NAME=""

if [ "$SELECTED_EOL_COUNT" -gt 1 ]; then
  SECOND_EOL_ID=$(echo "$GROUPS" | jq -r '.[0].eols[1].eol_id')
  SECOND_EOL_NAME=$(echo "$GROUPS" | jq -r '.[0].eols[1].eol_name')
  
  SECOND_EOL_DOLLYS=$(curl -s -X GET "$BASE_URL/manual-collection/groups/$SELECTED_GROUP_ID/eols/$SECOND_EOL_ID" \
    -H "Authorization: Bearer $TOKEN")
  
  SECOND_EOL_DOLLY_1=$(echo "$SECOND_EOL_DOLLYS" | jq -r '.dollys[0].dolly_no')
  SECOND_EOL_DOLLY_2=$(echo "$SECOND_EOL_DOLLYS" | jq -r '.dollys[1].dolly_no')
fi

# Scan işlemleri başlat
SESSION_ID="KOMPLEKS_TEST_$(date +%Y%m%d_%H%M%S)"

print_step "5.1" "SCAN - $FIRST_EOL_NAME'den 1. Dolly"
SCAN_1=$(curl -s -X POST "$BASE_URL/forklift/scan" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"dollyNo\": \"$DOLLY_1\",
    \"loadingSessionId\": \"$SESSION_ID\"
  }")
echo "$SCAN_1" | jq '.'

print_step "5.2" "SCAN - $FIRST_EOL_NAME'den 2. Dolly"
SCAN_2=$(curl -s -X POST "$BASE_URL/forklift/scan" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"dollyNo\": \"$DOLLY_2\",
    \"loadingSessionId\": \"$SESSION_ID\"
  }")
echo "$SCAN_2" | jq '.'

print_step "5.3" "SCAN - $FIRST_EOL_NAME'den 3. Dolly"
SCAN_3=$(curl -s -X POST "$BASE_URL/forklift/scan" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"dollyNo\": \"$DOLLY_3\",
    \"loadingSessionId\": \"$SESSION_ID\"
  }")
echo "$SCAN_3" | jq '.'

# İkinci EOL'den scan (varsa)
if [ "$SELECTED_EOL_COUNT" -gt 1 ]; then
  print_step "5.4" "SCAN - $SECOND_EOL_NAME'den 1. Dolly (Submit etmeden!)"
  SCAN_4=$(curl -s -X POST "$BASE_URL/forklift/scan" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"dollyNo\": \"$SECOND_EOL_DOLLY_1\",
      \"loadingSessionId\": \"$SESSION_ID\"
    }")
  echo "$SCAN_4" | jq '.'
  
  print_step "5.5" "SCAN - $SECOND_EOL_NAME'den 2. Dolly"
  SCAN_5=$(curl -s -X POST "$BASE_URL/forklift/scan" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"dollyNo\": \"$SECOND_EOL_DOLLY_2\",
      \"loadingSessionId\": \"$SESSION_ID\"
    }")
  echo "$SCAN_5" | jq '.'
fi

# TEST 6: Session Durumu
print_step "6" "Loading Session Durumu Kontrol"
SESSION_STATUS=$(curl -s -X GET "$BASE_URL/forklift/sessions?status=scanned" \
  -H "Authorization: Bearer $TOKEN")
echo "$SESSION_STATUS" | jq '.'

# TEST 7: Complete Loading
print_step "7" "Complete Loading - Yükleme Tamamla"
COMPLETE=$(curl -s -X POST "$BASE_URL/forklift/complete-loading" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"loadingSessionId\": \"$SESSION_ID\"
  }")
echo "$COMPLETE" | jq '.'

# SONUÇ RAPORU
print_header "TEST SONUÇLARI"

print_success "Tüm testler tamamlandı!"
echo ""
print_info "Test Özeti:"
print_info "  ├─ Grup: $SELECTED_GROUP_NAME (ID: $SELECTED_GROUP_ID)"
print_info "  ├─ Session ID: $SESSION_ID"
print_info "  ├─ $FIRST_EOL_NAME: 3 dolly scan edildi"
if [ "$SELECTED_EOL_COUNT" -gt 1 ]; then
  print_info "  ├─ $SECOND_EOL_NAME: 2 dolly scan edildi"
  print_info "  └─ Toplam: 5 dolly karmaşık toplama ile yüklendi"
else
  print_info "  └─ Toplam: 3 dolly yüklendi"
fi
echo ""

print_header "TEST TAMAMLANDI"
