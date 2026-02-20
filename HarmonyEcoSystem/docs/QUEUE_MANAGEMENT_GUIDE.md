# 🗂️ Sıra Yönetimi ve Arşivleme Sistemi

**Oluşturma Tarihi:** 14 Ocak 2026  
**Versiyon:** 1.0.0  
**Durum:** ✅ Tamamlandı

---

## 📋 Özet

Admin paneline dolly sıra yönetimi özelliği eklendi. Artık sıradaki dolly'leri manuel olarak kaldırabilir, arşivleyebilir ve isteğe bağlı olarak otomatik silinmelerini ayarlayabilirsiniz.

---

## 🎯 Özellikler

### 1. Manuel Dolly Kaldırma
- ✅ Sıradaki dolly'leri seçerek kaldırma
- ✅ Toplu kaldırma (birden fazla dolly)
- ✅ Kaldırma nedeni ekleme (opsiyonel)
- ✅ Checkbox ile tüm dolly'leri seçme

### 2. Arşivleme Seçenekleri
- ✅ **Süresiz Arşivleme:** Manuel geri yüklenene kadar saklanır
- ✅ **Zamanlı Arşivleme:** Belirtilen süre sonra otomatik silinir (saat cinsinden)

### 3. Geri Yükleme
- ✅ Arşivden dolly'yi tekrar sıraya alma
- ✅ Tek tıkla geri yükleme

### 4. Otomatik Temizleme
- ✅ Arka planda çalışan scheduler (her 60 dakika)
- ✅ Süresi dolmuş kayıtları otomatik siler
- ✅ Manuel temizleme butonu

---

## 🗄️ Database Değişiklikleri

### Yeni Tablo: DollyQueueRemoved

**Dosya:** `database/016_create_dolly_queue_removed.sql`

#### Kolonlar:
```sql
-- Primary Key
Id INT IDENTITY(1,1) PRIMARY KEY

-- DollyEOLInfo'dan kopyalanan alanlar
DollyNo INT NOT NULL
VinNo NVARCHAR(50) NOT NULL
CustomerReferans NVARCHAR(50) NULL
Adet INT NULL
EOLName NVARCHAR(50) NULL
EOLID NVARCHAR(20) NULL
EOLDATE DATE NULL
EOLDollyBarcode NVARCHAR(100) NULL
DollyOrderNo VARCHAR(20) NULL
RECEIPTID INT NULL
OriginalInsertedAt DATETIME2 NULL

-- Arşiv metadata
RemovedAt DATETIME2 NOT NULL DEFAULT GETDATE()
RemovedBy NVARCHAR(100) NULL
RemovalReason NVARCHAR(500) NULL

-- Otomatik silme ayarları
AutoDeleteAfterHours INT NULL          -- NULL = süresiz, değer = X saat sonra
ScheduledDeleteAt DATETIME2 NULL       -- Hesaplanmış silme zamanı
IsDeleted BIT NOT NULL DEFAULT 0       -- Soft delete flag
DeletedAt DATETIME2 NULL
```

#### Indexler:
- `IX_DollyQueueRemoved_DollyNo` - Unique index (DollyNo, VinNo, RemovedAt)
- `IX_DollyQueueRemoved_Cleanup` - Otomatik temizleme için
- `IX_DollyQueueRemoved_Active` - Aktif kayıtlar için

---

## 💻 Backend Değişiklikleri

### 1. Model
**Dosya:** `app/models/dolly_queue_removed.py`

```python
class DollyQueueRemoved(db.Model):
    # ... tüm kolonlar ...
    
    @classmethod
    def from_dolly_eol(cls, dolly_eol_record, removed_by, reason, auto_delete_hours):
        """DollyEOLInfo'dan arşiv kaydı oluştur"""
        
    def calculate_scheduled_delete(self):
        """Otomatik silme zamanını hesapla"""
        
    def to_dict(self):
        """JSON serialization"""
```

### 2. DollyService Metodları
**Dosya:** `app/services/dolly_service.py`

