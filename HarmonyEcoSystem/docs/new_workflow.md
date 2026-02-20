# 🚛 Yeni İş Akışı - Dolly Sevkiyat Sistemi

## 📋 Genel Bakış

```
┌─────────────────────────────────────────────────────────────────┐
│                    DOLLY SEVKIYAT SÜRECİ                        │
└─────────────────────────────────────────────────────────────────┘

1️⃣  EOL İstasyonu        →  Dolly üretim hattından çıkıyor
                             DollyEOLInfo tablosuna düşüyor
                             
2️⃣  Forklift Operatör    →  Android app ile barkod okutup TIR'a yüklüyor
    (Android App)            SIRAYLA okutması önemli!
                             DollySubmissionHold (Status: scanned)
                             
3️⃣  Forklift Tamamlama   →  "Yükleme Tamamlandı" butonuna basıyor
    (Android App)            Status: loading_completed
                             
4️⃣  Web Operatör         →  Ofiste dolly'leri kontrol ediyor
    (Dashboard)              Sefer No + Plaka giriyor
                             ASN veya İrsaliye gönderiyor
                             SeferDollyEOL tablosuna kayıt atıyor
                             Status: completed
```

---

## 🔄 Detaylı Akış Diyagramı

```
┌──────────────────┐
│  DollyEOLInfo    │ ← EOL istasyonundan dolly gelir
│  (Canlı Kuyruk)  │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────────────────────────────┐
│  FORKLIFT OPERATÖR (Android Barkod Okuyucu)         │
├──────────────────────────────────────────────────────┤
│  1. Yeni oturum başlat                               │
│     loadingSessionId = "LOAD_20251126_MEHMET"        │
│                                                      │
│  2. İLK dolly'yi oku → POST /api/forklift/scan       │
│     ┌─────────────────────────────────┐             │
│     │ DollySubmissionHold             │             │
│     │ - DollyNo: DL-5170427           │             │
│     │ - Status: scanned               │             │
│     │ - ScanOrder: 1                  │  ◄─ SIRA 1  │
│     │ - LoadingSessionId: LOAD_...    │             │
│     └─────────────────────────────────┘             │
│                                                      │
│  3. İKİNCİ dolly'yi oku                             │
│     ┌─────────────────────────────────┐             │
│     │ DollyNo: DL-5170428             │             │
│     │ ScanOrder: 2                    │  ◄─ SIRA 2  │
│     └─────────────────────────────────┘             │
│                                                      │
│  4. ... devam eder (15 dolly)                       │
│                                                      │
│  5. "YÜKLEME TAMAMLANDI" butonu                     │
│     POST /api/forklift/complete-loading             │
│     ┌─────────────────────────────────┐             │
│     │ Tüm dolly'ler:                  │             │
│     │ Status: loading_completed       │             │
│     │ LoadingCompletedAt: NOW         │             │
│     └─────────────────────────────────┘             │
└──────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────┐
│  WEB OPERATÖR (Dashboard - Ofis)                    │
├──────────────────────────────────────────────────────┤
│  1. /operator/shipments sayfası açılır              │
│                                                      │
│  2. Bekleyen sevkiyatları görür:                    │
│     ╔═══════════════════════════════════╗           │
│     ║ Session: LOAD_20251126_MEHMET     ║           │
│     ║ Forklift: Mehmet Yılmaz           ║           │
│     ║ Dolly Sayısı: 15                  ║           │
│     ║                                   ║           │
│     ║ Sıra  Dolly No    VIN             ║           │
│     ║  1    DL-5170427  3FA6P0LU...     ║           │
│     ║  2    DL-5170428  3FA6P0LU...     ║           │
│     ║  ...                              ║           │
│     ╚═══════════════════════════════════╝           │
│                                                      │
│  3. Form doldurur:                                  │
│     ┌────────────────────────────┐                  │
│     │ Sefer No: SFR2025001       │                  │
│     │ Plaka: 34 ABC 123          │                  │
│     │ Tip: ◉ ASN                 │                  │
│     │      ○ İrsaliye            │                  │
│     │      ○ Her İkisi           │                  │
│     └────────────────────────────┘                  │
│                                                      │
│  4. "Sevkiyatı Tamamla" butonuna basar              │
│     POST /api/operator/complete-shipment            │
│                                                      │
│  5. Sistem otomatik yapar:                          │
│     ┌─────────────────────────────────┐             │
│     │ SeferDollyEOL (her dolly için)  │             │
│     │ - SeferNumarasi: SFR2025001     │             │
│     │ - PlakaNo: 34 ABC 123           │             │
│     │ - ASNDate: NOW                  │             │
│     │ - IrsaliyeDate: NULL            │             │
│     │ - Status: completed             │             │
│     └─────────────────────────────────┘             │
│                                                      │
│     ┌─────────────────────────────────┐             │
│     │ DollyLifecycle                  │             │
│     │ - Status: COMPLETED_ASN         │             │
│     └─────────────────────────────────┘             │
└──────────────────────────────────────────────────────┘
```

---

## 📊 Veri Tabloları

### DollySubmissionHold (Geçici Tablo)

| Sütun               | Açıklama                          | Örnek                      |
|---------------------|-----------------------------------|----------------------------|
| DollyNo             | Dolly numarası                    | DL-5170427                 |
| VinNo               | Araç şasi numarası                | 3FA6P0LU6FR100001          |
| Status              | Durum                             | scanned → loading_completed → completed |
| TerminalUser        | Forklift operatör                 | Mehmet Yılmaz              |
| **LoadingSessionId**| Yükleme oturumu                   | LOAD_20251126_MEHMET       |
| **ScanOrder**       | Okutulma sırası                   | 1, 2, 3...                 |
| **SeferNumarasi**   | Sefer no (operatör girer)         | SFR2025001                 |
| **PlakaNo**         | TIR plakası (operatör girer)      | 34 ABC 123                 |
| LoadingCompletedAt  | Forklift tamamlama zamanı         | 2025-11-26 15:45:00        |
| SubmittedAt         | Operatör gönderim zamanı          | 2025-11-26 16:30:00        |

