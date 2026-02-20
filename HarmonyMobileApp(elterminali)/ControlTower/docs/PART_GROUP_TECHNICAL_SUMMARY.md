# 🏗️ Part ve Grup Yapısı - Teknik Özet

## 📋 Veri Modeli Hiyerarşisi

```
DollyGroup (Grup Tanımı)
    ├── Id: 1
    ├── Name: "V710-MR Montaj Grubu"
    ├── Description: "V710 model montaj hattı dolly'leri"
    └── DollyGroupEOL (Grup içindeki EOL'ler)
            ├── PWorkStationId: 42 (EOL ID)
            ├── Tag: "both" / "asn" / "irsaliye"
            └── PWorkStation (Üretim Hattı)
                    ├── WorkStationId: 42
                    ├── WorkStationName: "V710-MR-EOL"
                    ├── WorkStationNumber: "EOL-001"
                    └── DollyEOLInfo (Bu hattan gelen dolly'ler)
                            ├── DollyNo: "5170427"
                            ├── VinNo: "VIN001\nVIN002\nVIN003"
                            ├── CustomerReferans: "CUST123"
                            ├── EOLName: "V710-MR-EOL"
                            ├── EOLID: "42"
                            ├── Adet: 3
                            └── EOLDollyBarcode: "BARCODE123"
```

---

## 🔄 İş Akışı ve Veri Tabanı Değişiklikleri

### Adım 1: Üretim Hattından Dolly Gelir

```sql
-- DollyEOLInfo tablosuna üretim hattından veri gelir
INSERT INTO DollyEOLInfo (
    DollyNo, VinNo, CustomerReferans, EOLName, EOLID, 
    Adet, EOLDollyBarcode, EOLDate
)
VALUES (
    '5170427', 'VIN001\nVIN002\nVIN003', 'CUST123', 
    'V710-MR-EOL', '42', 3, 'BARCODE123', GETDATE()
)
```

**Durum:** Dolly beklemede, henüz taranmadı.

---

### Adım 2: Forklift Operatörü Dolly'yi Tarar

```http
POST /api/forklift/scan
{
  "dollyNo": "5170427"
}
```

**Backend İşlemleri:**

1. **DollyEOLInfo'dan Oku**
```sql
SELECT * FROM DollyEOLInfo 
WHERE DollyNo = '5170427'
```

2. **DollySubmissionHold'a Kaydet (VIN breakdown ile)**
```sql
-- Her VIN için ayrı kayıt
INSERT INTO DollySubmissionHold (
    DollyNo, VinNo, Status, TerminalUser, LoadingSessionId,
    PartNumber, ScanOrder, CustomerReferans, EOLName, EOLID,
    Adet, CreatedAt, UpdatedAt
)
VALUES 
    ('5170427', 'VIN001', 'scanned', 'MEHMET', 'LOAD_20251214_MEHMET', 
     'PART-20251214-ABC', 1, 'CUST123', 'V710-MR-EOL', '42', 
     3, GETUTCDATE(), GETUTCDATE()),
    ('5170427', 'VIN002', 'scanned', 'MEHMET', 'LOAD_20251214_MEHMET', 
     'PART-20251214-ABC', 1, 'CUST123', 'V710-MR-EOL', '42', 
     3, GETUTCDATE(), GETUTCDATE()),
    ('5170427', 'VIN003', 'scanned', 'MEHMET', 'LOAD_20251214_MEHMET', 
     'PART-20251214-ABC', 1, 'CUST123', 'V710-MR-EOL', '42', 
     3, GETUTCDATE(), GETUTCDATE())
```

**ÖNEMLİ:** DollyEOLInfo'dan **SİLİNMEZ**, sadece okunur. Manuel koleksiyonda silinir.

**Durum:** Dolly tarandı, status = "scanned"

---

### Adım 3: Forklift Operatörü Yüklemeyi Tamamlar

