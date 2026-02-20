# 🌐 API Endpoint'leri - Tam Liste

## Base URL
```
http://10.25.1.174:8181/api
```

---

## 🔐 Authentication Endpoints

### 1. Login
```
POST /forklift/login
```
- **Auth:** ❌ Gerekmez
- **Body:** `{ "operatorBarcode": "EMP123", "deviceId": "android-123" }`
- **Response:** `{ "success": true, "sessionToken": "...", "operatorName": "..." }`
- **Kullanım:** Operatör çalışan barkodunu okutarak giriş yapar

### 2. Logout
```
POST /forklift/logout
```
- **Auth:** ✅ Bearer token
- **Body:** Boş
- **Response:** `{ "success": true, "message": "Çıkış yapıldı" }`
- **Kullanım:** Operatör çıkış yapar

### 3. Validate Session
```
GET /forklift/session/validate
```
- **Auth:** ✅ Bearer token
- **Response:** `{ "valid": true, "operatorName": "...", "expiresAt": "..." }`
- **Kullanım:** Mevcut oturumun geçerli olup olmadığını kontrol eder

---

## 📦 Forklift Operations (Dolly İşlemleri)

### 4. Scan Dolly
```
POST /forklift/scan
```
- **Auth:** ✅ Bearer token
- **Body:** `{ "dollyNo": "DL-123", "loadingSessionId": "LOAD_...", "barcode": "..." }`
- **Response:** `{ "dolly_no": "...", "vin_no": "...", "scan_order": 1, ... }`
- **Kullanım:** TIR'a yüklenen dolly'yi sırayla okutma

### 5. Complete Loading
```
POST /forklift/complete-loading
```
- **Auth:** ✅ Bearer token
- **Body:** `{ "loadingSessionId": "LOAD_..." }`
- **Response:** `{ "loadingSessionId": "...", "dollyCount": 15, "completedAt": "..." }`
- **Kullanım:** Tüm dolly'ler yüklendi, yükleme tamamlandı

### 6. List Sessions
```
GET /forklift/sessions?status=scanned
```
- **Auth:** ✅ Bearer token
- **Query:** `status` (optional): scanned, loading_completed, completed
- **Response:** `[{ "loadingSessionId": "...", "dollyCount": 8, ... }]`
- **Kullanım:** Aktif veya tamamlanmış yükleme oturumlarını listele

---

## 🖥️ Web Operator Endpoints

