# HarmonyEcoSystem - Release Notes v1.0.8

**Release Date:** 02 Aralık 2025  
**Version:** 1.0.8  
**Previous Version:** 1.0.7 (27-30 Kasım 2025)

---

## Overview

Bu sürüm, forklift operasyonları için barkod tabanlı kimlik doğrulama, kısmi sevkiyat desteği, gelişmiş validasyonlar ve kritik hata/iz kayıtları ile güvenlik ve izlenebilirliği üretim seviyesine taşıyor. Android ekipleri için tam uçtan uca entegrasyon rehberleri eklendi; veri modeli eksik kolonlar tamamlandı.

---

## New Features & Improvements

### 1) Forklift Barkod Login & Oturum Yönetimi
- Yeni endpoints: `POST /api/forklift/login`, `POST /api/forklift/logout`, `GET /api/forklift/session/validate` (`app/routes/api.py`)  
- 8 saat geçerli Bearer token, cihaz bilgisi ve app versiyonu metadata olarak saklanıyor (`app/utils/forklift_auth.py`, model `ForkliftLoginSession`)  
- Tüm forklift çağrıları artık zorunlu olarak `Authorization: Bearer <token>` header'ı ile çalışıyor; eski `forkliftUser` body alanı kaldırıldı.  
- Her login/logout, scan ve complete işlemi `AuditLog`'a işleniyor.

### 2) Forklift İşlem Güvenliği + LIFO Geri Alma
- `POST /api/forklift/scan`, `/forklift/complete-loading`, `/forklift/sessions` auth decorator ile korumaya alındı.  
- Yeni LIFO endpoint: `POST /api/forklift/remove-last` ile sadece son okutulan dolly geri alınabiliyor.  
- Hata durumları standart formata döndü: `{"error": "...", "message": "...", "retryable": bool}`; transaction rollback otomatik.  
- Lifecycle genişletildi: `LOADING_IN_PROGRESS`, `LOADING_COMPLETED` gibi durumlar eklendi.

### 3) Operatör Kısmi Sevkiyat & Validasyonlar
- Web UI'da checkbox ile kısmi sevkiyat seçimi; API `POST /api/operator/complete-shipment` isteğe bağlı `selectedDollyIds` listesiyle çalışıyor.  
- Sefer/Plaka doğrulamaları: regex kontrollü format, mükerrer sefer numarası engeli, net hata mesajları.  
- Lojistik alanları (`SeferNumarasi`, `PlakaNo`, `LoadingSessionId`) zorunlu akışta doğrulanıyor; hatalarda otomatik rollback.

### 4) Android Entegrasyon Rehberleri
- Tam dokümantasyon güncellendi: `docs/ANDROID_API_FULL_GUIDE.md`, `docs/ANDROID_QUICK_REFERENCE.md`, `docs/API_ENDPOINTS.md`, `docs/ANDROID_QUICK_REFERENCE_GUIDE.md`.  
- Login → token saklama → her çağrıya Bearer header ekleme → 401 yakalama akışı için Kotlin örnekleri ve test senaryoları eklendi.  
- Yeni iş akışı anlatımı: `docs/new_workflow.md`.

---

## Database Changes

- **Migration 012:** `database/012_create_forklift_login_sessions.sql` (ForkliftLoginSession tablosu).  
- **Migration 013:** `database/013_add_missing_columns_dolly_submission_hold.sql` (PartNumber, CustomerReferans, EOLName, EOLID, DollyOrderNo, Adet kolonları ve `IX_DollySubmissionHold_DollyNo_VinNo` index'i).  
- Yeni dependency yok; mevcut `requirements.txt` yeterli.

---

## API Değişiklik Özeti
- **Yeni:** `/api/forklift/login`, `/api/forklift/logout`, `/api/forklift/session/validate`, `/api/forklift/remove-last`  
- **Breaking change:** Tüm forklift endpoint'leri token zorunlu; body'de kullanıcı bilgisi gönderilmiyor.  
- **Validasyon:** `/api/operator/complete-shipment` sefer/plaka format ve duplicate kontrolleri; kısmi sevkiyat desteği.

---

## Testing & Validation

- Curl testleri: login → scan → complete-loading → logout akışı 200; hatalı token 401 döndürüyor.  
- Validasyon testleri: Geçersiz sefer/plaka formatında 400; duplicate seferde bloklama.  
- LIFO senaryoları: Son dolly geri alınabiliyor, ortadan geri alma denemesinde hata bekleniyor.  
- Flask başlatma ve py_compile kontrolleri sorunsuz (`app/routes/api.py`).

---

## Upgrade Steps

1) SQL migration'ları sırayla çalıştırın:  
```bash
sqlcmd -S <server> -d ControlTower -i database/012_create_forklift_login_sessions.sql
sqlcmd -S <server> -d ControlTower -i database/013_add_missing_columns_dolly_submission_hold.sql
```  
2) Kodu çekin ve servisi yeniden başlatın:  
```bash
git pull
sudo systemctl restart harmony-ecosystem
```  
3) Doğrulama: `/api/forklift/login` ile token alın; token ile `/api/forklift/scan` ve `/api/forklift/complete-loading` testlerini çalıştırın; kısmi sevkiyat ve validasyon hatalarını doğrulayın.

---

## Known Issues

- Bilinen kritik açık yok. Android istemcileri token yönetimi eklenmeden eski çağrı formatıyla çalışamayacak; güncelleme zorunlu.

---

**End of Release Notes v1.0.8**
