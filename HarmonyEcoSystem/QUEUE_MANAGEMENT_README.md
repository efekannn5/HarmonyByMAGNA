# 🎯 Hızlı Başlangıç - Sıra Yönetimi

## 📦 Kurulum

### 1. SQL Migration
```sql
-- SQL Server'da çalıştır
sqlcmd -S 10.25.64.72 -d HarmonyEcoSystem -i database/016_create_dolly_queue_removed.sql
```

### 2. Uygulamayı Başlat
```bash
python run.py
```

Göreceksiniz:
```
✅ Queue cleanup scheduler başlatıldı (interval: 60 dakika)
```

## 🚀 Kullanım

### Admin Paneli
```
URL: http://10.25.64.181:8181/queue/manage
```

### Dolly Kaldırma
1. ✅ Dolly'leri seç (checkbox)
2. 📝 Neden yaz (opsiyonel)
3. ⏱️ Süre seç:
   - **Süresiz:** İşaretli bırak
   - **Zamanlı:** Saat gir (örn: 24)
4. 🗑️ "Kaldır" butonuna tıkla

### Geri Yükleme
1. Arşiv tablosunda dolly bul
2. ↩️ "Geri Yükle" butonuna tıkla

### Otomatik Temizleme
- Arka planda her 60 dakikada çalışır
- Manuel tetikleme: 🧹 "Temizle" butonu

## 📋 Özellikler

| Özellik | Durum |
|---------|-------|
| Manuel dolly kaldırma | ✅ |
| Toplu kaldırma | ✅ |
| Süresiz arşivleme | ✅ |
| Zamanlı arşivleme | ✅ |
| Geri yükleme | ✅ |
| Otomatik temizleme | ✅ |
| Audit logging | ✅ |

## 🗂️ Dosyalar

```
database/
  └── 016_create_dolly_queue_removed.sql     # Migration

app/
  ├── models/
  │   └── dolly_queue_removed.py             # Model
  ├── services/
  │   ├── dolly_service.py                   # Service metodları
  │   └── queue_cleanup_scheduler.py         # Scheduler
  ├── routes/
  │   └── dashboard.py                       # Endpoints
  └── templates/
      └── dashboard/
          └── queue_manage.html              # UI

docs/
  └── QUEUE_MANAGEMENT_GUIDE.md              # Detaylı döküman
```

## 📖 Detaylı Bilgi

Tüm detaylar için: [QUEUE_MANAGEMENT_GUIDE.md](QUEUE_MANAGEMENT_GUIDE.md)