```python
def remove_dolly_from_queue(dolly_no, vin_no, removed_by, reason, auto_delete_hours):
    """Tekil dolly kaldırma"""

def remove_multiple_dollys_from_queue(dolly_list, removed_by, reason, auto_delete_hours):
    """Toplu dolly kaldırma"""

def list_removed_dollys(include_deleted=False):
    """Arşivlenmiş dolly'leri listele"""

def restore_dolly_to_queue(archive_id, restored_by):
    """Arşivden geri yükle"""

def cleanup_expired_removed_dollys():
    """Süresi dolmuş kayıtları temizle"""
```

### 3. Dashboard Routes
**Dosya:** `app/routes/dashboard.py`

```python
@dashboard_bp.get("/queue/manage")
def manage_queue():
    """Sıra yönetimi sayfası"""

@dashboard_bp.post("/queue/remove")
def remove_from_queue():
    """Seçili dolly'leri kaldır"""

@dashboard_bp.post("/queue/restore/<int:archive_id>")
def restore_to_queue():
    """Arşivden geri yükle"""

@dashboard_bp.post("/queue/cleanup")
def cleanup_expired():
    """Manuel temizleme"""
```

### 4. Otomatik Temizleme Scheduler
**Dosya:** `app/services/queue_cleanup_scheduler.py`

```python
class QueueCleanupScheduler:
    cleanup_interval_minutes = 60  # Her 60 dakika
    
    def start_scheduler(app):
        """Uygulama başlangıcında otomatik başlar"""
    
    def _cleanup_loop():
        """Arka planda sürekli çalışır"""
```

**Entegrasyon:** `app/__init__.py`
```python
def _setup_queue_cleanup_scheduler(app):
    queue_cleanup_scheduler.start_scheduler(app)
```

---

## 🎨 UI Özellikleri

### Sıra Yönetimi Sayfası
**Dosya:** `app/templates/dashboard/queue_manage.html`

**URL:** `/queue/manage`

#### Üst Bölüm - Aktif Sıra:
- Checkbox ile dolly seçimi
- Master checkbox (tümünü seç)
- Kaldırma nedeni input alanı
- Radio button seçenekleri:
  - ✅ Süresiz arşivle
  - ⏱️ Zamanlı arşivle (saat input)
- Aksiyon butonları:
  - 🗑️ Seçili Dolly'leri Kaldır
  - Tümünü Seç
  - Seçimi Temizle

#### Alt Bölüm - Arşiv:
- Arşivlenmiş dolly listesi
- Kaldırma bilgileri
- Silme süreleri (eğer varsa)
- ↩️ Geri Yükle butonu
- 🧹 Süresi Dolmuş Kayıtları Temizle butonu

#### JavaScript Özellikleri:
- Dinamik seçim sayacı
- Form validasyonu
- Onay diyalogları
- Radio button toggle (zamanlı/süresiz)

---

## 🚀 Kullanım Kılavuzu

### Adım 1: SQL Migration Çalıştır

```bash
# SQL Server'a bağlan ve migration'ı çalıştır
sqlcmd -S <server> -d <database> -i database/016_create_dolly_queue_removed.sql

# VEYA
# Azure Data Studio / SSMS'den dosyayı çalıştır
```

### Adım 2: Uygulamayı Başlat

```bash
# Uygulama başlatıldığında scheduler otomatik çalışır
python run.py
```

Log'da göreceksiniz:
```
✅ Queue cleanup scheduler başlatıldı (interval: 60 dakika)
```

### Adım 3: Admin Paneline Git

```
URL: http://10.25.64.181:8181/queue/manage
Kullanıcı: admin
```

### Adım 4: Dolly Kaldırma

1. Kaldırmak istediğiniz dolly'leri seçin
2. Kaldırma nedeni yazın (opsiyonel)
3. Arşivleme tipini seçin:
   - **Süresiz:** Checkbox işaretli bırakın
   - **Zamanlı:** Timed radio button'u seç, saat gir (örn: 24, 48, 72)
4. "Seçili Dolly'leri Kaldır" butonuna tıklayın
5. Onay verin

### Adım 5: Geri Yükleme

1. Alt bölümdeki arşiv tablosunu kontrol edin
2. Geri yüklemek istediğiniz dolly'nin yanındaki "↩️ Geri Yükle" butonuna tıklayın
3. Onay verin
4. Dolly tekrar sıraya eklenir

### Adım 6: Manuel Temizleme