```http
POST /api/forklift/complete-loading
{
  "loadingSessionId": "LOAD_20251214_MEHMET"
}
```

**Backend İşlemleri:**

```sql
-- Tüm VIN'lerin status'ünü güncelle
UPDATE DollySubmissionHold
SET Status = 'loading_completed',
    UpdatedAt = GETUTCDATE()
WHERE LoadingSessionId = 'LOAD_20251214_MEHMET'
  AND Status = 'scanned'
```

**Durum:** Yükleme tamamlandı, web operatör bekliyor, status = "loading_completed"

---

### Adım 4: Web Operatör Sefer No ve Plaka Girer

```http
POST /api/operator/complete-shipment
{
  "loadingSessionId": "LOAD_20251214_MEHMET",
  "seferNumarasi": "SFR001",
  "plakaNo": "34 ABC 123",
  "shippingType": "both"
}
```

**Backend İşlemleri:**

1. **DollySubmissionHold'u Güncelle**
```sql
UPDATE DollySubmissionHold
SET Status = 'completed',
    SeferNumarasi = 'SFR001',
    PlakaNo = '34 ABC 123',
    SubmittedAt = GETUTCDATE(),
    CompletedAt = GETUTCDATE(),
    UpdatedAt = GETUTCDATE()
WHERE LoadingSessionId = 'LOAD_20251214_MEHMET'
  AND Status = 'loading_completed'
```

2. **SeferDollyEOL'e Kaydet (CEVA'ya gönderilecek)**
```sql
INSERT INTO SeferDollyEOL (
    SeferNumarasi, PlakaNo, DollyNo, VinNo, Lokasyon,
    CustomerReferans, Adet, EOLName, EOLID, EOLDate,
    TerminalUser, TerminalDate, PartNumber, SendToASN, SendToIrsaliye
)
SELECT 
    SeferNumarasi, PlakaNo, DollyNo, VinNo, 'GHZNA',
    CustomerReferans, Adet, EOLName, EOLID, CONVERT(date, CreatedAt),
    TerminalUser, GETUTCDATE(), PartNumber,
    CASE WHEN ShippingType IN ('asn', 'both') THEN 1 ELSE 0 END,
    CASE WHEN ShippingType IN ('irsaliye', 'both') THEN 1 ELSE 0 END
FROM DollySubmissionHold
WHERE LoadingSessionId = 'LOAD_20251214_MEHMET'
  AND Status = 'completed'
```

3. **CEVA API'sine Gönder**
```python
# ASN gönder
if shipping_type in ['asn', 'both']:
    ceva_service.send_asn(sefer_numarasi, plaka_no, dollys)

# İrsaliye gönder
if shipping_type in ['irsaliye', 'both']:
    ceva_service.send_irsaliye(sefer_numarasi, plaka_no, dollys)
```

**Durum:** Sevkiyat tamamlandı, CEVA'ya gönderildi, status = "completed"

---

## 📦 Part Number ve Grup İlişkisi

### PartNumber Nedir?

**PartNumber**, bir grup dolly'yi tanımlayan benzersiz bir ID'dir. Aynı yükleme seansındaki tüm dolly'lerde aynıdır.

**Format:**
```
PART-{Tarih}-{RandomID}
veya
MANUEL-{CustomerRef}-{EOL}-{Timestamp}-{Random}
```

**Örnek:**
```
PART-20251214-ABC123
MANUEL-CUST123-V710MR-20251214120000-A1B2C3D4
```

### Grup ve Part İlişkisi

#### 1. Forklift Yükleme (Otomatik Part)

```
LoadingSessionId = "LOAD_20251214_MEHMET"
    ↓
Backend otomatik PartNumber oluşturur: "PART-20251214-ABC123"
    ↓
Tüm dolly'ler bu PartNumber ile işaretlenir
    ↓
PartNumber = Grup ID
```

