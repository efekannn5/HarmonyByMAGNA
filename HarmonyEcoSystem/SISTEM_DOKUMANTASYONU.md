# 📚 HarmonyEcoSystem - Kapsamlı Sistem Dokümantasyonu

## 🎯 Sistem Genel Bakış

**HarmonyEcoSystem**, Magna üretim tesisinde dolly'lerin (parça taşıma arabaları) lojistik takibini sağlayan kapsamlı bir Control Tower sistemidir. Sistem, üretim hattından çıkan dolly'lerin TIR'a yüklenmesine, sevkiyat kontrolüne ve dokümantasyon süreçlerine kadar tüm operasyonları yönetir.

### 🏗️ Sistem Mimarisi

```
┌─────────────────────────────────────────────────────────────────┐
│                      HARMONYECOSYSTEM                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐ │
│  │  Android App     │  │  Web Dashboard   │  │  Backend API  │ │
│  │  (Forklift)      │  │  (Operator)      │  │  (Flask)      │ │
│  └─────────┬────────┘  └─────────┬────────┘  └───────┬───────┘ │
│            │                      │                    │         │
│            └──────────────────────┴────────────────────┘         │
│                               │                                  │
│                               ▼                                  │
│                    ┌────────────────────┐                        │
│                    │   SQL Server DB    │                        │
│                    │  (16+ Tablo)       │                        │
│                    └────────────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 VERİ TABANISI TABLOLARI

### 1. 🏭 **DollyEOLInfo** (Ana Kuyruk Tablosu)

**Amaç:** Üretim hattından çıkan dolly'lerin CANLI KUYRUK tablosudur. EOL (End of Line) istasyonlarından gelen tüm dolly'ler burada bekler.

**Veri Kaynağı:** EOL istasyonlarındaki üretim sisteminden otomatik olarak dolly çıktığında kayıt düşer.

**Tuttuğu Veriler:**
- **DollyNo** (PK): Dolly numarası (örn: DL-5170427)
- **VinNo** (PK): Araç şasi numarası (örn: 3FA6P0LU6FR100001)
- **DollyOrderNo**: Dolly sipariş numarası
- **CustomerReferans**: Müşteri referans kodu
- **Adet**: Dolly üzerindeki parça adedi (genelde 1)
- **EOLName**: Hangi EOL istasyonundan çıktı (örn: "EOL-ENGINE-01")
- **EOLID**: EOL istasyon ID'si
- **EOLDATE**: Dolly'nin EOL'den çıkış tarihi
- **EOLDollyBarcode**: Dolly üzerindeki barkod
- **RECEIPTID**: Alındı belgesi ID
- **InsertedAt**: Sisteme eklenme zamanı

**İş Akışındaki Rolü:**
```
EOL İstasyon → Dolly Üretildi → DollyEOLInfo'ya eklenir → Kuyrukta Bekler
                                        ↓
                         Forklift okutunca → DollySubmissionHold'a taşınır
                                        ↓
                         DollyEOLInfo'dan SİLİNİR (kuyruktan çıkar)
```

**Kritik Özellikler:**
- ✅ Composite Primary Key (DollyNo + VinNo) - Aynı dolly farklı VIN'lerle gelebilir
- ⚡ Real-time veri - Sürekli güncellenir
- 🔄 Dinamik tablo - Dolly sevk edildikçe kayıtlar silinir

---

### 2. 📦 **DollySubmissionHold** (Geçici Tutma Tablosu)

**Amaç:** Forklift operatörünün okuttuğu ancak henüz web operatör tarafından onaylanmamış dolly'leri GEÇİCİ olarak tutar. Bu tablo bir "staging area" görevi görür.

**Veri Akışı:**
```
DollyEOLInfo → Forklift Okutma → DollySubmissionHold (Status: scanned)
                                        ↓
                           "Yükleme Tamamlandı" → Status: loading_completed
                                        ↓
                      Web Operator Onay → SeferDollyEOL'a taşınır
                                        ↓
                           DollySubmissionHold'dan SİLİNİR
```

**Tuttuğu Veriler:**
- **Id** (PK): Otomatik artan ID
- **DollyNo, VinNo**: Dolly ve VIN bilgisi
- **Status**: Durum takibi
  - `pending` → Yeni oluşturuldu
  - `scanned` → Forklift tarafından okundu
  - `loading_completed` → Forklift yüklemeyi tamamladı
  - `completed` → Web operatör onayladı
- **TerminalUser**: Hangi forklift operatör okutti (örn: "Mehmet Yılmaz")
- **ScanOrder**: Okutulma sırası (1, 2, 3...) - TIR'a YÜKLENİŞ SIRASI
- **LoadingSessionId**: Toplu yükleme oturumu (örn: "LOAD_20251126_MEHMET")
- **LoadingCompletedAt**: Forklift "Tamamlandı" butonuna bastığı zaman
- **SeferNumarasi**: Web operatörün girdiği sefer numarası
- **PlakaNo**: TIR plakası
- **PartNumber**: Parça numarası (analytics için)
- **EOL Bilgileri**: EOLName, EOLID, CustomerReferans, Adet (kopyalanan)
- **SubmittedAt**: Web operatör onay zamanı

**Kritik Özellikler:**
- ⏱️ **GEÇİCİ** tablo - Veriler kalıcı olarak SeferDollyEOL'a taşınır
- 📊 **ScanOrder** - Forklift hangi sırayla yükledi bilgisi
- 🔐 **LoadingSessionId** - Aynı forklift operatörün aynı TIR'a yüklediği tüm dolly'ler gruplanır
- 🚀 **İki Aşamalı Onay** - Önce forklift, sonra web operatör

---

### 3. 📝 **SeferDollyEOL** (Tarihsel Kayıt Tablosu)

**Amaç:** Sevk edilen tüm dolly'lerin TARİHSEL KAYIT tablosudur. Gönderilen her dolly'nin sefer bilgileriyle birlikte kalıcı kaydı burada tutulur. Bu tablo **ASLA SİLİNMEZ**, yalnızca eklenme yapılır.

**Veri Kaynağı:** Web operatör sevkiyatı tamamladığında DollySubmissionHold'dan kopyalanır.

**Veri Akışı:**
```
Web Operatör → "Sevkiyatı Tamamla" → DollySubmissionHold verileri kopyalanır
                                              ↓
                                    SeferDollyEOL'a INSERT edilir
                                              ↓
                              Tarihsel kayıt - Hiç silinmez
