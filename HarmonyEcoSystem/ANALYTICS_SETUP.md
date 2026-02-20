# HarmonyEcoSystem Analytics Platform - Kurulum ve Test Rehberi

## Durum: ALTYAPI TAMAMLANDI

### Ne Yapıldı

#### 1. Database Layer (SQL Views) ✓
- [x] 10 adet analytics view oluşturuldu
- [x] Read-only erişim için hazırlandı
- [x] Dosya: `database/019_create_analytics_views.sql`

#### 2. Backend Layer (Flask App) ✓
- [x] Ayrı analytics modülü (`analytics/`)
- [x] 7 adet API endpoint (read-only)
- [x] Bağımsız Flask uygulaması
- [x] Port 8190 konfigürasyonu
- [x] Ana sistem servislerini kullanıyor

#### 3. Frontend Layer (Templates) ✓
- [x] Login sayfası
- [x] Ana dashboard (KPI kartları + grafikler)
- [x] Timeline analiz sayfası
- [x] Production line performans
- [x] Operator performansı (anonim)
- [x] Bottleneck tespiti
- [x] Aylık raporlar

#### 4. Static Files ✓
- [x] CSS (analytics.css) - Profesyonel tasarım
- [x] JavaScript (analytics.js) - Yardımcı fonksiyonlar
- [x] Chart.js entegrasyonu
- [x] Bootstrap 5 + Icons

#### 5. Documentation ✓
- [x] Analytics README
- [x] API dokümantasyonu
- [x] Kurulum adımları
- [x] Start/stop scriptleri

---

## Kurulum Adımları

### Adım 1: SQL Views Oluştur

SQL Server'da analytics view'larını çalıştırın:

```bash
# Option 1: SSMS ile (önerilen)
# database/019_create_analytics_views.sql dosyasını SSMS'de açıp Execute edin

# Option 2: sqlcmd ile
sqlcmd -S 10.25.1.174 -U sua_appowneruser1 -P "Magna2026!!" -d ControlTower -i database/019_create_analytics_views.sql
```

**Kontrol:**
```sql
-- Bu sorgu 10 view döndürmeli
SELECT TABLE_NAME 
FROM INFORMATION_SCHEMA.VIEWS 
WHERE TABLE_NAME LIKE 'vw_Analytics_%'
ORDER BY TABLE_NAME;
```

### Adım 2: Test Başlatma

#### Sadece Analytics:
```bash
python3 run_analytics.py
```

#### Her İki Sistem Birlikte:
```bash
./start_all.sh
```

### Adım 3: Erişim Testi

**Analytics Login:**
- URL: http://localhost:8190/analytics/login
- Kullanıcı: Admin hesabınız (ana sistemden)
- Şifre: Admin şifreniz

**API Test:**
```bash
# Health check
curl http://localhost:8190/analytics/api/health

# Overview (login gerekli)
# Önce login olun, sonra browser'dan veya Postman'den test edin
```

---

## Sistem Mimarisi

```
┌─────────────────────────────────────────────────────────┐
│                    SQL Server                            │
│                  (ControlTower DB)                       │
│                                                          │
│  Operational Tables          Analytics Views            │
│  ├─ DollyEOLInfo            ├─ vw_Analytics_DollyJourney│
│  ├─ DollySubmissionHold     ├─ vw_Analytics_DailySummary│
│  ├─ SeferDollyEOL           ├─ vw_Analytics_LinePerf... │
│  ├─ DollyLifecycle          ├─ vw_Analytics_Operator... │
│  └─ ...                     └─ ... (10 views total)     │
└─────────────────────────────────────────────────────────┘
           ▲                              ▲
           │                              │
           │ READ/WRITE                   │ READ-ONLY
           │                              │
┌──────────┴──────────┐        ┌─────────┴─────────────┐
│   Main App (8181)   │        │  Analytics (8190)     │
│                     │        │                       │
│  ├─ API             │        │  ├─ Dashboard         │
│  ├─ Dashboard       │        │  ├─ API (read-only)   │
│  ├─ SocketIO        │        │  ├─ Charts            │
│  └─ Services        │◄───────┤  └─ Reports           │
│                     │ Shared │                       │
│  Port: 8181         │Services│  Port: 8190           │
└─────────────────────┘        └───────────────────────┘
```

### Paylaşılan Kaynaklar:
- Database bağlantısı (aynı credentials)
- DollyService, LifecycleService (kod paylaşımı)
- UserAccount model (login için)
- Config dosyası (config.yaml)

### Ayrı Kaynaklar:
- Port (8181 vs 8190)
- Blueprints (analytics_dashboard_bp, analytics_api_bp)
- Templates klasörü
- Static files klasörü
- Log dosyası (analytics.log)

---

## API Endpoint'ler

### Analytics API (`/analytics/api/`)

#### 1. Overview
```http
GET /analytics/api/overview?date_from=2026-01-11&date_to=2026-01-18
```
**Response:**
```json
{
  "success": true,
  "data": {
    "realtime": {
      "PRODUCTION": {"DollyCount": 125, "AvgWaitHours": 1.2},
      "COMPLETED": {"DollyCount": 892}
    },
    "daily": {
      "TotalDollys": 1250,
      "CompletedDollys": 892,
      "AvgHours_Total": 4.2,
      "TargetAchievementPercent": 87.5
    }
  }
}
```

