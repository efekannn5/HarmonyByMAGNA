# HARMONYECOSYSTEM - MANUEL API TEST KOMUTLARI
# Grup Bazlı Karmaşık Toplama Senaryoları

## BASE URL
```bash
BASE_URL="http://localhost:8181/api"
```

## 1. HEALTH CHECK
```bash
curl -X GET "$BASE_URL/health" | jq '.'
```

## 2. FORKLIFT LOGIN
```bash
# Normal kullanıcı login
curl -X POST "$BASE_URL/forklift/login" \
  -H "Content-Type: application/json" \
  -d '{
    "operatorBarcode": "TESTUSER001",
    "operatorName": "Test Operatör",
    "deviceId": "test-device-001"
  }' | jq '.'

# Response'tan TOKEN al
TOKEN="<buraya_token_yapıştır>"
```

## 3. GRUP LİSTELE (Manuel Toplama)
```bash
# Tüm grupları EOL detaylarıyla listele
curl -X GET "$BASE_URL/manual-collection/groups" \
  -H "Authorization: Bearer $TOKEN" | jq '.'

# Beklenen Response:
# [
#   {
#     "group_id": 1,
#     "group_name": "710grup",
#     "eols": [
#       {
#         "eol_id": 1,
#         "eol_name": "V710-LLS-EOL",
#         "dolly_count": 14,
#         "scanned_count": 0
#       },
#       {
#         "eol_id": 5,
#         "eol_name": "V710-MR-EOL",
#         "dolly_count": 21,
#         "scanned_count": 0
#       }
#     ],
#     "total_dolly_count": 35,
#     "total_scanned_count": 0
#   }
# ]
```

## 4. BELİRLİ BİR EOL'DEKİ DOLLY'LERİ LİSTELE
```bash
# Grup ID ve EOL ID'yi yukarıdaki response'tan al
GROUP_ID=1
EOL_ID=1

curl -X GET "$BASE_URL/manual-collection/groups/$GROUP_ID/eols/$EOL_ID" \
  -H "Authorization: Bearer $TOKEN" | jq '.'

# Beklenen Response:
# {
#   "group_id": 1,
#   "group_name": "710grup",
#   "eol_id": 1,
#   "eol_name": "V710-LLS-EOL",
#   "dollys": [
#     {
#       "dolly_no": "1061469",
#       "dolly_order_no": "1",
#       "vin_no": "VIN001\nVIN002\nVIN003",
#       "scanned": false
#     }
#   ]
# }
```

## 5. KARMAŞIK TOPLAMA - FARKLI EOL'LERDEN SCAN

### Senaryo: X EOL'den 3 dolly, Y EOL'den 2 dolly (submit etmeden)

```bash
SESSION_ID="KOMPLEKS_TEST_001"

# X EOL'den 1. Dolly
curl -X POST "$BASE_URL/forklift/scan" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "dollyNo": "1061469",
    "loadingSessionId": "'$SESSION_ID'"
  }' | jq '.'

# X EOL'den 2. Dolly
curl -X POST "$BASE_URL/forklift/scan" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "dollyNo": "1061470",
    "loadingSessionId": "'$SESSION_ID'"
  }' | jq '.'

# X EOL'den 3. Dolly
curl -X POST "$BASE_URL/forklift/scan" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "dollyNo": "1061471",
    "loadingSessionId": "'$SESSION_ID'"
  }' | jq '.'

# ===== ŞİMDİ SUBMIT ETMEDEN Y EOL'E GEÇ =====

# Y EOL'den 1. Dolly (Farklı EOL, aynı grup!)
curl -X POST "$BASE_URL/forklift/scan" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "dollyNo": "1061500",
    "loadingSessionId": "'$SESSION_ID'"
  }' | jq '.'

# Y EOL'den 2. Dolly
curl -X POST "$BASE_URL/forklift/scan" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "dollyNo": "1061501",
    "loadingSessionId": "'$SESSION_ID'"
  }' | jq '.'
```

## 6. SESSION DURUMU KONTROL
```bash
# Tüm scanned durumundaki sessionları listele
curl -X GET "$BASE_URL/forklift/sessions?status=scanned" \
  -H "Authorization: Bearer $TOKEN" | jq '.'

# Beklenen: X EOL'den 3, Y EOL'den 2 dolly görülmeli
```