**Örnek:**
```
DollyNo  | VinNo  | PartNumber          | LoadingSessionId
---------|--------|---------------------|--------------------
5170427  | VIN001 | PART-20251214-ABC   | LOAD_20251214_MEHMET
5170427  | VIN002 | PART-20251214-ABC   | LOAD_20251214_MEHMET
5170428  | VIN003 | PART-20251214-ABC   | LOAD_20251214_MEHMET
5170429  | VIN004 | PART-20251214-ABC   | LOAD_20251214_MEHMET
```

Bu 4 VIN (2 dolly + VIN breakdown) **aynı grup**ta.

#### 2. Manuel Toplama (Manuel Part)

```
Operatör grup seçer: "V710-MR-EOL"
    ↓
Dolly'leri sırayla tarar
    ↓
Backend PartNumber oluşturur: "MANUEL-CUST123-V710MR-20251214-XYZ"
    ↓
Submit edilen tüm dolly'ler bu PartNumber ile gruplanır
```

---

## 🗂️ DollyGroup (Web Operatör Görev Sisteminde)

### Grup Tanımı (Admin Tarafından Oluşturulan)

```sql
-- Grup oluşturma
INSERT INTO DollyGroup (Name, Description, IsActive, CreatedAt, UpdatedAt)
VALUES ('V710-MR Montaj Grubu', 'V710 model montaj hattı', 1, GETUTCDATE(), GETUTCDATE())

-- Gruba EOL ekleme
INSERT INTO DollyGroupEOL (GroupId, PWorkStationId, Tag)
VALUES 
    (1, 42, 'both'),      -- V710-MR-EOL
    (1, 43, 'asn'),       -- V710-FR-EOL (sadece ASN)
    (1, 44, 'irsaliye')   -- V710-LR-EOL (sadece İrsaliye)
```

### Web Operatör Görev Oluşturma

```http
POST /api/web-operator/create-manual-task
{
  "group_id": 1,
  "task_count": 5,
  "shipping_tag": "both"
}
```

**Backend İşlemleri:**

```sql
-- Her görev için WebOperatorTask oluştur
INSERT INTO WebOperatorTask (
    PartNumber, Status, GroupId, GroupTag, TotalItems, ProcessedItems,
    CanSubmitASN, CanSubmitIrsaliye, CreatedAt, UpdatedAt
)
VALUES 
    ('PART-V710-TASK-001', 'pending', 1, 'both', 0, 0, 1, 1, GETUTCDATE(), GETUTCDATE()),
    ('PART-V710-TASK-002', 'pending', 1, 'both', 0, 0, 1, 1, GETUTCDATE(), GETUTCDATE()),
    ('PART-V710-TASK-003', 'pending', 1, 'both', 0, 0, 1, 1, GETUTCDATE(), GETUTCDATE()),
    ('PART-V710-TASK-004', 'pending', 1, 'both', 0, 0, 1, 1, GETUTCDATE(), GETUTCDATE()),
    ('PART-V710-TASK-005', 'pending', 1, 'both', 0, 0, 1, 1, GETUTCDATE(), GETUTCDATE())
```

**Durum:** 5 görev oluşturuldu, operatör atanmayı bekliyor.

---

## 🔍 Android Ekibi İçin Kritik Noktalar

### 1. VIN Breakdown (Çok Önemli!)

**Backend'den gelen:**
```json
{
  "vin_no": "VIN001\nVIN002\nVIN003"
}
```

**Android'de parse et:**
```kotlin
val vins = response.vin_no.split("\n")
// ["VIN001", "VIN002", "VIN003"]

// UI'da göster
val displayText = vins.joinToString(", ")
// "VIN001, VIN002, VIN003"
```

### 2. Status Değişiklikleri

```kotlin
enum class DollyStatus(val value: String) {
    SCANNED("scanned"),           // Forklift taradı
    LOADING_COMPLETED("loading_completed"),  // Forklift tamamladı
    COMPLETED("completed")         // Web operatör tamamladı
}
```

### 3. LoadingSessionId vs PartNumber

