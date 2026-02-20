# 📋 BACKEND API - GRUP MANTIĞI SPESİFİKASYONU

**Tarih:** 12 Ocak 2026  
**Konu:** Mobil Uygulama - Backend API Entegrasyonu  
**Öncelik:** 🔴 YÜKSEK - Uygulama şu an çalışmıyor

---

## 🚨 **ACİL SORUNLAR**

### ✅ **1. dolly_order_no NULL geliyor - ÇÖZÜLDİ**
```json
// DÜZELTME ÖNCESİ:
{
  "dolly_no": "1070744",
  "dolly_order_no": null,  ← NULL geliyordu
  "vin_no": "TANRTL77984\nTANXTL79360",
  "scanned": false
}

// ✅ ŞİMDİ (DÜZELDİ):
{
  "dolly_no": "1070744",
  "dolly_order_no": "1",  ← Artık dolu geliyor!
  "vin_no": "TANRTL77984\nTANXTL79360",
  "scanned": false
}
```

**Çözüm:** SQL query'ye `DollyOrderNo` eklendi ve response mapping'e dahil edildi.
**Tarih:** 12 Ocak 2026
**Durum:** ✅ Çözüldü - Service restart sonrası aktif

---

### ✅ **2. Grup adı/EOL adı karışıklığı - ÇÖZÜLDİ**
```
// DÜZELTME ÖNCESİ:
Backend'den gelen hata:
"Bu dolly 'V710-LLS-EOL' grubuna ait, '710grup' değil"

// SORUN:
Backend EOL adını grup adı ile karşılaştırıyordu (yanlış)

// ✅ ŞİMDİ (DÜZELDİ):
- Backend DollyGroup ve DollyGroupEOL tablolarını kullanıyor
- Dolly'nin EOLID'si grubun EOL listesinde kontrol ediliyor
- Grup adı ve EOL adı doğru şekilde ayrılıyor
```

**Çözüm:** Validation logic tamamen yeniden yazıldı - DollyGroup → DollyGroupEOL ilişkisi kullanılıyor.
**Tarih:** 12 Ocak 2026
**Durum:** ✅ Çözüldü - Grup yapısı düzgün çalışıyor

---

### ✅ **3. ID Uyumsuzluğu Sorunu - ÇÖZÜLDÜ**

**Sorun:** `DollyEOLInfo.EOLID` (104) ve `PWorkStation.Id` (11/27) farklı ID sistemleri kullanıyordu.

**Sonuç:** Grup validasyonu başarısız oluyordu çünkü EOLID ile PWorkStationId eşleşmiyordu.

**Çözüm:** EOL Name üzerinden PWorkStation bulunup grup eşleştirmesi yapıldı.

**Tarih:** 12 Ocak 2026 11:51  
**Durum:** ✅ Çözüldü - EOL Name bazlı eşleştirme aktif

---

## 🎯 **GRUP MANTIĞI - NASIL ÇALIŞMALI**