## 7. SON SCAN'İ SİL (Hatalı scan durumunda)
```bash
curl -X POST "$BASE_URL/forklift/remove-last" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "loadingSessionId": "'$SESSION_ID'",
    "dollyBarcode": "BARCODE_TO_VERIFY"
  }' | jq '.'
```

## 8. COMPLETE LOADING (Yükleme Tamamla)
```bash
curl -X POST "$BASE_URL/forklift/complete-loading" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "loadingSessionId": "'$SESSION_ID'"
  }' | jq '.'

# Bu komut tüm scan edilmiş dolly'leri submit eder
```

## 9. LOGOUT
```bash
curl -X POST "$BASE_URL/forklift/logout" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" | jq '.'
```

---

## TEST SENARYOLARI

### Senaryo 1: Aynı Gruptan Farklı EOL'lerden Karışık Toplama
**Amaç:** Bir gruptan birden fazla EOL olduğunda, submit etmeden farklı EOL'lerden dolly toplanabilmeli

**Adımlar:**
1. Login yap
2. Grupları listele → Birden fazla EOL'ü olan bir grup seç
3. İlk EOL'den 5 dolly scan et
4. **Submit etmeden** ikinci EOL'den 3 dolly scan et
5. Session durumunu kontrol et → 8 dolly görülmeli
6. Complete loading ile tümünü submit et

**Beklenen Sonuç:** ✅ Başarılı - Farklı EOL'lerden dolly'ler aynı session'da toplanabilir

---

### Senaryo 2: EOL'ler Kendi İçinde Sıralı Kontrolü
**Amaç:** Her EOL kendi içinde dolly'leri sıralı toplamalı (orderNo bazlı)

**Adımlar:**
1. Bir EOL'den dolly listesini al
2. OrderNo: 1, 3, 5 şeklinde NON-SEQUENTIAL scan etmeyi dene
3. Sistem hata vermeli

**Beklenen Sonuç:** ✅ Her EOL kendi içinde sequential olmalı

---

### Senaryo 3: Grup Değiştirme
**Amaç:** Bir sessionda sadece tek bir gruptan dolly toplanabilmeli

**Adımlar:**
1. Grup A'dan bir dolly scan et
2. Aynı sessionda Grup B'den dolly scan etmeyi dene
3. Sistem hata vermeli

**Beklenen Sonuç:** ✅ Hata: "Farklı gruptan dolly eklenemez"

---

## DEBUGGING

### Database'de scan edilenleri kontrol et
```sql
-- DollySubmissionHold tablosunda scan edilmiş dolly'ler
SELECT 
    DollyNo, 
    VinNo, 
    PartNumber, 
    Status, 
    TerminalUser, 
    ScannedAt
FROM DollySubmissionHold
WHERE Status = 'scanned'
ORDER BY ScannedAt DESC;
```

### Grup ve EOL ilişkilerini kontrol et
```sql
-- Hangi grupta hangi EOL'ler var?
SELECT 
    g.GroupName,
    w.PWorkStationName,
    ge.ShippingTag
FROM DollyGroup g
INNER JOIN DollyGroupEOL ge ON g.Id = ge.GroupId
INNER JOIN PWorkStation w ON ge.PWorkStationId = w.Id
WHERE g.IsActive = 1
ORDER BY g.GroupName, w.PWorkStationName;
```

### Dolly'lerin EOL dağılımı
```sql
-- Hangi EOL'de kaç dolly var?
SELECT 
    EOLName,
    COUNT(DISTINCT DollyNo) as DollyCount,
    COUNT(*) as VinCount
FROM DollyEOLInfo
GROUP BY EOLName
ORDER BY DollyCount DESC;
```

---

## NOTLAR

1. **Grup İçi Esneklik:** Aynı grup içindeki farklı EOL'lerden submit etmeden dolly toplanabilir
2. **EOL Bazlı Sıralama:** Her EOL kendi içinde sıralı (orderNo: 1,2,3...) olmalı
3. **Session İzolasyonu:** Bir session sadece tek bir gruba ait olabilir
4. **Token Süresi:** Token varsayılan 8 saat geçerlidir
5. **Hata Durumu:** Hatalı scan'de `remove-last` endpoint'i ile geri alınabilir
