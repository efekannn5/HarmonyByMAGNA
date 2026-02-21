# HarmonyView — Detaylı Teknik Döküman
# Yönetici ve Operatör Dashboard'ları

---

| Alan | Bilgi |
|------|-------|
| **Versiyon** | 1.0.0 |
| **Tarih** | 2026-02-21 |
| **Backend** | FastAPI (Python), Port 8000 |
| **Frontend** | React 18 + Vite + Tailwind CSS |
| **Veritabanı** | SQL Server (salt okunur — View'lar üzerinden) |

---

## İçindekiler

1. [Proje Yapısı](#1-proje-yapısı)
2. [Backend — FastAPI](#2-backend--fastapi)
3. [Veritabanı Bağlantısı](#3-veritabanı-bağlantısı)
4. [SQL View'ları](#4-sql-viewları)
5. [API Endpointleri](#5-api-endpointleri)
6. [Frontend — Manager Dashboard](#6-frontend--manager-dashboard)
7. [Frontend — TV Ekranı](#7-frontend--tv-ekranı)
8. [WebSocket Desteği](#8-websocket-desteği)
9. [Servis Yönetimi](#9-servis-yönetimi)
10. [Geliştirici Notları](#10-geliştirici-notları)

---

## 1. Proje Yapısı

```
HarmonyView/harmonyview/
│
├── backend/                          # FastAPI backend
│   ├── app.py                        # Ana uygulama (Manager/TV Dashboard)
│   ├── app_manager.py                # Yönetici uygulama başlatıcı
│   ├── database.py                   # SQL Server bağlantısı (SQLAlchemy)
│   ├── models.py                     # Pydantic veri modelleri
│   ├── models_manager.py             # Yönetici veri modelleri
│   ├── queries.py                    # Manager Dashboard sorguları
│   ├── queries_dashboard.py          # Genel dashboard sorguları
│   ├── queries_manager.py            # Yönetici sorguları
│   ├── queries_views.py              # SQL View sorguları
│   ├── endpoints_chat.py             # Chatbot entegrasyonu
│   ├── apply_sql.py                  # SQL View uygulama scripti
│   ├── requirements.txt              # Python bağımlılıkları
│   └── sql/
│       └── views_duration_analysis.sql  # Süre analizi view'ları
│
├── frontend/                         # Operatör Dashboard (React)
│   ├── src/
│   │   ├── App.jsx                   # Ana bileşen
│   │   ├── main.jsx                  # Giriş noktası
│   │   └── index.css                 # Global stiller
│   ├── package.json                  # Node.js bağımlılıkları
│   ├── vite.config.js                # Vite yapılandırması
│   └── tailwind.config.js
│
├── frontend-manager/                 # Yönetici Dashboard (React)
│   ├── src/
│   │   ├── App.jsx                   # Yönetici ana bileşeni
│   │   └── ...
│   └── package.json
│
├── frontend-manager-tv/              # TV/Büyük Ekran Görünümü (React)
│   ├── src/
│   │   ├── App.jsx                   # TV ekranı bileşeni
│   │   └── ...
│   └── package.json
│
├── harmonyview-backend.service       # systemd — Manager backend
├── harmonyview-frontend.service      # systemd — Manager frontend
├── harmonyview-operator-backend.service
└── harmonyview-operator-frontend.service
```

---

## 2. Backend — FastAPI

### 2.1 Ana Uygulama (app.py)

```python
# backend/app.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Harmony Control Tower API",
    description="Real-time dashboard for Magna dolly logistics",
    version="1.0.0"
)

# CORS yapılandırması
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # Üretimde kısıtlayın
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2.2 Uygulama Başlatma

**Doğrudan Python ile:**
```bash
cd backend
source venv/bin/activate
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

**app_manager.py ile:**
```bash
python3 app_manager.py
```

### 2.3 Ortam Değişkenleri (.env)

```bash
# backend/.env
DB_SERVER=10.19.236.39
DB_NAME=ControlTower
DB_USER=sua_appowneruser1
DB_PASSWORD=SIFRE
DB_DRIVER=ODBC Driver 18 for SQL Server
DB_TRUST_SERVER_CERT=yes

# CORS
CORS_ORIGINS=http://localhost:3000,http://SUNUCU_IP:3000

# Port
PORT=8000
```

---

## 3. Veritabanı Bağlantısı

### 3.1 SQLAlchemy Engine

```python
# backend/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

def get_connection_string():
    server   = os.getenv("DB_SERVER")
    database = os.getenv("DB_NAME")
    user     = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    driver   = os.getenv("DB_DRIVER", "ODBC Driver 18 for SQL Server")
    trust    = os.getenv("DB_TRUST_SERVER_CERT", "yes")
    
    return (
        f"mssql+pyodbc://{user}:{password}@{server}/{database}"
        f"?driver={driver.replace(' ', '+')}"
        f"&TrustServerCertificate={trust}"
    )

engine = create_engine(get_connection_string())
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_connection():
    """Başlangıçta bağlantı testi yap"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"DB bağlantı hatası: {e}")
        return False
```

### 3.2 HarmonyView Okuma Prensibi

> **ÖNEMLİ:** HarmonyView veritabanına **yalnızca okuma** (SELECT) işlemi yapar.
> Tüm yazma işlemleri HarmonyEcoSystem üzerinden gerçekleştirilir.
> Bu ayrım, verinin tutarlılığını ve yetkilendirmeyi korur.

---

## 4. SQL View'ları

HarmonyView performansı için SQL Server üzerinde view'lar oluşturulmalıdır:

### 4.1 View'ları Uygulama

```bash
# backend/ dizininde
python3 apply_sql.py

# Ya da doğrudan SQL çalıştır
sqlcmd -S HOST -U USER -P PASS -d ControlTower \
  -i sql/views_duration_analysis.sql
```

### 4.2 Temel View'lar

```sql
-- Dolly süre analizi view'u
CREATE OR ALTER VIEW vw_DollyDurationAnalysis AS
SELECT
    s.DollyNo,
    s.VinNo,
    s.SeferNumarasi,
    s.PlakaNo,
    s.EOLName,
    s.PartNumber,
    s.LoadingSessionId,
    s.SubmittedAt,
    
    -- EOL'den sisteme giriş süresi (saat)
    e.InsertedAt AS EolInsertedAt,
    
    -- Tarama zamanı
    h.InsertedAt AS ScanTime,
    
    -- Yükleme tamamlanma zamanı
    h.LoadingCompletedAt,
    
    -- Sevkiyat zamanı
    s.SubmittedAt AS ShipmentTime,
    
    -- Süre hesaplamaları (dakika)
    DATEDIFF(MINUTE, e.InsertedAt, h.InsertedAt) AS EolToScanMinutes,
    DATEDIFF(MINUTE, h.InsertedAt, h.LoadingCompletedAt) AS ScanToLoadMinutes,
    DATEDIFF(MINUTE, h.LoadingCompletedAt, s.SubmittedAt) AS LoadToShipMinutes,
    DATEDIFF(MINUTE, e.InsertedAt, s.SubmittedAt) AS TotalMinutes
    
FROM SeferDollyEOL s
LEFT JOIN DollyEOLInfo e ON s.DollyNo = e.DollyNo AND s.VinNo = e.VinNo
LEFT JOIN DollySubmissionHold h ON s.LoadingSessionId = h.LoadingSessionId
    AND s.DollyNo = h.DollyNo;

-- Operatör performans view'u
CREATE OR ALTER VIEW vw_OperatorPerformance AS
SELECT
    TerminalUser AS OperatorName,
    COUNT(DISTINCT LoadingSessionId) AS TotalSessions,
    COUNT(*) AS TotalDollys,
    AVG(DATEDIFF(MINUTE, InsertedAt, LoadingCompletedAt)) AS AvgLoadingMinutes,
    MIN(InsertedAt) AS FirstActivity,
    MAX(InsertedAt) AS LastActivity
FROM DollySubmissionHold
WHERE Status IN ('loading_completed', 'completed')
AND TerminalUser IS NOT NULL
GROUP BY TerminalUser;
```

---

## 5. API Endpointleri

### 5.1 Dashboard Veri Endpointleri

```http
GET /api/dashboard
```
**Yanıt:**
```json
{
    "total_dollys_today": 245,
    "total_shipments_today": 18,
    "active_sessions": 3,
    "pending_operator_approval": 2,
    "eol_distribution": [
        {"eol_name": "V710-LLS-EOL", "count": 45},
        {"eol_name": "V710-MR-EOL", "count": 38}
    ]
}
```

```http
GET /api/operators
```
**Yanıt:**
```json
[
    {
        "operator_name": "Mehmet Yılmaz",
        "total_sessions": 12,
        "total_dollys": 156,
        "avg_loading_minutes": 23.5
    }
]
```

```http
GET /api/timeline?date=2025-11-26
```

```http
GET /api/shifts?date=2025-11-26
```

```http
GET /api/bottlenecks?days=7
```

### 5.2 Filtreler

Tüm endpointlerde şu query parametreleri desteklenir:

| Parametre | Tür | Açıklama |
|-----------|-----|----------|
| `date` | YYYY-MM-DD | Belirli tarih filtresi |
| `start_date` | YYYY-MM-DD | Tarih aralığı başlangıcı |
| `end_date` | YYYY-MM-DD | Tarih aralığı bitişi |
| `shift` | 1/2/3 | Vardiya filtresi |
| `eol_name` | string | EOL istasyon filtresi |
| `operator` | string | Operatör filtresi |

### 5.3 Sağlık Kontrolü

```http
GET /health
```
**Yanıt:** `{"status": "ok", "db_connected": true}`

---

## 6. Frontend — Manager Dashboard

### 6.1 Teknoloji Yığını

| Kütüphane | Versiyon | Amaç |
|-----------|---------|------|
| React | 18.2.0 | UI framework |
| Vite | 5.x | Build aracı |
| Tailwind CSS | 3.4.1 | CSS framework |
| Recharts | 2.10.3 | Grafik kütüphanesi |
| Framer Motion | 10.x | Animasyonlar |
| date-fns | 3.x | Tarih formatlama |

### 6.2 Kurulum ve Geliştirme

```bash
cd frontend-manager

# Bağımlılıkları yükle
npm install

# .env dosyası oluştur
echo "VITE_API_URL=http://SUNUCU_IP:8000" > .env

# Geliştirme sunucusu başlat (Port 5173)
npm run dev

# Üretim build
npm run build
# Çıktı: dist/ klasörü
```

### 6.3 App.jsx — Ana Bileşen Yapısı

```jsx
// frontend-manager/src/App.jsx

function App() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);

    // 60 saniyede bir otomatik yenileme
    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 60000);
        return () => clearInterval(interval);
    }, []);

    const fetchData = async () => {
        const response = await fetch(`${import.meta.env.VITE_API_URL}/api/dashboard`);
        const json = await response.json();
        setData(json);
        setLoading(false);
    };

    return (
        <div className="min-h-screen bg-gray-900 text-white">
            <Header />
            <main className="container mx-auto p-4">
                <SummaryCards data={data?.summary} />
                <EOLDistributionChart data={data?.eol_distribution} />
                <OperatorRanking data={data?.operators} />
                <DurationAnalysis data={data?.durations} />
            </main>
        </div>
    );
}
```

### 6.4 Vite Yapılandırması

```js
// vite.config.js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
})
```

### 6.5 Nginx ile Statik Dosya Sunumu

```nginx
# Üretim ortamında React build'ini Nginx ile sun
location / {
    root /path/to/frontend-manager/dist;
    try_files $uri $uri/ /index.html;
    
    # Statik dosyalar için önbellek
    location ~* \.(js|css|png|jpg|svg|ico)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

---

## 7. Frontend — TV Ekranı

TV görünümü, fabrika içindeki büyük monitörler için optimize edilmiştir.

### 7.1 Özellikler

- Tam ekran görüntüleme
- 30 saniyede bir otomatik yenileme
- Yüksek kontrast, uzaktan okunabilir yazı boyutu
- Animasyonlu metrik kartları
- EOL bazlı anlık kuyruk sayıları

### 7.2 Kurulum

```bash
cd frontend-manager-tv

npm install
echo "VITE_API_URL=http://SUNUCU_IP:8000" > .env
npm run build
```

---

## 8. WebSocket Desteği

HarmonyView, gerçek zamanlı güncellemeler için WebSocket bağlantısı kullanır.

### 8.1 Backend WebSocket (FastAPI)

```python
# backend/app.py

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    async def broadcast(self, message: str):
        for conn in self.active_connections:
            try:
                await conn.send_text(message)
            except Exception:
                pass

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Her 10 saniyede güncel veri gönder
            data = await get_realtime_data()
            await websocket.send_text(json.dumps(data))
            await asyncio.sleep(10)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

### 8.2 Frontend WebSocket Bağlantısı

```jsx
// App.jsx içinde
useEffect(() => {
    const ws = new WebSocket(`ws://${SUNUCU_IP}:8000/ws`);
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setRealtimeData(data);
    };
    
    ws.onclose = () => {
        // 5 saniye sonra yeniden bağlan
        setTimeout(() => connectWebSocket(), 5000);
    };
    
    return () => ws.close();
}, []);
```

---

## 9. Servis Yönetimi

### 9.1 Mevcut systemd Servis Dosyaları

| Dosya | Port | Açıklama |
|-------|------|----------|
| `harmonyview-backend.service` | 8000 | Manager Dashboard backend |
| `harmonyview-frontend.service` | — | Manager frontend (Nginx ile çalışır) |
| `harmonyview-operator-backend.service` | — | Operatör backend |
| `harmonyview-operator-frontend.service` | — | Operatör frontend |

### 9.2 Servis Kurulumu

```bash
# Backend servisi
sudo cp harmonyview-backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable harmonyview-backend
sudo systemctl start harmonyview-backend

# Durum kontrol
sudo systemctl status harmonyview-backend
curl http://localhost:8000/health
```

### 9.3 Frontend Güncelleme

```bash
cd frontend-manager

# Kodu güncelle
git pull

# Yeniden build al
npm run build

# Nginx yeniden yükle (statik dosyalar güncellendi)
sudo systemctl reload nginx
```

---

## 10. Geliştirici Notları

### 10.1 Yeni Grafik/Metrik Ekleme

1. **Backend:** `queries.py` içine yeni sorgu fonksiyonu ekle
2. **API:** `app.py` içine yeni endpoint ekle
3. **Frontend:** `App.jsx` içine yeni React bileşeni ekle

```python
# queries.py — Örnek yeni sorgu
async def get_new_metric(db: Session, date: str = None):
    query = """
    SELECT EOLName, COUNT(*) as DollyCount
    FROM DollyEOLInfo
    WHERE CAST(InsertedAt AS DATE) = COALESCE(:date, CAST(GETDATE() AS DATE))
    GROUP BY EOLName
    ORDER BY DollyCount DESC
    """
    result = db.execute(text(query), {"date": date})
    return [{"eol_name": r[0], "count": r[1]} for r in result.fetchall()]
```

### 10.2 Python Bağımlılıkları

| Paket | Versiyon | Amaç |
|-------|---------|------|
| fastapi | 0.109.0 | Web framework |
| uvicorn | 0.27.0 | ASGI server |
| sqlalchemy | 2.0.25 | ORM |
| pyodbc | 5.0.1 | SQL Server ODBC |
| python-dotenv | 1.0.0 | .env yükleme |
| pydantic | 2.5.3 | Veri doğrulama |
| websockets | 12.0 | WebSocket |

### 10.3 Frontend Bağımlılıkları

| Paket | Versiyon | Amaç |
|-------|---------|------|
| react | 18.2.0 | UI framework |
| recharts | 2.10.3 | Grafik bileşenleri |
| framer-motion | 10.x | Animasyon |
| date-fns | 3.x | Tarih işleme |
| tailwindcss | 3.4.1 | CSS framework |
| vite | 5.x | Build aracı |
