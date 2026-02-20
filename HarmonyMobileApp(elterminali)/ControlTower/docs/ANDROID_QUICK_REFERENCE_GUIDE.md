# 📱 Android Forklift API - Hızlı Referans

## 🌐 Temel Bilgiler

```
Base URL: http://10.25.1.174:8181/api
Content-Type: application/json
Authorization: Bearer <sessionToken>
```

---

## 🔑 Authentication

### Login
```http
POST /forklift/login
```
```json
Request:
{
  "operatorBarcode": "EMP12345",
  "deviceId": "android-123"
}

Response:
{
  "success": true,
  "sessionToken": "eyJhbGc...",
  "operatorName": "Mehmet Yılmaz",
  "expiresAt": "2025-12-14T16:00:00Z",
  "isAdmin": false,
  "role": "forklift"
}

Admin Response:
{
  "success": true,
  "sessionToken": "eyJhbGc...",
  "operatorName": "Admin User",
  "expiresAt": "2025-12-14T16:00:00Z",
  "isAdmin": true,
  "role": "admin"
}
```

### Logout
```http
POST /forklift/logout
Authorization: Bearer <token>
```

### Validate Session
```http
GET /forklift/session/validate
Authorization: Bearer <token>
```

---

## 🚛 Dolly Yükleme

### 1. Dolly Tara
```http
POST /forklift/scan
Authorization: Bearer <token>
```
```json
Request:
{
  "dollyNo": "5170427",
  "loadingSessionId": "LOAD_20251214_MEHMET"  // optional
}

Response:
{
  "dolly_no": "5170427",
  "vin_no": "VIN001",
  "status": "scanned",
  "eol_name": "V710-MR-EOL",
  "scanned_at": "2025-12-14T10:30:00Z"
}
```

### 2. Son Dolly'yi Çıkar (LIFO)
```http
POST /forklift/remove-last
Authorization: Bearer <token>
```
```json
Request:
{
  "loadingSessionId": "LOAD_20251214_MEHMET",
  "dollyBarcode": "BARCODE123"
}

Response:
{
  "dollyNo": "5170427",
  "scanOrder": 3,
  "removedAt": "2025-12-14T10:45:00Z"
}
```

### 3. Yüklemeyi Tamamla
```http
POST /forklift/complete-loading
Authorization: Bearer <token>
```
```json
Request:
{
  "loadingSessionId": "LOAD_20251214_MEHMET"
}

Response:
{
  "loadingSessionId": "LOAD_20251214_MEHMET",
  "dollyCount": 15,
  "completedAt": "2025-12-14T11:00:00Z",
  "status": "loading_completed"
}
```

### 4. Oturumları Listele
```http
GET /forklift/sessions?status=scanned
Authorization: Bearer <token>
```

---

## 📦 Manuel Toplama

### 1. Grupları Listele
```http
GET /manual-collection/groups
Authorization: Bearer <token>
```
```json
Response:
[
  {
    "group_name": "V710-MR-EOL",
    "dolly_count": 8,
    "scanned_count": 3
  }
]
```

### 2. Grup Dolly'lerini Getir
```http
GET /manual-collection/groups/{groupName}
Authorization: Bearer <token>
```
```json
Response:
{
  "group_name": "V710-MR-EOL",
  "dollys": [
    {
      "dolly_no": "5170427",
      "vin_no": "VIN001\nVIN002",
      "scanned": false
    }
  ]
}
```

### 3. Dolly Tara
```http
POST /manual-collection/scan
Authorization: Bearer <token>
```
```json
Request:
{
  "group_name": "V710-MR-EOL",
  "barcode": "5170427"
}

Response:
{
  "success": true,
  "dolly_no": "5170427",
  "message": "Dolly eklendi"
}
```

### 4. Son Dolly'yi Çıkar
```http
POST /manual-collection/remove-last
Authorization: Bearer <token>
```
```json
Request:
{
  "group_name": "V710-MR-EOL",
  "barcode": "5170427"
}
```

---

## ⚠️ Hata Kodları

| Status | Açıklama | Retry? |
|--------|----------|--------|
| 200 | Başarılı | - |
| 400 | Kullanıcı hatası | ❌ |
| 401 | Token geçersiz → Login'e yönlendir | ❌ |
| 404 | Kayıt bulunamadı | ❌ |
| 409 | Zaten var (duplicate) | ❌ |
| 500 | Sunucu hatası | ✅ Retry |

### Error Response Format
```json
{
  "error": "Hata mesajı",
  "retryable": true
}
```

---

## 📊 Veri Modelleri (Kotlin)

```kotlin
// Authentication
data class LoginRequest(
    val operatorBarcode: String,
    val deviceId: String? = null
)

data class LoginResponse(
    val success: Boolean,
    val sessionToken: String?,
    val operatorName: String?,
    val expiresAt: String?,
    val isAdmin: Boolean = false,
    val role: String? = "forklift"
)

// Dolly Operations
data class ScanDollyRequest(
    val dollyNo: String,
    val loadingSessionId: String? = null
)

data class DollyHoldEntry(
    val dolly_no: String,
    val vin_no: String,
    val status: String,
    val eol_name: String?,
    val scanned_at: String?
)

// Manual Collection
data class EOLGroup(
    val group_name: String,
    val dolly_count: Int,
    val scanned_count: Int
)

data class GroupDolly(
    val dolly_no: String,
    val vin_no: String,
    val scanned: Boolean
)
```

---

## 🚀 Retrofit Interface

```kotlin
interface ForkliftApi {
    @POST("forklift/login")
    suspend fun login(@Body request: LoginRequest): Response<LoginResponse>
    
    @POST("forklift/scan")
    suspend fun scanDolly(
        @Header("Authorization") token: String,
        @Body request: ScanDollyRequest
    ): Response<DollyHoldEntry>
    
    @POST("forklift/complete-loading")
    suspend fun completeLoading(
        @Header("Authorization") token: String,
        @Body request: CompleteLoadingRequest
    ): Response<CompleteLoadingResponse>
    
    @GET("manual-collection/groups")
    suspend fun getManualCollectionGroups(
        @Header("Authorization") token: String
    ): Response<List<EOLGroup>>
}
```

---

## 💡 Önemli Notlar

### VIN Breakdown
```
Backend'den gelen: "VIN001\nVIN002\nVIN003"
UI'da göster: "VIN001, VIN002, VIN003"
```

### Status Flow
```
scanned → loading_completed → completed
```

### LIFO (Last In First Out)
Sadece en son taranan dolly çıkartılabilir!

### Token Expiration
Token 8 saat geçerli. Expired olunca 401 gelir → Login ekranına yönlendir.

---

## 📱 Ekran Akışı

```
Login (Barkod Okut)
    ↓
Ana Menü
    ├── Dolly Yükleme
    │       ↓
    │   [Dolly Tara] → Liste → [Tamamla]
    │
    └── Manuel Toplama
            ↓
        Grup Seç → Dolly Listesi → [Tara] → [Tamamla]
```

---

## 🔧 Test Credentials

```
Operatör Barkodu: EMP12345
Test Dolly: 5170427
Test Barkod: BARCODE123
```

---

**Versiyon:** 1.0  
**Tarih:** 14 Aralık 2025  
**Detaylı Doküman:** `ANDROID_COMPLETE_INTEGRATION_GUIDE.md`