```

**Tuttuğu Veriler:**
- **SeferNumarasi** (PK): Sefer numarası (örn: "SFR2025001")
- **DollyNo** (PK): Dolly numarası
- **VinNo** (PK): VIN numarası
- **PlakaNo**: TIR plaka numarası (örn: "34 ABC 123")
- **CustomerReferans**: Müşteri referans kodu
- **Adet**: Parça adedi
- **EOLName, EOLID**: Hangi EOL istasyonundan geldi
- **EOLDate**: EOL'den çıkış tarihi
- **TerminalUser**: Forklift operatör adı
- **TerminalDate**: Forklift okutma zamanı
- **VeriGirisUser**: Web operatör adı
- **ASNDate**: ASN gönderim tarihi (eğer ASN gönderildiyse)
- **IrsaliyeDate**: İrsaliye gönderim tarihi (eğer İrsaliye gönderildiyse)
- **PartNumber**: Parça numarası
- **DollyOrderNo**: Dolly sipariş numarası

**Kritik Özellikler:**
- 📜 **Append-Only** - Yalnızca INSERT yapılır, UPDATE/DELETE yapılmaz
- 📊 **Analytics Tablosu** - Tüm raporlamalar buradan yapılır
- 🔍 **Composite PK** - (SeferNumarasi + DollyNo + VinNo) - Aynı dolly farklı seferlerde gidebilir
- 📅 **ASN/İrsaliye Tracking** - Hangi belge gönderildi bilgisi

**Örnek Kayıt:**
```
SeferNumarasi: SFR2025001
DollyNo: DL-5170427
VinNo: 3FA6P0LU6FR100001
PlakaNo: 34 ABC 123
ASNDate: 2025-11-26 16:30:00
IrsaliyeDate: NULL
TerminalUser: Mehmet Yılmaz
VeriGirisUser: Ayşe Demir
```

---

### 4. 🔄 **DollyLifecycle** (Durum Değişiklik Logları)

**Amaç:** Her dolly'nin yaşam döngüsündeki TÜM DURUM DEĞİŞİKLİKLERİNİ loglar. Bir dolly'nin üretimden sevkiyata kadar geçirdiği tüm aşamaları kayıt altına alır.

**Tuttuğu Veriler:**
- **Id** (PK): Otomatik ID
- **DollyNo**: Dolly numarası
- **VinNo**: VIN numarası
- **Status**: Durum değişikliği
  - `EOL_READY` → EOL'den çıktı
  - `SCAN_CAPTURED` → Forklift tarafından okundu
  - `WAITING_SUBMIT` → Yükleme tamamlandı, operatör bekliyor
  - `SUBMITTED_TERMINAL` → Terminal'e gönderildi
  - `WAITING_OPERATOR` → Web operatör onayı bekliyor
  - `COMPLETED_ASN` → ASN gönderildi
  - `COMPLETED_IRSALIYE` → İrsaliye gönderildi
  - `COMPLETED_BOTH` → Her ikisi de gönderildi
  - `QUEUE_REMOVED` → Kuyruktan manuel kaldırıldı
  - `QUEUE_RESTORED` → Kuyruğa geri eklendi
- **Source**: Hangi kaynak tetikledi (örn: "forklift_scan", "web_operator")
- **Metadata**: Ek JSON bilgiler
- **CreatedAt**: Log zamanı

**Veri Akışı:**
```
EOL Çıkış → EOL_READY log
Forklift Okut → SCAN_CAPTURED log
Yükleme Tamamla → WAITING_SUBMIT log
Operatör Onay → COMPLETED_ASN log
```

**Kritik Özellikler:**
- 📊 **Tam Audit Trail** - Tüm dolly hareketleri kayıt altında
- 🔍 **Debugging Tool** - Sorun çıkarsa dolly'nin nerede takıldığı anlaşılır
- 📈 **Performance Analytics** - Her aşamada ne kadar süre kaldı hesaplanabilir
- 🔐 **Immutable** - Loglar asla değiştirilmez

---

### 5. 🗑️ **DollyQueueRemoved** (Arşiv Tablosu)

**Amaç:** Kuyruktan MANUEL olarak kaldırılan dolly'lerin ARŞİV tablosudur. Hatalı, bozuk veya başka sebeplerle kaldırılan dolly'ler burada tutulur.

**Veri Kaynağı:** Admin/Operator kuyruk yönetim ekranından manuel silme işlemi.

**Veri Akışı:**
```
Admin/Operator → "Dolly Kaldır" → DollyEOLInfo'dan SİLİNİR
                                          ↓
                          Tüm veri kopyalanarak DollyQueueRemoved'a eklenir
                                          ↓
                     "Geri Yükle" → DollyEOLInfo'ya tekrar INSERT edilir