Süresi dolmuş kayıtları hemen temizlemek için:
1. "🧹 Süresi Dolmuş Kayıtları Temizle" butonuna tıklayın
2. Sistem otomatik olarak ScheduledDeleteAt <= NOW olan kayıtları soft delete yapar

---

## 🔧 Ayarlar

### Cleanup Interval Değiştirme

**Dosya:** `app/services/queue_cleanup_scheduler.py`

```python
class QueueCleanupScheduler:
    cleanup_interval_minutes = 60  # Bunu değiştir (örn: 30, 120)
```

### Otomatik Temizlemeyi Devre Dışı Bırakma

**Dosya:** `app/__init__.py`

```python
def create_app():
    # ...
    # _setup_queue_cleanup_scheduler(app)  # Bu satırı comment out et
```

---

## 📊 Audit Logging

Tüm işlemler audit log'a kaydedilir:

```python
# Dolly kaldırma
action: "queue.remove_dolly"
resource: "dolly_queue"
metadata: {
    "dolly_no": 123,
    "vin_no": "ABC123",
    "reason": "Hasar",
    "auto_delete_hours": 24
}

# Toplu kaldırma
action: "queue.remove_multiple_dollys"
metadata: {
    "total_requested": 10,
    "success_count": 10,
    "failed_count": 0
}

# Geri yükleme
action: "queue.restore_dolly"
metadata: {
    "archive_id": 5,
    "dolly_no": 123
}

# Otomatik temizleme
action: "queue.cleanup_expired"
actor_name: "SYSTEM"
metadata: {
    "deleted_count": 3
}
```

---

## ⚠️ Önemli Notlar

### 1. Soft Delete Sistemi
- Arşivden "silinen" kayıtlar aslında soft delete edilir (`IsDeleted = 1`)
- Fiziksel olarak silinmezler, gerekirse kurtarılabilir
- Hard delete için manuel SQL çalıştırılmalı

### 2. Duplicate Kontrolü
- Aynı DollyNo + VinNo kombinasyonu sırada yalnızca bir kez olabilir
- Geri yükleme sırasında duplicate kontrolü yapılır

### 3. Thread Safety
- Scheduler arka planda daemon thread olarak çalışır
- App context içinde çalışır
- Graceful shutdown destekler

### 4. Performance
- Indexler sayesinde hızlı cleanup
- WHERE clause'lu filtered index kullanımı
- Batch işlemler için transaction desteği

---

## 🧪 Test Senaryoları

### Senaryo 1: Süresiz Arşivleme
```
1. 3 dolly seç
2. "Süresiz arşivle" seçeneğini işaretle
3. Kaldır
4. Arşivde göreceksin: "Süresiz" badge
5. 60 dakika sonra bile silinmez
```

### Senaryo 2: Zamanlı Arşivleme
```
1. 2 dolly seç
2. "Zamanlı arşivle" seçeneğini işaretle
3. 1 saat gir
4. Kaldır
5. Arşivde göreceksin: "1 saat" badge + silme zamanı
6. 61 dakika sonra scheduler otomatik siler
```

### Senaryo 3: Geri Yükleme
```
1. Arşivdeki bir dolly'yi geri yükle
2. Aktif sırada tekrar görünür
3. Arşivde "IsDeleted = 1" olur
```

### Senaryo 4: Toplu İşlem
```
1. 50 dolly seç
2. Toplu kaldır
3. Success/fail count göreceksin
4. Failed olanlar için hata mesajları
```

---

## 📞 Destek

Sorular için:
- Backend geliştirici ile iletişime geçin
- Audit log'ları inceleyin: `/admin/logs`
- Uygulama log'larını kontrol edin: `logs/app.log`

---

## ✅ Checklist

Kurulum tamamlandı mı?
- [ ] SQL migration çalıştırıldı
- [ ] Uygulama başlatıldı
- [ ] Scheduler log'da görünüyor
- [ ] Admin panelde "Sıra Yönetimi" linki var
- [ ] Sayfa açılıyor ve dolly'ler listeleniyor
- [ ] Test kaldırma işlemi başarılı
- [ ] Test geri yükleme başarılı
- [ ] Otomatik temizleme çalışıyor

---

**Geliştirici:** GitHub Copilot  
**Son Güncelleme:** 14 Ocak 2026
