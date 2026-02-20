## HarmonyEcoSystem 

Magna üretim hattındaki dolly'lerin (parça taşıma arabaları) lojistik takibini yapan Flask tabanlı Control Tower sistemi.

### 📱 Üç Ana Modül

1. **Backend/API** – SQL Server'dan gelen dolly verilerini işler, forklift ve web operatör işlemlerini koordine eder. REST API üzerinden Android ve Web Dashboard ile iletişim kurar.
2. **Web Dashboard** – Lojistik operatörlerin sevkiyatları kontrol edip sefer no + plaka girerek ASN/İrsaliye gönderdiği panel. Admin/Operator rollü kullanıcı yönetimi.
3. **Android Forklift App** – Forklift operatörlerin çalışan barkodlarıyla giriş yapıp dolly'leri sırayla okutup TIR'a yüklemesini sağlayan mobil uygulama.

### 🚀 Yeni İş Akışı

```
1. EOL İstasyonu → Dolly çıkar (DollyEOLInfo tablosu)
2. Forklift (Android) → Çalışan barkodu ile giriş
3. Forklift (Android) → Dolly'leri SIRAYLA okut (TIR'a yüklerken)
4. Forklift (Android) → "Yükleme Tamamlandı" butonu
5. Web Operatör → Sefer No + Plaka gir + ASN/İrsaliye seç → Gönder
6. Sistem → SeferDollyEOL tablosuna kaydet → BİTTİ ✅
```

### 📚 Dokümantasyon

- **[Android API Tam Rehber](docs/ANDROID_API_FULL_GUIDE.md)** - Kotlin kod örnekleri, tüm endpoint'ler
- **[Hızlı Başlangıç](docs/ANDROID_QUICK_REFERENCE.md)** - API özet kullanım
- **[API Endpoint Listesi](docs/API_ENDPOINTS.md)** - Tüm endpoint'lerin detaylı listesi
- **[Yeni İş Akışı](docs/new_workflow.md)** - İş akışı diyagramları ve açıklamalar

### 🔐 Forklift Authentication (Barkod Login)

**Database Migration:**
```bash
# SQL Server'da çalıştır
database/012_create_forklift_login_sessions.sql
```

**Login Endpoint:**
```http
POST /api/forklift/login
{
  "operatorBarcode": "EMP12345",
  "operatorName": "Mehmet Yılmaz",
  "deviceId": "android-123"
}
```

**Response:**
```json
{
  "success": true,
  "sessionToken": "eyJhbGc...",
  "operatorName": "Mehmet Yılmaz",
  "expiresAt": "2025-11-26T23:30:00Z"
}
```

**Sonraki İstekler:**
```http
Authorization: Bearer eyJhbGc...
```

### 📡 API Endpoint'leri

**Forklift (Android App):**
- `POST /api/forklift/login` - Barkod ile giriş
- `POST /api/forklift/scan` - Dolly okut
- `POST /api/forklift/complete-loading` - Yükleme tamamla
- `POST /api/forklift/logout` - Çıkış

**Web Operator (Dashboard):**
- `GET /operator/shipments` - Bekleyen sevkiyatlar
- `POST /operator/shipments/complete` - Sefer no + plaka + ASN/İrsaliye

**Detaylı liste:** [docs/API_ENDPOINTS.md](docs/API_ENDPOINTS.md)

### 🔧 Teknik Detaylar

