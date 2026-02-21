# HarmonyEcoSystem — Detaylı Teknik Döküman
# Ana Backend & Control Tower Sistemi

---

| Alan | Bilgi |
|------|-------|
| **Versiyon** | 1.2.0 |
| **Tarih** | 2026-02-21 |
| **Teknoloji** | Python 3.9+, Flask 2.3, SQL Server, JWT |
| **Port** | 8181 (Ana API), 8190 (Analytics) |

---

## İçindekiler

1. [Proje Yapısı](#1-proje-yapısı)
2. [Mimari ve Akış](#2-mimari-ve-akış)
3. [Yapılandırma](#3-yapılandırma)
4. [Veritabanı Modelleri](#4-veritabanı-modelleri)
5. [Servis Katmanı](#5-servis-katmanı)
6. [API Endpointleri](#6-api-endpointleri)
7. [Kimlik Doğrulama Sistemi](#7-kimlik-doğrulama-sistemi)
8. [Analitik Modül](#8-analitik-modül)
9. [Denetim Günlüğü](#9-denetim-günlüğü)
10. [CEVA Entegrasyonu](#10-ceva-entegrasyonu)
11. [Servis Yönetimi](#11-servis-yönetimi)
12. [Geliştirici Notları](#12-geliştirici-notları)

---

## 1. Proje Yapısı

```
HarmonyEcoSystem/
│
├── run.py                    # Ana giriş noktası (Port 8181 + 8190)
├── wsgi.py                   # Gunicorn WSGI entry point
├── gunicorn_config.py        # Gunicorn yapılandırması
├── requirements.txt          # Python bağımlılıkları
│
├── config/
│   └── config.yaml           # Tüm sistem yapılandırması
│
├── app/                      # Ana Flask uygulaması
│   ├── __init__.py           # Uygulama fabrikası (create_app)
│   ├── extensions.py         # Flask eklentileri (SQLAlchemy, SocketIO, LoginManager)
│   │
│   ├── models/               # SQLAlchemy ORM modelleri
│   │   ├── dolly.py          # DollyEOLInfo modeli
│   │   ├── dolly_backup.py   # DollySubmissionHold modeli
│   │   ├── dolly_hold.py     # DollyHold yardımcı model
│   │   ├── dolly_queue_removed.py  # Kaldırılan dolly'ler
│   │   ├── forklift_session.py     # ForkliftLoginSession
│   │   ├── group.py          # DollyGroup, DollyGroupEOL
│   │   ├── lifecycle.py      # DollyLifecycle
│   │   ├── pworkstation.py   # PWorkStation
│   │   ├── sefer.py          # SeferDollyEOL
│   │   ├── user.py           # UserAccount, UserRole
│   │   └── web_operator_task.py   # WebOperatorTask
│   │
│   ├── routes/               # Flask Blueprint'leri
│   │   ├── api.py            # REST API endpointleri (/api/...)
│   │   ├── auth.py           # Web kimlik doğrulama (/auth/...)
│   │   └── dashboard.py      # Web dashboard sayfaları (/)
│   │
│   ├── services/             # İş mantığı katmanı
│   │   ├── dolly_service.py  # Ana dolly iş mantığı
│   │   ├── audit_service.py  # Denetim günlüğü
│   │   ├── ceva_service.py   # CEVA SOAP entegrasyonu
│   │   ├── database_monitor.py    # DB bağlantı izleme
│   │   ├── excel_export_service.py # Excel dışa aktarma
│   │   ├── lifecycle_service.py   # Dolly yaşam döngüsü
│   │   ├── queue_cleanup_scheduler.py  # Kuyruk temizleme
│   │   └── realtime_service.py    # WebSocket gerçek zamanlı
│   │
│   ├── utils/                # Yardımcı araçlar
│   │   ├── auth.py           # Web kimlik doğrulama yardımcıları
│   │   ├── config_loader.py  # YAML yapılandırma yükleyici
│   │   ├── datetime_helper.py # Zaman dilimi yardımcıları
│   │   ├── forklift_auth.py  # Forklift JWT yönetimi
│   │   └── security.py       # Şifre hashleme
│   │
│   ├── modules/
│   │   └── operator_edit.py  # Operatör düzenleme modülü
│   │
│   └── templates/            # Jinja2 HTML şablonları
│       ├── layout.html       # Ana şablon
│       └── yuzde.html        # Yüzde görünümü
│
├── analytics/                # Analitik modül (Port 8190)
│   ├── __init__.py           # Analytics uygulama fabrikası
│   ├── routes/
│   │   ├── api.py            # Analytics API endpointleri
│   │   └── dashboard.py      # Analytics dashboard sayfaları
│   └── templates/            # Analytics HTML şablonları
│
├── database/                 # SQL migration betikleri
│   ├── 001_create_dolly_submission_hold.sql
│   ├── 002_create_dolly_groups.sql
│   └── ... (024'e kadar)
│
├── docs/                     # Teknik belgeler
├── logs/                     # Uygulama günlükleri
├── ssl/                      # SSL sertifikaları
└── harmonyecosystem.service  # systemd servis tanımı
```

---

## 2. Mimari ve Akış

### 2.1 Uygulama Fabrikası Deseni

```python
# app/__init__.py — create_app() fonksiyonu
def create_app(config_path=None):
    config_data = ConfigLoader.load(config_path)
    app = Flask(__name__)
    
    _apply_core_config(app, config_data)   # SECRET_KEY, DB URI, vb.
    _configure_logging(app, config_data)   # Döngüsel dosya günlüğü
    _register_template_filters(app, ...)   # Zaman dilimi filtresi
    
    init_extensions(app)                   # SQLAlchemy, SocketIO, LoginManager
    _register_blueprints(app, config_data) # API, Auth, Dashboard
    _setup_database_monitoring(app)        # DB bağlantı izleyici
    
    return app
```

### 2.2 Uçtan Uca Dolly Akışı

```
EOL İstasyonu
    │
    │  (TrixServices veya doğrudan DB kaydı)
    ▼
DollyEOLInfo (Ana Kuyruk)
    │
    │  POST /api/forklift/login
    │  ← JWT token
    │
    │  POST /api/forklift/scan
    ▼
DollySubmissionHold (Status: "scanned")
DollyLifecycle (Status: SCAN_CAPTURED)
    │
    │  POST /api/forklift/complete-loading
    ▼
DollySubmissionHold (Status: "loading_completed")
DollyLifecycle (Status: LOADING_COMPLETED)
WebOperatorTask (oluşturulur)
    │
    │  Web Operatör paneli görür
    │  POST /api/operator/complete-shipment
    │  (sefer no + plaka + ASN/İrsaliye)
    ▼
SeferDollyEOL (kalıcı kayıt)
DollySubmissionHold (silindi)
DollyLifecycle (Status: COMPLETED_ASN / COMPLETED_IRS / COMPLETED_BOTH)
AuditLog (işlem kaydı)
    │
    │  (CEVA Servisi çağrısı — opsiyonel)
    ▼
CEVA Logistics (ASN/İrsaliye gönderimi)
```

### 2.3 Blueprint Yapısı

| Blueprint | Prefix | Açıklama |
|-----------|--------|----------|
| `api_bp` | `/api` | REST API (JSON yanıtlar) |
| `auth_bp` | `/auth` | Web giriş/çıkış (HTML yanıtlar) |
| `dashboard_bp` | `/` | Web dashboard sayfaları (HTML) |

---

## 3. Yapılandırma

### 3.1 config.yaml Tüm Alanlar

```yaml
app:
  name: HarmonyEcoSystem            # Uygulama adı
  secret_key: "..."                 # Flask oturum şifreleme anahtarı
  environment: production           # development / production
  api_prefix: "/api"                # API URL ön eki
  host: "0.0.0.0"                   # Dinleme adresi
  port: 8181                        # Dinleme portu
  timezone: "Europe/Istanbul"       # Zaman dilimi

database:
  dialect: mssql+pyodbc             # SQLAlchemy dialect
  username: "sua_appowneruser1"
  password: "..."
  host: "10.19.236.39"
  port: 1433
  database: "ControlTower"
  driver: "ODBC Driver 18 for SQL Server"
  options:
    Encrypt: "yes"
    TrustServerCertificate: "yes"
  echo: false                       # true = SQL sorgularını logla

logging:
  level: INFO                       # DEBUG / INFO / WARNING / ERROR
  file: logs/app.log                # Log dosyası yolu
  rotation: 10485760                # Maks. dosya boyutu (10 MB)

features:
  enable_mock_data: false           # Test modu

pworkstation:
  require_finish_product_station: false  # true = sadece bitmiş ürün EOL'leri

ceva:
  enabled: true
  environment: "production"         # uat / production
  uat:
    url: "https://trtmsuat.cevalogistics.com/..."
    username: "KULLANICI"
    password: "SIFRE"
    supplier_code: "GSDB_KOD"
    user_id: "0"
  production:
    url: "https://trweb04.cevalogistics.com/..."
    username: "KULLANICI"
    password: "SIFRE"
    supplier_code: "GSDB_KOD"
    user_id: "0"
  timeout: 30                       # Saniye
  retry_count: 2                    # Yeniden deneme sayısı
```

### 3.2 Veritabanı Bağlantı URI Oluşturma

```python
# app/__init__.py — _build_database_uri()
uri = "mssql+pyodbc://username:password@host:port/database"
     + "?driver=ODBC+Driver+18+for+SQL+Server"
     + "&Encrypt=yes"
     + "&TrustServerCertificate=yes"
```

### 3.3 SQLAlchemy Bağlantı Havuzu

```python
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_size": 10,        # Aynı anda açık bağlantı sayısı
    "pool_recycle": 3600,   # 1 saatte bir bağlantıları yenile
    "pool_pre_ping": True,  # Kullanmadan önce bağlantıyı test et
    "pool_timeout": 30,     # Bağlantı bekleme süresi (sn)
    "max_overflow": 20,     # Ek bağlantı sayısı (pool dolunca)
}
```

---

## 4. Veritabanı Modelleri

### 4.1 DollyEOLInfo — Ana Kuyruk

```python
# app/models/dolly.py
class DollyEOLInfo(db.Model):
    __tablename__ = "DollyEOLInfo"
    
    DollyNo          = db.Column(db.String(50), primary_key=True)
    VinNo            = db.Column(db.String(50), primary_key=True)
    DollyOrderNo     = db.Column(db.String(50))
    CustomerReferans = db.Column(db.String(100))
    Adet             = db.Column(db.Integer)
    EOLName          = db.Column(db.String(100))
    EOLID            = db.Column(db.Integer)
    EOLDATE          = db.Column(db.Date)
    EOLDollyBarcode  = db.Column(db.String(100))
    RECEIPTID        = db.Column(db.String(50))
    InsertedAt       = db.Column(db.DateTime, default=datetime.utcnow)
```

**Önemli:** Bileşik birincil anahtar (`DollyNo + VinNo`). Aynı dolly birden fazla VIN içerebilir (set başına birden fazla araç şasisi).

### 4.2 DollySubmissionHold — Geçici Kuyruk

```python
# app/models/dolly_backup.py
class DollySubmissionHold(db.Model):
    __tablename__ = "DollySubmissionHold"
    
    Id                 = db.Column(db.Integer, primary_key=True, autoincrement=True)
    DollyNo            = db.Column(db.String(50))
    VinNo              = db.Column(db.String(50))
    Status             = db.Column(db.String(30), default="pending")
    # Olası değerler: pending, scanned, loading_completed, completed, removed
    
    TerminalUser       = db.Column(db.String(100))   # Forklift operatör adı
    ScanOrder          = db.Column(db.Integer)        # TIR'a yüklenme sırası
    LoadingSessionId   = db.Column(db.String(50))     # LOAD_YYYYMMDD_OPERATOR
    LoadingCompletedAt = db.Column(db.DateTime)
    
    SeferNumarasi      = db.Column(db.String(20))     # Operatör girer
    PlakaNo            = db.Column(db.String(20))
    PartNumber         = db.Column(db.String(50))
    
    EOLName            = db.Column(db.String(100))
    EOLID              = db.Column(db.Integer)
    CustomerReferans   = db.Column(db.String(100))
    Adet               = db.Column(db.Integer)
    
    SubmittedAt        = db.Column(db.DateTime)
    InsertedAt         = db.Column(db.DateTime, default=datetime.utcnow)
```

### 4.3 ForkliftLoginSession — JWT Oturumları

```python
# app/models/forklift_session.py
class ForkliftLoginSession(db.Model):
    __tablename__ = "ForkliftLoginSession"
    
    Id              = db.Column(db.Integer, primary_key=True, autoincrement=True)
    OperatorBarcode = db.Column(db.String(50), nullable=False)
    OperatorName    = db.Column(db.String(100))
    SessionToken    = db.Column(db.String(128), unique=True, nullable=False)
    IsActive        = db.Column(db.Boolean, default=True)
    LoginAt         = db.Column(db.DateTime, default=datetime.utcnow)
    ExpiresAt       = db.Column(db.DateTime, nullable=False)
    LastActivityAt  = db.Column(db.DateTime)
    DeviceId        = db.Column(db.String(100))
    LogoutAt        = db.Column(db.DateTime)
    Role            = db.Column(db.String(30), default="terminal_operator")
```

### 4.4 DollyLifecycle — Durum Geçiş Günlüğü

```python
# app/models/lifecycle.py
class DollyLifecycle(db.Model):
    __tablename__ = "DollyLifecycle"
    
    Id        = db.Column(db.Integer, primary_key=True, autoincrement=True)
    DollyNo   = db.Column(db.String(50), nullable=False)
    VinNo     = db.Column(db.String(50), nullable=False)
    Status    = db.Column(db.String(50), nullable=False)
    Actor     = db.Column(db.String(100))    # Kim yaptı
    SessionId = db.Column(db.String(50))
    Notes     = db.Column(db.String(500))
    CreatedAt = db.Column(db.DateTime, default=datetime.utcnow)
```

**Tanımlı Durumlar:**
- `EOL_READY` — Dolly EOL'den çıktı
- `SCAN_CAPTURED` — Forklift okutu
- `LOADING_IN_PROGRESS` — Yükleme devam ediyor
- `LOADING_COMPLETED` — Yükleme tamamlandı
- `WAITING_OPERATOR` — Operatör bekleniyor
- `COMPLETED_ASN` — ASN gönderildi
- `COMPLETED_IRS` — İrsaliye gönderildi
- `COMPLETED_BOTH` — Her ikisi gönderildi

### 4.5 SeferDollyEOL — Kalıcı Arşiv

```python
# app/models/sefer.py
class SeferDollyEOL(db.Model):
    __tablename__ = "SeferDollyEOL"
    
    Id               = db.Column(db.Integer, primary_key=True)
    DollyNo          = db.Column(db.String(50))
    VinNo            = db.Column(db.String(50))
    SeferNumarasi    = db.Column(db.String(20))
    PlakaNo          = db.Column(db.String(20))
    EOLName          = db.Column(db.String(100))
    EOLID            = db.Column(db.Integer)
    DollyOrderNo     = db.Column(db.String(50))
    PartNumber       = db.Column(db.String(50))
    CustomerReferans = db.Column(db.String(100))
    ScanOrder        = db.Column(db.Integer)
    LoadingSessionId = db.Column(db.String(50))
    ShippingType     = db.Column(db.String(20))  # asn / irsaliye / both
    Lokasyon         = db.Column(db.String(100))
    SubmittedAt      = db.Column(db.DateTime, default=datetime.utcnow)
    InsertedAt       = db.Column(db.DateTime)
```

---

## 5. Servis Katmanı

### 5.1 DollyService — Ana İş Mantığı

```python
# app/services/dolly_service.py

class DollyService:
    def __init__(self, config: dict):
        self.config = config
    
    # Forklift tarafından çağrılan metodlar
    def scan_dolly(self, dolly_no, loading_session_id, barcode, terminal_user):
        """Dolly barkodunu okut ve DollySubmissionHold'a kaydet"""
    
    def complete_loading(self, loading_session_id, terminal_user):
        """Yükleme oturumunu tamamla"""
    
    def remove_last_dolly(self, loading_session_id, barcode):
        """LIFO: Son okutulan dolly'yi kaldır"""
    
    # Web operatör tarafından çağrılan metodlar
    def operator_complete_shipment(self, loading_session_id, sefer_no, plaka, 
                                   shipping_type, selected_dolly_ids=None):
        """Sevkiyatı tamamla — validation + CEVA çağrısı + DB kayıtları"""
    
    def validate_sefer_format(self, sefer_no):
        """Sefer numarası format kontrolü"""
    
    def validate_plaka_format(self, plaka_no):
        """Plaka format kontrolü (Türk plaka formatı)"""
    
    def check_duplicate_sefer(self, sefer_no):
        """Mükerrer sefer numarası kontrolü"""
```

### 5.2 Hata Yönetimi ve Rollback

```python
def operator_complete_shipment(self, ...):
    try:
        # 1. Doğrulama
        if not self.validate_sefer_format(sefer_no):
            raise ValueError("Geçersiz sefer numarası formatı")
        
        # 2. İş mantığı
        holds = self._get_holds(loading_session_id, selected_dolly_ids)
        for hold in holds:
            hold.Status = "completed"
            # SeferDollyEOL'a taşı
            sefer_record = SeferDollyEOL(...)
            db.session.add(sefer_record)
        
        # 3. CEVA gönderimi
        if shipping_type in ("asn", "both"):
            self.ceva_service.send_asn(...)
        
        db.session.commit()   # Tek commit
        
    except Exception as e:
        db.session.rollback()  # Tüm değişiklikler geri alınır
        self._log_critical_error("operator_complete_shipment", e, {...})
        raise RuntimeError("İşlem geri alındı, lütfen tekrar deneyin.")
```

### 5.3 AuditService

```python
# app/services/audit_service.py

def log_action(action, actor_type, actor_name, resource=None, metadata=None):
    """AuditLog tablosuna kayıt düş"""
    record = AuditLog(
        Action=action,
        ActorType=actor_type,
        ActorName=actor_name,
        Resource=resource,
        Metadata=json.dumps(metadata) if metadata else None,
        CreatedAt=datetime.utcnow()
    )
    db.session.add(record)
    db.session.commit()
```

**Loglanılan Aksiyonlar:**

| Aksiyon | Tetikleyen |
|---------|-----------|
| `forklift.login` | Barkod ile giriş |
| `forklift.logout` | Çıkış |
| `forklift.scan` | Dolly barkod okutma |
| `forklift.remove_dolly` | LIFO kaldırma |
| `forklift.complete_loading` | Yükleme tamamlama |
| `operator.complete_shipment` | Sevkiyat onayı |
| `system.critical_error` | Kritik hata |
| `ceva.asn_sent` | CEVA ASN gönderimi |
| `ceva.asn_failed` | CEVA hata |

---

## 6. API Endpointleri

### 6.1 Kimlik Doğrulama

#### POST /api/forklift/login

```http
POST /api/forklift/login
Content-Type: application/json

{
    "operatorBarcode": "EMP12345",
    "operatorName": "Mehmet Yılmaz",
    "deviceId": "android-001"
}
```

**Yanıt (200 OK):**
```json
{
    "success": true,
    "sessionToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "operatorName": "Mehmet Yılmaz",
    "operatorBarcode": "EMP12345",
    "expiresAt": "2025-11-27T08:00:00Z",
    "message": "Hoş geldiniz Mehmet Yılmaz",
    "isAdmin": false,
    "role": "forklift"
}
```

#### POST /api/forklift/logout

```http
POST /api/forklift/logout
Authorization: Bearer <token>
```

#### GET /api/forklift/session/validate

```http
GET /api/forklift/session/validate
Authorization: Bearer <token>
```

### 6.2 Forklift İşlemleri

#### POST /api/forklift/scan

```http
POST /api/forklift/scan
Authorization: Bearer <token>
Content-Type: application/json

{
    "dollyNo": "DL-5170427",
    "loadingSessionId": "LOAD_20251126_MEHMET",
    "barcode": "BARCODE_DOLLY_001"
}
```

**Yanıt (200):**
```json
{
    "dolly_no": "DL-5170427",
    "vin_no": "VIN001",
    "scan_order": 3,
    "loading_session_id": "LOAD_20251126_MEHMET",
    "scanned_at": "2025-11-26T10:30:00Z"
}
```

**Hata Yanıtları:**
- `400` — Gerekli alan eksik
- `401` — Geçersiz/süresi dolmuş token
- `404` — Dolly bulunamadı
- `409` — Dolly zaten bu oturumda taranmış

#### POST /api/forklift/complete-loading

```http
POST /api/forklift/complete-loading
Authorization: Bearer <token>
Content-Type: application/json

{
    "loadingSessionId": "LOAD_20251126_MEHMET"
}
```

#### POST /api/forklift/remove-last

```http
POST /api/forklift/remove-last
Authorization: Bearer <token>
Content-Type: application/json

{
    "loadingSessionId": "LOAD_20251126_MEHMET",
    "dollyBarcode": "BARCODE_DOLLY_001"
}
```

**İş Kuralı:** Yalnızca `ScanOrder` en yüksek olan (en son okutulan) dolly kaldırılabilir.

#### GET /api/forklift/sessions

```http
GET /api/forklift/sessions?status=scanned
Authorization: Bearer <token>
```

### 6.3 Web Operatör Endpointleri

#### GET /api/operator/pending-shipments

```http
GET /api/operator/pending-shipments
```

**Yanıt:**
```json
[
    {
        "loadingSessionId": "LOAD_20251126_MEHMET",
        "operatorName": "Mehmet Yılmaz",
        "dollyCount": 15,
        "completedAt": "2025-11-26T10:45:00Z",
        "dollys": [
            {"id": 1, "dollyNo": "DL-001", "vinNo": "VIN001", "scanOrder": 1},
            ...
        ]
    }
]
```

#### POST /api/operator/complete-shipment

```http
POST /api/operator/complete-shipment
Content-Type: application/json

{
    "loadingSessionId": "LOAD_20251126_MEHMET",
    "seferNumarasi": "SFR20250001",
    "plakaNo": "34 ABC 123",
    "shippingType": "both",
    "selectedDollyIds": [1, 2, 4]
}
```

**shippingType değerleri:**
- `"asn"` — Sadece ASN gönder
- `"irsaliye"` — Sadece İrsaliye gönder
- `"both"` — Her ikisini gönder

### 6.4 Grup ve EOL Yönetimi

```http
GET /api/groups                  # Tüm dolly grupları
GET /api/group-sequences         # EOL bazlı grup sıralamaları
GET /api/pworkstations/eol       # EOL istasyonları
GET /api/groups/definitions      # Grup tanımları
GET /api/manual-collection/groups                       # Manuel toplama grupları
GET /api/manual-collection/groups/<gid>/eols/<eid>      # Grup EOL dolly listesi
```

### 6.5 Yardımcı

```http
GET /api/health                  # Sunucu sağlık durumu
```

---

## 7. Kimlik Doğrulama Sistemi

### 7.1 JWT Token Yapısı

```python
# app/utils/forklift_auth.py

import jwt
from datetime import datetime, timedelta

def create_forklift_session(operator_barcode, operator_name, device_id=None):
    """Yeni JWT oturum belgeci oluştur"""
    
    expires_at = datetime.utcnow() + timedelta(hours=8)
    
    payload = {
        "sub": operator_barcode,
        "name": operator_name,
        "iat": datetime.utcnow(),
        "exp": expires_at,
        "type": "forklift"
    }
    
    token = jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")
    
    # Veritabanına kaydet
    session = ForkliftLoginSession(
        OperatorBarcode=operator_barcode,
        OperatorName=operator_name,
        SessionToken=token,
        ExpiresAt=expires_at,
        DeviceId=device_id,
        IsActive=True
    )
    db.session.add(session)
    db.session.commit()
    
    return token, expires_at
```

### 7.2 Kimlik Doğrulama Decorator

```python
def require_forklift_auth(f):
    """API endpoint'lerini korumak için kullanılan decorator"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Token gerekli", "retryable": False}), 401
        
        token = auth_header[7:]  # "Bearer " kaldır
        
        # Veritabanında token varlığı ve aktifliği kontrol et
        session = ForkliftLoginSession.query.filter_by(
            SessionToken=token,
            IsActive=True
        ).first()
        
        if not session or session.ExpiresAt < datetime.utcnow():
            return jsonify({"error": "Token geçersiz veya süresi dolmuş", "retryable": False}), 401
        
        # Son aktivite zamanını güncelle
        session.LastActivityAt = datetime.utcnow()
        db.session.commit()
        
        return f(*args, **kwargs)
    
    return decorated
```

### 7.3 Web Kimlik Doğrulama (Flask-Login)

Web dashboard için Flask-Login kullanılır:

```python
# app/routes/auth.py
@auth_bp.post("/login")
def login():
    username = request.form.get("username")
    password = request.form.get("password")
    
    user = UserAccount.query.filter_by(Username=username).first()
    
    if user and check_password_hash(user.PasswordHash, password):
        login_user(user)
        return redirect(url_for("dashboard.index"))
    
    return render_template("login.html", error="Hatalı kullanıcı adı veya şifre")
```

---

## 8. Analitik Modül

### 8.1 Genel Bakış

Analitik modül `analytics/` dizininde ayrı bir Flask uygulaması olarak çalışır ve **8190** portunu kullanır. `run.py` içinde ayrı bir thread'de başlatılır.

### 8.2 Analitik View'ları (SQL Server)

```sql
-- Örnek: Operatör performans view'u
CREATE VIEW vw_OperatorPerformance AS
SELECT 
    TerminalUser,
    COUNT(*) AS TotalScans,
    COUNT(DISTINCT LoadingSessionId) AS TotalSessions,
    AVG(DATEDIFF(MINUTE, InsertedAt, LoadingCompletedAt)) AS AvgLoadingMinutes
FROM DollySubmissionHold
WHERE Status = 'loading_completed'
GROUP BY TerminalUser;
```

```sql
-- Vardiya bazlı üretim
CREATE VIEW vw_ShiftProduction AS
SELECT
    DollyNo,
    CASE
        WHEN DATEPART(HOUR, InsertedAt) BETWEEN 0 AND 7 THEN 'SHIFT_1'
        WHEN DATEPART(HOUR, InsertedAt) BETWEEN 8 AND 15 THEN 'SHIFT_2'
        ELSE 'SHIFT_3'
    END AS Shift,
    CAST(InsertedAt AS DATE) AS ProductionDate
FROM DollyEOLInfo;
```

### 8.3 Analitik API Endpointleri

```http
GET /analytics/api/dashboard     # Genel özet metrikler
GET /analytics/api/operators     # Operatör performansı
GET /analytics/api/shifts        # Vardiya bazlı analiz
GET /analytics/api/bottlenecks   # Darboğaz analizi
GET /analytics/api/lines         # Hat bazlı üretim
GET /analytics/api/timeline      # Zaman serisi verileri
```

---

## 9. Denetim Günlüğü

### 9.1 AuditLog Tablosu

```sql
CREATE TABLE AuditLog (
    Id        INT PRIMARY KEY IDENTITY(1,1),
    Action    NVARCHAR(100) NOT NULL,    -- forklift.login, operator.complete_shipment, vb.
    ActorType NVARCHAR(50),              -- forklift / web_user / system
    ActorName NVARCHAR(100),             -- Operatör/kullanıcı adı
    Resource  NVARCHAR(100),             -- Etkilenen kaynak (dolly no, session id)
    Metadata  NVARCHAR(MAX),             -- JSON metadata
    CreatedAt DATETIME2 DEFAULT GETDATE()
);
```

### 9.2 Sorgu Örnekleri

```sql
-- Son 24 saatin forklift işlemleri
SELECT * FROM AuditLog
WHERE ActorType = 'forklift'
AND CreatedAt >= DATEADD(HOUR, -24, GETDATE())
ORDER BY CreatedAt DESC;

-- Belirli bir dolly'nin tüm geçmişi
SELECT * FROM AuditLog
WHERE Resource = 'DL-5170427'
ORDER BY CreatedAt;

-- Kritik hatalar
SELECT * FROM AuditLog
WHERE Action = 'system.critical_error'
ORDER BY CreatedAt DESC;
```

---

## 10. CEVA Entegrasyonu

### 10.1 Genel Bakış

CEVA Logistics ASN (Advance Shipping Notice) ve İrsaliye gönderimi için kullanılır. İletişim SOAP/XML protokolü üzerinden gerçekleşir.

```python
# app/services/ceva_service.py

import zeep  # SOAP istemcisi

class CevaService:
    def __init__(self, config: dict):
        self.config = config
        self.client = zeep.Client(wsdl=config["url"])
    
    def send_asn(self, dolly_records, sefer_no, plaka_no):
        """ASN gönder"""
        try:
            response = self.client.service.SendASN(
                Username=self.config["username"],
                Password=self.config["password"],
                SupplierCode=self.config["supplier_code"],
                ...
            )
            return response
        except zeep.exceptions.Fault as e:
            raise RuntimeError(f"CEVA SOAP hatası: {e}")
```

### 10.2 Yapılandırma

```yaml
ceva:
  enabled: true
  environment: "production"  # "uat" değerini test için kullanın
  timeout: 30
  retry_count: 2
```

---

## 11. Servis Yönetimi

### 11.1 systemd Komutları

```bash
# Servisi başlat
sudo systemctl start harmonyecosystem

# Servisi durdur
sudo systemctl stop harmonyecosystem

# Servisi yeniden başlat (kod güncellemesi sonrası)
sudo systemctl restart harmonyecosystem

# Servis durumu
sudo systemctl status harmonyecosystem

# Anlık log izleme
sudo journalctl -u harmonyecosystem -f

# Uygulama log dosyası
tail -f logs/app.log

# Son 100 satır log
tail -100 logs/app.log
```

### 11.2 Kod Güncellemesi

```bash
# 1. Kodu güncelle
cd ~/Harmony/HarmonyByMAGNA
git pull

# 2. Bağımlılıkları güncelle (gerekirse)
source HarmonyEcoSystem/.venv/bin/activate
pip install -r HarmonyEcoSystem/requirements.txt

# 3. Servisi yeniden başlat
sudo systemctl restart harmonyecosystem

# 4. Durumu kontrol et
sudo systemctl status harmonyecosystem
curl http://localhost:8181/api/health
```

---

## 12. Geliştirici Notları

### 12.1 Yeni API Endpoint Ekleme

```python
# app/routes/api.py — Mevcut desene uyun

@api_bp.post("/yeni-endpoint")
@require_forklift_auth  # Kimlik doğrulama gerekiyorsa ekle
def yeni_endpoint():
    payload = request.get_json(force=True, silent=True) or {}
    
    try:
        service = _service()
        result = service.yeni_metod(payload)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e), "retryable": True}), 400
    except Exception as e:
        current_app.logger.exception("Beklenmeyen hata")
        return jsonify({"error": "Sistem hatası", "retryable": True}), 500
```

### 12.2 Yeni Veritabanı Migrasyonu

```bash
# 1. database/ klasöründe yeni SQL dosyası oluştur
touch database/025_aciklama.sql

# 2. SQL'i yaz
# 3. SQL Server'da çalıştır
sqlcmd -S HOST -U USER -P PASS -d ControlTower -i database/025_aciklama.sql

# 4. Varsa ilgili modeli güncelle
nano app/models/ilgili_model.py
```

### 12.3 Eklenti Listesi (requirements.txt)

| Paket | Versiyon | Amaç |
|-------|---------|------|
| Flask | 2.3.3 | Ana web framework |
| Flask-SQLAlchemy | 3.1.1 | ORM |
| Flask-Login | 0.6.3 | Web oturum yönetimi |
| Flask-SocketIO | 5.3.5 | WebSocket (gerçek zamanlı) |
| Flask-Caching | 2.1.0 | Önbellekleme |
| eventlet | 0.33.3 | Async I/O (SocketIO için) |
| zeep | 4.2.1 | SOAP/CEVA istemcisi |
| PyYAML | 6.0.1 | config.yaml okuma |
| openpyxl | 3.1.2 | Excel dışa aktarma |
| requests | 2.31.0 | HTTP istemcisi |
