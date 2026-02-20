# Real-time Updates Implementation Guide

## ✅ Ne Yapıldı?

HarmonyEcoSystem'e **Flask-SocketIO** ile canlı güncelleme özelligi eklendi. Artık manuel toplama ve diğer işlemler olduğunda sayfa otomatik olarak güncelleniyor.

## 📦 Eklenen Bileşenler

### 1. Backend (Python)
- **Flask-SocketIO**: WebSocket bağlantısı için
- **RealtimeService**: Event broadcasting servisi (`app/services/realtime_service.py`)
- Real-time event emit'ler manuel toplama, grup oluşturma vs. için

### 2. Frontend (JavaScript)
- Socket.IO client kütüphanesi
- Otomatik bağlantı ve yeniden bağlanma
- Toast bildirimleri
- Sayfa verilerini AJAX ile güncelleme

### 3. Stil (CSS)
- Toast notification tasarımı
- Loading göstergeleri
- Mobil uyumlu bildirimler

## 🚀 Kurulum

### 1. Yeni kütüphaneleri yükleyin:
```bash
pip3 install flask-socketio python-socketio eventlet
```

Veya tüm requirements'ları tekrar yükleyin:
```bash
pip3 install -r requirements.txt
```

### 2. Uygulamayı başlatın:

**Development:**
```bash
python3 run.py
```

**Production (Systemd Service):**
```bash
sudo systemctl restart harmonyecosystem
```

## 🎯 Özellikler

### Otomatik Güncellenen Olaylar:

1. **Manuel Dolly Toplama**
   - Bir operatör manuel toplama yaptığında
   - Tüm kullanıcılara bildirim gider
   - Dashboard otomatik güncellenir

2. **Grup Oluşturma**
   - Yeni grup oluşturulduğunda
   - Grup listesi otomatik yenilenir

3. **Görev Güncellemeleri**
   - Task durumu değiştiğinde
   - İlgili sayfalar güncellenir

4. **Sevkiyat Güncellemeleri**
   - Shipment status değişikliklerinde
   - Real-time bildirim

### Toast Bildirimleri:
- ✅ **Success** (Yeşil) - Başarılı işlemler
- ℹ️ **Info** (Mavi) - Bilgilendirme
- ⚠️ **Warning** (Sarı) - Uyarılar
- ❌ **Error** (Kırmızı) - Hatalar

## 🔧 Nasıl Çalışıyor?

### Backend'de Event Gönderme:

```python
from app.services.realtime_service import RealtimeService

# Manuel toplama bildirimi
RealtimeService.emit_manual_collection(
    group_id=1,
    group_name="Grup A",
    dolly_count=5,
    actor="operator_name"
)

# Grup oluşturma bildirimi
RealtimeService.emit_group_created(
    group_id=1,
    group_name="Yeni Grup"
)

# Genel bildirim
RealtimeService.emit_notification(
    message="İşlem tamamlandı!",
    notification_type="success"
)
```

### Frontend'de Dinleme:

JavaScript otomatik olarak bu event'leri dinliyor ve:
1. Toast bildirimi gösteriyor
2. İlgili sayfa bölümlerini AJAX ile yeniliyor
3. Sayfa yenilemeden veri güncelliyor

## 📊 Hangi Sayfalarda Aktif?

- ✅ Ana Dashboard (`/`)
- ✅ Manuel Toplama (`/manual-collection`)
- ✅ Grup Yönetimi (`/groups/manage`)
- ✅ Operatör Paneli (`/operator/*`)
- ✅ Tüm admin sayfaları

## 🔍 Debug

Browser console'da SocketIO bağlantısını kontrol edebilirsiniz:

```javascript
// Console'da bağlantı durumu
window.harmonySocket.connected  // true/false

// Manuel event gönderme (test için)
window.harmonySocket.emit('test_event', {data: 'test'})
```

## ⚙️ Gunicorn Ayarları

SocketIO için özel ayarlar yapıldı:
- **Worker**: 1 (tek worker gerekli)
- **Worker class**: eventlet (async desteği)
- **Bind**: 0.0.0.0:8181

## 🐛 Sorun Giderme

### SocketIO bağlanmıyor?
```bash
# Port kontrolü
sudo lsof -i :8181

# Logları kontrol et
tail -f logs/app.log
tail -f logs/gunicorn_error.log
```

### Bildirimler görünmüyor?
- Browser console'u kontrol edin
- Network tab'de WebSocket bağlantısına bakın
- AdBlock veya güvenlik eklentilerini devre dışı bırakın

### Firewall problemi?
```bash
# 8181 portunu aç
sudo ufw allow 8181
```

## 📝 Notlar

- Real-time özellik **mevcut kodu bozmadan** eklendi
- Tüm eski endpoint'ler çalışmaya devam ediyor
- SocketIO bağlantısı kopsa bile uygulama çalışır
- Otomatik yeniden bağlanma aktif (max 10 deneme)

## 🎨 Özelleştirme

Toast bildirimlerini özelleştirmek için `app/static/css/main.css` dosyasındaki `.realtime-notification` sınıflarını düzenleyin.

Event tipleri eklemek için `app/services/realtime_service.py` dosyasına yeni methodlar ekleyin.