```

**Tuttuğu Veriler:**
- **Id** (PK): Otomatik ID
- **DollyNo, VinNo**: Dolly ve VIN bilgisi
- **DollyEOLInfo'daki tüm alanlar**: CustomerReferans, Adet, EOLName, EOLID, EOLDATE, EOLDollyBarcode, DollyOrderNo, RECEIPTID
- **OriginalInsertedAt**: Orijinal eklenme zamanı
- **RemovedAt**: Kaldırılma zamanı
- **RemovedBy**: Kaldıran kullanıcı
- **RemovalReason**: Kaldırma sebebi (örn: "Bozuk dolly", "Hatalı kayıt")

**Kritik Özellikler:**
- 🔄 **Geri Yüklenebilir** - Yanlışlıkla silinen dolly'ler geri alınabilir
- ⏱️ **Zamanlı Kaldırma** - X saat sonra otomatik geri yüklenme ayarlanabilir
- 📊 **Audit** - Kim, ne zaman, neden kaldırdı bilgisi

**Kullanım Senaryoları:**
- ❌ Bozuk dolly üretim hattına geri gönderildi
- ❌ Hatalı VIN girişi düzeltilmesi gerekiyor
- ⏱️ Geçici olarak bekletilmesi gereken dolly'ler (24 saat sonra otomatik geri gelecek)

---

### 6. 👥 **UserAccount** (Kullanıcı Hesapları)

**Amaç:** Sistemdeki tüm kullanıcıların hesap bilgilerini tutar (web operatörler, adminler, forklift operatörleri).

**Tuttuğu Veriler:**
- **Id** (PK): Kullanıcı ID
- **Username**: Kullanıcı adı (örn: "mehmet.yilmaz")
- **DisplayName**: Görünen ad (örn: "Mehmet Yılmaz")
- **PasswordHash**: Şifreli parola (bcrypt ile hash'lenmiş)
- **Barcode**: Forklift operatörlerinin barkod numarası
- **RoleId**: Rol ID (Foreign Key → UserRole)
- **IsActive**: Aktif/Pasif durum
- **LastLoginAt**: Son giriş zamanı
- **CreatedAt, UpdatedAt**: Oluşturma/güncelleme zamanları

**Kritik Özellikler:**
- 🔐 **Güvenli Şifre** - bcrypt ile hash
- 🏷️ **Barkod Login** - Forklift operatörleri barkod ile giriş yapar
- 👤 **Rol Tabanlı** - Admin, Operator, Forklift rolleri

---

### 7. 🎭 **UserRole** (Kullanıcı Rolleri)

**Amaç:** Kullanıcı rollerini tanımlar (Admin, Operator, Forklift).

**Roller:**
- **Admin** → Tüm yetkilere sahip
- **Operator** → Web panelinden sevkiyat yönetimi
- **Forklift** → Android app ile dolly okutma

**Tuttuğu Veriler:**
- **Id** (PK): Rol ID
- **Name**: Rol adı (örn: "Admin", "Operator", "Forklift")
- **Description**: Rol açıklaması
- **CreatedAt**: Oluşturma zamanı

---

### 8. 📱 **ForkliftLoginSession** (Forklift Giriş Oturumları)

**Amaç:** Forklift operatörlerinin Android app üzerinden barkod ile giriş oturumlarını yönetir.

**Veri Akışı:**
```
Operatör → Barkod Okut (EMP12345) → POST /api/forklift/login
                                            ↓
                          ForkliftLoginSession oluşturulur
                                            ↓
                          SessionToken döner (JWT benzeri)
                                            ↓
                    Her istekte Authorization: Bearer TOKEN