```kotlin
// Forklift işlemlerinde
val loadingSessionId = "LOAD_20251214_MEHMET"  // Session ID

// Backend'den dönen PartNumber (grup ID gibi)
val partNumber = "PART-20251214-ABC123"

// İlişki:
// 1 LoadingSessionId → 1 PartNumber
// 1 PartNumber → N DollySubmissionHold kayıtları (VIN breakdown)
```

### 4. Manuel Toplama - Grup ve EOL Farkı

```
DollyGroup (Admin tanımladı)
    ├── V710-MR Montaj Grubu
    └── İçinde 3 EOL var:
            ├── V710-MR-EOL (42)
            ├── V710-FR-EOL (43)
            └── V710-LR-EOL (44)

Manuel Toplama API'si:
    → EOL bazlı çalışır (PWorkStation.WorkStationName)
    → Grup değil, direkt EOL seç!
```

**Android UI:**
```
Manuel Toplama Ekranı:
    ├── V710-MR-EOL (8 dolly, 3 tarandı)  ← EOL
    ├── V710-FR-EOL (5 dolly, 0 tarandı)  ← EOL
    └── V720-LR-EOL (12 dolly, 12 tarandı) ← EOL
```

### 5. Error Handling - Retryable Logic

```kotlin
fun handleApiError(error: ApiError) {
    when {
        error.retryable -> {
            // Retry butonu göster
            showRetryButton {
                retryLastOperation()
            }
        }
        error.error.contains("zaten taranmış") -> {
            // Kullanıcıya bildir, başka dolly taratır
            showToast("Bu dolly zaten tarandı!")
        }
        error.error.contains("Oturum geçersiz") -> {
            // Login ekranına yönlendir
            clearTokenAndNavigateToLogin()
        }
        else -> {
            // Genel hata mesajı
            showErrorDialog(error.error)
        }
    }
}
```

---

## 📞 Backend Developer'a Sorulacak Sorular (Hazır Liste)

### 1. Data Flow
- [ ] DollyEOLInfo'dan ne zaman silinir? (Manuel koleksiyonda mı?)
- [ ] PartNumber backend'de otomatik oluşuyor mu yoksa client gönderir mi?
- [ ] LoadingSessionId formatı nedir? (LOAD_{DATE}_{OPERATOR})

### 2. Error Scenarios
- [ ] Aynı dolly 2 kez taranırsa ne olur?
- [ ] Yanlış grup/EOL'de dolly taranırsa ne olur?
- [ ] Network kesintisinde transaction rollback olur mu?

### 3. Edge Cases
- [ ] Bir dolly'de kaç VIN olabilir? (Max limit var mı?)
- [ ] Token expire olursa background request'ler ne olur?
- [ ] Offline mode desteklenecek mi?

### 4. Performance
- [ ] Büyük dolly listelerinde pagination var mı?
- [ ] Real-time update için WebSocket var mı yoksa polling mu?

---

## 🎯 Özet: Android Ekibi Yapacaklar

### ✅ Yapılması Gerekenler

1. **API Entegrasyonu**
   - Retrofit + OkHttp
   - Token management (SharedPreferences)
   - Error handling (retry logic)

2. **Ekranlar**
   - Login (barkod okuyucu)
   - Ana Menü
   - Dolly Yükleme
   - Manuel Toplama (Grup → Dolly listesi)

3. **UI/UX**
   - Büyük butonlar (forklift operatörleri için)
   - Barkod okuyucu entegrasyonu
   - Loading/error states
   - VIN breakdown gösterimi (virgülle ayrılmış)

4. **Local Storage**
   - Token cache
   - Operator bilgileri
   - (Optional) Offline mode için Room Database

5. **Testing**
   - API test cases
   - UI test cases
   - Barcode scanner test

---

**Versiyon:** 1.0  
**Tarih:** 14 Aralık 2025  
**Hazırlayan:** Backend Code Analysis
