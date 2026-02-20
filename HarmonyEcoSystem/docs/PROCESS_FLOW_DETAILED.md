# Harmony EcoSystem Process Flow (Detailed Narrative)

## Amaç
Bu doküman, sistemin baştan sona işleyişini **sözlü/akış anlatımı** şeklinde açıklar. Raporlama ve analiz için hangi adımda hangi veri üretildiğini netleştirir.

## Roller ve Bileşenler
- **El Terminali (Forklift Operatörü)**: Barkod okutur, dolly’yi sisteme “scanned” olarak sokar.
- **Web Operatör**: Görevleri (part) görür, sevkiyat (ASN/İrsaliye) işlemlerini tamamlar.
- **Admin / Yönetici**: Gruplama, manuel queue yönetimi, izleme ve raporlama.
- **Sistem Bileşenleri**:
  - `DollyEOLInfo`: Üretim/EOL çıktıları (dolly + vin kayıtları)
  - `DollySubmissionHold`: Forklift/terminal tarama ve bekleyen kayıtlar
  - `WebOperatorTask`: Operatör görevleri (part bazlı)
  - `SeferDollyEOL`: Sevkiyatla kapanan son kayıtlar
  - `DollyLifecycle`: Tüm durum değişimleri

## Uçtan Uca İş Akışı

### 1) Üretim / EOL Aşaması
1. Üretim hattı (EOL) dolly + VIN bilgilerini üretir.
2. Bu kayıtlar `DollyEOLInfo` tablosuna düşer.
3. Bu kayıt, dolly’nin “sistemde var” olduğunu gösteren ilk resmi kayıttır.

**Önemli alanlar:**
- `DollyNo`, `VinNo`, `EOLName`, `EOLID`, `DollyOrderNo`, `InsertedAt`, `EOLDATE`.

---

### 2) Gruplama ve Görüntüleme
1. Yönetici/operatör paneli, `DollyEOLInfo` üzerinden grupları ve EOL’leri listeler.
2. Grup içinde EOL seçilince o EOL’e ait dolly’ler görünür.
3. Dolly seçilince VIN listesi açılır.

**Amaç:** Operatörün hangi dolly’leri okutacağını ve hangi EOL’lere ait olduklarını netleştirmek.

---

### 3) Forklift / El Terminali Okutma (Scan)
1. Forklift operatörü dolly üzerindeki barkodu okutur.
2. API çağrısı ile dolly numarası sisteme gelir.
3. Sistem bu dolly’ye ait **tüm VIN** kayıtlarını `DollySubmissionHold` içine aktarır.
4. Her kayıt için:
   - `Status = 'scanned'`
   - `LoadingSessionId` ve `ScanOrder` atanır.
5. `DollyLifecycle` içine `SCAN_CAPTURED` statüsü düşer.

**Amaç:** Dolly’nin “okutuldu” bilgisini sisteme yazmak ve loading session başlatmak.

---

### 4) Yükleme Tamamlama (Loading Completed)
1. Forklift, aynı session içindeki tüm dolly’leri bitirince “loading_completed” yapılır.
2. `DollySubmissionHold` kayıtları `Status = 'loading_completed'` olur.
3. Bu session için bir `WebOperatorTask` (PartNumber) oluşturulur.
4. Artık iş web operatörün ekranında “bekleyen görev” olarak görünür.

**Amaç:** Forklift işlemi biter, kontrol ve sevkiyat operatöre geçer.

---

### 5) Web Operatör Görevleri (Part Bazlı)
1. Operatör paneli `WebOperatorTask` üzerinden part görevlerini listeler.
2. Operatör bir task seçince ilgili dolly/VIN listesi görüntülenir.
3. Operatör, gerekli sevkiyat bilgilerini girer:
   - Sefer No, Plaka No
   - ASN veya İrsaliye seçimi

---

### 6) ASN / İrsaliye Gönderimi
1. Operatör “ASN Gönder” veya “İrsaliye Gönder” işlemini başlatır.
2. Seçilen dolly/VIN kayıtları sıralı şekilde hazırlanır.
3. CEVA servisine gönderim yapılır.
4. Başarılı ise:
   - `DollySubmissionHold` kayıtları **silinir**
   - `SeferDollyEOL` tablosuna kalıcı kayıt eklenir

**Amaç:** Dolly/VIN için işlem kapanır, sevkiyat resmiyet kazanır.

---

### 7) Süreç Kapanışı ve Raporlama
- Süreç kapanınca `SeferDollyEOL` artık tek gerçek kayıttır.
- `DollyLifecycle` ise tüm geçişlerin kronolojik izini tutar.
- Analitik view’ler bu tabloları birleştirerek:
  - Üretim → Scan → Loading → Task → Shipment sürelerini çıkarır
  - Operatör performanslarını ölçer
  - Vardiya bazlı performans sağlar

---

## Zaman ve Vardiya Mantığı
Sistem raporlarında **Türkiye yerel saati** kullanılır. Vardiyalar:
- **SHIFT_1:** 00:00 – 08:00
- **SHIFT_2:** 08:00 – 16:00
- **SHIFT_3:** 16:00 – 00:00

Vardiya hesapları, mümkün olan en güvenilir zaman damgasına göre yapılır:
1) Scan zamanı
2) Loading completed
3) Shipment zamanı
4) Üretim kayıt zamanı

---

## Kritik Noktalar / İşleyiş Gerçeği
- `DollySubmissionHold` kayıtları **ASN sonrası silinir** → geçmiş forklift verisi burada kalmaz.
- Forklift performansında bu yüzden `DollyLifecycle` kayıtları esas alınır.
- `EOLDATE` sadece **gün** içerir, saat içermez → saat bazlı üretim süresi tam hassas değildir.
- Part / Task bazlı analiz `WebOperatorTask` ve `SeferDollyEOL` birleşimiyle çıkarılır.

---

## Özet
Bu akış sayesinde:
- Dolly’nin üretimden sevkiyata kadar tüm yolculuğu takip edilir.
- Operatörler ve forklift performansı ölçülür.
- Vardiya bazlı raporlarla yönetsel kararlar desteklenir.
- Her kayıt, raporlama view’leri üzerinden read-only şekilde analiz edilir.

