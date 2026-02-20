# 📱 Android Dolly Toplama Sistemi - API Entegrasyon Kılavuzu

## 📋 İçindekiler
1. [Genel Bakış](#genel-bakış)
2. [Authentication (Kimlik Doğrulama)](#authentication)
3. [Workflow (İş Akışı)](#workflow)
4. [API Endpoint'leri](#api-endpointleri)
5. [Hata Yönetimi](#hata-yönetimi)
6. [Test Senaryoları](#test-senaryoları)

---

## 🎯 Genel Bakış

Dolly Toplama sistemi, forklift operatörlerinin Android cihazlarından dolly'leri tarayıp, sıralı olarak toplayıp, operator paneline görev olarak göndermesini sağlar. Bu **normal/standart** dolly toplama işlemidir. 

> **Not:** Web üzerinden yapılan "Manuel Toplama" farklıdır - o sadece acil durumlarda kullanılır.

### Temel Özellikler
- ✅ **Sıralı Okutma**: Her EOL için dolly'ler sırayla taranmalıdır (1 → 2 → 3)
- ✅ **Çoklu EOL**: Farklı EOL'ler arası geçiş serbesttir
- ✅ **Geri Alma**: Son taranan dolly çıkartılabilir
- ✅ **Batch Submit**: Taranan tüm dolly'ler tek PartNumber ile submit edilir
- ✅ **Operator Paneli Entegrasyonu**: Submit edilen dolly'ler otomatik olarak görev olarak düşer

---

## 🔐 Authentication

### Base URL
```
http://10.25.64.181:8181/api
```

### 1. Login (Operatör Girişi)

**Endpoint:** `POST /forklift/login`

**Request:**
```json
{
  "operatorBarcode": "TESTOP001",
  "operatorName": "Ahmet Yılmaz",
  "deviceId": "android-device-123"
}
```

**Response (Success):**
```json
{
  "success": true,
  "sessionToken": "xxa3oUwD8AywIFdQnw0KWW2Rq8FNnCoeX8IeefCH...",
  "operatorName": "Ahmet Yılmaz",
  "operatorBarcode": "TESTOP001",
  "expiresAt": "2025-12-24T16:00:00Z",
  "message": "Hoş geldiniz Ahmet Yılmaz",
  "isAdmin": false,
  "role": "forklift"
}
```

**Response (Error):**
```json
{
  "success": false,
  "message": "Operatör barkodu gerekli"
}
```

**Notlar:**
- `sessionToken` **tüm API isteklerinde** `Authorization: Bearer <token>` header'ında gönderilmelidir
- Token 8 saat geçerlidir
- Admin operatörler: Barcode'u `ADMIN`, `ADM`, `SUPERUSER`, `SU` ile başlayanlar
- `deviceId` opsiyoneldir (cihaz takibi için)

---

## 🔄 Workflow (İş Akışı)

```
┌─────────────────────────────────────────────────────────────┐
│              NORMAL DOLLY TOPLAMA AKIŞI (ANDROID)            │
└─────────────────────────────────────────────────────────────┘

1️⃣ LOGIN
   ↓
   POST /forklift/login
   → sessionToken al

2️⃣ GRUP LİSTESİNİ AL (Opsiyonel)
   ↓
   GET /manual-collection/groups
   → Aktif grupları ve EOL'leri gör

3️⃣ EOL SEÇ VE DOLLY'LERİ GÖR
   ↓
   GET /manual-collection/groups/{group_id}/eols/{eol_id}
   → V710-MR-EOL için dolly listesi
   → scanned: true/false bilgisi

4️⃣ DOLLY TARA (Sıralı)
   ↓
   POST /manual-collection/scan
   {
     "group_name": "V710-MR-EOL",
     "barcode": "1062076"
   }
   → İlk dolly tarandı ✅
   
   POST /manual-collection/scan
   {
     "group_name": "V710-MR-EOL",
     "barcode": "1062081"
   }
   → İkinci dolly tarandı ✅
   
   ❌ Sıra atlanırsa HATA!
   POST /manual-collection/scan
   {
     "group_name": "V710-MR-EOL",
     "barcode": "1062087"  // 3. dolly (2'yi atladık)
   }
   → Error: "Sıralı okutma zorunlu! Sıradaki: 1062081"

5️⃣ HATA DÜZELTME (Opsiyonel)
   ↓
   POST /manual-collection/remove-last
   {
     "group_name": "V710-MR-EOL",
     "barcode": "1062081"
   }
   → Son dolly çıkartıldı
   → Tekrar sırayla taranabilir

6️⃣ FARKLI EOL'E GEÇİŞ (Serbest)
   ↓
   POST /manual-collection/scan
   {
     "group_name": "V710-LLS-EOL",  // Farklı EOL
     "barcode": "1062085"
   }
   → V710-LLS-EOL için 1. dolly tarandı ✅
   
   POST /manual-collection/scan
   {
     "group_name": "V710-MR-EOL",  // Geri döndük
     "barcode": "1062087"
   }
   → V710-MR-EOL için 3. dolly tarandı ✅

7️⃣ TARANMIŞ DOLLY'LERİ KONTROL ET
   ↓
   GET /manual-collection/groups/{group_id}/eols/{eol_id}
   → scanned: true olan dolly'leri gör

8️⃣ SUBMIT ET (Operator Paneline Gönder)
   ↓
   POST /manual-collection/mobile-submit
   {
     "eol_name": "V710-MR-EOL"
   }
   → Tüm taranan dolly'ler submit edildi
   → PartNumber oluşturuldu
   → Operator paneline görev olarak düştü ✅
```

---

## 📡 API Endpoint'leri

### 2. Dolly Grup Listesi (Opsiyonel)

**Endpoint:** `GET /manual-collection/groups`

> **Not:** Endpoint adında "manual-collection" var ama bu **normal toplama** işlemidir.

**Headers:**
```
Authorization: Bearer <sessionToken>
```

**Response:**
```json
[
  {
    "group_id": 2,
    "group_name": "710grup",
    "is_active": true,
    "eols": [
      {
        "eol_id": 11,
        "eol_name": "V710-LLS-EOL",
        "dolly_count": 16,
        "scanned_count": 0
      },
      {
        "eol_id": 26,
        "eol_name": "V710-MR-EOL",
        "dolly_count": 31,
        "scanned_count": 3
      }
    ]
  }
]
```

**Notlar:**
- `dolly_count`: Bu EOL'de toplam kaç dolly var
- `scanned_count`: Kaç dolly taranmış (henüz submit edilmemiş)
- Bu endpoint normal dolly toplama için kullanılır

---

### 3. EOL Dolly Listesi

**Endpoint:** `GET /manual-collection/groups/{group_id}/eols/{eol_id}`

**Örnek:** `GET /manual-collection/groups/2/eols/26`

**Headers:**
```
Authorization: Bearer <sessionToken>
```

**Response:**
```json
{
  "dollys": [
    {
      "dolly_no": 1062076,
      "scanned": true,
      "vin_no": "TANRSE63720\nTANRSE69115\nTANRSE69234\nTANRSE69741\nTANVSE68002\nTANXSE66440\nTANXSE68171\nTANXSE69299"
    },
    {
      "dolly_no": 1062081,
      "scanned": true,
      "vin_no": "TANRSE66471\nTANRSE67948\nTANRSE68716\nTANRSE69762\nTANSSE66624\nTANSSE66947\nTANSSE68120\nTANVSE67672"
    },
    {
      "dolly_no": 1062087,
      "scanned": false,
      "vin_no": "TANLSE66831\nTANRSE68575\nTANRSE70652\nTANRSE70655\nTANVSE67160\nTANXSE66770\nTANXSE68148\nTANXSE68258"
    }
  ]
}
```

**Notlar:**
- `scanned: true`: Bu dolly taranmış (sarı/yeşil renk göster)
- `scanned: false`: Bu dolly henüz taranmamış
- VIN'ler `\n` (newline) ile ayrılmış

---

### 4. Dolly Tara (SCAN)

**Endpoint:** `POST /manual-collection/scan`

**Headers:**
```
Authorization: Bearer <sessionToken>
Content-Type: application/json
```

**Request:**
```json
{
  "group_name": "V710-MR-EOL",
  "barcode": "1062076"
}
```

**Response (Success):**
```json
{
  "success": true,
  "dolly_no": 1062076,
  "message": "Dolly eklendi"
}
```

**Response (Error - Sıra Atlandı):**
```json
{
  "error": "V710-MR-EOL için sıralı okutma zorunlu! Sıradaki dolly: 1062081 (Siz okuttunuz: 1062087)",
  "expected_dolly": 1062081,
  "retryable": true,
  "scanned_count": 1,
  "total_count": 31
}
```

**Response (Error - Zaten Taranmış):**
```json
{
  "error": "Bu dolly zaten taranmış",
  "retryable": true
}
```

**Response (Error - Dolly Bulunamadı):**
```json
{
  "error": "Barkod '1062999' sistemde bulunamadı",
  "retryable": true
}
```

**Response (Error - Yanlış Grup):**
```json
{
  "error": "Bu dolly 'V710-LLS-EOL' grubuna ait, 'V710-MR-EOL' değil",
  "retryable": true
}
```

**Kritik Kurallar:**

1. **Sıralı Okutma Zorunlu (Her EOL için ayrı)**
   ```
   ✅ DOĞRU:
   V710-MR-EOL:  1 → 2 → 3
   V710-LLS-EOL: 1 → 2 → 3
   
   ✅ DOĞRU (Farklı EOL'ler arası geçiş):
   V710-MR-EOL #1 → V710-LLS-EOL #1 → V710-MR-EOL #2 → V710-LLS-EOL #2
   
   ❌ YANLIŞ (Aynı EOL'de atlama):
   V710-MR-EOL: 1 → 3 (2'yi atladık)
   ```

2. **Duplicate Kontrol**
   - Aynı dolly 2 kez taranamaz
   - `"Bu dolly zaten taranmış"` hatası

3. **Grup Kontrolü**
   - Dolly sadece kendi EOL'ünde taranabilir
   - Başka EOL'ün dolly'sini tarayamazsınız

---

### 5. Son Dolly'yi Çıkart (REMOVE LAST)

**Endpoint:** `POST /manual-collection/remove-last`

**Headers:**
```
Authorization: Bearer <sessionToken>
Content-Type: application/json
```

**Request:**
```json
{
  "group_name": "V710-MR-EOL",
  "barcode": "1062081"
}
```

**Response (Success):**
```json
{
  "success": true,
  "dolly_no": 1062081,
  "message": "Dolly çıkartıldı"
}
```

**Response (Error):**
```json
{
  "error": "Bu dolly taranmamış",
  "retryable": true
}
```

**Kullanım Senaryoları:**

1. **Yanlış Dolly Tarandı**
   ```
   Tarama: 1062076 ✅
   Tarama: 1062099 ❌ (Yanlış!)
   Çıkart: 1062099 → Son dolly çıkartıldı
   Tarama: 1062081 ✅ (Doğru)
   ```

2. **Sadece Taranmış Dolly'ler Çıkartılabilir**
   - Submit edilmiş dolly'ler çıkartılamaz
   - Sadece `Status='scanned'` olanlar

---

### 6. Submit (Operator Paneline Gönder)

**Endpoint:** `POST /manual-collection/mobile-submit`

**Headers:**
```
Authorization: Bearer <sessionToken>
Content-Type: application/json
```

**Request:**
```json
{
  "eol_name": "V710-MR-EOL"
}
```

**Response (Success):**
```json
{
  "success": true,
  "submitted_count": 3,
  "vin_count": 24,
  "part_number": "PART-PZ3117683FM5YZ9-V710-MR-EOL-20251224092226",
  "message": "3 dolly (24 VIN) başarıyla submit edildi"
}
```

**Response (Error - Hiç Tarama Yok):**
```json
{
  "error": "Hiç taranmış dolly bulunamadı",
  "retryable": true
}
```

**Submit Sonrası:**

1. **Taranmış dolly'ler operator paneline düşer**
   - Web UI: http://10.25.64.181:8181/operator-panel
   - API: `GET /api/operator/tasks`
   - Operator bu görevi alıp etiketleme işlemi yapar

2. **PartNumber oluşturulur**
   - Format: `PART-{MüşteriRef}-{EOLName}-{Timestamp}`
   - Örnek: `PART-PZ3117683FM5YZ9-V710-MR-EOL-20251224092226`
   - **TEK** batch için **TEK** PartNumber (tüm dolly'ler aynı)

3. **Status değişir**
   - `scanned` → `pending`
   - Artık operator bu görevi alıp işleyebilir

4. **DollyEOLInfo'dan silinir**
   - Dolly artık toplama listesinde görünmez
   - Tekrar taranamaz
   
> **Normal İş Akışı:** Android'den dolly taranır → Submit edilir → Operator paneline düşer → Operator etiketler → Sevkiyata hazır

---

## ⚠️ Hata Yönetimi

### HTTP Status Kodları

| Kod | Anlamı | Aksiyon |
|-----|--------|---------|
| 200 | Başarılı | Devam et |
| 400 | Hatalı istek | Kullanıcıya göster, düzelt |
| 401 | Kimlik doğrulama hatası | Yeniden login yap |
| 404 | Bulunamadı | Kullanıcıya bilgi ver |
| 409 | Conflict (duplicate) | Kullanıcıya göster |
| 500 | Sunucu hatası | Retry yap |

### Error Response Formatı

```json
{
  "error": "Hata mesajı",
  "retryable": true,
  "expected_dolly": 1062081,  // Opsiyonel
  "scanned_count": 1,         // Opsiyonel
  "total_count": 31           // Opsiyonel
}
```

### Retry Stratejisi

```java
// Pseudo-code
if (response.retryable && retryCount < 3) {
    Thread.sleep(1000 * retryCount);  // Exponential backoff
    retry();
} else {
    showErrorToUser(response.error);
}
```

---

## 🧪 Test Senaryoları

### Test 1: Başarılı İş Akışı

```bash
# 1. Login
curl -X POST http://10.25.64.181:8181/api/forklift/login \
  -H "Content-Type: application/json" \
  -d '{"operatorBarcode": "TEST001", "operatorName": "Test User"}'
# Response: sessionToken al

# 2. Dolly listesini gör
curl -X GET http://10.25.64.181:8181/api/manual-collection/groups/2/eols/26 \
  -H "Authorization: Bearer <TOKEN>"

# 3. İlk dolly'yi tara
curl -X POST http://10.25.64.181:8181/api/manual-collection/scan \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"group_name": "V710-MR-EOL", "barcode": "1062076"}'
# Response: success: true

# 4. İkinci dolly'yi tara
curl -X POST http://10.25.64.181:8181/api/manual-collection/scan \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"group_name": "V710-MR-EOL", "barcode": "1062081"}'
# Response: success: true

# 5. Submit et
curl -X POST http://10.25.64.181:8181/api/manual-collection/mobile-submit \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"eol_name": "V710-MR-EOL"}'
# Response: success: true, part_number: "PART-..."
```

### Test 2: Sıra Atlama Hatası

```bash
# 1. İlk dolly
curl -X POST .../scan \
  -d '{"group_name": "V710-MR-EOL", "barcode": "1062076"}'
# ✅ Success

# 2. 3. dolly (2'yi atladık)
curl -X POST .../scan \
  -d '{"group_name": "V710-MR-EOL", "barcode": "1062087"}'
# ❌ Error: "Sıralı okutma zorunlu! Sıradaki: 1062081"
```

### Test 3: Farklı EOL Geçişi

```bash
# 1. V710-MR-EOL #1
curl -X POST .../scan \
  -d '{"group_name": "V710-MR-EOL", "barcode": "1062076"}'
# ✅ Success

# 2. V710-LLS-EOL #1 (Farklı EOL)
curl -X POST .../scan \
  -d '{"group_name": "V710-LLS-EOL", "barcode": "1062085"}'
# ✅ Success (Farklı EOL'e geçiş serbest)

# 3. V710-MR-EOL #2 (Geri döndük)
curl -X POST .../scan \
  -d '{"group_name": "V710-MR-EOL", "barcode": "1062081"}'
# ✅ Success
```

### Test 4: Geri Alma

```bash
# 1. İlk dolly
curl -X POST .../scan \
  -d '{"group_name": "V710-MR-EOL", "barcode": "1062076"}'
# ✅ Success

# 2. İkinci dolly
curl -X POST .../scan \
  -d '{"group_name": "V710-MR-EOL", "barcode": "1062081"}'
# ✅ Success

# 3. Son dolly'yi çıkart
curl -X POST .../remove-last \
  -d '{"group_name": "V710-MR-EOL", "barcode": "1062081"}'
# ✅ Success - 1062081 çıkartıldı

# 4. Yeniden tara
curl -X POST .../scan \
  -d '{"group_name": "V710-MR-EOL", "barcode": "1062081"}'
# ✅ Success
```

---

## 📊 UI Önerileri

### Dolly Listesi Gösterimi

```
┌────────────────────────────────────────┐
│ 📦 V710-MR-EOL (3/31 tarandı)         │
├────────────────────────────────────────┤
│ ✅ #1  1062076  [8 VIN]  TARANDI      │
│ ✅ #2  1062081  [8 VIN]  TARANDI      │
│ ⬜ #3  1062087  [8 VIN]  BEKLİYOR     │
│ ⬜ #4  1062093  [8 VIN]  BEKLİYOR     │
│ ⬜ #5  1062102  [8 VIN]  BEKLİYOR     │
│                                        │
│ [🔍 Barkod Tara] [⬅️ Geri Al]         │
│ [✅ Submit Et (3 dolly)]               │
└────────────────────────────────────────┘
```

### Renk Kodları

- 🟢 **Yeşil**: Taranmış dolly (`scanned: true`)
- ⚪ **Gri**: Henüz taranmamış
- 🔴 **Kırmızı**: Hata (yanlış sıra, duplicate)
- 🟡 **Sarı**: Sıradaki dolly (highlight)

### Buton Durumları

```java
// Pseudo-code
if (scannedCount > 0) {
    btnRemoveLast.setEnabled(true);
    btnSubmit.setEnabled(true);
} else {
    btnRemoveLast.setEnabled(false);
    btnSubmit.setEnabled(false);
}
```

---

## 🔧 Önemli Notlar

### 1. PartNumber Yapısı

**Tüm taranmış dolly'ler TEK PartNumber alır:**

```
V710-MR-EOL (Normal Toplama):
  - 1062076 }
  - 1062081 } → PART-PZ3117683FM5YZ9-V710-MR-EOL-20251224092226
  - 1062087 }

V710-LLS-EOL (Normal Toplama):
  - 1062085 }
  - 1062096 } → PART-PZ3117683FM5YZ9-V710-LLS-EOL-20251224092330
```

**Not:** Her EOL için ayrı PartNumber oluşturulur. Web'den yapılan "Manuel Toplama" ise farklı bir PartNumber formatı kullanır.

### 2. Session Yönetimi

- Token 8 saat geçerli
- Token expire olursa:
  ```json
  {
    "error": "authentication_required",
    "message": "Giriş yapmanız gerekiyor. Lütfen barkodunuzu okutun."
  }
  ```
- Yeniden login yapın

### 3. Network Hataları

```java
try {
    response = apiCall();
} catch (NetworkException e) {
    if (isRetryable(response)) {
        showToast("Bağlantı hatası, tekrar deneyin");
        retryLater();
    } else {
        showError("Lütfen internet bağlantınızı kontrol edin");
    }
}
```

### 4. Offline Mod (Gelecek Geliştirme)

**ŞU ANDA DESTEKLENM İYOR!**
Tüm işlemler online olmalıdır. Normal dolly toplama işlemi gerçek zamanlı çalışır.

### 5. Normal Toplama vs Manuel Toplama

**Normal Toplama (Bu Sistem - Android):**
- ✅ Forklift operatörü Android'den tarar
- ✅ Sıralı okutma zorunlu
- ✅ Operator paneline otomatik düşer
- ✅ Günlük operasyon

**Manuel Toplama (Web - Acil Durum):**
- ⚠️ Sadece web üzerinden
- ⚠️ Acil durumlar için
- ⚠️ Farklı PartNumber formatı
- ⚠️ Android uygulaması kullanmaz

---

## 📞 Destek

**Sorun yaşarsanız:**

1. **Log Kontrol**: `/logs/app.log` dosyasını kontrol edin
2. **API Response**: Hata mesajlarını kaydedin
3. **Network**: Ping testi yapın: `ping 10.25.64.181`
4. **Token**: Token expire olmuş olabilir, yeniden login yapın

**Test Ortamı:**
- URL: `http://10.25.64.181:8181/api`
- Test Operatör: `TESTOP001` / `Test User`

---

## ✅ Checklist - Android Developer

Uygulamanızda şunları implement edin:

- [ ] Login ekranı (barcode scan)
- [ ] Token yönetimi (8 saat expire)
- [ ] EOL seçim ekranı
- [ ] Dolly listesi (scanned durumu göster)
- [ ] Barcode scanner entegrasyonu
- [ ] Sıralı okutma kontrol UI'ı
- [ ] "Geri Al" butonu
- [ ] "Submit" butonu
- [ ] Hata mesajları (Toast/Dialog)
- [ ] Network hata yönetimi
- [ ] Retry mekanizması
- [ ] Loading indicator'ları
- [ ] Offline durum kontrolü

---

**Son Güncelleme:** 24 Aralık 2025  
**API Versiyonu:** v1.0  
**Hazırlayan:** HarmonyEcoSystem Backend Team