```

**Tuttuğu Veriler:**
- **Id** (PK): Oturum ID
- **OperatorBarcode**: Operatör barkodu (örn: "EMP12345")
- **OperatorName**: Operatör adı (örn: "Mehmet Yılmaz")
- **DeviceId**: Android cihaz ID
- **SessionToken**: Güvenlik tokeni (128 karakter)
- **IsActive**: Aktif/Pasif
- **IsAdmin**: Admin yetkisi var mı?
- **Role**: Rol (default: "forklift")
- **LoginAt**: Giriş zamanı
- **LogoutAt**: Çıkış zamanı
- **ExpiresAt**: Token'ın son geçerlilik zamanı (8 saat)
- **LastActivityAt**: Son aktivite
- **IpAddress**: Giriş yapılan IP
- **UserAgent**: Cihaz bilgisi
- **Metadata**: Ek bilgiler (JSON)

**Kritik Özellikler:**
- ⏱️ **Otomatik Expire** - 8 saat sonra geçersiz olur
- 🔐 **Token-Based Auth** - Her istekte token kontrolü
- 📊 **Activity Tracking** - Son aktivite izlenir

---

### 9. 📋 **AuditLog** (Sistem Audit Logları)

**Amaç:** Sistemdeki kritik işlemlerin KIM, NE, NE ZAMAN yaptığını loglar.

**Tuttuğu Veriler:**
- **Id** (PK): Log ID
- **ActorType**: Kim yaptı? ("user", "device", "system")
- **ActorId**: Kullanıcı/Cihaz ID
- **ActorName**: İsim
- **Action**: Ne yapıldı? (örn: "dolly_removed", "shipment_completed")
- **Resource**: Hangi kaynak? (örn: "DollyEOLInfo", "SeferDollyEOL")
- **ResourceId**: Kaynak ID (örn: "DL-5170427")
- **Payload**: Detaylı bilgi (JSON)
- **CreatedAt**: Log zamanı

**Örnek Kayıt:**
```json
{
  "ActorType": "user",
  "ActorId": 5,
  "ActorName": "Ayşe Demir",
  "Action": "shipment_completed",
  "Resource": "SeferDollyEOL",
  "ResourceId": "SFR2025001",
  "Payload": "{\"dolly_count\": 15, \"plaka\": \"34 ABC 123\"}",
  "CreatedAt": "2025-11-26 16:30:00"
}
```

**Kritik Özellikler:**
- 🔍 **Full Traceability** - Her işlem kayıt altında
- 🔐 **Security** - Yetkisiz işlemler tespit edilebilir
- 📊 **Compliance** - Denetim raporları hazırlanabilir

---

### 10. 🏭 **PWorkStation** (EOL İstasyon Tanımları)

**Amaç:** Üretim hattındaki EOL istasyonlarını tanımlar. Sistem hangi istasyonlardan dolly bekleyeceğini buradan öğrenir.

**Tuttuğu Veriler:**
- **Id** (PK): İstasyon ID
- **PlantId**: Tesis ID
- **PWorkCenterId**: İş merkezi ID
- **PWorkStationNo**: İstasyon numarası
- **PWorkStationName**: İstasyon adı (örn: "EOL-ENGINE-01")
- **GroupCode**: Grup kodu
- **ErpWorkStationNo**: ERP entegrasyon numarası
- **Status**: Aktif/Pasif
- **IsFinishProductStation**: Bitmiş ürün istasyonu mu?
- **InsertDate**: Eklenme tarihi

**Kritik Özellikler:**
- 🏷️ **EOL Filtreleme** - Adı "EOL" ile biten istasyonlar otomatik algılanır
- 🔗 **ERP Entegrasyonu** - ErpWorkStationNo ile SAP/Oracle gibi sistemlere bağlanır
- 📊 **Grup Yönetimi** - DollyGroup/DollyGroupEOL ile ilişkilendirilir

---

### 11. 📦 **DollyGroup** (Dolly Grup Tanımları)

**Amaç:** Dolly'leri kategorize etmek için grup tanımları (örn: "Motor Dolly'leri", "Şanzıman Dolly'leri").

**Tuttuğu Veriler:**
- **Id** (PK): Grup ID
- **GroupName**: Grup adı (örn: "ENGINE_DOLLIES")
- **Description**: Açıklama
- **IsActive**: Aktif/Pasif
- **CreatedAt, UpdatedAt**: Oluşturma/güncelleme zamanları

---

### 12. 🔗 **DollyGroupEOL** (Grup-EOL İlişkisi)

**Amaç:** Hangi EOL istasyonlarının hangi gruplara ait olduğunu ve sevkiyat etiketini (ASN/İrsaliye) tanımlar.

**Tuttuğu Veriler:**
- **Id** (PK): İlişki ID
- **GroupId**: Grup ID (Foreign Key → DollyGroup)
- **PWorkStationId**: İstasyon ID (Foreign Key → PWorkStation)
- **ShippingTag**: Sevkiyat tipi ("asn", "irsaliye", "both")
- **CreatedAt**: Oluşturma zamanı

**Kullanım:**
```sql
-- "ENGINE_DOLLIES" grubu için "EOL-ENGINE-01" istasyonu ASN gönderecek
INSERT INTO DollyGroupEOL (GroupId, PWorkStationId, ShippingTag)
VALUES (1, 5, 'asn');
```

---

### 13. 🖥️ **TerminalDevice** (Terminal Cihaz Tanımları)

**Amaç:** Sistemde kayıtlı terminal cihazları (tablet, PC, barkod okuyucu).

**Tuttuğu Veriler:**
- **Id** (PK): Cihaz ID
- **Name**: Cihaz adı (örn: "Forklift-Tablet-01")
- **DeviceIdentifier**: Cihaz benzersiz ID
- **RoleId**: Cihaz rolü
- **ApiKey**: API anahtarı
- **BarcodeSecret**: Barkod şifreleme anahtarı
- **IsActive**: Aktif/Pasif
- **CreatedAt, UpdatedAt**: Zaman damgaları

---

### 14. 🔐 **TerminalBarcodeSession** (Terminal Barkod Oturumları)

**Amaç:** Terminal cihazlarının barkod tabanlı oturum yönetimi.

**Tuttuğu Veriler:**
- **Id** (PK): Oturum ID
- **DeviceId**: Cihaz ID (Foreign Key → TerminalDevice)
- **UserId**: Kullanıcı ID (Foreign Key → UserAccount)
- **Token**: Oturum tokeni
- **ExpiresAt**: Son geçerlilik zamanı
- **UsedAt**: Kullanıldı zamanı
- **CreatedAt**: Oluşturma zamanı

---

### 15. 📋 **WebOperatorTask** (Web Operatör Görevleri)

**Amaç:** Web operatörlere atanan görevleri yönetir (örn: belirli bir PartNumber için tüm dolly'leri işle).

**Tuttuğu Veriler:**
- **Id** (PK): Görev ID
- **PartNumber**: İşlenecek parça numarası (örn: "ENG-12345")
- **Status**: Görev durumu ("pending", "in_progress", "completed")
- **AssignedTo**: Atanan kullanıcı ID (Foreign Key → UserAccount)
- **GroupTag**: Sevkiyat tipi ("asn", "irsaliye", "both")
- **TotalItems**: Toplam dolly sayısı
- **ProcessedItems**: İşlenen dolly sayısı
- **Metadata**: Ek bilgiler (JSON)
- **CreatedAt, UpdatedAt, CompletedAt**: Zaman damgaları

**Hesaplanan Özellikler:**
- `progress_percentage` → (ProcessedItems / TotalItems) * 100
- `can_submit_asn` → GroupTag "asn" veya "both" ise True
- `can_submit_irsaliye` → GroupTag "irsaliye" veya "both" ise True

---

### 16. 📦 **DollyEOLInfoBackup** (Yedek Tablo)

**Amaç:** DollyEOLInfo tablosunun yedek/arşiv kopyası. Üretim tarihlerini aramak için kullanılır.

**Tuttuğu Veriler:** DollyEOLInfo ile aynı
**Kullanım:** READ-ONLY - Yalnızca tarihsel sorgulamalar için

---

### 17. 🎫 **SovosSystem** (Harici Entegrasyon Tablosu)

**Amaç:** Sovos e-Fatura/e-Arşiv sistemi entegrasyonu için kullanılan tablo. (Detayları sistemde tanımlı değil, muhtemelen üçüncü taraf sistem)

---

## 🔄 VERİ AKIŞI - KAPSAMLI SÜREÇ

### Adım 1: EOL İstasyonundan Dolly Çıkışı

```
[Üretim Hattı] → [EOL İstasyonu] → [DollyEOLInfo Tablosu]
                                           │
                                           ├─ DollyNo: DL-5170427
                                           ├─ VinNo: 3FA6P0LU6FR100001
                                           ├─ EOLName: "EOL-ENGINE-01"
                                           ├─ EOLDATE: 2025-11-26 10:00:00
                                           └─ InsertedAt: NOW
                                           
                     [DollyLifecycle Log]
                     └─ Status: EOL_READY
