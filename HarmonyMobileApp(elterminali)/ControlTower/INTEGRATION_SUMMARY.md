# Control Tower - Harmony Ecosystem API Entegrasyonu

## 📋 Proje Özeti

Bu Android uygulaması, Harmony Ecosystem backend API'si ile entegre edilmiş forklift dolly yönetim sistemidir. Operatörler barkod okuyucu ile dolly'leri tarayarak TIR yükleme işlemlerini gerçekleştirir.

## 🔧 Yapılan Değişiklikler

### 1. Gradle Bağımlılıkları (app/build.gradle.kts)
```kotlin
// Retrofit2 + Gson + OkHttp Logging
implementation("com.squareup.retrofit2:retrofit:2.9.0")
implementation("com.squareup.retrofit2:converter-gson:2.9.0")
implementation("com.google.code.gson:gson:2.10.1")
implementation("com.squareup.okhttp3:logging-interceptor:4.12.0")
```

### 2. API Model Sınıfları
**Oluşturulan dosyalar:**
- `api/models/LoginRequest.java`
- `api/models/LoginResponse.java`
- `api/models/ScanDollyRequest.java`
- `api/models/DollyHoldEntry.java`
- `api/models/EOLGroup.java`
- `api/models/GroupDolly.java`
- `api/models/GroupDollysResponse.java`
- `api/models/ManualScanRequest.java`
- `api/models/ManualScanResponse.java`
- `api/models/RemoveLastRequest.java`
- `api/models/CompleteLoadingRequest.java`
- `api/models/CompleteLoadingResponse.java`
- `api/models/ApiError.java`

### 3. Retrofit API Service
**Dosya:** `api/ForkliftApiService.java`

**Endpoint'ler:**
- `POST /api/forklift/login` - Operatör girişi
- `POST /api/forklift/scan` - Dolly tarama
- `POST /api/forklift/remove-last` - Son dolly'yi çıkar
- `POST /api/forklift/complete-loading` - Yüklemeyi tamamla
- `GET /api/manual-collection/groups` - EOL gruplarını listele
- `GET /api/manual-collection/groups/{groupName}` - Grup dolly'lerini getir
- `POST /api/manual-collection/scan` - Manuel dolly tarama
- `POST /api/manual-collection/remove-last` - Manuel son dolly'yi çıkar

### 4. ApiClient Güncellemesi
**Özellikler:**
- Retrofit instance oluşturma
- OkHttp logging interceptor (debug için)
- Auto authorization header injection
- Gson converter factory
- Legacy JSON metodları (geriye uyumluluk)

### 5. Güncellenen Activity'ler

#### AuthActivity
- Retrofit ile login endpoint kullanımı
- Asenkron Callback yapısı
- Error handling (401, 400, network errors)
- Session token yönetimi

#### GroupActivity
- `/api/manual-collection/groups` endpoint entegrasyonu
- Retrofit Call + Callback pattern
- Auto-refresh (1 saniye aralık)
- Session validation