### 7. Pending Shipments
```
GET /operator/pending-shipments
```
- **Auth:** ❌ (Web dashboard'dan çağrılır)
- **Response:** `[{ "loadingSessionId": "...", "dollys": [...] }]`
- **Kullanım:** Forklift'in tamamladığı, operatör bekleyen sevkiyatlar

### 8. Shipment Details
```
GET /operator/shipment/<loading_session_id>
```
- **Auth:** ❌ (Web dashboard'dan çağrılır)
- **Response:** `{ "loadingSessionId": "...", "dollys": [...], "dollyCount": 15 }`
- **Kullanım:** Belirli bir sevkiyatın detayları

### 9. Complete Shipment
```
POST /operator/complete-shipment
```
- **Auth:** ❌ (Web dashboard'dan çağrılır)
- **Body:** `{ "loadingSessionId": "...", "seferNumarasi": "SFR001", "plakaNo": "34 ABC 123", "shippingType": "asn" }`
- **Response:** `{ "loadingSessionId": "...", "dollyCount": 15, "completedAt": "..." }`
- **Kullanım:** Operatör sefer no + plaka girip ASN/İrsaliye gönderiyor

---

## 🔍 Utility Endpoints

### 10. Health Check
```
GET /health
```
- **Auth:** ❌ Gerekmez
- **Response:** `{ "status": "ok", "app": "HarmonyEcoSystem" }`
- **Kullanım:** Sunucunun çalışıp çalışmadığını kontrol et

### 11. List Groups
```
GET /groups
```
- **Auth:** ❌ Gerekmez
- **Response:** `[{ "dolly_no": "...", "vin_no": "...", "status": "..." }]`
- **Kullanım:** Tüm dolly gruplarını listele

### 12. Group Sequences
```
GET /group-sequences
```
- **Auth:** ❌ Gerekmez
- **Response:** `[{ "definition": {...}, "queue": [...] }]`
- **Kullanım:** EOL bazlı grup sıralamaları

### 13. EOL Workstations
```
GET /pworkstations/eol
```
- **Auth:** ❌ Gerekmez
- **Response:** `[{ "workstation_id": 1, "name": "EOL-A1", ... }]`
- **Kullanım:** EOL istasyonlarını listele

### 14. Group Definitions
```
GET /groups/definitions
```
- **Auth:** ❌ Gerekmez
- **Response:** `[{ "group_id": 1, "name": "...", "eols": [...] }]`
- **Kullanım:** Tanımlı grupları listele

---

## 📊 Endpoint Özeti

| # | Method | Endpoint | Auth | Kullanıcı | Açıklama |
|---|--------|----------|------|-----------|----------|
| 1 | POST | `/forklift/login` | ❌ | Android | Barkod ile giriş |
| 2 | POST | `/forklift/logout` | ✅ | Android | Çıkış |
| 3 | GET | `/forklift/session/validate` | ✅ | Android | Session kontrolü |
| 4 | POST | `/forklift/scan` | ✅ | Android | Dolly okut |
| 5 | POST | `/forklift/complete-loading` | ✅ | Android | Yükleme tamamla |
| 6 | GET | `/forklift/sessions` | ✅ | Android | Session listesi |
| 7 | GET | `/operator/pending-shipments` | ❌ | Web | Bekleyen sevkiyatlar |
| 8 | GET | `/operator/shipment/<id>` | ❌ | Web | Sevkiyat detayı |
| 9 | POST | `/operator/complete-shipment` | ❌ | Web | Sevkiyat tamamla |
| 10 | GET | `/health` | ❌ | Tümü | Sunucu durumu |

---

## 🔑 Authentication Header Formatı

Tüm `✅` işaretli endpoint'ler için:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## 📱 Android İçin Öncelikli Endpoint'ler

1. **POST /forklift/login** - İlk açılışta
2. **POST /forklift/scan** - Her dolly okutmada
3. **POST /forklift/complete-loading** - Yükleme bitince
4. **POST /forklift/logout** - Çıkış

---

## 🖥️ Web Dashboard İçin Öncelikli Endpoint'ler

1. **GET /operator/pending-shipments** - Ana sayfa
2. **GET /operator/shipment/<id>** - Detay görüntüle
3. **POST /operator/complete-shipment** - Sefer tamamla

---

## 📱 Manuel Toplama (Group-Based Collection)

### 11. Get Manual Collection Groups
```
GET /manual-collection/groups
```
- **Auth:** ✅ Bearer token
- **Response:** 
```json
[
  {
    "group_id": 2,
    "group_name": "710grup",
    "eols": [
      {
        "eol_id": 11,
        "eol_name": "V710-LLS-EOL",
        "dolly_count": 2,
        "scanned_count": 0
      },
      {
        "eol_id": 26,
        "eol_name": "V710-MR-EOL",
        "dolly_count": 2,
        "scanned_count": 0
      }
    ],
    "total_dolly_count": 4,
    "total_scanned_count": 0
  }
]
```
- **Kullanım:** Grup bazlı EOL listesini gösterir. Aynı grup içindeki EOL'ler arasında serbest geçiş yapılabilir.

### 12. Get EOL Dollys in Group
```
GET /manual-collection/groups/<group_id>/eols/<eol_id>
```
- **Auth:** ✅ Bearer token
- **URL Params:** 
  - `group_id`: Grup ID'si (örn: 2)
  - `eol_id`: EOL istasyon ID'si (örn: 11)
- **Response:**
```json
{
  "group_id": 2,
  "group_name": "710grup",
  "eol_id": 11,
  "eol_name": "V710-LLS-EOL",
  "dollys": [
    {
      "dolly_no": "1062037",
      "vin_no": "VIN001\nVIN002\nVIN003",
      "scanned": false
    }
  ]
}
```
- **Kullanım:** Belirli bir EOL için dolly listesini getirir. Aynı grup içinde farklı EOL'ler arasında geçiş yapılabilir.

**İş Akışı:**
1. `GET /manual-collection/groups` ile grupları listele
2. Kullanıcı bir grup seçer
3. Kullanıcı grup içinde istediği EOL'ü seçer (sıralama zorunlu değil)
4. `GET /manual-collection/groups/{group_id}/eols/{eol_id}` ile dolly'leri göster
5. Kullanıcı istediği zaman başka bir EOL'e geçebilir (aynı grup içinde)

---

## ⚠️ Önemli Notlar

1. **Base URL:** Tüm endpoint'lere `http://10.25.1.174:8181/api` eklenmeli
2. **Content-Type:** Her POST request için `application/json` header gerekli
3. **Token Expiry:** Login token'ları 8 saat sonra sona erer
4. **Auto-Logout:** Süre dolunca otomatik çıkış yapar
5. **Activity Tracking:** Her API çağrısı `AuditLog` tablosuna kaydedilir

---

## 🔄 Örnek İş Akışı

```
Android App                    API Server                    Web Dashboard
    |                              |                              |
    |-- POST /forklift/login -->   |                              |
    |<-- token ----------------    |                              |
    |                              |                              |
    |-- POST /forklift/scan -->    |                              |
    |<-- scan_order: 1 --------    |                              |
    |                              |                              |
    |-- POST /forklift/scan -->    |                              |
    |<-- scan_order: 2 --------    |                              |
    |                              |                              |
    |-- POST /complete-loading ->  |                              |
    |<-- dollyCount: 2 --------    |                              |
    |                              |                              |
    |                              |  <- GET /pending-shipments --|
    |                              |  --> shipments list -------> |
    |                              |                              |
    |                              |  <- POST /complete-shipment -|
    |                              |  --> success -------------> |
    |                              |                              |
    |-- POST /forklift/logout -->  |                              |
    |<-- success --------------    |                              |
```

---

**Versiyon:** 1.0  
**Tarih:** 26 Kasım 2025  
**Sunucu:** 10.25.1.174:8181