```

**Ne Oluyor:**
1. Motor montaj hattında dolly bitmiş ürünle birlikte EOL istasyonuna ulaşır
2. EOL sistemi (üretim yazılımı) dolly'yi tarar
3. DollyEOLInfo tablosuna yeni kayıt INSERT edilir
4. DollyLifecycle tablosuna "EOL_READY" log atılır
5. Dolly artık **KUYRUKTA BEKLER**

---

### Adım 2: Forklift Operatör Giriş Yapıyor

```
[Android App] → Barkod Okut: EMP12345
                     ↓
        POST /api/forklift/login
        {
          "operatorBarcode": "EMP12345",
          "operatorName": "Mehmet Yılmaz",
          "deviceId": "android-123"
        }
                     ↓
        [ForkliftLoginSession Oluştur]
        ├─ OperatorBarcode: EMP12345
        ├─ OperatorName: Mehmet Yılmaz
        ├─ SessionToken: "eyJhbGc..." (128 karakter)
        ├─ ExpiresAt: NOW + 8 hours
        └─ IsActive: True
                     ↓
        Response:
        {
          "success": true,
          "sessionToken": "eyJhbGc...",
          "operatorName": "Mehmet Yılmaz",
          "expiresAt": "2025-11-26T18:30:00Z"
        }
```

**Ne Oluyor:**
1. Forklift operatörü sabah işe geldiğinde Android tablet'e barkodunu okuttur
2. Sistem barkodu doğrular
3. 8 saat geçerli bir oturum tokeni üretilir
4. Token Android app'te saklanır
5. Bundan sonraki tüm API istekleri: `Authorization: Bearer TOKEN`

---

### Adım 3: Forklift Dolly'leri Okutmaya Başlıyor

```
[Android App] → 1. Dolly Okut: DL-5170427
                     ↓
        POST /api/forklift/scan
        Headers: Authorization: Bearer eyJhbGc...
        {
          "dollyNo": "DL-5170427",
          "vinNo": "3FA6P0LU6FR100001",
          "loadingSessionId": "LOAD_20251126_MEHMET"
        }
                     ↓
        [Backend İşlemler]
        ├─ 1. Token doğrula (ForkliftLoginSession kontrol)
        ├─ 2. DollyEOLInfo'da kayıt var mı? (✅)
        ├─ 3. DollyEOLInfo → DollySubmissionHold'a KOPYALA
        │     ├─ DollyNo: DL-5170427
        │     ├─ VinNo: 3FA6P0LU6FR100001
        │     ├─ Status: scanned
        │     ├─ TerminalUser: Mehmet Yılmaz
        │     ├─ ScanOrder: 1 (İLK OKUNAN)
        │     ├─ LoadingSessionId: LOAD_20251126_MEHMET
        │     └─ CreatedAt: NOW
        ├─ 4. DollyEOLInfo'dan SİL (kuyruktan çıkar)
        └─ 5. DollyLifecycle log: SCAN_CAPTURED
                     ↓
        Response:
        {
          "success": true,
          "message": "Dolly scanned successfully",
          "scanOrder": 1
        }
```

**Ne Oluyor:**
1. Forklift operatör TIR'ın yanında bekler
2. İLK dolly'yi okuttur (barkod veya manuel giriş)
3. Backend dolly'yi DollyEOLInfo'dan alır
4. DollySubmissionHold'a kopyalar (Status: scanned, ScanOrder: 1)
5. DollyEOLInfo'dan SİLİNİR (artık kuyrukta değil)
6. Android ekranında "1. Dolly Eklendi" mesajı görünür

**Önemli:** ScanOrder TIR'a YÜKLENİŞ SIRASINI tutar!

---

### Adım 4: Forklift Tüm Dolly'leri Okutmaya Devam Ediyor

```
2. Dolly → POST /api/forklift/scan → ScanOrder: 2
3. Dolly → POST /api/forklift/scan → ScanOrder: 3
...
15. Dolly → POST /api/forklift/scan → ScanOrder: 15

[DollySubmissionHold Tablosu]
├─ DL-5170427 | ScanOrder: 1  | Status: scanned
├─ DL-5170428 | ScanOrder: 2  | Status: scanned
├─ DL-5170429 | ScanOrder: 3  | Status: scanned
...
└─ DL-5170441 | ScanOrder: 15 | Status: scanned
```

---

### Adım 5: Forklift "Yükleme Tamamlandı" Butonu

```
[Android App] → "Yükleme Tamamlandı" Butonu
                     ↓
        POST /api/forklift/complete-loading
        Headers: Authorization: Bearer eyJhbGc...
        {
          "loadingSessionId": "LOAD_20251126_MEHMET"
        }
                     ↓
        [Backend İşlemler]
        ├─ 1. Tüm dolly'leri bul (LoadingSessionId = LOAD_20251126_MEHMET)
        ├─ 2. UPDATE DollySubmissionHold
        │     ├─ Status: scanned → loading_completed
        │     └─ LoadingCompletedAt: NOW
        └─ 3. DollyLifecycle log: WAITING_SUBMIT (her dolly için)
                     ↓
        Response:
        {
          "success": true,
          "message": "Loading completed",
          "totalDollies": 15
        }
