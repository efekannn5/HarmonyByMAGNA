# HarmonyByMAGNA — Hata Çözme Rehberi
# Kapsamlı Sorun Giderme Kılavuzu

---

| Alan | Bilgi |
|------|-------|
| **Versiyon** | 1.0.0 |
| **Tarih** | 2026-02-21 |
| **Kapsam** | Tüm bileşenler: EcoSystem, TrixServices, MobileApp, HarmonyView |

---

## İçindekiler

1. [HarmonyEcoSystem Hataları](#1-harmonyecosystem-hataları)
2. [SQL Server / Veritabanı Hataları](#2-sql-server--veritabanı-hataları)
3. [TrixServices Hataları](#3-trixservices-hataları)
4. [Android Uygulama Hataları](#4-android-uygulama-hataları)
5. [HarmonyView Hataları](#5-harmonyview-hataları)
6. [Nginx / SSL Hataları](#6-nginx--ssl-hataları)
7. [Performans Sorunları](#7-performans-sorunları)
8. [Güvenlik Uyarıları](#8-güvenlik-uyarıları)
9. [Log Okuma Rehberi](#9-log-okuma-rehberi)
10. [Kontrol Komutları Hızlı Başvuru](#10-kontrol-komutları-hızlı-başvuru)

---

## 1. HarmonyEcoSystem Hataları

---

### HATA: Servis başlamıyor

**Belirti:**
```bash
sudo systemctl status harmonyecosystem
# Active: failed (Result: exit-code)
```

**Teşhis adımları:**

```bash
# 1. systemd günlüklerini oku
sudo journalctl -u harmonyecosystem -n 50 --no-pager

# 2. Uygulama log dosyasını oku
tail -50 /home/ymc_harmony/Harmony/HarmonyByMAGNA/HarmonyEcoSystem/logs/app.log
tail -50 /home/ymc_harmony/Harmony/HarmonyByMAGNA/HarmonyEcoSystem/logs/app_error.log
```

**Olası nedenler ve çözümler:**

| Hata Mesajı | Neden | Çözüm |
|-------------|-------|-------|
| `ModuleNotFoundError: No module named 'flask'` | Sanal ortam aktif değil | `.venv/bin/python3` kullanıldığından emin olun |
| `FileNotFoundError: config.yaml` | Yapılandırma dosyası bulunamadı | `config/config.yaml` var mı kontrol edin |
| `Address already in use` | Port 8181 başka bir süreç tarafından kullanılıyor | `sudo lsof -i :8181` ile süreci bulun, öldürün |
| `Permission denied: logs/app.log` | Logs dizini izinleri hatalı | `sudo chown -R ymc_harmony:ymc_harmony logs/` |

---

### HATA: `500 Internal Server Error` — API yanıtı

**Belirti:** API istekleri 500 kodu döndürüyor.

**Teşhis:**
```bash
# Anlık log izleme
tail -f logs/app.log

# 500 hatalarını filtrele
grep "ERROR\|CRITICAL\|Traceback" logs/app.log | tail -20
```

**Olası nedenler:**

| Hata | Çözüm |
|------|-------|
| `pyodbc.OperationalError: Login failed` | SQL Server kullanıcı adı/şifresi yanlış |
| `pyodbc.OperationalError: TCP Provider` | SQL Server'a erişilemiyor, ağ bağlantısını kontrol edin |
| `AttributeError: NoneType` | Veritabanında beklenen veri yok, migration eksik olabilir |
| `sqlalchemy.exc.ProgrammingError: Invalid column name` | Tablo şeması güncellenmemiş, migration çalıştırın |

---

### HATA: `401 Unauthorized` — Tüm API istekleri

**Belirti:** Tüm forklift API istekleri 401 döndürüyor.

**Teşhis:**
```sql
-- Aktif oturumları kontrol et
SELECT * FROM ForkliftLoginSession WHERE IsActive = 1;

-- Süresi dolmuş oturumları kontrol et
SELECT * FROM ForkliftLoginSession WHERE ExpiresAt < GETDATE();
```

**Çözümler:**

```bash
# 1. Token süresini kontrol et (8 saat sonra sona erer)
# Android uygulamasında yeniden giriş yapılması gerekir

# 2. SECRET_KEY değişti mi?
grep secret_key config/config.yaml
# SECRET_KEY değişirse TÜM aktif tokenlar geçersiz olur!

# 3. Tabloyu kontrol et
sqlcmd -S HOST -U USER -P PASS -d ControlTower -Q \
  "SELECT TOP 5 * FROM ForkliftLoginSession ORDER BY LoginAt DESC"
```

---

### HATA: WebSocket bağlantısı kurulamıyor

**Belirti:** Web dashboard gerçek zamanlı güncellemeler almıyor.

**Teşhis:**
```bash
# SocketIO bağlantısını test et
curl -i -N \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  http://localhost:8181/socket.io/?transport=websocket

# Eventlet yüklü mü?
source .venv/bin/activate
python3 -c "import eventlet; print('OK')"
```

**Çözüm:**
```bash
# Eventlet yükle
pip install eventlet

# Gunicorn worker class kontrol
grep worker_class gunicorn_config.py
# 'eventlet' olmalı

sudo systemctl restart harmonyecosystem
```

---

### HATA: CEVA servisi başarısız

**Belirti:** ASN gönderimi yapılamıyor, log'da SOAP hatası var.

**Teşhis:**
```bash
grep "CEVA\|ceva\|SOAP" logs/app.log | tail -20
```

**Olası nedenler:**

| Hata | Çözüm |
|------|-------|
| `Connection refused` | CEVA URL erişilemiyor, internet bağlantısını kontrol edin |
| `Timeout` | Timeout değerini config.yaml'da artırın (`timeout: 60`) |
| `Invalid credentials` | CEVA kullanıcı adı/şifresini kontrol edin |
| `zeep.exceptions.Fault` | CEVA SOAP yanıtında hata, log'daki mesaja bakın |
| `SSLError` | SSL sertifika sorunu, IT'den CEVA sertifikasını isteyin |

```bash
# CEVA URL erişimini test et
curl -I https://trweb04.cevalogistics.com/Ceva.DT.Supplier.WebService/DTSupplierService.asmx
```

---

### HATA: `config.yaml` değişiklikleri etkili olmuyor

**Çözüm:**
```bash
# Uygulamayı yeniden başlatın — config sadece başlangıçta okunur
sudo systemctl restart harmonyecosystem
```

---

## 2. SQL Server / Veritabanı Hataları

---

### HATA: `pyodbc.OperationalError: ('08001', '...')`

**Belirti:** Veritabanına bağlanılamıyor.

**Teşhis adımları:**

```bash
# 1. SQL Server'a ağ bağlantısını test et
ping 10.19.236.39
nc -zv 10.19.236.39 1433      # Port erişilebilir mi?
telnet 10.19.236.39 1433       # Alternatif

# 2. ODBC Driver kurulu mu?
odbcinst -q -d
# "ODBC Driver 18 for SQL Server" listede görünmeli
```

**Olası nedenler:**

| Mesaj | Çözüm |
|-------|-------|
| `[08001] TCP Provider: No connection could be made` | SQL Server'a ağ erişimi yok. Güvenlik duvarı kurallarını kontrol edin (1433/TCP) |
| `[28000] Login failed for user` | Kullanıcı adı veya şifre yanlış |
| `[HY000] Data source name not found` | ODBC Driver yüklü değil ya da adı yanlış yazılmış |
| `[01000] SSL Provider ... certificate chain` | TrustServerCertificate=yes ekleyin |

```bash
# ODBC Driver 18 kurulumu (Ubuntu)
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
curl https://packages.microsoft.com/config/ubuntu/22.04/prod.list \
  | sudo tee /etc/apt/sources.list.d/mssql-release.list
sudo apt update
sudo ACCEPT_EULA=Y apt install -y msodbcsql18
```

---

### HATA: `Invalid column name 'XYZ'`

**Belirti:** API çağrısı 500 hatası ile başarısız oluyor.

**Teşhis:**
```sql
-- Mevcut kolonları kontrol et
SELECT COLUMN_NAME, DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'DollySubmissionHold'
ORDER BY ORDINAL_POSITION;
```

**Çözüm:**
```bash
# Migration betiklerini sırayla kontrol et ve eksik olanı çalıştır
ls database/*.sql

# Örnek: Eksik kolon için
sqlcmd -S HOST -U USER -P PASS -d ControlTower \
  -i database/013_add_missing_columns_dolly_submission_hold.sql
```

---

### HATA: `The object name 'DollyEOLInfo' is invalid`

**Belirti:** `DollyEOLInfo` tablosu yok.

**Çözüm:**
```bash
# TrixServices'ın EOL verisi yazması için tablo gerekli
# EcoSystem'in migration'ı zaten oluşturur, ama manuel oluşturmak için:
sqlcmd -S HOST -U USER -P PASS -d ControlTower -Q "
CREATE TABLE DollyEOLInfo (
    DollyNo NVARCHAR(50) NOT NULL,
    VinNo NVARCHAR(50) NOT NULL,
    DollyOrderNo NVARCHAR(50),
    CustomerReferans NVARCHAR(100),
    Adet INT,
    EOLName NVARCHAR(100),
    EOLID INT,
    EOLDATE DATE,
    EOLDollyBarcode NVARCHAR(100),
    RECEIPTID NVARCHAR(50),
    InsertedAt DATETIME2 DEFAULT GETDATE(),
    CONSTRAINT PK_DollyEOLInfo PRIMARY KEY (DollyNo, VinNo)
);"
```

---

### HATA: Bağlantı havuzu doldu / `QueuePool limit of size 10 overflow 20`

**Belirti:** Yoğun kullanımda API çöküyor.

**Çözüm:**
```yaml
# config.yaml — pool boyutunu artır (uygulama yeniden başlatma gerektirir)
database:
  pool_size: 20      # Varsayılan 10
  max_overflow: 40   # Varsayılan 20
```

veya

```python
# app/__init__.py — SQLAlchemy engine options
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_size": 20,
    "max_overflow": 40,
    "pool_recycle": 1800,  # 30 dakikada bir yenile
}
```

---

## 3. TrixServices Hataları

---

### HATA: Servis başlamıyor (Windows)

**Teşhis:**
```cmd
REM Olay Görüntüleyicisi'ni aç
eventvwr.msc
REM Windows Logs > Application > HarmonyDollyEOLService hatalarını ara

REM Komut satırından kontrol
sc query HarmonyDollyEOLService

REM Log dosyasını kontrol et
type C:\HarmonyServices\DollyEOLService\logs\2025-11\service.log
```

**Olası nedenler:**

| Hata | Çözüm |
|------|-------|
| `ModuleNotFoundError: win32serviceutil` | `pip install pywin32` çalıştırın |
| `pywin32_postinstall hatası` | `python Scripts/pywin32_postinstall.py -install` |
| `Access denied` | install_service.bat'ı Yönetici olarak çalıştırın |
| `Port already in use` | 8181 portunu başka bir uygulama kullanıyor |

---

### HATA: EOL sistemi bağlanıp veri gönderemiyor

**Teşhis:**
```cmd
REM TrixServices'a test isteği gönder
curl -X POST http://localhost:8181/dolly-eol -H "Content-Type: application/json" ^
  -d "{\"RECEIPTID\":\"TEST\",\"DOLLYID\":\"DL-001\"}"
```

**Olası nedenler:**

| Belirti | Çözüm |
|---------|-------|
| `Connection refused` | Servis çalışmıyor, başlatın |
| `{"STATUS": 0}` | JSON formatı geçersiz veya RECEIPTID eksik |
| Yanıt yok (timeout) | Güvenlik duvarı 8181 portunu engelliyor |

---

### HATA: Veriler DollyEOLInfo'ya yazılmıyor

**Teşhis:**
```bash
# Log dosyasında DB hatası var mı?
grep "DB HATA\|DB upsert HATA" logs/2025-11/service.log

# SQL Server bağlantısını test et
python3 -c "
import pyodbc
conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=10.19.236.39;DATABASE=ControlTower;UID=kullanici;PWD=sifre;TrustServerCertificate=yes;')
print('OK')
"
```

**Sık Karşılaşılan Sorunlar:**

1. **`primary_key_column` yanlış** — config.json'da `"primary_key_column"` gerçek birincil anahtar ile eşleşmeli
2. **Tip uyuşmazlığı** — JSON'da string gelen değer DB'de INT ise hata oluşur
3. **NULL kısıtlaması** — DB'de NOT NULL olan bir kolon eşlemede belirtilmemiş

---

### HATA: Yedek tablo INSERT başarısız

```python
# Backup hatası ana işlemi durdurmaz! Sadece loglara bakın:
grep "BACKUP HATASI" logs/2025-11/service.log
```

```sql
-- Yedek tablo oluştur
CREATE TABLE DollyEOLInfoBackup (
    RECEIPTID NVARCHAR(50),
    DollyNo NVARCHAR(50),
    VinNo NVARCHAR(50),
    EOLName NVARCHAR(100),
    InsertedAt DATETIME2 DEFAULT GETDATE()
);
```

---

## 4. Android Uygulama Hataları

---

### HATA: "Sunucuya bağlanılamıyor"

**Teşhis adımları:**

```bash
# 1. Sunucu çalışıyor mu?
curl http://10.25.1.174:8181/api/health

# 2. Cihaz ağını test et (Android debug logları)
adb logcat -s "OkHttp"
```

**Olası nedenler:**

| Belirti | Çözüm |
|---------|-------|
| Sunucu IP değişti | `ForkliftApiService.java`'daki `BASE_URL`'i güncelleyin ve APK'yı yeniden derleyin |
| Wi-Fi bağlantısı yok | Cihazın fabrika Wi-Fi'sine bağlı olduğunu kontrol edin |
| Güvenlik duvarı engeli | Sunucuda 8181 portuna erişim açık mı kontrol edin |
| HTTP → HTTPS sorunu | `android:usesCleartextTraffic="true"` manifest'e eklenmiş olmalı (HTTP için) |

---

### HATA: Giriş barkodu çalışmıyor

**Teşhis:**
```bash
# API ile test et
curl -X POST http://10.25.1.174:8181/api/forklift/login \
  -H "Content-Type: application/json" \
  -d '{"operatorBarcode":"EMP12345","deviceId":"test"}'
```

**Olası nedenler:**

| Hata | Çözüm |
|------|-------|
| `400 — Geçersiz barkod` | Barkod formatı yanlış veya çalışan DB'de kayıtlı değil |
| `500` | Sunucu hatası — EcoSystem log'unu kontrol edin |
| Barkod okuyucu çalışmıyor | Cihaz barkod okuyucusunu test edin, fiziksel arıza olabilir |

```sql
-- Forklift login için çalışan barkodunun varlığını kontrol et
-- (Eğer UserAccount tablosunda kayıt zorunlu ise)
SELECT * FROM UserAccount WHERE OperatorBarcode = 'EMP12345';
```

---

### HATA: `401 Unauthorized` — Süre dolmadı ama yetki reddedildi

**Olası nedenler:**
1. **SECRET_KEY değişti** — Tüm tokenlar geçersiz olur. Operatörler yeniden giriş yapmalı.
2. **DB'deki token silindi** — ForkliftLoginSession tablosunu kontrol edin.

```sql
-- Token varlığını kontrol et
SELECT * FROM ForkliftLoginSession WHERE IsActive = 1 ORDER BY LoginAt DESC;

-- Süresi dolan tokenları temizle (opsiyonel)
DELETE FROM ForkliftLoginSession WHERE ExpiresAt < DATEADD(DAY, -1, GETDATE());
```

---

### HATA: Dolly barkod taraması yanıt vermiyor

**Teşhis:**
```bash
# API ile test et
curl -X POST http://10.25.1.174:8181/api/forklift/scan \
  -H "Authorization: Bearer TOKEN_BURAYA" \
  -H "Content-Type: application/json" \
  -d '{"dollyNo":"DL-001","loadingSessionId":"LOAD_TEST","barcode":"TEST"}'
```

**Hata Kodları:**

| HTTP Kodu | Anlam | Çözüm |
|-----------|-------|-------|
| 401 | Token geçersiz | Yeniden giriş yap |
| 404 | Dolly DollyEOLInfo'da yok | EOL sisteminin veri gönderdiğini kontrol et |
| 409 | Dolly zaten taranmış | Normal durum — aynı dolly tekrar taranamazdı |
| 500 | Sunucu hatası | EcoSystem log'unu kontrol et |

---

### HATA: APK yüklenmiyor

```
INSTALL_FAILED_OLDER_SDK
```
**Çözüm:** Cihaz Android sürümü minSdk (29 = Android 10) altında.

```
INSTALL_FAILED_TEST_ONLY
```
**Çözüm:** Release APK kullanın veya `adb install -t` ile yükleyin.

---

## 5. HarmonyView Hataları

---

### HATA: Backend başlamıyor

```bash
sudo systemctl status harmonyview-backend
sudo journalctl -u harmonyview-backend -n 30 --no-pager
```

| Hata | Çözüm |
|------|-------|
| `ModuleNotFoundError: fastapi` | `pip install -r requirements.txt` çalıştırın |
| `.env not found` | `.env` dosyasını oluşturun |
| `Port already in use (8000)` | `sudo lsof -i :8000` ile süreci bulun |

---

### HATA: Frontend boş/beyaz ekran gösteriyor

**Teşhis:**
```bash
# Tarayıcı geliştirici araçlarında konsolu kontrol edin (F12)

# VITE_API_URL doğru mu?
cat frontend-manager/.env
# VITE_API_URL=http://SUNUCU_IP:8000 olmalı

# Backend çalışıyor mu?
curl http://SUNUCU_IP:8000/health
```

**Yaygın sebepler:**
1. `VITE_API_URL` yanlış ayarlanmış — `.env` dosyasını düzenleyip yeniden build alın
2. CORS hatası — `Access-Control-Allow-Origin` başlığı eksik
3. API endpoint'i bulunamıyor — backend'in çalıştığından emin olun

---

### HATA: Grafikler veri göstermiyor

**Teşhis:**
```bash
# API'den veri geliyor mu?
curl http://SUNUCU_IP:8000/api/dashboard
```

**Olası nedenler:**

| Belirti | Çözüm |
|---------|-------|
| API yanıtı boş `[]` | Veritabanında o tarihe ait veri yok — tarih filtresini değiştirin |
| SQL View bulunamadı | `python3 apply_sql.py` ile view'ları oluşturun |
| `500` API hatası | Backend log'unu kontrol edin |

---

### HATA: WebSocket bağlantısı sürekli kopuyor

**Çözüm:**
```nginx
# Nginx yapılandırmasına WebSocket timeout ekleyin
location /ws {
    proxy_pass http://127.0.0.1:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_read_timeout 86400;       # 24 saat
    proxy_send_timeout 86400;
}
```

---

## 6. Nginx / SSL Hataları

---

### HATA: `502 Bad Gateway`

**Belirti:** Nginx çalışıyor ama uygulama 502 döndürüyor.

```bash
# Nginx hata log'u
sudo tail -f /var/log/nginx/error.log

# Arka uç uygulamaları çalışıyor mu?
curl http://localhost:8181/api/health  # EcoSystem
curl http://localhost:8000/health      # HarmonyView
```

**Çözüm:** İlgili uygulamayı yeniden başlatın:
```bash
sudo systemctl restart harmonyecosystem
sudo systemctl restart harmonyview-backend
```

---

### HATA: SSL Sertifikası Sorunları

```bash
# Sertifika geçerlilik tarihini kontrol et
sudo openssl x509 -in /etc/ssl/certs/harmony.crt -noout -dates

# Let's Encrypt sertifikası yenile
sudo certbot renew

# Otomatik yenileme cron
sudo crontab -e
# Ekle: 0 2 * * * certbot renew --quiet && systemctl reload nginx
```

---

### HATA: Android uygulaması HTTPS sertifikasına güvenmiyor

**Belirti:** Cihaz sunucuya HTTPS ile bağlanamıyor.

**Çözüm 1:** HTTP kullanın (dahili ağ için güvenli)
```xml
<!-- res/xml/network_security_config.xml -->
<network-security-config>
    <domain-config cleartextTrafficPermitted="true">
        <domain includeSubdomains="true">10.25.1.174</domain>
    </domain-config>
</network-security-config>
```

**Çözüm 2:** Özel CA sertifikasını cihaza yükleyin (kurumsal)
```bash
# Sertifikayı cihaza ADB ile ilet
adb push magna_ca.crt /sdcard/
# Cihazda: Ayarlar → Güvenlik → Sertifika Yükle
```

---

## 7. Performans Sorunları

---

### Yavaş API Yanıtları (> 2 sn)

**Teşhis:**
```bash
# Yavaş sorguları bul
grep "duration" logs/app.log | awk '{if ($NF > 2000) print}' | tail -20

# Aktif SQL Server sorguları
sqlcmd -S HOST -U USER -P PASS -d ControlTower -Q "
SELECT TOP 10 
    r.total_elapsed_time / 1000 AS elapsed_ms,
    t.text AS query_text
FROM sys.dm_exec_requests r
CROSS APPLY sys.dm_exec_sql_text(r.sql_handle) t
WHERE r.status = 'running'
ORDER BY r.total_elapsed_time DESC;"
```

**Çözümler:**

```sql
-- DollyEOLInfo tablosuna indeks ekle (sık sorgulanan kolonlar)
CREATE INDEX IX_DollyEOLInfo_EOLID ON DollyEOLInfo (EOLID);
CREATE INDEX IX_DollySubmissionHold_Status_Session 
ON DollySubmissionHold (Status, LoadingSessionId);
CREATE INDEX IX_AuditLog_CreatedAt ON AuditLog (CreatedAt);
```

---

### Yüksek Bellek Kullanımı

```bash
# Python process bellek kullanımı
ps aux | grep python | grep -v grep

# Bellek kullanımını izle
watch -n 5 'ps aux --sort=-%mem | head -10'
```

**Çözümler:**
- `pool_recycle` değerini düşürün (veritabanı bağlantıları yenilenir)
- Gunicorn `max_requests` değerini düşürün (worker'lar daha sık yeniden başlar)
- Flask-Caching önbellek sürelerini kısaltın

---

### Disk Doldu

```bash
# Disk kullanımını kontrol et
df -h
du -sh /var/log/* | sort -rh | head -10
du -sh logs/ | sort -rh | head -10

# Eski log dosyalarını temizle
find logs/ -name "*.log.*" -mtime +30 -delete
find /var/log/ -name "*.gz" -mtime +30 -delete

# Systemd journal'ı temizle
sudo journalctl --vacuum-time=30d
```

---

## 8. Güvenlik Uyarıları

---

### UYARI: `secret_key` üretimde değiştirilmedi

**Belirti:** config.yaml'da `"CHANGE_ME_SECRET"` veya `"unsafe-secret"` gibi varsayılan değerler.

**Çözüm:**
```bash
# Güvenli rastgele anahtar oluştur
python3 -c "import secrets; print(secrets.token_hex(32))"
# Çıktıyı config.yaml'a yaz

sudo systemctl restart harmonyecosystem
```

> **DİKKAT:** secret_key değiştiğinde tüm aktif JWT tokenlar geçersiz olur. Operatörler yeniden giriş yapmalı.

---

### UYARI: Şifreler config dosyasında açık metin

**Sorun:** SQL şifresi `config.yaml`'da açık yazılı.

**Çözüm:**
```bash
# config.yaml izinlerini kısıtla
chmod 600 config/config.yaml
chown ymc_harmony:ymc_harmony config/config.yaml

# Git'e dahil etme (zaten .gitignore'da olmalı)
echo "config/config.yaml" >> .gitignore
```

---

## 9. Log Okuma Rehberi

### 9.1 EcoSystem Log Formatı

```
2025-11-26 10:30:15 INFO app routes.api Forklift login: EMP12345
2025-11-26 10:30:16 ERROR app services.dolly_service DB error: ...
2025-11-26 10:30:17 CRITICAL app services.dolly_service Rollback executed
```

**Format:** `ZAMAN SEVİYE MODÜL MESAJ`

### 9.2 Kritik Log Mesajları

| Mesaj | Anlam | Aksiyon |
|-------|-------|---------|
| `CRITICAL ... Rollback executed` | İşlem geri alındı | API yanıtını ve hata detayını inceleyin |
| `ERROR DB upsert HATA` | SQL Server yazma hatası | DB bağlantısını ve tabloyu kontrol edin |
| `ERROR CEVA HATA` | CEVA gönderimi başarısız | CEVA URL erişimini test edin |
| `WARNING Forklift oturum bulunamadı` | Geçersiz token | Android uygulamasını yeniden başlatın |

### 9.3 TrixServices Log Formatı

```
2025-11-26 10:30:15 [INFO] İstek geldi [10.25.1.50]: {"RECEIPTID":"6743700"...}
2025-11-26 10:30:15 [INFO] DB upsert OK. Table=dbo.DollyEOLInfo, RECEIPTID=6743700
2025-11-26 10:30:15 [ERROR] DB upsert HATA! Table=dbo.DollyEOLInfo
```

### 9.4 Log Dosyaları

| Sistem | Log Dosyası |
|--------|------------|
| EcoSystem Ana | `HarmonyEcoSystem/logs/app.log` |
| EcoSystem Hata | `HarmonyEcoSystem/logs/app_error.log` |
| Gunicorn Erişim | `HarmonyEcoSystem/logs/gunicorn_access.log` |
| Gunicorn Hata | `HarmonyEcoSystem/logs/gunicorn_error.log` |
| TrixServices | `DollyEOLService/logs/YYYY-MM/service.log` |
| Nginx | `/var/log/nginx/access.log`, `/var/log/nginx/error.log` |
| systemd | `journalctl -u harmonyecosystem` |

---

## 10. Kontrol Komutları Hızlı Başvuru

### Linux Sunucu

```bash
# ===== SERVİS DURUMU =====
sudo systemctl status harmonyecosystem
sudo systemctl status harmonyview-backend
sudo systemctl status nginx

# ===== SERVİS YÖNETİMİ =====
sudo systemctl restart harmonyecosystem    # Kod güncellemesi sonrası
sudo systemctl reload nginx               # Nginx yapılandırması değişince

# ===== ANLIKT LOG =====
sudo journalctl -u harmonyecosystem -f    # systemd log
tail -f logs/app.log                     # Uygulama log

# ===== PORT KONTROLÜ =====
ss -tlnp | grep -E '8181|8190|8000|80|443'
sudo lsof -i :8181                       # 8181'i hangi süreç kullanıyor?

# ===== API SAĞLIK TESTİ =====
curl http://localhost:8181/api/health
curl http://localhost:8000/health

# ===== FORKLIFT GİRİŞ TESTİ =====
curl -X POST http://localhost:8181/api/forklift/login \
  -H "Content-Type: application/json" \
  -d '{"operatorBarcode":"EMP12345","deviceId":"test-001"}'

# ===== DISK/BELLEK =====
df -h
free -m
ps aux --sort=-%mem | head -10
```

### SQL Server

```sql
-- Aktif oturumlar
SELECT * FROM ForkliftLoginSession WHERE IsActive = 1;

-- Bugünkü dolly kuyruğu
SELECT COUNT(*), EOLName FROM DollyEOLInfo 
WHERE CAST(InsertedAt AS DATE) = CAST(GETDATE() AS DATE)
GROUP BY EOLName;

-- Bekleyen sevkiyatlar
SELECT LoadingSessionId, COUNT(*) AS DollyCount 
FROM DollySubmissionHold 
WHERE Status = 'loading_completed'
GROUP BY LoadingSessionId;

-- Son denetim kayıtları
SELECT TOP 20 * FROM AuditLog ORDER BY CreatedAt DESC;

-- Tablolar ve satır sayıları
SELECT TABLE_NAME, 
       (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS c 
        WHERE c.TABLE_NAME = t.TABLE_NAME) AS ColumnCount
FROM INFORMATION_SCHEMA.TABLES t
WHERE TABLE_SCHEMA = 'dbo'
ORDER BY TABLE_NAME;
```

### Windows (TrixServices)

```cmd
REM Servis durumu
sc query HarmonyDollyEOLService

REM Test isteği
curl -X POST http://localhost:8181/dolly-eol ^
  -H "Content-Type: application/json" ^
  -d "{\"RECEIPTID\":\"TEST001\",\"DOLLYID\":\"DL-001\",\"VINNO\":\"VIN001\"}"

REM Log dosyasını görüntüle
type logs\2025-11\service.log

REM 8181 portunu hangi uygulama kullanıyor?
netstat -ano | findstr :8181
```

### Android (ADB)

```bash
# Bağlı cihazlar
adb devices

# Uygulama logları
adb logcat -s "HarmonyApp"

# Uygulamayı yeniden başlat
adb shell am force-stop com.magna.controltower
adb shell am start com.magna.controltower/.LoginActivity

# APK yükle
adb install -r app-debug.apk
```