- Proje Flask üstünde inşa edilir; modüler yapı (config, extensions, modeller, servisler, blueprint’ler) sayesinde ileride mikro servis ya da farklı istemciler eklenebilir.
- Yapılandırmalar `config/config.yaml` içinden yüklenir. SQL kullanıcı adı, parola, veritabanı adı, log ayarları gibi sabitler bu dosyada tutulur ve ortam değişkeniyle farklı dosyalar seçilebilir.
- `PWorkStation` tablosundaki istasyon isimleri otomatik olarak taranır; adı `EOL` ile biten kayıtlar grup seçiminde kullanılmaya hazır hale gelir (isterseniz `config/config.yaml` altında `pworkstation.require_finish_product_station` ile bitmiş ürün filtrelemesi açılabilir). Dashboard’daki “Grup Yönetimi” formu bu istasyonlardan yola çıkarak kalıcı `DollyGroup`/`DollyGroupEOL` kayıtlarını üretir ve her istasyon için gönderim etiketi (ASN, İrsaliye veya Her İkisi) belirlemenize izin verir.
- SQLAlchemy modelleri `DollyEOLInfo` ve `SeferDollyEOL` tablolarını karşılar; ilki canlı sırayı tutarken ikincisi yalnızca onay sonrası yazılan sefer logları ve geçmiş analizler için kullanılır. Servis katmanı gerektiğinde prosedür çağrıları veya ek iş kuralları için genişletilebilir.
- SQL Server bağlantı cümlesi `database.options` altındaki değerlerle `Encrypt`, `TrustServerCertificate` gibi ODBC parametrelerini kabul eder; sertifika doğrulamaya dair ihtiyaçlar buradan yönetilir.
- Forklift terminal süreci için geçici veriler `DollySubmissionHold` tablosunda tutulur. Tabloyu oluşturmak için `database/001_create_dolly_submission_hold.sql` dosyasını SQL Server üzerinde çalıştırın.
- `PWorkStation` tablosundaki istasyon isimleri otomatik olarak taranır; adı `EOL` ile biten kayıtlar grup seçiminde kullanılmaya hazır hale gelir (isterseniz `config/config.yaml` altında `pworkstation.require_finish_product_station` ile bitmiş ürün filtrelemesi açılabilir). Dashboard’daki “Grup Yönetimi” formu bu istasyonlardan yola çıkarak kalıcı `DollyGroup`/`DollyGroupEOL` kayıtlarını üretir ve her istasyon için gönderim etiketi (ASN, İrsaliye veya Her İkisi) belirlemenize izin verir.
- Gelişmiş grup yönetimi için `DollyGroup` ve `DollyGroupEOL` tabloları kullanılır; `database/002_create_dolly_groups.sql` ve `database/003_alter_dolly_group_eol_add_tag.sql` scriptlerini çalıştırarak yapılandırın. Tablolar boşsa sistem `PWorkStation` verilerinden dinamik gruplar üretir.
- `DollyEOLInfo` tablosuna `EOLDollyBarcode` kolonu eklendi (`database/004_alter_dolly_eolinfo_add_barcode.sql`). Forklift uygulaması barkod okuyup backend’deki kayıtla eşleştirebilir.
- `DollyLifecycle` tablosu (`database/005_create_dolly_lifecycle.sql`) her dolly’nin durum değişikliklerini (`EOL_READY`, `SCAN_CAPTURED`, `WAITING_SUBMIT`, `SUBMITTED_TERMINAL`, `WAITING_OPERATOR`, `COMPLETED_*`) loglar. Bu log gelecekteki history raporları için temel alınır.
- Güvenlik için `UserAccount`, `UserRole` ve terminal cihaz kayıtlarını içeren yeni tablo seti oluşturulacak; kullanıcı parolaları bcrypt/argon2 gibi güçlü bir algoritmayla hash’lenir. Web admin paneli kullanıcı/rol yönetimini sağlar; forklift operatörleri terminalde oluşturulan barkod/OTP ile oturum açar.
- Kimlik doğrulaması için `database/006_create_user_tables.sql` scripti `UserRole`, `UserAccount`, `TerminalDevice` ve `TerminalBarcodeSession` tablolarını oluşturur. Böylece web/terminal rollerini ayrı ayrı yönetebilir, barkod tabanlı girişleri kayıt altına alabilirsiniz.
- Her aksiyonu kim hangi cihazdan yaptı sorusuna cevap vermek için `database/007_create_audit_log.sql` scripti `AuditLog` tablosunu ekler. `AuditService` kritik operasyonlarda kayıt düşer.

### Terminal Bekleme Akışı

1. Forklift operatörü barkodu okuttuğunda Android uygulaması `POST /api/groups/<dollyNo>/hold` çağrısını yapar. Bu çağrı `vinNo`, `terminalUser` ve opsiyonel metadata iletilmesini bekler; kayıt `DollySubmissionHold` tablosuna yazılır.
2. Terminaldeki kullanıcı kontrol edip onayladığında `POST /api/groups/<dollyNo>/submit` çağrısı yapılır. Servis bu kaydı `submitted/processed` durumuna çeker, `SeferDollyEOL` tablosuna log atar ve dolly’i üretimden çıkmış sayar.
3. Bekleyen tüm kayıtlar `GET /api/holds` uç noktası veya dashboard’daki “Terminal Bekleyen Kayıtlar” tablosundan izlenebilir. İsteğe göre `status` parametresiyle filtre uygulanabilir.

### Grup Bazlı Sıralama