### SeferDollyEOL (Tarihsel Kayıt)

Operatör tamamladıktan sonra buraya kopyalanır:

| Sütun          | Değer                                          |
|----------------|------------------------------------------------|
| SeferNumarasi  | Operatörün girdiği (SFR2025001)                |
| PlakaNo        | Operatörün girdiği (34 ABC 123)                |
| DollyNo        | DL-5170427                                     |
| VinNo          | 3FA6P0LU6FR100001                              |
| ASNDate        | 2025-11-26 16:30:00 (tip=ASN ise)              |
| IrsaliyeDate   | NULL (tip=ASN ise) veya NOW (tip=İrsaliye ise) |
| TerminalUser   | Forklift operatör                              |
| VeriGirisUser  | Web operatör                                   |

---

## 🎯 Kullanıcı Rolleri

### 1. Forklift Operatör (Android App)

**Sorumluluklar:**
- Dolly barkodlarını SIRAYLA okutmak
- TIR'a fiziksel olarak yüklemek
- Yükleme tamamlandığında uygulamadan onaylamak

**Kullandığı Endpoint'ler:**
- `POST /api/forklift/scan` - Barkod okut
- `POST /api/forklift/complete-loading` - Yükleme tamamlandı
- `GET /api/forklift/sessions` - Aktif oturumları gör (opsiyonel)

### 2. Web Operatör (Dashboard)

**Sorumluluklar:**
- Forklift'in yüklediği dolly'leri kontrol etmek
- Sefer numarası girmek
- Plaka numarası girmek
- ASN veya İrsaliye tipini seçmek
- Sisteme gönderim yapmak

**Kullandığı Sayfalar:**
- `/operator/shipments` - Bekleyen sevkiyatlar
- Form ile Sefer No + Plaka girişi

---

## 🔐 Güvenlik

### API Authentication

```javascript
// Android App - Her istekte header ekle
headers: {
  'Content-Type': 'application/json',
  'Authorization': 'Bearer <forklift_token>'
}
```

### Audit Trail

Her işlem `AuditLog` tablosuna kaydedilir:

```sql
SELECT * FROM AuditLog 
WHERE Action IN (
  'forklift.scan',
  'forklift.complete_loading',
  'operator.complete_shipment'
)
ORDER BY CreatedAt DESC;
```

---

## 📈 Raporlama

### Günlük Sevkiyat Raporu

```sql
SELECT 
    SeferNumarasi,
    PlakaNo,
    COUNT(*) as DollyCount,
    STRING_AGG(DollyNo, ', ') as DollyList,
    MIN(TerminalDate) as FirstLoad,
    MAX(ASNDate) as ASNSent
FROM SeferDollyEOL
WHERE CAST(ASNDate AS DATE) = CAST(GETDATE() AS DATE)
GROUP BY SeferNumarasi, PlakaNo
ORDER BY FirstLoad DESC;
```

### Forklift Performans

```sql
SELECT 
    TerminalUser,
    COUNT(DISTINCT LoadingSessionId) as SessionCount,
    COUNT(*) as TotalDollysScanned,
    AVG(DATEDIFF(MINUTE, CreatedAt, LoadingCompletedAt)) as AvgLoadingTime
FROM DollySubmissionHold
WHERE CAST(CreatedAt AS DATE) = CAST(GETDATE() AS DATE)
GROUP BY TerminalUser
ORDER BY TotalDollysScanned DESC;
```

---

## ⚡ Performans İpuçları

1. **Batch Insert:** Birden fazla dolly aynı anda okutuluyorsa batch API eklenebilir
2. **Cache:** Android app son 100 dolly bilgisini cache'lesin
3. **Offline Mode:** Network koparsa queue'ya alsın, sonra sync etsin
4. **Index:** `LoadingSessionId` ve `ScanOrder` üzerine index var

---

## 🐛 Hata Senaryoları

### 1. Barkod Okunamıyor
```
Çözüm: Manuel dolly no girişi ekle
```

### 2. Network Koptu
```
Çözüm: Offline mode - Local database'e kaydet, sonra sync
```

### 3. Yanlış Dolly Okutuldu
```
Çözüm: "Son Okutmayı İptal Et" butonu ekle
DELETE FROM DollySubmissionHold WHERE Id = <last_id>
```

### 4. Operatör Yanlış Sefer No Girdi
```
Çözüm: Admin panel'den düzeltme ekranı
UPDATE SeferDollyEOL SET SeferNumarasi = 'YENİ_NO' WHERE SeferNumarasi = 'ESKİ_NO'
```

---

## 🎉 Özet

**Önceki Sistem:**
❌ Terminal operatör kavramı vardı (gereksiz)
❌ Part number otomatik üretiliyordu (karışık)
❌ Submit işlemi belirsizdi

**Yeni Sistem:**
✅ Forklift Android app ile okutup tamamlıyor
✅ Web operatör sadece kontrol + Sefer/Plaka girişi yapıyor
✅ Sıra takibi (`ScanOrder`) var
✅ Session bazlı gruplama var
✅ ASN/İrsaliye net ayrımı var
✅ Audit log tam takip sağlıyor

**İş Akışı Özet:**
1. Forklift → Okut (SCAN)
2. Forklift → Tamamla (COMPLETE)
3. Operatör → Sefer+Plaka Gir + Gönder (SUBMIT)
4. Sistem → SeferDollyEOL'a Kaydet (DONE)
