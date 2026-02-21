# TrixServices — Detaylı Teknik Döküman
# Windows EOL Entegrasyon Servisi

---

| Alan | Bilgi |
|------|-------|
| **Versiyon** | 1.0.0 |
| **Tarih** | 2026-02-21 |
| **Teknoloji** | Python 3.11+, Flask, pyodbc, pywin32 |
| **İşletim Sistemi** | Windows 10 / Windows Server 2016+ |
| **Amaç** | EOL üretim sisteminden dolly verilerini alıp SQL Server'a yazmak |

---

## İçindekiler

1. [Genel Bakış](#1-genel-bakış)
2. [Proje Yapısı](#2-proje-yapısı)
3. [config.json Referansı](#3-configjson-referansı)
4. [Dolly Service (Flask API)](#4-dolly-service-flask-api)
5. [Windows Servis Sargısı](#5-windows-servis-sargısı)
6. [Veri Akışı ve Mapping](#6-veri-akışı-ve-mapping)
7. [Veritabanı UPSERT Mantığı](#7-veritabanı-upsert-mantığı)
8. [Günlük Sistemi](#8-günlük-sistemi)
9. [Servis Kurulumu ve Yönetimi](#9-servis-kurulumu-ve-yönetimi)
10. [Geliştirici Notları](#10-geliştirici-notları)

---

## 1. Genel Bakış

TrixServices, Magna'nın EOL (End of Line) üretim istasyonlarıyla ana Harmony sistemi arasında köprü görevi gören Windows background servisidir.

### 1.1 İş Akışı

```
EOL Üretim Sistemi
        │
        │  HTTP POST /dolly-eol
        │  (JSON payload)
        ▼
TrixServices Flask API (Port 8181)
        │
        │  JSON → DB Kolon Eşleme (mapping)
        ▼
SQL Server — DollyEOLInfo Tablosu (UPSERT)
        │
        │  Aynı anda
        ▼
SQL Server — DollyEOLInfoBackup Tablosu (INSERT)
        │
        ▼
HarmonyEcoSystem API Sunucusu
(Dolly'ler artık kuyrukta görünür)
```

### 1.2 Temel Prensipler

- EOL sistemi, dolly üretildiğinde HTTP POST isteği gönderir.
- TrixServices bu isteği alır, JSON alanlarını DB kolonlarıyla eşler ve SQL Server'a yazar.
- **Hata durumunda bile EOL sistemine `STATUS: 1` (başarılı) yanıtı döner** — EOL sisteminin üretim sürecini durdurmaması için.
- Gerçek hatalar log dosyasına yazılır.

---

## 2. Proje Yapısı

```
DollyEOLService/
│
├── dolly_service.py         # Ana Flask uygulaması (HTTP sunucu + DB işlemleri)
├── harmony_dolly_service_win.py  # Windows Service sargısı
├── service_wrapper.py       # Ek servis yardımcısı
├── config.json              # Tüm yapılandırma
├── install_service.bat      # Servisi kur ve başlat (Yönetici olarak çalıştır)
├── uninstall_service.bat    # Servisi kaldır
└── logs/                    # Günlük dosyaları (ay bazında klasörlenir)
    └── 2025-11/
        └── service.log
```

---

## 3. config.json Referansı

```json
{
  "server": {
    "host": "0.0.0.0",           // Dinleme adresi (tüm arayüzler için 0.0.0.0)
    "port": 8181,                 // Dinleme portu
    "endpoint": "/dolly-eol"      // İstek alınacak URL yolu
  },
  
  "database": {
    "driver": "{ODBC Driver 17 for SQL Server}",  // ODBC sürücü adı
    "server": "10.19.236.39",     // SQL Server IP:Port (varsayılan 1433)
    "database": "ControlTower",   // Veritabanı adı
    "username": "sua_appowneruser1",
    "password": "...",
    "target_table": "dbo.DollyEOLInfo",      // Ana tablo
    "primary_key_column": "RECEIPTID",        // UPSERT için birincil anahtar
    "backup_table": "dbo.DollyEOLInfoBackup"  // Yedek tablo (null = yedekleme kapalı)
  },
  
  "mapping": {
    // "JSON_ALANI": "DB_KOLONU"
    "RECEIPTID":       "RECEIPTID",
    "DOLLYID":         "DollyNo",
    "DOLLYORDERNO":    "DollyOrderNo",
    "VINNO":           "VinNo",
    "EOLID":           "EOLID",
    "EOLNAME":         "EOLName",
    "FORDCUSTOMERCODE":"CustomerReferans",
    "QUANTITY":        "Adet",
    "EOLDATE":         "EOLDATE"
  },
  
  "mapping2": {
    // Yedek tablo için farklı eşleme (yoksa mapping kullanılır)
    "RECEIPTID":       "RECEIPTID",
    "DOLLYID":         "DollyNo",
    // ... (mapping ile aynı olabilir veya farklı kolonlar eklenebilir)
  },
  
  "logging": {
    "base_dir": "logs"            // Log klasörü (C:\\HarmonyServices\\... gibi tam yol da olabilir)
  }
}
```

### 3.1 Alanların Açıklaması

| Alan | Açıklama |
|------|----------|
| `server.endpoint` | EOL sistemi bu URL'e POST gönderir |
| `database.primary_key_column` | UPSERT için hangi alan kontrol edilir |
| `database.backup_table` | null veya boş ise yedekleme yapılmaz |
| `mapping` | Gelen JSON'dan hangi alan, tabloda hangi kolona gider |
| `mapping2` | Yedek tablo için farklı eşleme (genellikle aynı) |

---

## 4. Dolly Service (Flask API)

### 4.1 Ana İstek İşleyici

```python
# dolly_service.py

@app.route("/dolly-eol", methods=["POST"])
def handle_dolly_eol():
    client_ip = request.remote_addr
    raw_data = request.data.decode("utf-8", errors="ignore")
    logging.info(f"İstek geldi [{client_ip}]: {raw_data}")

    receipt_id = "00000"  # Hata durumu için varsayılan
    
    try:
        payload = request.get_json(silent=True)
        
        # JSON formatı geçerli mi?
        if payload is None:
            logging.error("Geçersiz JSON formatı")
            return jsonify({"RECEIPTID": "00000", "STATUS": 0})
        
        receipt_id = payload.get("RECEIPTID", "00000")
        
        # JSON → DB kolon eşlemesi
        mapped_values = map_json_to_db_columns(payload, mapping_cfg)
        
        if mapped_values:
            # 1. Ana tabloya UPSERT
            upsert_dolly_eol_info(mapped_values, db_cfg)
            
            # 2. Yedek tabloya INSERT
            mapped_backup = map_json_to_db_columns(payload, mapping2_cfg)
            insert_backup_dolly_eol_info(mapped_backup, db_cfg)
        
    except Exception as exc:
        # HATA OLSA BİLE STATUS=1 DÖN — EOL sistemini durdurmamak için
        logging.exception(f"Hata: {exc}")
    
    return jsonify({"RECEIPTID": receipt_id, "STATUS": 1})
```

### 4.2 Gelen JSON Örneği (EOL Sistemi)

```json
{
    "RECEIPTID": "6743700",
    "DOLLYID": "DL-5170427",
    "DOLLYORDERNO": "DO-001",
    "VINNO": "3FA6P0LU6FR100001",
    "EOLID": 11,
    "EOLNAME": "V710-LLS-EOL",
    "FORDCUSTOMERCODE": "FORD_REF_001",
    "QUANTITY": 1,
    "EOLDATE": "2025-11-26"
}
```

### 4.3 Yanıt Formatı

**Başarılı:**
```json
{"RECEIPTID": "6743700", "STATUS": 1}
```

**Hata (geçersiz JSON):**
```json
{"RECEIPTID": "00000", "STATUS": 0}
```

> **Not:** EOL sistemi `STATUS: 0` aldığında yeniden deneyebilir. Bu nedenle geçerli ancak DB hatası olan durumlarda bile `STATUS: 1` dönülür (veri kaybı yerine yeniden deneme tercih edilir).

---

## 5. Windows Servis Sargısı

### 5.1 Servis Sınıfı

```python
# harmony_dolly_service_win.py

import win32serviceutil
import win32service
import win32event
import servicemanager

class HarmonyDollyEOLService(win32serviceutil.ServiceFramework):
    _svc_name_         = "HarmonyDollyEOLService"
    _svc_display_name_ = "Harmony Dolly EOL JSON Service"
    _svc_description_  = "Dolly EOL verilerini SQL Server'a yazan servis"
    
    def SvcDoRun(self):
        """Servis başladığında çağrılır"""
        self.main()
    
    def SvcStop(self):
        """Servis durdurulduğunda çağrılır"""
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.is_alive = False
        win32event.SetEvent(self.hWaitStop)
    
    def main(self):
        # Flask uygulamasını ayrı thread'de çalıştır
        flask_thread = threading.Thread(target=self.run_flask_app)
        flask_thread.daemon = True
        flask_thread.start()
        
        # Durdurulana kadar bekle
        while self.is_alive:
            if win32event.WaitForSingleObject(self.hWaitStop, 1000) == win32event.WAIT_OBJECT_0:
                break
    
    def run_flask_app(self):
        from dolly_service import app
        app.run(host='0.0.0.0', port=8181, threaded=True, use_reloader=False)
```

---

## 6. Veri Akışı ve Mapping

### 6.1 JSON → Veritabanı Kolon Eşleme

```python
def map_json_to_db_columns(payload: dict, mapping_cfg: dict) -> dict:
    """
    JSON alanlarını DB kolonlarıyla eşler.
    Sadece config.json'da tanımlı VE JSON'da mevcut alanlar işlenir.
    """
    mapped = {}
    
    for json_field, db_column in mapping_cfg.items():
        if json_field in payload:
            mapped[db_column] = payload[json_field]
        # JSON'da olmayan alanlar sessizce atlanır
    
    # Özel kural: DollyNo varsa ama EOLDollyBarcode yoksa,
    # barcode alanını DollyNo değeriyle doldur
    if "DollyNo" in mapped and "EOLDollyBarcode" not in mapped:
        mapped["EOLDollyBarcode"] = mapped["DollyNo"]
    
    return mapped
```

### 6.2 Eşleme Örneği

| Gelen JSON Alanı | DB Kolonu | Örnek Değer |
|-----------------|-----------|------------|
| `RECEIPTID` | `RECEIPTID` | `"6743700"` |
| `DOLLYID` | `DollyNo` | `"DL-5170427"` |
| `DOLLYORDERNO` | `DollyOrderNo` | `"DO-001"` |
| `VINNO` | `VinNo` | `"3FA6P0LU6FR100001"` |
| `EOLID` | `EOLID` | `11` |
| `EOLNAME` | `EOLName` | `"V710-LLS-EOL"` |
| `FORDCUSTOMERCODE` | `CustomerReferans` | `"FORD_REF"` |
| `QUANTITY` | `Adet` | `1` |
| `EOLDATE` | `EOLDATE` | `"2025-11-26"` |

---

## 7. Veritabanı UPSERT Mantığı

Sistem, `primary_key_column` (RECEIPTID) değerine göre:
- **Kayıt varsa:** UPDATE yapar
- **Kayıt yoksa:** INSERT yapar

```sql
-- Dinamik SQL (dolly_service.py içinde üretilir)
IF EXISTS (SELECT 1 FROM DollyEOLInfo WHERE RECEIPTID = ?)
    UPDATE DollyEOLInfo
    SET DollyNo = ?, VinNo = ?, ...
    WHERE RECEIPTID = ?;
ELSE
BEGIN
    INSERT INTO DollyEOLInfo (RECEIPTID, DollyNo, VinNo, ...)
    VALUES (?, ?, ?, ...);
END
```

### 7.1 Parametre Sırası

```python
params = []
params.append(key_value)                 # IF EXISTS kontrolü
params.extend(non_key_values)            # UPDATE SET değerleri
params.append(key_value)                 # UPDATE WHERE koşulu
params.extend(all_values)               # INSERT değerleri
```

---

## 8. Günlük Sistemi

### 8.1 Log Dosyası Yapısı

```
logs/
├── 2025-11/
│   └── service.log
├── 2025-12/
│   └── service.log
└── 2026-01/
    └── service.log
```

Her ay yeni bir klasör açılır.

### 8.2 Log Seviyeleri

| Seviye | Ne Zaman |
|--------|----------|
| `INFO` | Normal işlemler (istek geldi, DB başarılı) |
| `WARNING` | Eksik JSON alanları, boş mapping |
| `ERROR` | DB hatası, geçersiz JSON |
| `CRITICAL` | Servis çöküşü |

### 8.3 Örnek Log Çıktısı

```
2025-11-26 10:30:15 [INFO] İstek geldi [10.25.1.50]: {"RECEIPTID":"6743700","DOLLYID":"DL-5170427"...}
2025-11-26 10:30:15 [INFO] İşleniyor: RECEIPTID=6743700, Toplam 9 alan
2025-11-26 10:30:15 [INFO] Mapping başarılı: 9 kolon eşleşti
2025-11-26 10:30:15 [INFO] DB upsert OK. Table=dbo.DollyEOLInfo, RECEIPTID=6743700
2025-11-26 10:30:15 [INFO] Backup INSERT OK. Table=dbo.DollyEOLInfoBackup
2025-11-26 10:30:15 [INFO] Response [10.25.1.50]: {"RECEIPTID": "6743700", "STATUS": 1}
```

---

## 9. Servis Kurulumu ve Yönetimi

### 9.1 install_service.bat

```batch
@echo off
echo Harmony Dolly EOL Service kurulumu basliyor...

cd /d C:\HarmonyServices\DollyEOLService

REM Servisi kur
python harmony_dolly_service_win.py install

REM Servisi başlat
python harmony_dolly_service_win.py start

echo Kurulum tamamlandi.
pause
```

### 9.2 Servis Yönetim Komutları

```cmd
REM Servisi kur
python harmony_dolly_service_win.py install

REM Servisi başlat
python harmony_dolly_service_win.py start

REM Servisi durdur
python harmony_dolly_service_win.py stop

REM Servisi kaldır
python harmony_dolly_service_win.py remove

REM Servis durumu (cmd)
sc query HarmonyDollyEOLService

REM Services.msc ile görsel yönetim
services.msc
```

### 9.3 Servisin Otomatik Başlama Ayarı

```cmd
REM PowerShell ile otomatik başlatma ayarla
Set-Service -Name "HarmonyDollyEOLService" -StartupType Automatic
```

veya Services.msc → Sağ tık → Properties → Startup type: Automatic.

### 9.4 Yapılandırma Değişikliği Sonrası

```cmd
REM config.json değiştirdikten sonra
python harmony_dolly_service_win.py stop
python harmony_dolly_service_win.py start
```

---

## 10. Geliştirici Notları

### 10.1 Yeni JSON Alanı Ekleme

1. `config.json` içindeki `mapping` bölümüne yeni satır ekle:
   ```json
   "YENİ_JSON_ALANI": "YeniDBKolonu"
   ```
2. SQL Server'da ilgili kolonu kontrol et (yoksa migration ile ekle)
3. Servisi yeniden başlat

### 10.2 Farklı EOL Sistemi Desteği

Her EOL sisteminin gönderdiği JSON formatı farklı olabilir. Bu durumda:

1. `config.json` içindeki `mapping` bölümünü o sisteme göre ayarla
2. Her makine için farklı `config.json` kullanılabilir
3. Aynı servis kodu farklı yapılandırmalarla çalışabilir

### 10.3 Python Bağımlılıkları

```bash
pip install flask pyodbc pywin32
```

| Paket | Amaç |
|-------|------|
| flask | HTTP sunucu |
| pyodbc | SQL Server bağlantısı |
| pywin32 | Windows Service API |

### 10.4 Test Ortamı

```cmd
REM Servisi kurmadan doğrudan çalıştırma (test için)
python dolly_service.py

REM Test isteği gönder
curl -X POST http://localhost:8181/dolly-eol ^
  -H "Content-Type: application/json" ^
  -d "{\"RECEIPTID\":\"TEST001\",\"DOLLYID\":\"DL-001\",\"VINNO\":\"VIN001\",\"EOLNAME\":\"TEST-EOL\",\"EOLID\":99}"
```

Beklenen yanıt: `{"RECEIPTID":"TEST001","STATUS":1}`

SQL Server'da kontrol:
```sql
SELECT * FROM DollyEOLInfo WHERE RECEIPTID = 'TEST001';
SELECT * FROM DollyEOLInfoBackup WHERE RECEIPTID = 'TEST001';
```