1. EOL istasyonları `GET /api/pworkstations/eol` uç noktasından alınabilir. Bu uç varsayılan olarak yalnızca adı `EOL` ile biten `PWorkStation` kayıtlarını döner; `pworkstation.require_finish_product_station` true yapılırsa bitmiş ürün filtresi de uygulanır.
2. `GET /api/groups/definitions` ile her EOL istasyonuna karşılık gelen dinamik veya kullanıcı tarafından oluşturulmuş grup tanımları (etiket bilgileri dahil), `GET /api/group-sequences` ile grup bazlı sıra + dolly kuyruğu izlenir. Dashboard’daki “Grup Yönetimi” sayfası aynı bilgileri görselleştirir ve etiketli grup ekleme formu sağlar.
3. Barkod eşleştirmesi için `POST /api/barcode/lookup` uç noktası ve `POST /api/groups/<dollyNo>/hold` (body’de `barcode` alanı) kullanılır. Barkod değeri `DollyEOLInfo.EOLDollyBarcode` ile doğrulanır.

### Dolly Yaşam Döngüsü

1. **EOL_READY** – Dolly `DollyEOLInfo` tablosuna düştüğünde loglanır.
2. **SCAN_CAPTURED** → **WAITING_SUBMIT** – Forklift okutma (`POST /groups/<dolly>/hold`) sonrası.
3. **SUBMITTED_TERMINAL** → **WAITING_OPERATOR** – El terminalinden gönderim (`POST /groups/<dolly>/submit`) sonrası.
4. **COMPLETED_ASN / COMPLETED_IRS / COMPLETED_BOTH** – Operator onayı (`POST /groups/<dolly>/ack`) sonrası; `DollyGroupEOL.ShippingTag` değerine göre `SeferDollyEOL` tablosu güncellenir.

### Güvenlik ve Roller

- **Web Admin (`admin`)**: Dashboard ayarları, API anahtarları, terminal cihaz yönetimi, kullanıcı/rol oluşturma ve sıfırlama işlemleri yapar.
- **Web Operator (`operator`)**: Dashboard’da sadece dolly kuyruğunu görür, grup onayı/ack işlemlerini yürütür, kendi şifresini değiştirir.
- **Terminal Admin (`terminal_admin`)**: Forklift cihazlarını eşler, barkod oturumlarını üretir, cihaz bazlı ayarları düzenler.
- **Terminal Operator (`terminal_operator`)**: Mobil uygulamada barkodla giriş yapar; sadece okutma ve submit API’lerine erişebilir.
- Barkod oturumları `TerminalBarcodeSession` tablosunda saklanır; token’lar kısa süreli OTP olarak üretilir ve API üzerinden doğrulanır. Token kullanıldığında `UsedAt` alanı dolarak tekrar kullanım engellenir.
- Tüm kritik hareketler (grup oluşturma/güncelleme, forklift oku/submit, operatör onayı vb.) `AuditLog` tablosunda saklanır. Log kayıtları `actor_type`, `actor_name`, aksiyon, kaynak bilgisi ve opsiyonel JSON metadata içerir; böylece “kim ne yaptı” sorguları doğrudan SQL üzerinden çekilebilir.
- Web giriş ekranı `/auth/login` adresindedir. İlk kullanıcıyı oluşturmak için `UserAccount` tablosuna bcrypt hash’iyle (örn. Flask shell’de `from app.utils.security import hash_password`) kayıt ekleyin; giriş yaptıktan sonra dashboard menüsünden diğer kullanıcı ve terminal ayarları yönetilebilir.
- Admin menüsünde iki sekme bulunur: “Ayarlar” (kullanıcı oluşturma, şifre sıfırlama, terminal barkodu üretme) ve “Loglar” (SQL tabanlı olaylar + dosya log’larının ön izlemesi). Böylece hem SQL hem de dosya logları tek ekrandan izlenebilir.
- API blueprint’i (JSON) ve dashboard blueprint’i (HTML) ayrıdır; böylece Android istemcisi için gerekli uçlar ile web arayüzü birbirini engellemez.
- Tasarım şu an sade tutulur; amaç, algoritmalar ve veri akışını doğrulayabileceğimiz sağlam bir altyapı kurmaktır. İleride CSS/JS katmanı genişletilebilir.

### Başlangıç Adımları

1. `python -m venv .venv && source .venv/bin/activate`
2. `pip install -r requirements.txt`
3. `export APP_CONFIG_FILE=config/config.yaml` (veya Windows eşdeğeri)
4. `flask --app run.py --debug run`

Varsayılan host/port `config/config.yaml` içindeki `app.host` ve `app.port` alanlarıyla yönetilir (şu anda 0.0.0.0:8181). API ve dashboard aynı portta servis edilir.

> Not: Gerçek bağlantı bilgilerini `config/config.yaml` içindeki ilgili alanlara girin veya ayrı bir dosya oluşturup `APP_CONFIG_FILE` değişkeniyle gösterin.

Harmony By Magna
