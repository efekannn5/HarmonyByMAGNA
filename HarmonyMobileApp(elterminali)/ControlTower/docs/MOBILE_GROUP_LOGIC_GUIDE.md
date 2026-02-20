
# 📱 Mobil Uygulama - Grup Mantığı Kullanım Kılavuzu

**Tarih:** 12 Ocak 2026  
**Hedef Kitle:** Mobil (Android) Geliştirme Ekibi  
**Kapsam:** Dolly Gruplama Sistemi ve API Entegrasyonu

---

## 📋 İçindekiler

1. [Grup Mantığı Nedir?](#grup-mantığı-nedir)
2. [Neden Grup Sistemi Var?](#neden-grup-sistemi-var)
3. [PartNumber Yapısı](#partnumber-yapısı)
4. [Okutma Kuralları](#okutma-kuralları)
5. [API Endpoint'leri](#api-endpointleri)
6. [Kullanım Senaryoları](#kullanım-senaryoları)
7. [Hata Durumları](#hata-durumları)
8. [Test Senaryoları](#test-senaryoları)

---

## 🎯 Grup Mantığı Nedir?

**Grup sistemi**, farklı EOL'lerden gelen dollyların **aynı tıra yüklenmesini** sağlayan organizasyon mekanizmasıdır.

### Temel Kavramlar:

| Kavram | Açıklama | Örnek |
|--------|----------|-------|
| **PartNumber** | Grup kimliği (Unique) | `PART-PZ3117683AGM5YZ-V710-MR-EOL-20260108104700` |
| **EOL** | Dolly'nin geldiği üretim hattı | `V710`, `MR`, `V820` |
| **DollyNo** | Fiziksel dolly numarası | `D001`, `D002`, ... |
| **Grup** | Aynı PartNumber'a sahip tüm dollyler | 1 Grup = 1 Tır Yükü |

---

## 🚛 Neden Grup Sistemi Var?

### Problem:
Farklı EOL'lerden gelen dollyler aynı müşteriye veya aynı sevkiyat noktasına gidebilir.

### Çözüm:
**PartNumber bazlı gruplama** ile:
- ✅ Aynı tıra yüklenecek dollyler bir arada takip edilir
- ✅ Farklı EOL'ler aynı grupta olabilir
- ✅ Karışıklık olmadan organize edilir

### Örnek Senaryo:

```
TIR #1 (Grup: PART-ABC123-V710-MR-EOL-...)
├─ V710 EOL
│   ├─ D001 (3 VIN)  ✓ Okutuldu
│   ├─ D002 (5 VIN)  ✓ Okutuldu
│   └─ D003 (2 VIN)  ✗ Henüz okutulmadı
│
└─ MR EOL (Aynı tıra gidecek!)
    ├─ D011 (4 VIN)  ✓ Okutuldu
    └─ D012 (2 VIN)  ✓ Okutuldu

→ Hepsi aynı PartNumber → Aynı tır → Aynı Excel export

TIR #2 (Farklı Grup: PART-XYZ789-V820-EOL-...)
└─ V820 EOL
    ├─ D020 (6 VIN)
    └─ D021 (3 VIN)

→ Farklı PartNumber → Farklı tır → Farklı Excel export
```

---

## 🔑 PartNumber Yapısı

### Format:
```
PART-{PartNo}-{EOL1}-{EOL2}-...-EOL-{Timestamp}
```

### Örnek:
```
PART-PZ3117683AGM5YZ-V710-MR-EOL-20260108104700
     ^^^^^^^^^^^^^^^ ^^^^-^^     ^^^^^^^^^^^^^^
     |               |            |
     Part No         EOL'ler      Oluşturulma Zamanı
                     (Aynı grupta olacak)
```

### Önemli Notlar:
- ✅ **Aynı PartNumber** = Aynı tıra gidecek dollyler
- ✅ **Birden fazla EOL** olabilir (V710-MR gibi)
- ✅ **Timestamp** benzersizlik sağlar
- ❌ **PartNumber değiştirilemez** (sabit kalır)

---

## 📖 Okutma Kuralları

### ✅ İZİN VERİLEN:

#### 1. **Aynı EOL'de Sıralı Okutma**
```
Kural: Aynı EOL'deki dollyler kendi içinde SIRALI okutulmalı
Örnek:
  V710: D001 → D002 → D003 ✓ Doğru
  V710: D001 → D003 → D002 ✗ Yanlış (D002 atlandı)
```

#### 2. **Farklı EOL'ler Arası Geçiş**
```
Kural: Bir EOL'deki dollyler bitmeden başka EOL'e geçilebilir
Örnek:
  V710: D001 → D002 (5 dolly'den sadece 2 okutuldu)
  MR:   D011 → D012 (başka EOL'e geçildi) ✓ Doğru!
  V710: D003 → D004 (V710'a geri dönüldü) ✓ Doğru!
```

#### 3. **Karışık EOL Okutma**
```
Senaryo: Operatör istediği sırada EOL değiştirebilir

V710: D001 ✓
V710: D002 ✓
MR:   D011 ✓  ← Farklı EOL'e geçiş
V710: D003 ✓  ← V710'a geri dönüş
MR:   D012 ✓  ← Tekrar MR
V710: D004 ✓  ← Tekrar V710

→ Tüm dollyler AYNI PARTNUMBER'da → AYNI TIR → Sorun yok! ✓
```

### ❌ İZİN VERİLMEYEN:

#### 1. **Aynı EOL'de Dolly Atlamak**
```
V710: D001 ✓
V710: D003 ✗ HATA! (D002 atlandı)

→ Mobil uygulama bunu ENGELLEMELİ!
```

#### 2. **Farklı PartNumber Karıştırmak**
```
PART-ABC (Grup 1): D001 ✓
PART-XYZ (Grup 2): D020 ✗ HATA! (Farklı grup!)

→ Aynı session'da sadece 1 PartNumber olmalı!
```

---

## 🔌 API Endpoint'leri

### 1. Manuel Toplama - VIN Okutma

**Endpoint:**
```
POST /api/manuel-toplama-submit
```

**Request Body:**
```json
{
  "username": "operator123",
  "dolly_order_no": "ORD12345",
  "dolly_no": "D001",
  "part_number": "PZ3117683AGM5YZ",
  "customer_referans": "MAGNA",
  "eol_name": "V710",
  "vinler": [
    {
      "vin_no": "VIN001",
      "adet": 1
    },
    {
      "vin_no": "VIN002",
      "adet": 1
    }
  ],
  "sefer_no": "SF001",
  "plaka_no": "34ABC123",
  "irsaliye_no": "IR2024001",
  "lokasyon": "GHZNA"
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "2 VIN başarıyla kaydedildi",
  "part_number": "PART-PZ3117683AGM5YZ-V710-MR-EOL-20260112140000",
  "dolly_no": "D001",
  "eol_name": "V710",
  "total_vins": 2,
  "scan_order_start": 1,
  "scan_order_end": 2
}
```

**Response (Error - Dolly Atlandı):**
```json
{
  "success": false,
  "error": "Dolly sırası yanlış! Önceki dolly (D001) okutulmadan D003 okutulamaz.",
  "expected_dolly": "D001",
  "received_dolly": "D003",
  "eol_name": "V710"
}
```

---

### 2. Grup Bilgisi Sorgulama

**Endpoint:**
```
GET /api/group-status/{part_number}
```

**Response:**
```json
{
  "part_number": "PART-PZ3117683AGM5YZ-V710-MR-EOL-20260112140000",
  "eol_groups": {
    "V710": {
      "total_dollys": 10,
      "scanned_dollys": 5,
      "last_dolly": "D005",
      "pending_dollys": ["D006", "D007", "D008", "D009", "D010"]
    },
    "MR": {
      "total_dollys": 8,
      "scanned_dollys": 3,
      "last_dolly": "D012",
      "pending_dollys": ["D013", "D014", "D015", "D016", "D017"]
    }
  },
  "total_vins": 45,
  "scanned_vins": 23,
  "status": "pending"
}
```

---

## 🎬 Kullanım Senaryoları

### Senaryo 1: Normal Sıralı Okutma (Tek EOL)

```
Operatör: V710 hattında dolly okutacak

Adım 1: D001 okut
  POST /api/manuel-toplama-submit
  {
    "dolly_no": "D001",
    "eol_name": "V710",
    "vinler": [...]
  }
  → ✓ Başarılı (İlk dolly)

Adım 2: D002 okut
  POST /api/manuel-toplama-submit
  {
    "dolly_no": "D002",
    "eol_name": "V710",
    "vinler": [...]
  }
  → ✓ Başarılı (Sıralı)

Adım 3: D003 okut
  POST /api/manuel-toplama-submit
  {
    "dolly_no": "D003",
    "eol_name": "V710",
    "vinler": [...]
  }
  → ✓ Başarılı (Sıralı)
```

---

### Senaryo 2: Karışık EOL Okutma (Farklı EOL'lere Geçiş)

```
Operatör: V710'da başladı, MR'a geçti, tekrar V710'a döndü

Adım 1: V710 - D001 okut
  → ✓ Başarılı

Adım 2: V710 - D002 okut
  → ✓ Başarılı

Adım 3: MR - D011 okut (Farklı EOL'e geçiş!)
  {
    "dolly_no": "D011",
    "eol_name": "MR",  ← Farklı EOL
    ...
  }
  → ✓ Başarılı (Aynı PartNumber'da olduğu için sorun yok)

Adım 4: MR - D012 okut
  → ✓ Başarılı

Adım 5: V710 - D003 okut (V710'a geri dönüş!)
  {
    "dolly_no": "D003",
    "eol_name": "V710",  ← V710'a geri döndü
    ...
  }
  → ✓ Başarılı (V710'da D002'den sonra D003 gelir, sıralı!)
```

**Sonuç:**
```
PartNumber: PART-ABC-V710-MR-EOL-...
└─ V710: D001, D002, D003 ✓
└─ MR:   D011, D012      ✓

→ Tüm dollyler AYNI TIR'a gidecek!
```

---

### Senaryo 3: Hatalı Dolly Sırası (HATA)

```
Operatör: Dolly atlamaya çalışıyor

Adım 1: V710 - D001 okut
  → ✓ Başarılı

Adım 2: V710 - D003 okut (D002 atlandı!)
  {
    "dolly_no": "D003",
    "eol_name": "V710",
    ...
  }
  → ✗ HATA!
  Response:
  {
    "success": false,
    "error": "V710 EOL'de dolly sırası yanlış! D002 okutulmadan D003 okutulamaz.",
    "expected_dolly": "D002",
    "received_dolly": "D003"
  }

→ Mobil uygulama kullanıcıya uyarı göstermeli!
```

---

## ⚠️ Hata Durumları

### 1. Dolly Sırası Hatası
**Durum:** Aynı EOL'de dolly atlandı  
**HTTP:** `400 Bad Request`  
**Response:**
```json
{
  "success": false,
  "error": "Dolly sırası yanlış! Önceki dolly (D001) okutulmadan D003 okutulamaz.",
  "expected_dolly": "D001",
  "eol_name": "V710"
}
```
**Mobil Aksiyon:** Kullanıcıya uyarı göster, doğru dolly'yi okutmasını iste

---

### 2. Farklı Grup Karışımı
**Durum:** Başka PartNumber'dan dolly okutulmaya çalışıldı  
**HTTP:** `400 Bad Request`  
**Response:**
```json
{
  "success": false,
  "error": "Bu dolly farklı bir gruba ait!",
  "current_part_number": "PART-ABC-V710-MR-EOL-...",
  "dolly_part_number": "PART-XYZ-V820-EOL-..."
}
```
**Mobil Aksiyon:** Session'ı sonlandır, yeni grup başlat

---

### 3. Duplicate VIN
**Durum:** Aynı VIN tekrar okutuldu  
**HTTP:** `409 Conflict`  
**Response:**
```json
{
  "success": false,
  "error": "VIN zaten kayıtlı!",
  "vin_no": "VIN001",
  "existing_dolly": "D001",
  "existing_eol": "V710"
}
```
**Mobil Aksiyon:** Kullanıcıya bildir, VIN'i atla

---

## 🧪 Test Senaryoları

### Test 1: Tek EOL Sıralı Okutma
```
✓ D001 okut (V710)
✓ D002 okut (V710)
✓ D003 okut (V710)
✓ Tüm dollyler aynı PartNumber'da
```

### Test 2: Karışık EOL Okutma
```
✓ D001 okut (V710)
✓ D002 okut (V710)
✓ D011 okut (MR)    ← Farklı EOL
✓ D003 okut (V710)  ← Geri dönüş
✓ D012 okut (MR)    ← Tekrar farklı EOL
✓ Tüm dollyler aynı PartNumber'da
```

### Test 3: Dolly Atlama Hatası
```
✓ D001 okut (V710)
✗ D003 okut (V710)  ← HATA! D002 atlandı
✓ Hata mesajı gösterildi
✓ D002 okut (V710)  ← Doğru dolly okutuldu
✓ D003 okut (V710)  ← Şimdi başarılı
```

### Test 4: Farklı Grup Karışımı
```
✓ Grup 1: D001 okut (PART-ABC)
✗ Grup 2: D020 okut (PART-XYZ)  ← HATA! Farklı grup
✓ Hata mesajı gösterildi
✓ Session sonlandırıldı
```

---

## 📱 Mobil Uygulama Gereksinimleri

### 1. Session Yönetimi
- ✅ Kullanıcı bir PartNumber'la işleme başladığında session açılmalı
- ✅ Session boyunca sadece o PartNumber'a dolly eklenebilmeli
- ✅ Farklı PartNumber okutulursa yeni session başlatılmalı

### 2. EOL Geçişleri
- ✅ Kullanıcı istediği zaman farklı EOL'e geçebilmeli
- ✅ Aynı PartNumber içindeyse sorun yok
- ✅ Her EOL'ün kendi sıralaması takip edilmeli

### 3. Dolly Sırası Kontrolü
- ✅ Aynı EOL içinde dolly atlaması engellenMELİ
- ✅ API'den dönen hata mesajı kullanıcıya gösterilmeli
- ✅ Beklenen dolly numarası belirtilmeli

### 4. Offline Desteği
- ✅ Offline mod destekleniyorsa:
  - Okutmalar local'de saklanmalı
  - Online olunca sırayla gönderilmeli
  - Dolly sırası kontrolü local'de de yapılmalı


---

## 🔐 Güvenlik Notları

1. **PartNumber Validasyonu**
   - API her request'te PartNumber'ı kontrol eder
   - Farklı PartNumber karışımı engellenir

2. **Dolly Sırası Kontrolü**
   - Backend tarafında da kontrol edilir
   - Mobil'den gönderilen sıra API'de doğrulanır

3. **Duplicate Kontrolü**
   - VIN, DollyNo, PartNumber kombinasyonu unique
   - Database constraint var


---