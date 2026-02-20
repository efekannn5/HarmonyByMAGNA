# 🚀 Android Forklift API - Hızlı Başlangıç

## 📍 Server Bilgileri

```
Base URL: http://10.25.1.174:8181/api
Content-Type: application/json
Authorization: Bearer <sessionToken>
```

---

## 🔑 1. LOGIN

```http
POST /forklift/login
```

```json
{
  "operatorBarcode": "EMP12345",
  "deviceId": "android-123"
}
```

**Response:**
```json
{
  "success": true,
  "sessionToken": "eyJhbGc...",
  "operatorName": "Mehmet Yılmaz",
  "expiresAt": "2025-11-26T23:30:00Z"
}
```

---

## 📦 2. SCAN DOLLY

```http
POST /forklift/scan
Authorization: Bearer <token>
```

```json
{
  "dollyNo": "DL-5170427",
  "loadingSessionId": "LOAD_20251126_MEHMET"
}
```

**Response:**
```json
{
  "dolly_no": "DL-5170427",
  "vin_no": "3FA6P0LU6FR100001",
  "scan_order": 1,
  "scanned_at": "2025-11-26T14:30:52Z"
}
```

---

## 🗑️ 3. REMOVE LAST DOLLY 🆕

```http
POST /forklift/remove-last
Authorization: Bearer <token>
```

```json
{
  "loadingSessionId": "LOAD_20251126_MEHMET",
  "dollyBarcode": "BARCODE123"
}
```

**Response (Success):**
```json
{
  "dollyNo": "DL-5170427",
  "vinNo": "3FA6P0LU6FR100001",
  "scanOrder": 15,
  "removedAt": "2025-11-26T15:50:00Z"
}
```

**Response (Error - Not Last):**
```json
{
  "error": "Sadece en son eklenen dolly çıkarılabilir. En son: Sıra 15, Seçilen: Sıra 10",
  "retryable": true
}
```

**Kural:** ⚠️ Sadece en son eklenen dolly çıkartılabilir!

---

## ✅ 4. COMPLETE LOADING

```http
POST /forklift/complete-loading
Authorization: Bearer <token>
```

```json
{
  "loadingSessionId": "LOAD_20251126_MEHMET"
}
```

**Response:**
```json
{
  "loadingSessionId": "LOAD_20251126_MEHMET",
  "status": "loading_completed",
  "dollyCount": 15,
  "completedAt": "2025-11-26T15:45:00Z"
}
```

---

## 🚪 4. LOGOUT

```http
POST /forklift/logout
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "message": "Çıkış yapıldı"
}
```

---

## 🎯 Kotlin Örnek

```kotlin
// 1. Login
val loginResponse = apiClient.post("$BASE_URL/forklift/login") {
    setBody(mapOf("operatorBarcode" to barcode))
}

// 2. Scan
val scanResponse = apiClient.post("$BASE_URL/forklift/scan") {
    header("Authorization", "Bearer $token")
    setBody(mapOf(
        "dollyNo" to dollyNo,
        "loadingSessionId" to sessionId
    ))
}

// 3. Complete
val completeResponse = apiClient.post("$BASE_URL/forklift/complete-loading") {
    header("Authorization", "Bearer $token")
    setBody(mapOf("loadingSessionId" to sessionId))
}

// 4. Logout
apiClient.post("$BASE_URL/forklift/logout") {
    header("Authorization", "Bearer $token")
}
```

---

## ⚡ İş Akışı

```
1. Uygulama açılır
   ↓
2. Operatör barkodunu okut → LOGIN
   ↓
3. Session token al ve sakla
   ↓
4. Yeni loading session başlat
   sessionId = "LOAD_" + timestamp + "_" + operatorName
   ↓
5. Her dolly için:
   - Barkod okut
   - SCAN API çağır
   - scan_order otomatik artar (1, 2, 3...)
   ↓
5a. Yanlış okuttuysan (opsiyonel):
   - REMOVE LAST API çağır (sadece son dolly çıkar)
   - Doğru dolly'yi okut
   ↓
6. Tüm dolly'ler yüklendi
   ↓
7. "TAMAMLANDI" butonu → COMPLETE LOADING
   ↓
8. Session sıfırla, yeni yüklemeye hazır
   ↓
9. İş bitince → LOGOUT
```

---

## 🐛 Hata Yönetimi 🆕

**Standart Error Format:**
```json
{
  "error": "Kullanıcıya gösterilecek mesaj",
  "retryable": true  // true = Tekrar dene, false = Tekrar deneme
}
```

### 401 Unauthorized (retryable: false)
```json
{
  "error": "Session expired"
}
```
**Çözüm:** Login ekranına yönlendir

### 400 Bad Request (retryable: true)
```json
{
  "error": "Dolly DL-999999 bulunamadı",
  "retryable": true
}
```
**Çözüm:** Kullanıcıya göster, retry butonu ekle

### 500 Server Error (retryable: true)
```json
{
  "error": "Database error. İşlem geri alındı, lütfen tekrar deneyin.",
  "retryable": true
}
```
**Çözüm:** Retry yap (transaction rollback yapıldı, güvenle retry edilebilir)

**Best Practice:**
```kotlin
if (error.retryable) {
    showRetryDialog(error.error)
} else {
    navigateToLogin()
}
```

---

## 📱 Tüm Endpoint'ler

| Method | Endpoint | Auth | Açıklama |
|--------|----------|------|----------|
| GET | `/health` | ❌ | Sunucu durumu |
| POST | `/forklift/login` | ❌ | Giriş yap |
| POST | `/forklift/logout` | ✅ | Çıkış yap |
| GET | `/forklift/session/validate` | ✅ | Session kontrolü |
| POST | `/forklift/scan` | ✅ | Dolly okut |
| POST | `/forklift/remove-last` | ✅ | 🆕 Son dolly çıkart |
| POST | `/forklift/complete-loading` | ✅ | Yükleme tamamla |
| GET | `/forklift/sessions` | ✅ | Session listesi |

✅ = Authorization header gerekli

---

## 💾 Token Yönetimi

```kotlin
// SharedPreferences ile sakla
val prefs = context.getSharedPreferences("forklift_prefs", Context.MODE_PRIVATE)

// Save
prefs.edit().putString("session_token", token).apply()

// Load
val token = prefs.getString("session_token", null)

// Clear on logout
prefs.edit().remove("session_token").apply()
```

---

## 🔒 Güvenlik

1. **Token encryption:** EncryptedSharedPreferences kullan
2. **Auto-logout:** 8 saat sonra otomatik çıkış
3. **Network security:** HTTPS kullan (production'da)
4. **Certificate pinning:** API sertifikasını doğrula

---

## 📞 Yardım

- **Dokümantasyon:** `docs/ANDROID_API_FULL_GUIDE.md`
- **Sunucu:** 10.25.1.174:8181
- **Destek:** IT Departmanı

**v1.0 | 26 Kasım 2025**