```

**Ne Oluyor:**
1. Forklift operatör tüm dolly'leri TIR'a yükledi
2. "Tamamlandı" butonuna bastı
3. Backend aynı LoadingSessionId'ye sahip tüm dolly'lerin durumunu günceller
4. Artık dolly'ler **web operatörün onayını bekliyor**

---

### Adım 6: Web Operatör Bekleyen Sevkiyatları Görüyor

```
[Web Dashboard] → URL: http://10.25.64.181:8181/operator/shipments
                     ↓
        GET /api/operator/pending-shipments
                     ↓
        [Backend Sorgu]
        SELECT * FROM DollySubmissionHold
        WHERE Status = 'loading_completed'
        GROUP BY LoadingSessionId
                     ↓
        Response:
        [
          {
            "sessionId": "LOAD_20251126_MEHMET",
            "forkliftOperator": "Mehmet Yılmaz",
            "dollyCount": 15,
            "loadingCompletedAt": "2025-11-26 15:45:00",
            "dollies": [
              {
                "scanOrder": 1,
                "dollyNo": "DL-5170427",
                "vinNo": "3FA6P0LU6FR100001",
                "eolName": "EOL-ENGINE-01"
              },
              ...
            ]
          }
        ]
```

**Web Operatör Görüyor:**
```
╔════════════════════════════════════════╗
║ Bekleyen Sevkiyatlar                   ║
╠════════════════════════════════════════╣
║ Session: LOAD_20251126_MEHMET          ║
║ Forklift: Mehmet Yılmaz                ║
║ Dolly Sayısı: 15                       ║
║ Tamamlanma: 2025-11-26 15:45           ║
║                                        ║
║ Sıra  Dolly No    VIN          EOL     ║
║  1    DL-5170427  3FA6P0LU... ENGINE-01║
║  2    DL-5170428  3FA6P0LU... ENGINE-01║
║  ...                                   ║
║                                        ║
║ [Sefer No: ________]                   ║
║ [Plaka: ________]                      ║
║ [ ] ASN  [ ] İrsaliye  [ ] Her İkisi  ║
║                                        ║
║ [Sevkiyatı Tamamla]                    ║
╚════════════════════════════════════════╝
```

---

### Adım 7: Web Operatör Sevkiyatı Tamamlıyor

```
[Web Dashboard] → Form Doldur
                  ├─ Sefer No: SFR2025001
                  ├─ Plaka: 34 ABC 123
                  └─ Tip: ASN
                     ↓
        POST /api/operator/complete-shipment
        {
          "sessionId": "LOAD_20251126_MEHMET",
          "seferNumarasi": "SFR2025001",
          "plakaNo": "34 ABC 123",
          "shippingType": "asn"
        }
                     ↓
        [Backend İşlemler - TRANSACTION]
        
        1. Tüm dolly'leri bul:
           SELECT * FROM DollySubmissionHold
           WHERE LoadingSessionId = 'LOAD_20251126_MEHMET'
           AND Status = 'loading_completed'
        
        2. Her dolly için SeferDollyEOL'a INSERT:
           INSERT INTO SeferDollyEOL
           (SeferNumarasi, DollyNo, VinNo, PlakaNo, ASNDate, ...)
           VALUES
           ('SFR2025001', 'DL-5170427', '3FA6P0LU...', '34 ABC 123', NOW, NULL, ...)
        
        3. DollySubmissionHold'dan SİL:
           DELETE FROM DollySubmissionHold
           WHERE LoadingSessionId = 'LOAD_20251126_MEHMET'
        
        4. DollyLifecycle log (her dolly için):
           INSERT INTO DollyLifecycle
           (DollyNo, VinNo, Status, Source)
           VALUES
           ('DL-5170427', '3FA6P0LU...', 'COMPLETED_ASN', 'web_operator')
        
        5. AuditLog kayıt:
           INSERT INTO AuditLog
           (ActorType, ActorId, Action, Resource, Payload)
           VALUES
           ('user', 3, 'shipment_completed', 'SeferDollyEOL',
            '{"sefer": "SFR2025001", "dolly_count": 15}')
                     ↓
        Response:
        {
          "success": true,
          "message": "Shipment completed successfully",
          "seferNumarasi": "SFR2025001",
          "processedDollies": 15
        }
```

**Ne Oluyor:**
1. Web operatör sefer numarası, plaka ve sevkiyat tipini giriyor
2. Backend tüm dolly'leri **SeferDollyEOL tablosuna kopyalıyor**
3. DollySubmissionHold'dan **SİLİNİYOR** (artık geçici değil)
4. Her dolly için lifecycle log atılıyor
5. Audit log'a işlem kaydı düşüyor
6. **SeferDollyEOL tablosunda kalıcı kayıt oluştu** ✅

---

### Adım 8: Tarihsel Kayıt (SeferDollyEOL)

**Artık sistemde:**
```sql
SELECT * FROM SeferDollyEOL
WHERE SeferNumarasi = 'SFR2025001'
```

**Sonuç:**
```
SeferNumarasi | DollyNo     | VinNo           | PlakaNo     | ASNDate             | IrsaliyeDate
SFR2025001    | DL-5170427  | 3FA6P0LU6FR...  | 34 ABC 123  | 2025-11-26 16:30:00 | NULL
SFR2025001    | DL-5170428  | 3FA6P0LU6FR...  | 34 ABC 123  | 2025-11-26 16:30:00 | NULL
...
SFR2025001    | DL-5170441  | 3FA6P0LU6FR...  | 34 ABC 123  | 2025-11-26 16:30:00 | NULL
```

**Bu veriler:**
- ✅ **ASLA SİLİNMEZ**
- 📊 Raporlama için kullanılır
- 📈 Analytics için analiz edilir
- 🔍 Geçmiş sorgularda aranabilir
- 📄 İrsaliye/ASN yazdırılırken kullanılır

---

## 🎯 ÖZEL SENARYOLAR

### Senaryo 1: Manuel Dolly Kaldırma (Hatalı/Bozuk Dolly)

```
[Admin Panel] → /queue/manage
                     ↓
        Admin dolly seçer: DL-5170427
        Sebep: "Bozuk dolly, üretime geri gönderiliyor"
                     ↓
        POST /api/queue/remove
        {
          "dollyNo": "DL-5170427",
          "vinNo": "3FA6P0LU6FR100001",
          "reason": "Bozuk dolly, üretime geri gönderiliyor",
          "restoreAfterHours": null  // Süresiz kaldırma
        }
                     ↓
        [Backend İşlemler]
        1. DollyEOLInfo'dan kayıt AL
        2. DollyQueueRemoved'a KOPYALA
           ├─ RemovedBy: "admin_user"
           ├─ RemovalReason: "Bozuk dolly..."
           └─ RemovedAt: NOW
        3. DollyEOLInfo'dan SİL
        4. DollyLifecycle log: QUEUE_REMOVED
        5. AuditLog kayıt
                     ↓
        Response: "Dolly kuyruktan kaldırıldı"
