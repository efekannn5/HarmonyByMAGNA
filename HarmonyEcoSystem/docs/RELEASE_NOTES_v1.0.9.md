# HarmonyEcoSystem - Release Notes v1.0.9

**Release Date:** 24 Aralık 2025  
**Version:** 1.0.9  
**Previous Version:** 1.0.8 (02 Aralık 2025)

---

## Overview

Bu sürüm Android forklift login akışına rol bilgisi (admin/forklift) kazandırıyor, web panelden barkod atama yeteneği ekliyor ve manuel toplama için tablo tabanlı operatör ekranı + sıralı toplu submit akışını tamamlıyor. Ayrıca uygulama açılışında devreye giren database monitoring servisi ve ilgili API’ler eklendi.

---

## New Features & Improvements

### 1) Admin-Aware Forklift Login & Oturumlar
- `/api/forklift/login` yanıtı artık `isAdmin` ve `role` (admin | forklift | operator) alanlarını döndürüyor; `ADMIN/ADM/SUPERUSER/SU` prefix’li barkodlar otomatik admin olarak işaretleniyor, UserAccount role fallback’i korunuyor (`app/routes/api.py`, `app/utils/forklift_auth.py`).  
- Oturum modeli `ForkliftLoginSession` admin ve rol bilgisini tutacak şekilde genişletildi (`app/models/forklift_session.py`), audit log’lara isAdmin/role metadata’sı yazılıyor.  
- Android ekipleri için login yanıtı şeması güncellendi; admin kullanıcılar ayrı ekrana yönlendirilebiliyor (`BACKEND_API_TEST_RESULTS.md`).

### 2) Kullanıcı Barkod Yönetimi
- `UserAccount` tablosuna opsiyonel `Barcode` kolonu ve benzersiz index eklendi; web panelden kullanıcıya barkod bağlama senaryosu destekleniyor (`database/015_add_barcode_to_useraccount.sql`).  
- Admin tespiti artık hem barkod prefix’i hem de UserAccount rol/barkod eşleşmesiyle yapılabiliyor.

### 3) Manuel Toplama Tablo Arayüzü + Sıralı Submit
- Yeni operatör ekranı `dashboard/manual_collection_table.html` ile EOL bazlı dolly listesi, hızlı arama, toplu seç/temizle, seçili sayacı ve VIN modal’ı eklendi.  
- Kritik akış `/api/manual-collection/submit`: sıralı seçim kontrolü (1..N zorunlu), tek PartNumber ile batch insert, duplicate VIN engeli, DollyEOLInfo → DollySubmissionHold taşıma ve transaction rollback güvenliği (`app/routes/api.py`, `app/services/dolly_service.py`).  
- Gerçek zamanlı bildirimler ve yeni dolly kontrolü için `/api/manual-collection/check-updates` ve `RealtimeService.emit_manual_collection` kullanılıyor.

### 4) Database Monitoring Servisi
- Uygulama boot’unda otomatik başlayan izleme servisi eklendi; graceful shutdown için atexit hook tanımlı (`app/__init__.py`, `app/services/database_monitor.py`).  
- Yeni API’ler: `GET /api/monitoring/status`, `POST /api/monitoring/start`, `POST /api/monitoring/stop` (yetkili kullanıcılar için) ile anlık metrik ve kontrol akışı sağlanıyor.

---

## Database Changes

- **Migration 014:** `database/014_add_admin_role_to_forklift_sessions.sql`  
  - `ForkliftLoginSession` tablosuna `IsAdmin BIT NOT NULL DEFAULT(0)` ve `Role NVARCHAR(20) NOT NULL DEFAULT('forklift')` kolonları + `IX_ForkliftLoginSession_Role` index’i eklendi.  
  - Admin oturumlarını listeleyen view’lar (`vw_ActiveAdminSessions`, `vw_ForkliftSessionStats`) oluşturuldu.
- **Migration 015:** `database/015_add_barcode_to_useraccount.sql`  
  - `UserAccount.Barcode` kolonu ve benzersiz index `IX_UserAccount_Barcode` (NULL hariç) eklendi; admin barkodlarını tanımlamak için kullanılacak.

---

## API Değişiklik Özeti
- **Güncellenen:** `POST /api/forklift/login` → `isAdmin`, `role` alanları ve admin prefix algılama eklendi.  
- **Yeni:** `GET /api/monitoring/status`, `POST /api/monitoring/start`, `POST /api/monitoring/stop` (database monitoring kontrolü).  
- **Manuel Toplama:** `POST /api/manual-collection/submit` sıralı seçim doğrulaması ve tek PartNumber üretimi; `GET /api/manual-collection/check-updates` performanslı sayım ile yeni dolly tespiti.  
- **Real-time:** Manual collection ve grup olayları `RealtimeService` üzerinden `dolly_update` kanalıyla yayınlanıyor.

---

## Testing & Validation

- Normal ve admin kullanıcı login senaryoları prefix + UserAccount rol kontrolüyle test edildi; yanıt şemasında `isAdmin/role` doğrulandı (`BACKEND_API_TEST_RESULTS.md`).  
- VIN formatı ve manual-collection grup sorguları (newline ayrımlı VIN listeleri) API üzerinden doğrulandı.  
- Manuel toplama submit akışı transaction/duplicate korumalarıyla denendi; hatada rollback, başarıda DollyEOLInfo’dan temizleme davranışı gözlemlendi (`database/TEST_manuel_toplama_submit.sql` referansı).  
- Database monitoring start/stop/status uçları çalıştırılarak temel metrik dönüşü ve log kayıtları kontrol edildi.

---

## Upgrade Steps

1) SQL migration’ları sırayla çalıştırın:  
```bash
sqlcmd -S <server> -d <database> -i database/014_add_admin_role_to_forklift_sessions.sql
sqlcmd -S <server> -d <database> -i database/015_add_barcode_to_useraccount.sql
```  
2) Admin kullanıcı barkodlarını `UserAccount.Barcode` alanına tanımlayın; gerekirse migration içindeki örnek update bloklarını güncelleyin.  
3) Kodu deploy edin ve servisi yeniden başlatın:  
```bash
git pull
sudo systemctl restart harmony-ecosystem
```  
4) Android ekipleri için login yanıtında `isAdmin/role` alanlarını tüketen akışı güncelleyin.  
5) Database monitoring’in çalıştığını `GET /api/monitoring/status` ile doğrulayın; gerekirse `POST /api/monitoring/stop` ile kapatın.

---

## Known Issues

- Admin barkodları production ortamında tanımlanmazsa tüm kullanıcılar `role=forklift` olarak oturum açar; migration sonrası kullanıcı/barcode eşlemesini tamamlayın.  
- Manual collection submit işlemi sıralama dışı seçimde 400 döndürür; operatör ekranındaki sıra numarasını takip etmek gerekir.  
- Database monitoring uzun süre çalıştırıldığında log dosyaları büyüyebilir; RotatingFileHandler yapılandırmasıyla sınırlandırın.

---

**End of Release Notes v1.0.9**