### **Temel Konsept:**
Farklı EOL istasyonlarından gelen dollyler **aynı tıra/sevkiyata** (aynı PartNumber'a) yüklenebilir.

### **Örnek Yapı:**
```
710grup (Grup)
├─ PartNumber: PART-PZ3117683AGM5YZ-V710FR-V710LLS-V710MR-EOL-20260112140000
│
├─ V710-FR-EOL (EOL İstasyonu 1)
│   ├─ Dolly: 1070001 (order: 1)
│   ├─ Dolly: 1070002 (order: 2)
│   └─ Dolly: 1070003 (order: 3)
│
├─ V710-LLS-EOL (EOL İstasyonu 2)
│   ├─ Dolly: 1070744 (order: 1)
│   ├─ Dolly: 1070787 (order: 2)
│   └─ Dolly: 1070845 (order: 3)
│
└─ V710-MR-EOL (EOL İstasyonu 3)
    ├─ Dolly: 1070999 (order: 1)
    └─ Dolly: 1071000 (order: 2)

→ Tüm dollyler AYNI GRUP (710grup)
→ Tüm dollyler AYNI PARTNUMBER
→ Farklı EOL'lerden geliyor (sorun değil!)
→ Her EOL kendi içinde sıralı
```

---

## 📊 **VERİTABANI YAPISI (ÖNERİ)**

### **Tablo: groups**
```sql
CREATE TABLE groups (
    id INT PRIMARY KEY AUTO_INCREMENT,
    group_name VARCHAR(100) NOT NULL,           -- "710grup"
    part_number VARCHAR(200) NOT NULL,          -- "PART-PZ3117683AGM5YZ-..."
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active'
);
```

### **Tablo: eol_stations**
```sql
CREATE TABLE eol_stations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    group_id INT NOT NULL,                      -- FK → groups.id
    eol_name VARCHAR(100) NOT NULL,             -- "V710-LLS-EOL"
    dolly_count INT DEFAULT 0,
    scanned_count INT DEFAULT 0,
    FOREIGN KEY (group_id) REFERENCES groups(id)
);
```

### **Tablo: dollys**
```sql
CREATE TABLE dollys (
    id INT PRIMARY KEY AUTO_INCREMENT,
    eol_station_id INT NOT NULL,                -- FK → eol_stations.id
    dolly_no VARCHAR(50) NOT NULL,              -- "1070744"
    dolly_order_no VARCHAR(10) NOT NULL,        -- "1", "2", "3" (EOL içindeki sırası)
    vin_no TEXT,                                -- "VIN1\nVIN2\nVIN3"
    scanned BOOLEAN DEFAULT FALSE,
    scanned_at TIMESTAMP NULL,
    part_number VARCHAR(200),                   -- Aynı grup için aynı
    FOREIGN KEY (eol_station_id) REFERENCES eol_stations(id)
);
```

---

## 🔌 **API ENDPOINT'LERİ**

### **1️⃣ GET /api/manual-collection/groups**
**Amaç:** Tüm grupları ve EOL'leri listele

**Response:**
```json
[
  {
    "group_id": 1,
    "group_name": "710grup",
    "part_number": "PART-PZ3117683AGM5YZ-V710FR-V710LLS-V710MR-EOL-20260112140000",
    "total_dolly_count": 18,
    "total_scanned_count": 5,
    "eols": [
      {
        "eol_id": 1,
        "eol_name": "V710-FR-EOL",
        "dolly_count": 6,
        "scanned_count": 2
      },
      {
        "eol_id": 2,
        "eol_name": "V710-LLS-EOL",
        "dolly_count": 6,
        "scanned_count": 2
      },
      {
        "eol_id": 3,
        "eol_name": "V710-MR-EOL",
        "dolly_count": 6,
        "scanned_count": 1
      }
    ]
  }
]
```

**ÖNEMLI:**
- ✅ `group_name` = Asıl grup adı ("710grup")
- ✅ `eol_name` = EOL istasyon adı ("V710-LLS-EOL")
- ✅ `part_number` = Tüm grup için aynı
- ✅ Bir grup birden fazla EOL içerebilir

---

### **2️⃣ GET /api/manual-collection/groups/{groupId}/eols/{eolId}**
**Amaç:** Belirli bir EOL'ün dollylerini listele

**Request:**
```
GET /api/manual-collection/groups/1/eols/2
```

**Response:**
```json
{
  "group_id": 1,
  "group_name": "710grup",
  "eol_id": 2,
  "eol_name": "V710-LLS-EOL",
  "part_number": "PART-PZ3117683AGM5YZ-V710FR-V710LLS-V710MR-EOL-20260112140000",
  "dollys": [
    {
      "dolly_no": "1070744",
      "dolly_order_no": "1",
      "vin_no": "TANRTL77984\nTANXTL79360",
      "scanned": false
    },
    {
      "dolly_no": "1070787",
      "dolly_order_no": "2",
      "vin_no": "TANLTL71718\nTANXTL75908",
      "scanned": false
    },
    {
      "dolly_no": "1070845",
      "dolly_order_no": "3",
      "vin_no": "TANLTL75159\nTANXTL75758",
      "scanned": false
    },
    {
      "dolly_no": "1070869",
      "dolly_order_no": "4",
      "vin_no": "TANRTL71798\nTANXTL75689",
      "scanned": false
    }
  ]
}
```

**KRİTİK NOKTALAR:**
- 🔴 `dolly_order_no` **MUTLAKA DOLU** olmalı! (NULL olmamalı)
- ✅ `vin_no` multiline string (VIN'ler `\n` ile ayrılmış)
- ✅ `group_name` = "710grup" (asıl grup adı)
- ✅ `eol_name` = "V710-LLS-EOL" (EOL istasyonu adı)
- ✅ Dollyler `dolly_order_no`'ya göre sıralı

---

### **3️⃣ POST /api/manual-collection/scan**
**Amaç:** Dolly okut ve kaydet

**Request Body:**
```json
{
  "group_name": "710grup",
  "eol_name": "V710-LLS-EOL",
  "barcode": "1070744"
}
```

**Backend İşlem Adımları:**

1. **Dolly'yi bul:**
   ```sql
   SELECT * FROM dollys WHERE dolly_no = '1070744'
   ```

2. **Grup kontrolü:**
   ```sql
   -- Dolly'nin ait olduğu grup adını al
   SELECT g.group_name, e.eol_name 
   FROM dollys d
   JOIN eol_stations e ON d.eol_station_id = e.id
   JOIN groups g ON e.group_id = g.id
   WHERE d.dolly_no = '1070744'
   
   -- Request ile karşılaştır
   IF dolly.group_name != request.group_name THEN
     RETURN ERROR "Bu dolly '{dolly.group_name}' grubuna ait, '{request.group_name}' değil"
   END IF
   ```

3. **EOL kontrolü:**
   ```sql
   IF dolly.eol_name != request.eol_name THEN
     RETURN ERROR "Bu dolly '{dolly.eol_name}' EOL'üne ait, '{request.eol_name}' değil"
   END IF
   ```

4. **Sıra kontrolü (SADECE AYNI EOL İÇİNDE):**
   ```sql
   -- Bu EOL'de son okutulmuş dolly'nin order_no'sunu al
   SELECT MAX(dolly_order_no) as last_scanned
   FROM dollys d
   JOIN eol_stations e ON d.eol_station_id = e.id
   WHERE e.eol_name = 'V710-LLS-EOL' 
     AND d.scanned = TRUE
   
   -- Sıradaki dolly'yi kontrol et
   expected_order = last_scanned + 1
   
   IF current_dolly.dolly_order_no != expected_order THEN
     -- Sıradaki dolly'yi bul
     SELECT dolly_no FROM dollys 
     WHERE eol_station_id = current_eol_id 
       AND dolly_order_no = expected_order
     
     RETURN ERROR {
       "error": "Dolly sırası yanlış!",
       "expected_dolly": "1070787",
       "received_dolly": "1070845",
       "eol_name": "V710-LLS-EOL"
     }
   END IF
   ```

5. **Başarılıysa kaydet:**
   ```sql
   UPDATE dollys 
   SET scanned = TRUE, 
       scanned_at = NOW() 
   WHERE dolly_no = '1070744'
   ```

**Success Response:**
```json
{
  "success": true,
  "dolly_no": "1070744",
  "message": "Dolly başarıyla okutuldu",
  "eol_name": "V710-LLS-EOL",
  "group_name": "710grup"
}
```

**Error Response (Dolly Sırası Yanlış):**
```json
{
  "success": false,
  "error": "V710-LLS-EOL EOL'de dolly sırası yanlış! Sıradaki dolly '1070787' okutulmalı",
  "expected_dolly": "1070787",
  "received_dolly": "1070845",
  "eol_name": "V710-LLS-EOL"
}
```

**Error Response (Farklı Grup):**
```json
{
  "success": false,
  "error": "Bu dolly 'V820grup' grubuna ait, '710grup' değil",
  "dolly_group_name": "V820grup",
  "request_group_name": "710grup"
}
```

---

### **4️⃣ POST /api/manual-collection/remove-last**
**Amaç:** Son okutulmuş dolly'yi çıkart

**Request Body:**
```json
{
  "group_name": "710grup",
  "eol_name": "V710-LLS-EOL",
  "barcode": "admin_barcode_veya_dolly_no"
}
```

**Backend İşlem:**
```sql
-- Bu EOL'de son okutulmuş dolly'yi bul
SELECT * FROM dollys d
JOIN eol_stations e ON d.eol_station_id = e.id
WHERE e.eol_name = 'V710-LLS-EOL'
  AND d.scanned = TRUE
ORDER BY d.scanned_at DESC
LIMIT 1

-- Çıkart
UPDATE dollys 
SET scanned = FALSE, 
    scanned_at = NULL 
WHERE id = last_dolly.id
```

**Response:**
```json
{
  "success": true,
  "dolly_no": "1070787",
  "message": "Son dolly çıkartıldı"
}
```

---

### **5️⃣ POST /api/manual-collection/mobile-submit**
**Amaç:** EOL'ü tamamla ve Excel'e aktar

**Request Body:**
```json
{
  "eol_name": "V710-LLS-EOL"
}
```

**Backend İşlem:**
```sql
-- Bu EOL'deki scanned dollyları bul
SELECT d.* FROM dollys d
JOIN eol_stations e ON d.eol_station_id = e.id
WHERE e.eol_name = 'V710-LLS-EOL'
  AND d.scanned = TRUE

-- Excel'e aktar
-- Arşivle veya sil
```

**Response:**
```json
{
  "success": true,
  "message": "V710-LLS-EOL başarıyla tamamlandı",
  "submitted_count": 6,
  "vin_count": 35,
  "part_number": "PART-PZ3117683AGM5YZ-V710FR-V710LLS-V710MR-EOL-20260112140000"
}
```

---

## ✅ **İZİN VERİLEN İŞLEMLER**

### **1. Aynı EOL'de sıralı okutma**
```
✅ DOĞRU:
V710-LLS-EOL: D001 (order:1) → D002 (order:2) → D003 (order:3)
```

### **2. Farklı EOL'lere geçiş (aynı grup içinde)**
```
✅ DOĞRU:
710grup grubunda:
  V710-LLS-EOL: D001 (order:1) ✓
  V710-LLS-EOL: D002 (order:2) ✓
  V710-MR-EOL:  D011 (order:1) ✓ ← Farklı EOL'e geçti (İZİN VER)
  V710-LLS-EOL: D003 (order:3) ✓ ← V710-LLS'e geri döndü (İZİN VER)
  V710-MR-EOL:  D012 (order:2) ✓ ← Tekrar V710-MR'e geçti (İZİN VER)

→ Tüm dollyler AYNI GRUP (710grup)
→ Tüm dollyler AYNI PARTNUMBER
→ Her EOL kendi içinde SIRALI
→ EOL'ler arası geçiş SERBEST
```

### **3. Karışık EOL okutma**
```
✅ DOĞRU:
710grup içinde:
  V710-LLS: D001 ✓
  V710-FR:  D101 ✓
  V710-MR:  D201 ✓
  V710-LLS: D002 ✓
  V710-FR:  D102 ✓
  V710-LLS: D003 ✓

→ Farklı EOL'lerden ama aynı grup
→ Her EOL kendi içinde sıralı
→ SORUN YOK!
```

---

## ❌ **ENGELLENMESİ GEREKEN İŞLEMLER**

### **1. Aynı EOL'de dolly atlamak**
```
❌ YANLIŞ:
V710-LLS-EOL: D001 (order:1) ✓
V710-LLS-EOL: D003 (order:3) ✗ ← HATA! D002 (order:2) atlandı

Hata mesajı:
"V710-LLS-EOL EOL'de dolly sırası yanlış! 
 Sıradaki: '1070787' (order:2), 
 Okutulan: '1070845' (order:3)"
```

### **2. Farklı gruba ait dolly**
```
❌ YANLIŞ:
710grup açık
V820grup'tan dolly okutulmaya çalışılıyor ✗

Hata mesajı:
"Bu dolly 'V820grup' grubuna ait, '710grup' değil"
```

### **3. Farklı EOL'e ait dolly (aynı istek EOL'ünde)**
```
❌ YANLIŞ:
Request: eol_name = "V710-LLS-EOL"
Dolly: eol_name = "V710-MR-EOL"

Hata mesajı:
"Bu dolly 'V710-MR-EOL' EOL'üne ait, 'V710-LLS-EOL' değil"
```

---

## 🧪 **TEST SENARYOLARI**

### **Senaryo 1: Normal Sıralı Okutma**
```
1. POST /scan {group: "710grup", eol: "V710-LLS-EOL", barcode: "1070744"}
   → ✅ Success

2. POST /scan {group: "710grup", eol: "V710-LLS-EOL", barcode: "1070787"}
   → ✅ Success

3. POST /scan {group: "710grup", eol: "V710-LLS-EOL", barcode: "1070845"}
   → ✅ Success
```

### **Senaryo 2: Dolly Atlama (HATA)**
```
1. POST /scan {group: "710grup", eol: "V710-LLS-EOL", barcode: "1070744"}
   → ✅ Success (order: 1)

2. POST /scan {group: "710grup", eol: "V710-LLS-EOL", barcode: "1070845"}
   → ❌ Error: "Sıradaki: 1070787 (order:2), Okutulan: 1070845 (order:3)"
```

### **Senaryo 3: Farklı EOL Geçiş (İZİN)**
```
1. POST /scan {group: "710grup", eol: "V710-LLS-EOL", barcode: "1070744"}
   → ✅ Success (V710-LLS order:1)

2. POST /scan {group: "710grup", eol: "V710-LLS-EOL", barcode: "1070787"}
   → ✅ Success (V710-LLS order:2)

3. POST /scan {group: "710grup", eol: "V710-MR-EOL", barcode: "1070999"}
   → ✅ Success (V710-MR order:1) ← Farklı EOL'e geçti

4. POST /scan {group: "710grup", eol: "V710-LLS-EOL", barcode: "1070845"}
   → ✅ Success (V710-LLS order:3) ← V710-LLS'e geri döndü

5. POST /scan {group: "710grup", eol: "V710-MR-EOL", barcode: "1071000"}
   → ✅ Success (V710-MR order:2) ← Tekrar V710-MR'e geçti
```

### **Senaryo 4: Farklı Grup (HATA)**
```
1. 710grup açık

2. POST /scan {group: "710grup", eol: "V710-LLS-EOL", barcode: "V820_DOLLY"}
   → ❌ Error: "Bu dolly 'V820grup' grubuna ait, '710grup' değil"
```

### **Senaryo 5: Remove Last**
```
1. POST /scan {group: "710grup", eol: "V710-LLS-EOL", barcode: "1070744"}
   → ✅ Success

2. POST /scan {group: "710grup", eol: "V710-LLS-EOL", barcode: "1070787"}
   → ✅ Success

3. POST /remove-last {group: "710grup", eol: "V710-LLS-EOL", barcode: "admin"}
   → ✅ Success: "1070787 çıkartıldı"

4. POST /scan {group: "710grup", eol: "V710-LLS-EOL", barcode: "1070787"}
   → ✅ Success (Tekrar okutulabilir)
```

---

## 🔧 **GEÇİCİ MOBİL FİX - ARTIK KALDIRILABİLİR**

✅ **Backend düzeltildi!** Mobil uygulamadaki geçici çözüm artık kaldırılabilir:

```java
// ESKİ (GEÇİCİ FİX):
ManualScanRequest(eolName, eolName, barcode)
// "V710-LLS-EOL", "V710-LLS-EOL", "1070843"

// ✅ YENİ (DOĞRU KULLANIM):
ManualScanRequest(groupName, eolName, barcode)
// "710grup", "V710-LLS-EOL", "1070843"
```

**Durum:** Backend artık `group_name` ve `eol_name` parametrelerini doğru şekilde işliyor.  
**Mobil TODO:** Geçici fix'i kaldırıp doğru parametreleri gönderin.

---

## 📋 **BACKEND YAPILACAKLAR LİSTESİ**

### **Öncelik 1: ACİL**
- [x] `dolly_order_no` field'ını doldur (NULL olmasın) ✅ **12 Ocak 2026**
- [x] Grup adı/EOL adı ayrımını düzelt ✅ **12 Ocak 2026**
- [x] Request validation'ı düzelt (`group_name` ≠ `eol_name`) ✅ **12 Ocak 2026**

### **Öncelik 2: ÖNEMLI**
- [x] Dolly sırası kontrolünü sadece **aynı EOL içinde** yap ✅ **12 Ocak 2026 12:00**
- [x] Farklı EOL geçişlerine izin ver (aynı grup ise) ✅ **12 Ocak 2026 12:00**
- [x] Error response'lara detay ekle (`expected_dolly`, `received_dolly`) ✅ **12 Ocak 2026 12:00**
- [x] DollyOrderNo bazlı sıra kontrolü (DollyNo alfabetik sıralama değil) ✅ **12 Ocak 2026 12:00**

### **Öncelik 3: İYİLEŞTİRME**
- [ ] Grup yapısını PWorkStation ile uyumlu hale getir
- [ ] API dokümantasyonu oluştur
- [ ] Test senaryolarını çalıştır

---

## 📞 **İLETİŞİM**

Sorular için:
- Mobil Geliştirme Ekibi
- Bu doküman: `docs/BACKEND_API_GRUP_SPEC.md`

---

**Son Güncelleme:** 12 Ocak 2026 12:00  
**Durum:** ✅ Tüm kritik sorunlar çözüldü - Production'da aktif