#### 2. Timeline
```http
GET /analytics/api/timeline?date_from=2026-01-11&date_to=2026-01-18&granularity=daily
```

#### 3. Line Performance
```http
GET /analytics/api/line-performance?date_from=2026-01-11&date_to=2026-01-18
```

#### 4. Bottlenecks
```http
GET /analytics/api/bottlenecks?alert_level=CRITICAL&limit=50
```

#### 5. Operator Performance
```http
GET /analytics/api/operator-performance?date_from=2026-01-11&date_to=2026-01-18
```

#### 6. Monthly Trend
```http
GET /analytics/api/monthly-trend?months=6
```

---

## Dashboard Sayfaları

### 1. Ana Dashboard (`/analytics`)
- KPI Kartları (Production, Loading, Processing, Completed)
- Processing Time Bar Chart
- Target Achievement Pie Chart
- Real-time Status Table
- Auto-refresh (30 saniye)

### 2. Timeline (`/analytics/timeline`)
- Günlük/Saatlik trend grafiği
- Tarih aralığı seçimi
- Average processing time

### 3. Production Lines (`/analytics/lines`)
- Hat bazlı karşılaştırma
- Bar chart (ortalama süre)

### 4. Operators (`/analytics/operators`)
- Anonim operatör performansı
- Forklift ve Web metrikleri
- Vardiya bazlı analiz

### 5. Bottlenecks (`/analytics/bottlenecks`)
- Geciken dollyler
- Alert seviyesi filtreleme
- Darboğaz tespit

### 6. Reports (`/analytics/reports`)
- Aylık trend grafiği
- Özet tablo
- CSV export

---

## Güvenlik

### Erişim Kontrolü
- Sadece admin/manager rolü giriş yapabilir
- Login gerekli (Flask-Login)
- Session tabanlı kimlik doğrulama

### Database Güvenliği
- Read-only views kullanılıyor
- Write işlemi YOK
- Ana sistem verilerine dokunmuyor

### Privacy
- Operatör isimleri MD5 hash'li
- Kişisel veri gösterilmiyor

---

## Performans

### Optimizasyonlar
- View-based queries (pre-computed joins)
- Küçük connection pool (5 bağlantı)
- Client-side caching
- Auto-refresh (30s interval)

### Beklenen Yük
- Eş zamanlı kullanıcı: 5-10
- API isteği/dakika: ~20
- Database sorguları: Read-only, hızlı

---

## Monitoring

### Log Dosyaları
```bash
# Analytics logs
tail -f logs/analytics.log

# Main app logs
tail -f logs/app.log

# Her ikisi birlikte
tail -f logs/*.log
```

### Sistem Kontrolü
```bash
# Port kontrol
lsof -i:8190  # Analytics
lsof -i:8181  # Main app

# Process kontrol
ps aux | grep python3
```

---

## Troubleshooting

### Problem: Analytics başlamıyor
**Çözüm:**
1. Main app'in çalıştığından emin olun (port 8181)
2. Database view'larının oluşturulduğunu kontrol edin
3. Log dosyasına bakın: `tail -f logs/analytics.log`

### Problem: Login çalışmıyor
**Çözüm:**
1. Admin/manager rolünde kullanıcı olduğundan emin olun
2. Ana sistemde login olabildiğinizi test edin
3. UserAccount tablosunda rolü kontrol edin

### Problem: Grafikler yüklenmiyor
**Çözüm:**
1. Browser console'da hata var mı kontrol edin
2. API endpoint'lerine erişilebildiğini test edin
3. View'larda veri olduğunu kontrol edin

### Problem: "View does not exist" hatası
**Çözüm:**
```sql
-- View'ları yeniden oluştur
USE ControlTower;
GO
-- 019_create_analytics_views.sql dosyasını çalıştır
```

---

## Sonraki Adımlar (Görsel İyileştirme)

### Yapılacaklar:
1. [ ] Logo ekleme (Magna veya HarmonyEcoSystem)
2. [ ] Renk teması özelleştirme
3. [ ] Daha fazla görselleştirme (gauge charts, heat maps)
4. [ ] Dashboard widget'ları sürükle-bırak
5. [ ] PDF export özelliği
6. [ ] Gerçek zamanlı bildirimler
7. [ ] Mobil responsive iyileştirme
8. [ ] Dark mode desteği

---

## Komutlar Özet

```bash
# SQL Views Oluştur
sqlcmd -S 10.25.1.174 -U sua_appowneruser1 -P "Magna2026!!" \
  -d ControlTower -i database/019_create_analytics_views.sql

# Analytics Başlat
python3 run_analytics.py

# Her İki Sistem
./start_all.sh

# Durdur
./stop_all.sh

# Loglar
tail -f logs/analytics.log
tail -f logs/app.log

# Test
curl http://localhost:8190/analytics/api/health
```

---

## Destek

Sorun yaşarsanız:
1. Log dosyalarına bakın
2. Database bağlantısını test edin
3. Port kullanımını kontrol edin
4. Ana sistemin çalıştığından emin olun

---

**Durum: HAZIR - Test edilebilir!** ✓

SQL view'ları çalıştırın ve sistemi başlatın.