#### GroupDetailActivity
- `/api/manual-collection/groups/{groupName}` dolly listesi
- `/api/manual-collection/scan` barkod okutma
- `/api/manual-collection/remove-last` son dolly çıkarma
- VIN breakdown parsing (\n ile ayrılmış VIN'ler)

### 6. Prefs Güncellemesi
Base URL varsayılan olarak güncellendi:
```java
http://10.25.1.174:8181
```

## 🚀 Kullanım

### 1. Uygulama Akışı

```
Login Ekranı (Barkod Okut)
    ↓
Ana Menü (EOL Grupları)
    ├── V710-MR-EOL (8 dolly, 3 tarandı)
    ├── V720-FR-EOL (5 dolly, 0 tarandı)
    └── ...
    
Grup Detayı (Dolly Listesi)
    ├── [ ] 5170427 (VIN001, VIN002, VIN003)
    ├── [✓] 5170428 (VIN004, VIN005)
    └── [ ] 5170429 (VIN006)
    
Aksiyonlar:
    - Barkod okut → Dolly ekle
    - "Son Kasayı Çıkart" → LIFO çıkarma
```

### 2. API Endpoints

#### Login
```java
POST /api/forklift/login
Body: { "operatorBarcode": "EMP12345", "deviceId": "android-xxx" }
Response: { "success": true, "sessionToken": "...", "operatorName": "..." }
```

#### Manuel Toplama Grupları
```java
GET /api/manual-collection/groups
Headers: Authorization: Bearer <token>
Response: [
  { "group_name": "V710-MR-EOL", "dolly_count": 8, "scanned_count": 3 }
]
```

#### Dolly Tarama
```java
POST /api/manual-collection/scan
Headers: Authorization: Bearer <token>
Body: { "group_name": "V710-MR-EOL", "barcode": "5170427" }
Response: { "success": true, "dolly_no": "5170427", "message": "Dolly eklendi" }
```

## 📱 Özellikler

### ✅ Tamamlanan
- ✅ Retrofit2 + Gson entegrasyonu
- ✅ Login flow (barkod okuyucu)
- ✅ Session management (token + expiration)
- ✅ EOL grupları listeleme
- ✅ Manuel dolly tarama
- ✅ Son dolly çıkarma (LIFO)
- ✅ VIN breakdown parsing
- ✅ Auto-refresh (1 saniye)
- ✅ Error handling (401, 400, network)
- ✅ Session expired handling
- ✅ OkHttp logging interceptor

### 🎯 Test Edilmesi Gerekenler
1. **Login Flow**
   - Barkod okuyucu ile giriş
   - Manuel barkod girişi
   - Hatalı barkod handling

2. **Manuel Toplama**
   - Grup listesi yükleme
   - Dolly tarama
   - Son dolly çıkarma
   - VIN breakdown gösterimi

3. **Session Yönetimi**
   - Token expiration (8 saat)
   - 401 response → login ekranına yönlendirme
   - Token yenileme

4. **Network Errors**
   - Sunucu kapalı
   - Timeout
   - İnternet kesintisi

## 🐛 Hata Senaryoları

### 1. Session Expired (401)
```
Response: 401 Unauthorized
Action: SessionManager.clear() → AuthActivity'ye yönlendir
Toast: "Oturum süresi doldu. Lütfen tekrar giriş yapın."
```

### 2. Dolly Bulunamadı (404)
```
Response: 404 Not Found
Toast: "Dolly sistemde bulunamadı"
```

### 3. Zaten Taranmış (400)
```
Response: 400 Bad Request
Toast: "Bu dolly zaten taranmış"
```

### 4. Network Error
```
Exception: IOException
Toast: "Bağlantı hatası: <error message>"
```

## 🔑 Önemli Noktlar

### VIN Breakdown
Backend'den gelen VIN'ler `\n` ile ayrılmış:
```java
String vinNo = "VIN001\nVIN002\nVIN003";
String[] vins = vinNo.split("\\r?\\n");
// ["VIN001", "VIN002", "VIN003"]
```

### LIFO (Last In First Out)
Sadece **en son taranan** dolly çıkartılabilir. Bu mantık backend tarafında kontrol edilir.

### Token Yönetimi
- Token 8 saat geçerli (28800 saniye)
- SessionManager'da expires_at kontrolü var
- Her API çağrısında auto header injection

### Auto Refresh
- GroupActivity: 1 saniye aralıkla grup listesi
- GroupDetailActivity: 1 saniye aralıkla dolly listesi
- onPause()/onDestroy()'da handler temizlenir

## 📚 Dokümantasyon Referansları

Proje `docs/` klasöründe detaylı dokümantasyon mevcut:
1. `ANDROID_COMPLETE_INTEGRATION_GUIDE.md` - Kapsamlı rehber
2. `ANDROID_QUICK_REFERENCE_GUIDE.md` - Hızlı referans
3. `PART_GROUP_TECHNICAL_SUMMARY.md` - Teknik özet

## 🛠️ Geliştirici Notları

### Debugging
OkHttp logging interceptor aktif. Tüm API çağrıları Logcat'te görünür:
```
D/OkHttp: --> POST http://10.25.1.174:8181/api/forklift/login
D/OkHttp: {"operatorBarcode":"EMP12345"}
D/OkHttp: <-- 200 OK (234ms)
```

### Base URL Değiştirme
```java
// SettingsActivity üzerinden (varsa)
Prefs.setBaseUrl(context, "http://yeni-ip:8181");

// Veya SharedPreferences'tan manuel
// Key: "base_url"
// Default: "http://10.25.1.174:8181"
```

## ✅ Checklist

- [x] Gradle bağımlılıkları eklendi
- [x] API model sınıfları oluşturuldu
- [x] Retrofit service interface hazır
- [x] ApiClient modernleştirildi
- [x] AuthActivity güncellendi
- [x] GroupActivity API'ye bağlandı
- [x] GroupDetailActivity API'ye bağlandı
- [x] Session management hazır
- [x] Error handling eklendi
- [x] Base URL güncellendi

## 🎯 Sonraki Adımlar

1. **Fiziksel cihazda test**
   - Barkod okuyucu ile test
   - Network stabilitesi
   - Session timeout

2. **UI/UX iyileştirmeleri**
   - Loading animasyonları
   - Error mesajları
   - Success feedback

3. **Performans optimizasyonu**
   - Image lazy loading (varsa)
   - RecyclerView optimizasyonu
   - Memory leak kontrolü

---

**Versiyon:** 1.0  
**Tarih:** 14 Aralık 2025  
**Geliştirici:** GitHub Copilot  
**Backend API:** Harmony Ecosystem v1.0