```

**Geri Yükleme:**
```
[Admin Panel] → Arşiv Tablosu → "Geri Yükle" Butonu
                     ↓
        POST /api/queue/restore
        {
          "removedId": 123
        }
                     ↓
        [Backend İşlemler]
        1. DollyQueueRemoved'dan kayıt AL
        2. DollyEOLInfo'ya GERİ EKLE
        3. DollyQueueRemoved'dan SİL
        4. DollyLifecycle log: QUEUE_RESTORED
                     ↓
        Response: "Dolly kuyruğa geri eklendi"
```

---

### Senaryo 2: Zamanlı Kaldırma (24 Saat Sonra Otomatik Geri Gelecek)

```
Admin → "Geçici olarak beklet" → 24 saat seç
                     ↓
        POST /api/queue/remove
        {
          "dollyNo": "DL-5170427",
          "vinNo": "3FA6P0LU6FR100001",
          "reason": "Kalite kontrol bekliyor",
          "restoreAfterHours": 24
        }
                     ↓
        [Backend İşlemler]
        1. Kaldırma işlemi (yukarıdaki gibi)
        2. Metadata'ya restore_at zamanı ekle:
           {
             "restore_at": "2025-11-27 16:30:00"
           }
                     ↓
        [Otomatik Scheduler - Her 60 Dakikada Çalışır]
        ├─ SELECT * FROM DollyQueueRemoved
        │  WHERE Metadata->>'restore_at' <= NOW
        ├─ Bulunan dolly'leri otomatik geri yükle
        └─ DollyEOLInfo'ya INSERT, DollyQueueRemoved'dan DELETE
```

---

### Senaryo 3: PartNumber Bazlı Toplu İşlem

```
[Web Operatör] → "ENG-12345 parça numaralı tüm dolly'leri işle"
                     ↓
        POST /api/operator/create-task
        {
          "partNumber": "ENG-12345",
          "shippingType": "asn"
        }
                     ↓
        [Backend İşlemler]
        1. WebOperatorTask oluştur:
           ├─ PartNumber: ENG-12345
           ├─ Status: pending
           ├─ GroupTag: asn
           └─ TotalItems: COUNT(DollySubmissionHold WHERE PartNumber = 'ENG-12345')
        
        2. Operatör görev listesine ekle
                     ↓
        [Operatör Görevleri Sayfası]
        ╔═════════════════════════════════════╗
        ║ Görev #15                           ║
        ║ PartNumber: ENG-12345               ║
        ║ Toplam: 25 dolly                    ║
        ║ İşlenen: 0 / 25                     ║
        ║ İlerleme: [░░░░░░░░░░░] 0%         ║
        ║ [İşleme Başla]                      ║
        ╚═════════════════════════════════════╝
                     ↓
        Operatör işlemeye başlar
        Her dolly işlendiğinde:
        ├─ ProcessedItems++
        └─ Progress = (ProcessedItems / TotalItems) * 100
```

---

## 📊 ANALYTİCS VE RAPORLAMA

### Analytics View'lar (database/019_create_analytics_views.sql)

Sistem analytics için özel SQL View'lar içerir:

**1. vw_daily_dolly_summary**
```sql
-- Günlük dolly istatistikleri
SELECT 
    CAST(EOLDate AS DATE) AS Date,
    EOLName,
    COUNT(*) AS TotalDollies,
    COUNT(DISTINCT VinNo) AS UniqueVINs,
    SUM(Adet) AS TotalParts
FROM SeferDollyEOL
GROUP BY CAST(EOLDate AS DATE), EOLName
```

**2. vw_shipment_performance**
```sql
-- Sevkiyat performans raporu
SELECT 
    SeferNumarasi,
    COUNT(*) AS DollyCount,
    MIN(TerminalDate) AS FirstScan,
    MAX(ASNDate) AS LastShipment,
    DATEDIFF(MINUTE, MIN(TerminalDate), MAX(ASNDate)) AS ProcessTimeMinutes
FROM SeferDollyEOL
GROUP BY SeferNumarasi
```

**3. vw_operator_productivity**
```sql
-- Operatör verimlilik raporu
SELECT 
    TerminalUser,
    COUNT(*) AS ScannedDollies,
    COUNT(DISTINCT SeferNumarasi) AS TotalShipments,
    AVG(ScanOrder) AS AvgScanOrder
