# HarmonyByMAGNA — Sıfırdan Kurulum Rehberi
# Tüm Bileşenler — Adım Adım Tam Kurulum

---

| Alan | Bilgi |
|------|-------|
| **Versiyon** | 1.0.0 |
| **Tarih** | 2026-02-21 |
| **Hedef Kitle** | IT Yöneticileri, Sistem Kurulumcuları |
| **Tahmini Süre** | ~2-3 saat (tüm bileşenler) |

---

## İçindekiler

1. [Genel Bakış ve Ön Koşullar](#1-genel-bakış-ve-ön-koşullar)
2. [Altyapı Hazırlığı — SQL Server](#2-altyapı-hazırlığı--sql-server)
3. [Bileşen 1 — HarmonyEcoSystem (Ana Backend)](#3-bileşen-1--harmonyecosystem-ana-backend)
4. [Bileşen 2 — HarmonyView (Dashboard'lar)](#4-bileşen-2--harmonyview-dashboardlar)
5. [Bileşen 3 — TrixServices (Windows EOL Servisi)](#5-bileşen-3--trixservices-windows-eol-servisi)
6. [Bileşen 4 — HarmonyMobileApp (Android)](#6-bileşen-4--harmonymobileapp-android)
7. [Nginx Yapılandırması](#7-nginx-yapılandırması)
8. [Kurulum Sonrası Kontroller](#8-kurulum-sonrası-kontroller)
9. [Güvenlik Adımları](#9-güvenlik-adımları)

---

## 1. Genel Bakış ve Ön Koşullar

### 1.1 Sistem Mimarisi

```
┌─────────────────────────────────────────────────────────────┐
│  Windows Makinesi (EOL Fabrika)                             │
│  └── TrixServices (Port 8181) → SQL Server'a veri gönderir │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTP POST /dolly-eol
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  Linux Sunucu (Ubuntu 22.04)                                │
│  ├── HarmonyEcoSystem  → Port 8181  (Ana Backend + API)    │
│  ├── Analytics         → Port 8190  (Analitik Dashboard)   │
│  ├── HarmonyView Backend → Port 8000 (Manager Dashboard)   │
│  ├── HarmonyView Frontend → Port 3000 (Manager UI)         │
│  └── Nginx → Port 80/443 (Ters Proxy)                      │
└────────────────────────────┬────────────────────────────────┘
                             │ SQL Server ODBC
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  SQL Server (10.19.236.39:1433)                             │
│  └── ControlTower Veritabanı                               │
└─────────────────────────────────────────────────────────────┘
                             ▲
                             │ REST API (HTTP/HTTPS)
┌─────────────────────────────────────────────────────────────┐
│  Android El Terminalleri (Fabrika Wi-Fi)                    │
│  └── HarmonyMobileApp — Forklift uygulaması                │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Sunucu Gereksinimleri

| Bileşen | İşletim Sistemi | RAM | CPU | Disk |
|---------|----------------|-----|-----|------|
| HarmonyEcoSystem | Ubuntu 22.04 LTS | 4 GB+ | 2+ çekirdek | 20 GB+ |
| HarmonyView | Ubuntu 22.04 LTS (aynı sunucu) | — | — | — |
| TrixServices | Windows 10/Server 2016+ | 2 GB+ | 1+ çekirdek | 10 GB+ |
| SQL Server | Windows Server 2019+ | 8 GB+ | 4+ çekirdek | 100 GB+ |

### 1.3 Ağ Gereksinimleri

| Port | Protokol | Açıklama |
|------|----------|----------|
| 1433 | TCP | SQL Server |
| 8181 | TCP | HarmonyEcoSystem API |
| 8190 | TCP | Analytics Dashboard |
| 8000 | TCP | HarmonyView Manager Backend |
| 3000 | TCP | HarmonyView Manager Frontend (dev) |
| 80 | TCP | Nginx HTTP |
| 443 | TCP | Nginx HTTPS |

---

## 2. Altyapı Hazırlığı — SQL Server

> Bu adımlar SQL Server yöneticisi tarafından gerçekleştirilmelidir.

### 2.1 Veritabanı Oluşturma

SQL Server Management Studio (SSMS) veya `sqlcmd` ile bağlanın:

```sql
-- 1. Veritabanı oluştur
CREATE DATABASE ControlTower;
GO

-- 2. Kullanıcı oluştur
USE ControlTower;
CREATE LOGIN sua_appowneruser1 WITH PASSWORD = 'GüçlüŞifre2026!!';
CREATE USER sua_appowneruser1 FOR LOGIN sua_appowneruser1;

-- 3. Gerekli izinleri ver
ALTER ROLE db_owner ADD MEMBER sua_appowneruser1;
GO
```

### 2.2 Migration Betiklerini Çalıştırma

Aşağıdaki betikleri sırayla çalıştırın (HarmonyEcoSystem/database/ klasöründe):

```bash
# Sunucuya bağlan ve sırayla çalıştır
sqlcmd -S 10.19.236.39 -U sua_appowneruser1 -P 'Şifre' -d ControlTower \
  -i 001_create_dolly_submission_hold.sql

sqlcmd -S 10.19.236.39 -U sua_appowneruser1 -P 'Şifre' -d ControlTower \
  -i 002_create_dolly_groups.sql

sqlcmd -S 10.19.236.39 -U sua_appowneruser1 -P 'Şifre' -d ControlTower \
  -i 003_alter_dolly_group_eol_add_tag.sql

sqlcmd -S 10.19.236.39 -U sua_appowneruser1 -P 'Şifre' -d ControlTower \
  -i 004_alter_dolly_eolinfo_add_barcode.sql

sqlcmd -S 10.19.236.39 -U sua_appowneruser1 -P 'Şifre' -d ControlTower \
  -i 005_create_dolly_lifecycle.sql

sqlcmd -S 10.19.236.39 -U sua_appowneruser1 -P 'Şifre' -d ControlTower \
  -i 006_create_user_tables.sql

sqlcmd -S 10.19.236.39 -U sua_appowneruser1 -P 'Şifre' -d ControlTower \
  -i 007_create_audit_log.sql

sqlcmd -S 10.19.236.39 -U sua_appowneruser1 -P 'Şifre' -d ControlTower \
  -i 008_add_partnumber_system.sql

# ... 024 numaralı betiğe kadar sırayla devam edin
```

> **İpucu:** Hepsini toplu çalıştırmak için:
> ```bash
> for f in $(ls database/*.sql | sort); do
>   echo "Running: $f"
>   sqlcmd -S 10.19.236.39 -U sua_appowneruser1 -P 'Şifre' -d ControlTower -i "$f"
> done
> ```

### 2.3 İlk Admin Kullanıcısı Oluşturma

```python
# Python ile hash oluştur (Flask shell'de çalıştırın)
from werkzeug.security import generate_password_hash
hash = generate_password_hash("AdminŞifre123!")
print(hash)
```

```sql
-- Oluşturulan hash ile admin kullanıcısı ekle
INSERT INTO UserRole (RoleName, Description) VALUES ('admin', 'Yönetici');
INSERT INTO UserRole (RoleName, Description) VALUES ('operator', 'Operatör');

INSERT INTO UserAccount (Username, PasswordHash, RoleId, IsActive, CreatedAt)
SELECT 'admin', '<yukarıda_oluşturulan_hash>', r.Id, 1, GETDATE()
FROM UserRole r WHERE r.RoleName = 'admin';
```

---

## 3. Bileşen 1 — HarmonyEcoSystem (Ana Backend)

### 3.1 Linux Sunucu Hazırlığı

```bash
# Sistemi güncelle
sudo apt update && sudo apt upgrade -y

# Python ve araçları kur
sudo apt install -y python3 python3-pip python3-venv git curl

# ODBC Driver 18 for SQL Server kur (Ubuntu 22.04 için)
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
curl https://packages.microsoft.com/config/ubuntu/22.04/prod.list \
  | sudo tee /etc/apt/sources.list.d/mssql-release.list

sudo apt update
sudo ACCEPT_EULA=Y apt install -y msodbcsql18
sudo apt install -y unixodbc-dev

# Nginx kur
sudo apt install -y nginx

# Kullanıcı oluştur
sudo useradd -m -s /bin/bash ymc_harmony
sudo usermod -aG sudo ymc_harmony
```

### 3.2 Kaynak Kodu İndirme

```bash
# Harmony kullanıcısına geç
sudo su - ymc_harmony

# Proje dizini oluştur
mkdir -p ~/Harmony && cd ~/Harmony

# Kodu klonla
git clone https://github.com/efekannn5/HarmonyByMAGNA.git
cd HarmonyByMAGNA/HarmonyEcoSystem
```

### 3.3 Python Sanal Ortam Kurulumu

```bash
# Sanal ortam oluştur
python3 -m venv .venv

# Aktifleştir
source .venv/bin/activate

# Bağımlılıkları yükle
pip install --upgrade pip
pip install -r requirements.txt

# Gunicorn ve eventlet yükle
pip install gunicorn eventlet
```

### 3.4 Yapılandırma Dosyası

```bash
# config dizinini kontrol et
cat config/config.yaml
```

Aşağıdaki alanlarda kendi değerlerinizi girin:

```yaml
# config/config.yaml
app:
  name: HarmonyEcoSystem
  secret_key: "ÜRETİMDE_MUTLAKA_DEĞİŞTİR_UZUN_RASTGELE_STRING"
  environment: production
  api_prefix: "/api"
  host: "0.0.0.0"
  port: 8181

database:
  dialect: mssql+pyodbc
  username: "sua_appowneruser1"
  password: "BURAYA_GERCEK_SIFRE"
  host: "10.19.236.39"          # SQL Server IP
  port: 1433
  database: "ControlTower"
  driver: "ODBC Driver 18 for SQL Server"
  options:
    Encrypt: "yes"
    TrustServerCertificate: "yes"
  echo: false

logging:
  level: INFO
  file: logs/app.log
  rotation: 10485760

ceva:
  enabled: true
  environment: "production"
  production:
    url: "https://trweb04.cevalogistics.com/Ceva.DT.Supplier.WebService/DTSupplierService.asmx"
    username: "CEVA_KULLANICI"
    password: "CEVA_SIFRE"
    supplier_code: "GSDB_KOD"
    user_id: "0"
  timeout: 30
  retry_count: 2
```

> **ÖNEMLİ:** `secret_key` üretim ortamında uzun ve tahmin edilemez olmalıdır:
> ```bash
> python3 -c "import secrets; print(secrets.token_hex(32))"
> ```

### 3.5 Logs Dizini Oluşturma

```bash
mkdir -p logs
chmod 755 logs
```

### 3.6 Bağlantı Testi

```bash
# Sanal ortam aktifken test et
source .venv/bin/activate

# Veritabanı bağlantısını test et
python3 -c "
import pyodbc
conn = pyodbc.connect(
    'DRIVER={ODBC Driver 18 for SQL Server};'
    'SERVER=10.19.236.39;'
    'DATABASE=ControlTower;'
    'UID=sua_appowneruser1;'
    'PWD=SIFRE;'
    'TrustServerCertificate=yes;'
)
print('✅ Veritabanı bağlantısı başarılı')
conn.close()
"
```

### 3.7 Manuel Çalıştırma (Test)

```bash
source .venv/bin/activate
python3 run.py
```

Çıktıda şunu görmelisiniz:
```
HARMONY ECOSYSTEM - MAIN SYSTEM STARTING - Port 8181
ANALYTICS DASHBOARD STARTING - Port 8190
```

### 3.8 systemd Servisi Kurulumu

```bash
# gunicorn_config.py içindeki yolları düzenle
nano gunicorn_config.py
# accesslog ve errorlog yollarını /home/ymc_harmony/... olarak güncelle

# harmonyecosystem.service içindeki yolları düzenle
nano harmonyecosystem.service
# WorkingDirectory, User, ExecStart yollarını güncelle
```

Örnek servis dosyası:

```ini
# /etc/systemd/system/harmonyecosystem.service
[Unit]
Description=HarmonyEcoSystem Flask Application
After=network.target

[Service]
Type=simple
User=ymc_harmony
Group=ymc_harmony
WorkingDirectory=/home/ymc_harmony/Harmony/HarmonyByMAGNA/HarmonyEcoSystem
Environment="PATH=/home/ymc_harmony/Harmony/HarmonyByMAGNA/HarmonyEcoSystem/.venv/bin:/usr/bin:/usr/local/bin"
ExecStart=/home/ymc_harmony/Harmony/HarmonyByMAGNA/HarmonyEcoSystem/.venv/bin/python3 run.py
Restart=always
RestartSec=10
NoNewPrivileges=true
PrivateTmp=true
StandardOutput=append:/home/ymc_harmony/Harmony/HarmonyByMAGNA/HarmonyEcoSystem/logs/app.log
StandardError=append:/home/ymc_harmony/Harmony/HarmonyByMAGNA/HarmonyEcoSystem/logs/app_error.log

[Install]
WantedBy=multi-user.target
```

```bash
# Servisi kur ve başlat
sudo cp harmonyecosystem.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable harmonyecosystem
sudo systemctl start harmonyecosystem

# Durumu kontrol et
sudo systemctl status harmonyecosystem
```

### 3.9 Kurulumu Doğrulama

```bash
# API sağlık kontrolü
curl http://localhost:8181/api/health
# Beklenen: {"status": "ok", "app": "HarmonyEcoSystem"}

# Analytics kontrolü
curl http://localhost:8190/analytics
```

---

## 4. Bileşen 2 — HarmonyView (Dashboard'lar)

HarmonyView üç ayrı parçadan oluşur:
- **Backend** (FastAPI, Port 8000) — Manager Dashboard için
- **Frontend** (React/Vite, Port 3000) — Manager Dashboard UI
- **Frontend Manager TV** (React/Vite) — TV/Büyük ekran görünümü

### 4.1 Node.js Kurulumu

```bash
# NVM ile Node.js 20 LTS kur
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.bashrc
nvm install 20
nvm use 20
node --version  # v20.x.x olmalı
```

### 4.2 Backend Kurulumu (FastAPI)

```bash
cd ~/Harmony/HarmonyByMAGNA/HarmonyView/harmonyview/backend

# Sanal ortam oluştur
python3 -m venv venv
source venv/bin/activate

# Bağımlılıkları yükle
pip install -r requirements.txt
```

#### .env Dosyası Oluşturma

```bash
cat > .env << 'EOF'
# SQL Server bağlantısı
DB_SERVER=10.19.236.39
DB_NAME=ControlTower
DB_USER=sua_appowneruser1
DB_PASSWORD=GERCEK_SIFRE_BURAYA
DB_DRIVER=ODBC Driver 18 for SQL Server
DB_TRUST_SERVER_CERT=yes

# CORS ayarları
CORS_ORIGINS=http://localhost:3000,http://SUNUCU_IP:3000

# Port
PORT=8000
EOF
```

#### Manuel Test

```bash
source venv/bin/activate
python3 app.py
# ya da
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

#### systemd Servisi

```bash
# /etc/systemd/system/harmonyview-backend.service oluştur
sudo tee /etc/systemd/system/harmonyview-backend.service << 'EOF'
[Unit]
Description=HarmonyView Manager Backend API
After=network.target

[Service]
Type=simple
User=ymc_harmony
WorkingDirectory=/home/ymc_harmony/Harmony/HarmonyByMAGNA/HarmonyView/harmonyview/backend
Environment="PATH=/home/ymc_harmony/Harmony/HarmonyByMAGNA/HarmonyView/harmonyview/backend/venv/bin:/usr/local/bin:/usr/bin"
ExecStart=/home/ymc_harmony/Harmony/HarmonyByMAGNA/HarmonyView/harmonyview/backend/venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable harmonyview-backend
sudo systemctl start harmonyview-backend
```

### 4.3 Frontend Kurulumu (Manager Dashboard)

```bash
cd ~/Harmony/HarmonyByMAGNA/HarmonyView/harmonyview/frontend-manager

# Bağımlılıkları yükle
npm install

# .env dosyası oluştur
cat > .env << 'EOF'
VITE_API_URL=http://SUNUCU_IP:8000
EOF

# Üretim build oluştur
npm run build
# dist/ klasörü oluşur
```

### 4.4 Frontend TV Ekranı Kurulumu

```bash
cd ~/Harmony/HarmonyByMAGNA/HarmonyView/harmonyview/frontend-manager-tv

npm install

cat > .env << 'EOF'
VITE_API_URL=http://SUNUCU_IP:8000
EOF

npm run build
```

### 4.5 Operatör Frontend Kurulumu

```bash
cd ~/Harmony/HarmonyByMAGNA/HarmonyView/harmonyview/frontend

npm install

cat > .env << 'EOF'
VITE_API_URL=http://SUNUCU_IP:8000
EOF

npm run build
```

---

## 5. Bileşen 3 — TrixServices (Windows EOL Servisi)

> Bu adımlar EOL istasyon bilgisayarında (Windows) gerçekleştirilir.

### 5.1 Python Kurulumu (Windows)

1. https://python.org adresinden Python 3.11+ indirin
2. Kurulum sırasında **"Add Python to PATH"** seçeneğini işaretleyin
3. Kurulumu doğrulayın:
   ```cmd
   python --version
   pip --version
   ```

### 5.2 ODBC Driver Kurulumu (Windows)

1. Microsoft Download Center'dan **ODBC Driver 17 for SQL Server** indirin:
   https://learn.microsoft.com/tr-tr/sql/connect/odbc/download-odbc-driver-for-sql-server
2. Kurulum sihirbazını tamamlayın

### 5.3 pywin32 Kurulumu (Windows Servis için)

```cmd
pip install pywin32
pip install pyodbc flask
```

### 5.4 Servis Dosyalarını Kopyalama

```cmd
# Uygun bir dizine kopyalayın, örn:
C:\HarmonyServices\DollyEOLService\
```

### 5.5 config.json Düzenleme

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8181,
    "endpoint": "/dolly-eol"
  },
  "database": {
    "driver": "{ODBC Driver 17 for SQL Server}",
    "server": "10.19.236.39",
    "database": "ControlTower",
    "username": "sua_appowneruser1",
    "password": "GERCEK_SIFRE",
    "target_table": "dbo.DollyEOLInfo",
    "primary_key_column": "RECEIPTID",
    "backup_table": "dbo.DollyEOLInfoBackup"
  },
  "mapping": {
    "RECEIPTID": "RECEIPTID",
    "DOLLYID": "DollyNo",
    "DOLLYORDERNO": "DollyOrderNo",
    "VINNO": "VinNo",
    "EOLID": "EOLID",
    "EOLNAME": "EOLName",
    "FORDCUSTOMERCODE": "CustomerReferans",
    "QUANTITY": "Adet",
    "EOLDATE": "EOLDATE"
  },
  "mapping2": {
    "RECEIPTID": "RECEIPTID",
    "DOLLYID": "DollyNo",
    "DOLLYORDERNO": "DollyOrderNo",
    "VINNO": "VinNo",
    "EOLID": "EOLID",
    "EOLNAME": "EOLName",
    "FORDCUSTOMERCODE": "CustomerReferans",
    "QUANTITY": "Adet",
    "EOLDATE": "EOLDATE"
  },
  "logging": {
    "base_dir": "C:\\HarmonyServices\\DollyEOLService\\logs"
  }
}
```

### 5.6 Manuel Test (Önce Test Edin)

```cmd
cd C:\HarmonyServices\DollyEOLService
python dolly_service.py
```

Başka bir CMD'den test isteği gönderin:
```cmd
curl -X POST http://localhost:8181/dolly-eol ^
  -H "Content-Type: application/json" ^
  -d "{\"RECEIPTID\":\"TEST001\",\"DOLLYID\":\"DL-001\",\"VINNO\":\"VIN001\",\"EOLNAME\":\"EOL-A1\"}"
```

Beklenen yanıt: `{"RECEIPTID":"TEST001","STATUS":1}`

### 5.7 Windows Servis Olarak Kurulum

```cmd
# Yönetici olarak CMD açın
cd C:\HarmonyServices\DollyEOLService

# Servisi kur
python harmony_dolly_service_win.py install

# Servisi başlat
python harmony_dolly_service_win.py start

# Durum kontrolü (Services.msc veya cmd ile)
sc query HarmonyDollyEOLService
```

Alternatif olarak `install_service.bat` dosyasını çift tıklayın (yönetici olarak).

### 5.8 Otomatik Başlatma Ayarı

```cmd
# Services.msc'yi açın
# "Harmony Dolly EOL JSON Service" servisini bulun
# Properties > Startup type: "Automatic" seçin
```

---

## 6. Bileşen 4 — HarmonyMobileApp (Android)

### 6.1 Geliştirici Ortamı Kurulumu

1. **Android Studio** indirin: https://developer.android.com/studio
2. Android Studio'yu kurun ve açın
3. SDK Manager'dan şunları kurun:
   - Android SDK Platform 36 (compileSdk)
   - Android SDK Platform 29 (minSdk)
   - Android SDK Build-Tools 36.x

### 6.2 Projeyi Açma

1. Android Studio → **File → Open**
2. `HarmonyMobileApp(elterminali)/ControlTower` klasörünü seçin
3. Gradle sync tamamlanana kadar bekleyin

### 6.3 API Adresi Yapılandırması

`app/src/main/java/com/magna/controltower/api/` klasöründeki API servis dosyasını bulun ve sunucu IP adresini güncelleyin:

```java
// ForkliftApiService.java veya benzeri
private static final String BASE_URL = "http://10.25.1.174:8181/api/";
// Kendi sunucu IP adresinizle değiştirin:
// private static final String BASE_URL = "http://SUNUCU_IP:8181/api/";
```

### 6.4 APK Derleme

**Debug APK (Test için):**
1. Build → Build Bundle(s) / APK(s) → Build APK(s)
2. APK: `app/build/outputs/apk/debug/app-debug.apk`

**Release APK (Üretim için):**
1. Build → Generate Signed Bundle / APK
2. KeyStore oluşturun veya mevcut olanı seçin
3. APK: `app/build/outputs/apk/release/app-release.apk`

### 6.5 Cihaza Yükleme

**USB Kablosu ile (ADB):**
```bash
# ADB kurulu ise
adb devices
adb install app/build/outputs/apk/debug/app-debug.apk
```

**APK Dosyası ile:**
1. APK dosyasını cihaza kopyalayın
2. Cihazda Ayarlar → Güvenlik → Bilinmeyen Kaynaklar → İzin Ver
3. APK'ya tıklayarak yükleyin

### 6.6 Kiosk Modu Kurulumu (Üretim Cihazları)

```bash
# ADB ile kiosk modunu etkinleştir
adb shell dpm set-device-owner com.magna.controltower/.DeviceAdminReceiver

# Kiosk betiği çalıştır
chmod +x setup_kiosk.sh
./setup_kiosk.sh
```

---

## 7. Nginx Yapılandırması

### 7.1 Nginx Kurulumu

```bash
sudo apt install -y nginx
sudo systemctl enable nginx
```

### 7.2 Site Yapılandırması

```bash
sudo nano /etc/nginx/sites-available/harmony
```

```nginx
# /etc/nginx/sites-available/harmony

# HarmonyEcoSystem API (Port 8181)
server {
    listen 80;
    server_name SUNUCU_IP ymcharmony.magna.global;

    # HarmonyEcoSystem Ana API
    location /api/ {
        proxy_pass http://127.0.0.1:8181;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket desteği
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 300s;
    }

    # HarmonyEcoSystem Dashboard
    location / {
        proxy_pass http://127.0.0.1:8181;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 300s;
    }

    # Analytics Dashboard
    location /analytics {
        proxy_pass http://127.0.0.1:8190;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# HarmonyView Manager Dashboard (Port 8000/3000)
server {
    listen 80;
    server_name manager.SUNUCU_IP;

    # Frontend (Static files)
    location / {
        root /home/ymc_harmony/Harmony/HarmonyByMAGNA/HarmonyView/harmonyview/frontend-manager/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

```bash
# Siteyi etkinleştir
sudo ln -s /etc/nginx/sites-available/harmony /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 7.3 HTTPS (SSL) Kurulumu

```bash
# Let's Encrypt ile ücretsiz SSL
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d ymcharmony.magna.global
```

---

## 8. Kurulum Sonrası Kontroller

### 8.1 Tüm Servislerin Durumu

```bash
# Linux sunucuda
sudo systemctl status harmonyecosystem
sudo systemctl status harmonyview-backend
sudo systemctl status nginx

# Portların açık olduğunu kontrol et
ss -tlnp | grep -E '8181|8190|8000|80|443'
```

### 8.2 API Testleri

```bash
# EcoSystem sağlık kontrolü
curl http://localhost:8181/api/health
# Beklenen: {"status":"ok","app":"HarmonyEcoSystem"}

# EOL istasyonları listesi
curl http://localhost:8181/api/pworkstations/eol

# Grup tanımları
curl http://localhost:8181/api/groups/definitions

# Forklift login testi
curl -X POST http://localhost:8181/api/forklift/login \
  -H "Content-Type: application/json" \
  -d '{"operatorBarcode":"EMP12345","deviceId":"test-001"}'
```

### 8.3 Windows Servis Testi

```cmd
# TrixServices'e test isteği gönder
curl -X POST http://EOL_MAKINE_IP:8181/dolly-eol ^
  -H "Content-Type: application/json" ^
  -d "{\"RECEIPTID\":\"TEST001\",\"DOLLYID\":\"DL-001\",\"VINNO\":\"VIN001\",\"EOLNAME\":\"EOL-A1\",\"EOLID\":1}"
```

SQL Server'da kontrol edin:
```sql
SELECT TOP 5 * FROM DollyEOLInfo ORDER BY InsertedAt DESC;
```

### 8.4 Veritabanı Kontrol Listesi

```sql
-- Tüm tabloların oluşturulduğunu kontrol et
SELECT TABLE_NAME 
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_SCHEMA = 'dbo'
ORDER BY TABLE_NAME;

-- Beklenen tablolar:
-- AuditLog, DollyEOLInfo, DollyGroup, DollyGroupEOL,
-- DollyLifecycle, DollyQueueRemoved, DollySubmissionHold,
-- ForkliftLoginSession, PWorkStation, SeferDollyEOL,
-- TerminalBarcodeSession, TerminalDevice, UserAccount, UserRole,
-- WebOperatorTask
```

---

## 9. Güvenlik Adımları

### 9.1 Üretim Ortamı Zorunlu Güvenlik Adımları

```bash
# 1. config.yaml'daki secret_key'i değiştir
python3 -c "import secrets; print(secrets.token_hex(32))"
# Çıktıyı config.yaml'daki secret_key alanına yaz

# 2. Güvenlik duvarı kuralları
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw deny 8181/tcp   # Doğrudan erişimi engelle (Nginx üzerinden erişilsin)
sudo ufw deny 8190/tcp   # Analytics (gerekirse)
sudo ufw enable

# 3. Sadece iç ağdan 8181 erişimi
sudo ufw allow from 10.0.0.0/8 to any port 8181

# 4. SSH brute force koruması
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
```

### 9.2 Hassas Dosya İzinleri

```bash
# config.yaml'ı sadece sahip okuyabilsin
chmod 600 HarmonyEcoSystem/config/config.yaml
chown ymc_harmony:ymc_harmony HarmonyEcoSystem/config/config.yaml

# .env dosyası
chmod 600 HarmonyView/harmonyview/backend/.env
```

### 9.3 Log Rotasyonu

```bash
sudo tee /etc/logrotate.d/harmony << 'EOF'
/home/ymc_harmony/Harmony/HarmonyByMAGNA/HarmonyEcoSystem/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0640 ymc_harmony ymc_harmony
    postrotate
        systemctl kill -s HUP harmonyecosystem 2>/dev/null || true
    endscript
}
EOF
```

---

## Kurulum Kontrol Listesi

```
Altyapı:
  ☐ SQL Server erişilebilir
  ☐ ControlTower veritabanı oluşturuldu
  ☐ Tüm migration betikleri çalıştırıldı (001-024)
  ☐ Admin kullanıcısı oluşturuldu

HarmonyEcoSystem:
  ☐ Python 3.9+ kurulu
  ☐ ODBC Driver 18 kurulu
  ☐ Sanal ortam oluşturuldu ve bağımlılıklar yüklendi
  ☐ config.yaml yapılandırıldı (secret_key, DB bilgileri)
  ☐ Veritabanı bağlantısı test edildi
  ☐ Manuel çalıştırma başarılı
  ☐ systemd servisi kuruldu ve aktif
  ☐ API /health endpoint'i yanıt veriyor

HarmonyView:
  ☐ Node.js 20+ kurulu
  ☐ Backend bağımlılıkları yüklendi (.env yapılandırıldı)
  ☐ Frontend build oluşturuldu
  ☐ Backend systemd servisi aktif

TrixServices:
  ☐ Python Windows'a kuruldu
  ☐ ODBC Driver 17 kuruldu
  ☐ config.json yapılandırıldı
  ☐ Manuel test başarılı
  ☐ Windows servisi kuruldu ve çalışıyor

HarmonyMobileApp:
  ☐ Android Studio kuruldu
  ☐ API adresi güncellendi
  ☐ APK derlendi
  ☐ Cihazlara yüklendi

Nginx:
  ☐ Yapılandırma dosyası oluşturuldu
  ☐ Test geçti (nginx -t)
  ☐ SSL sertifikası kuruldu (üretim ortamı)

Güvenlik:
  ☐ secret_key değiştirildi
  ☐ Güvenlik duvarı kuralları uygulandı
  ☐ Hassas dosya izinleri ayarlandı
  ☐ Log rotasyonu yapılandırıldı
```