FROM SeferDollyEOL
GROUP BY TerminalUser
```

---

## 🔐 GÜVENLİK YAPISI

### Kimlik Doğrulama Katmanları

**1. Forklift (Android App):**
```
Barkod Okutma → ForkliftLoginSession → SessionToken → Her istekte Bearer Token
```

**2. Web Operatör (Dashboard):**
```
Username/Password → Flask-Login Session → Cookie-based auth
```

**3. Admin Panel:**
```
Username/Password + RoleId=1 (Admin) → Full access
```

### Yetki Matrisi

| Rol       | DollyEOLInfo | DollySubmissionHold | SeferDollyEOL | Queue Remove | User Management |
|-----------|--------------|---------------------|---------------|--------------|-----------------|
| Admin     | ✅ RWD       | ✅ RWD              | ✅ RWD        | ✅ RWD       | ✅ RWD          |
| Operator  | ❌ Read Only | ✅ RW               | ✅ RW         | ⚠️ R only    | ❌ No access    |
| Forklift  | ❌ Read Only | ✅ Create           | ❌ No access  | ❌ No access | ❌ No access    |

---

## 🚀 SİSTEM PERFORMANSI VE OPTİMİZASYON

### Index'ler

**DollySubmissionHold:**
```sql
CREATE INDEX IX_DollySubmissionHold_Status ON DollySubmissionHold(Status)
CREATE INDEX IX_DollySubmissionHold_LoadingSessionId ON DollySubmissionHold(LoadingSessionId)
CREATE INDEX IX_DollySubmissionHold_DollyNo ON DollySubmissionHold(DollyNo)
```

**SeferDollyEOL:**
```sql
CREATE INDEX IX_SeferDollyEOL_SeferNumarasi ON SeferDollyEOL(SeferNumarasi)
CREATE INDEX IX_SeferDollyEOL_EOLDate ON SeferDollyEOL(EOLDate)
CREATE INDEX IX_SeferDollyEOL_PartNumber ON SeferDollyEOL(PartNumber)
```

**DollyLifecycle:**
```sql
CREATE INDEX IX_DollyLifecycle_DollyNo ON DollyLifecycle(DollyNo)
CREATE INDEX IX_DollyLifecycle_Status ON DollyLifecycle(Status)
CREATE INDEX IX_DollyLifecycle_CreatedAt ON DollyLifecycle(CreatedAt)
```

### Caching Stratejisi

```python
# PWorkStation EOL listesi - 1 saat cache
@cache.cached(timeout=3600, key_prefix='eol_stations')
def get_eol_stations():
    return PWorkStation.query.filter(
        PWorkStation.PWorkStationName.like('%EOL%')
    ).all()

# Bekleyen sevkiyatlar - 5 dakika cache
@cache.cached(timeout=300, key_prefix='pending_shipments')
def get_pending_shipments():
    return DollySubmissionHold.query.filter_by(
        Status='loading_completed'
    ).all()
```

---

## 📈 GELECEK GELİŞTİRMELER

### Planlanan Özellikler

1. **Real-time Notifications**
   - WebSocket ile canlı bildirimler
   - Forklift tamamladı → Web operatör'e anlık bildirim

2. **Mobile Dashboard**
   - Tablet için responsive web panel
   - QR kod ile hızlı dolly sorgulama

3. **AI-Powered Analytics**
   - Tahmine dayalı sevkiyat zamanları
   - Anomali tespiti (beklenmedik gecikmeler)

4. **ERP Entegrasyonu**
   - SAP/Oracle ile otomatik senkronizasyon
   - İrsaliye/ASN otomatik gönderimi

5. **Barcode Scanner SDK**
   - Zebra/Honeywell el terminalleri desteği
   - Voice-guided picking

---

## 🛠️ TEKNİK STACK

### Backend
- **Framework:** Flask 3.0+
- **ORM:** SQLAlchemy
- **Database:** SQL Server 2019+
- **Auth:** Flask-Login, JWT
- **Caching:** Flask-Caching (Redis/Memcached)
- **Scheduler:** APScheduler

### Frontendß
- **Web Dashboard:** Jinja2 Templates, Bootstrap 5
- **JavaScript:** Vanilla JS, AJAX
- **Charts:** Chart.js
- **Real-time:** Planned WebSocket

### Mobile
- **Android:** java
- **Min SDK:** Android 8.0 (API 26)
- **Barcode:** ZXing Library
- **HTTP Client:** Retrofit

### DevOps
- **Server:** Ubuntu 20.04+
- **WSGI:** Gunicorn
- **Reverse Proxy:** Nginx
- **Process Manager:** systemd
- **Monitoring:** Planned (Prometheus + Grafana)

---

## 📞 DESTEK VE SORUN GİDERME

### Sık Karşılaşılan Sorunlar

**1. Dolly kuyrukta görünmüyor**
```sql
-- DollyEOLInfo'da var mı kontrol et
SELECT * FROM DollyEOLInfo WHERE DollyNo = 'DL-5170427'

-- Lifecycle log'una bak
SELECT * FROM DollyLifecycle 
WHERE DollyNo = 'DL-5170427' 
ORDER BY CreatedAt DESC
```

**2. Forklift token expired**
```sql
-- Oturum kontrolü
SELECT * FROM ForkliftLoginSession 
WHERE OperatorBarcode = 'EMP12345' 
AND IsActive = 1
```

**3. Sevkiyat tamamlanamıyor**
```sql
-- Status kontrolü
SELECT * FROM DollySubmissionHold 
WHERE LoadingSessionId = 'LOAD_20251126_MEHMET'
AND Status != 'loading_completed'
```

---

## 📝 SONUÇ

HarmonyEcoSystem, dolly lojistiğini **EOL çıkışından TIR sevkiyatına** kadar uçtan uca yöneten, **16+ tablo**, **3 ana modül** ve **kapsamlı audit trail** ile çalışan profesyonel bir sistemdir. 

**Temel Prensipler:**
- ✅ **Veri Bütünlüğü** - Foreign key'ler, transaction'lar
- ✅ **Tam İzlenebilirlik** - DollyLifecycle + AuditLog
- ✅ **Güvenlik** - Rol tabanlı yetkilendirme
- ✅ **Performans** - Index'ler, caching
- ✅ **Kullanıcı Deneyimi** - Kolay forklift okutma, hızlı web onay

---

**Versiyon:** 1.0.0  
**Son Güncelleme:** 2025-11-26  
**Doküman Sahibi:** HarmonyEcoSystem Development Team
