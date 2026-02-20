# 📱 Android Forklift Uygulaması - Tam API Rehberi

## 🌐 API Bilgileri

### Base URL
```
http://10.25.1.174:8181/api
```

### Server Bilgileri
- **IP:** 10.25.1.174
- **Port:** 8181
- **Protokol:** HTTP (Production'da HTTPS olacak)
- **Content-Type:** application/json
- **Charset:** UTF-8

---

## 🔐 Authentication (Kimlik Doğrulama)

### 1. Login (Barkod ile Giriş)

Forklift operatör çalışan barkodunu okutarak giriş yapar.

**Endpoint:** `POST /forklift/login`

**Request Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "operatorBarcode": "EMP12345",
  "operatorName": "Mehmet Yılmaz",  // Opsiyonel
  "deviceId": "android-serial-123456"  // Opsiyonel ama önerilir
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "sessionToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "operatorName": "Mehmet Yılmaz",
  "operatorBarcode": "EMP12345",
  "expiresAt": "2025-11-26T23:30:00Z",
  "message": "Hoş geldiniz Mehmet Yılmaz"
}
```

**Error Response (400 Bad Request):**
```json
{
  "error": "Operatör barkodu gerekli",
  "retryable": true
}
```

**Kullanım (Kotlin):**
```kotlin
data class LoginRequest(
    val operatorBarcode: String,
    val operatorName: String? = null,
    val deviceId: String? = null
)

data class LoginResponse(
    val success: Boolean,
    val sessionToken: String?,
    val operatorName: String?,
    val operatorBarcode: String?,
    val expiresAt: String?,
    val message: String
)

suspend fun login(barcode: String): LoginResponse {
    val response = httpClient.post("$BASE_URL/forklift/login") {
        contentType(ContentType.Application.Json)
        setBody(LoginRequest(
            operatorBarcode = barcode,
            operatorName = null, // Sistem barkoddan bulacak
            deviceId = Settings.Secure.getString(context.contentResolver, Settings.Secure.ANDROID_ID)
        ))
    }
    return response.body()
}
```

---

### 2. Session Validation (Oturum Doğrulama)

Mevcut oturumun geçerli olup olmadığını kontrol eder.

**Endpoint:** `GET /forklift/session/validate`

**Request Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Success Response (200 OK):**
```json
{
  "valid": true,
  "operatorName": "Mehmet Yılmaz",
  "operatorBarcode": "EMP12345",
  "loginAt": "2025-11-26T08:30:00Z",
  "expiresAt": "2025-11-26T16:30:00Z"
}
```

**Error Response (401 Unauthorized):**
```json
{
  "error": "invalid_session",
  "message": "Oturumunuz sona erdi. Lütfen tekrar giriş yapın."
}
```

---

### 3. Logout (Çıkış)

**Endpoint:** `POST /forklift/logout`

**Request Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "Çıkış yapıldı. Güle güle!"
}
```

---

## 📦 Dolly Scanning (Okutma İşlemleri)

### 4. Dolly Scan (Barkod Okut)

TIR'a yüklenen her dolly için sırayla çağrılır.

**Endpoint:** `POST /forklift/scan`

**Request Headers:**
```
Authorization: Bearer <sessionToken>
Content-Type: application/json
```

**Request Body:**
```json
{
  "dollyNo": "DL-5170427",
  "loadingSessionId": "LOAD_20251126_143052_MEHMET",  // Opsiyonel
  "barcode": "BARCODE123456"  // Opsiyonel, doğrulama için
}
```

**Success Response (201 Created):**
```json
{
  "id": 123,
  "dolly_no": "DL-5170427",
  "vin_no": "3FA6P0LU6FR100001",
  "status": "scanned",
  "terminal_user": "Mehmet Yılmaz",
  "scanned_at": "2025-11-26T14:30:52Z",
  "scan_order": 1,
  "customer_referans": "FORD-EXPORT",
  "eol_name": "EOL-A1",
  "adet": 1,
  "eol_dolly_barcode": "BARCODE123456"
}
```

**Error Responses:**

Dolly bulunamadı (400):
```json
{
  "message": "Dolly DL-999999 bulunamadı"
}
```

Barkod eşleşmedi (400):
```json
{
  "message": "Barkod eşleşmedi"
}
```

Auth hatası (401):
```json
{
  "error": "authentication_required",
  "message": "Giriş yapmanız gerekiyor. Lütfen barkodunuzu okutun."
}
```

**Önemli Notlar:**
- `loadingSessionId` verilmezse otomatik üretilir
- `scan_order` otomatik artar (1, 2, 3...)
- Aynı dolly iki kez okutulamaz (hata verir)

**Error Response (400):**
```json
{
  "error": "Dolly DL-123 zaten bu session'a eklenmiş",
  "retryable": true
}
```

**Error Response (500):**
```json
{
  "error": "Dolly okutma hatası: Database error. İşlem geri alındı, lütfen tekrar deneyin.",
  "retryable": true
}
```

---

### 5. Complete Loading (Yükleme Tamamlandı)

Tüm dolly'ler TIR'a yüklendi, operatör "Tamamlandı" butonuna bastı.

**Endpoint:** `POST /forklift/complete-loading`

**Request Headers:**
```
Authorization: Bearer <sessionToken>
Content-Type: application/json
```

**Request Body:**
```json
{
  "loadingSessionId": "LOAD_20251126_143052_MEHMET"
}
```

**Success Response (200 OK):**
```json
{
  "loadingSessionId": "LOAD_20251126_143052_MEHMET",
  "status": "loading_completed",
  "dollyCount": 15,
  "completedAt": "2025-11-26T15:45:00Z",
  "dollys": [
    {
      "dollyNo": "DL-5170427",
      "vinNo": "3FA6P0LU6FR100001",
      "scanOrder": 1
    },
    {
      "dollyNo": "DL-5170428",
      "vinNo": "3FA6P0LU6FR100002",
      "scanOrder": 2
    }
    // ... 15 dolly toplam
  ]
}
```

**Error Response (400):**
```json
{
  "error": "Session LOAD_999 bulunamadı veya zaten tamamlanmış",
  "retryable": true
}
```

**Error Response (500):**
```json
{
  "error": "Loading tamamlama hatası: Database connection failed. İşlem geri alındı, lütfen tekrar deneyin.",
  "retryable": true
}
```

**Kotlin Örnek:**
```kotlin
viewModel.viewModelScope.launch {
    viewModel.completeLoading(sessionId)
        .onSuccess { result ->
            showToast("${result.dollyCount} dolly yüklendi")
            navigateToHome()
        }
        .onFailure { error ->
            when (error) {
                is ValidationException -> {
                    if (error.retryable) {
                        showErrorDialog(error.message, retryButton = true)
                    }
                }
                is SystemException -> {
                    showRetryDialog("Sistem hatası: ${error.message}")
                }
            }
        }
}
```

---

### 6. Remove Last Dolly (Son Dolly'yi Çıkart) 🆕

**Özellik:** Yanlışlıkla okutulan son dolly'yi çıkarabilirsiniz.

**Kural:** ⚠️ **SADECE EN SON EKLENEN DOLLY çıkarılabilir!** (LIFO - Last In First Out)

**Endpoint:** `POST /forklift/remove-last`

**Request Headers:**
```
Authorization: Bearer <sessionToken>
Content-Type: application/json
```

**Request Body:**
```json
{
  "loadingSessionId": "LOAD_20251126_143052_MEHMET",
  "dollyBarcode": "BARCODE123"  // Doğrulama için dolly barkodu
}
```

**Success Response (200 OK):**
```json
{
  "dollyNo": "DL-5170427",
  "vinNo": "3FA6P0LU6FR100001",
  "scanOrder": 15,
  "removedAt": "2025-11-26T15:50:00Z"
}
```

**Error Response (400 - Not Last Dolly):**
```json
{
  "error": "Sadece en son eklenen dolly çıkarılabilir. En son: Sıra 15, Seçilen: Sıra 10",
  "retryable": true
}
```

**Error Response (400 - Not Found):**
```json
{
  "error": "Dolly DL-123 bu session'da bulunamadı veya zaten çıkarılmış",
  "retryable": true
}
```

**Error Response (500 - System Error):**
```json
{
  "error": "Dolly çıkarma hatası: Transaction timeout. İşlem geri alındı, lütfen tekrar deneyin.",
  "retryable": true
}
```

**Kullanım (Kotlin):**
```kotlin
data class RemoveDollyRequest(
    val loadingSessionId: String,
    val dollyBarcode: String
)

data class RemoveDollyResponse(
    val dollyNo: String,
    val vinNo: String,
    val scanOrder: Int,
    val removedAt: String
)

suspend fun removeLastDolly(
    sessionId: String,
    barcode: String
): Result<RemoveDollyResponse> {
    return try {
        val response = httpClient.post("$BASE_URL/forklift/remove-last") {
            header("Authorization", "Bearer ${tokenManager.getToken()}")
            contentType(ContentType.Application.Json)
            setBody(RemoveDollyRequest(
                loadingSessionId = sessionId,
                dollyBarcode = barcode
            ))
        }
        
        when (response.status) {
            HttpStatusCode.OK -> {
                Result.success(response.body())
            }
            HttpStatusCode.BadRequest -> {
                val error: ApiError = response.body()
                Result.failure(ValidationException(error.error, error.retryable))
            }
            HttpStatusCode.InternalServerError -> {
                val error: ApiError = response.body()
                Result.failure(SystemException(error.error, error.retryable))
            }
            else -> {
                Result.failure(Exception("Unknown error: ${response.status}"))
            }
        }
    } catch (e: Exception) {
        Result.failure(NetworkException("Network error: ${e.message}"))
    }
}
```

**UI Örnek (Compose):**
```kotlin
@Composable
fun ScanningScreen(viewModel: ForkliftViewModel) {
    Column {
        // ... dolly listesi
        
        Row(
            modifier = Modifier.fillMaxWidth().padding(16.dp),
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Button(
                onClick = {
                    viewModel.viewModelScope.launch {
                        // Scan barcode
                        val barcode = scanBarcode()
                        
                        viewModel.removeLastDolly(
                            sessionId = currentSessionId,
                            barcode = barcode
                        ).onSuccess { removed ->
                            showToast("Çıkarıldı: ${removed.dollyNo}")
                            refreshSessionList()
                        }.onFailure { error ->
                            when (error) {
                                is ValidationException -> {
                                    showErrorDialog(
                                        title = "Uyarı",
                                        message = error.message,
                                        retryButton = error.retryable
                                    )
                                }
                                is SystemException -> {
                                    showRetryDialog(
                                        message = error.message,
                                        onRetry = { /* retry */ }
                                    )
                                }
                            }
                        }
                    }
                },
                colors = ButtonDefaults.buttonColors(
                    containerColor = MaterialTheme.colorScheme.error
                )
            ) {
                Icon(Icons.Default.Delete, "Çıkar")
                Text("Son Dolly'yi Çıkar")
            }
            
            Button(
                onClick = { viewModel.completeLoading(currentSessionId) }
            ) {
                Icon(Icons.Default.Check, "Tamamla")
                Text("Yükleme Tamamlandı")
            }
        }
    }
}
```

**Not:** 
- ✅ Sadece en son eklenen dolly çıkarılabilir
- ✅ Barkod doğrulaması yapılır (yanlış dolly çıkarılmasın)
- ✅ Hata durumunda transaction rollback yapılır (veri kaybı olmaz)
- ✅ Lifecycle durumu geri alınır

---

### 7. List Loading Sessions (Oturumları Listele)

Aktif veya tamamlanmış yükleme oturumlarını listeler.

**Endpoint:** `GET /forklift/sessions?status=scanned`

**Request Headers:**
```
Authorization: Bearer <sessionToken>
```

**Query Parameters:**
- `status` (optional): `scanned` | `loading_completed` | `completed`

**Success Response (200 OK):**
```json
[
  {
    "loadingSessionId": "LOAD_20251126_143052_MEHMET",
    "status": "scanned",
    "forkliftUser": "Mehmet Yılmaz",
    "dollyCount": 8,
    "firstScanAt": "2025-11-26T14:30:52Z",
    "completedAt": null
  },
  {
    "loadingSessionId": "LOAD_20251126_100000_ALI",
    "status": "loading_completed",
    "forkliftUser": "Ali Demir",
    "dollyCount": 12,
    "firstScanAt": "2025-11-26T10:00:00Z",
    "completedAt": "2025-11-26T11:15:00Z"
  }
]
```

---

## 🚨 Error Handling (Hata Yönetimi)

### Standart Error Format

Tüm endpoint'ler aynı hata formatını kullanır:

```json
{
  "error": "Kullanıcıya gösterilecek hata mesajı",
  "message": "Teknik detay (opsiyonel)",
  "retryable": true  // true = Tekrar denenebilir, false = Tekrar denenmemeli
}
```

### Error Types

#### 1. Validation Errors (400) - Retryable ✅

**Sebep:** Kullanıcı girişi hatalı

**Örnekler:**
```json
{"error": "dollyNo is required", "retryable": true}
{"error": "Geçersiz sefer numarası formatı: XYZ. Örnek: SFR20250001", "retryable": true}
{"error": "Sadece en son eklenen dolly çıkarılabilir", "retryable": true}
```

**Kotlin Handling:**
```kotlin
if (response.status == HttpStatusCode.BadRequest) {
    val error: ApiError = response.body()
    if (error.retryable) {
        showErrorDialog(
            message = error.error,
            positiveButton = "Tekrar Dene"
        )
    }
}
```

#### 2. Authentication Errors (401) - Not Retryable ❌

**Sebep:** Token geçersiz veya expire olmuş

**Handling:**
```kotlin
if (response.status == HttpStatusCode.Unauthorized) {
    tokenManager.clearToken()
    navController.navigate("login") {
        popUpTo(0)  // Clear back stack
    }
}
```

#### 3. System Errors (500) - Retryable ✅

**Sebep:** Database, network veya sistem hatası

**Örnekler:**
```json
{
  "error": "Dolly çıkarma hatası: Database connection timeout. İşlem geri alındı, lütfen tekrar deneyin.",
  "retryable": true
}
```

**Önemli:** Transaction otomatik rollback edilir, veri tutarlılığı korunur!

**Kotlin Handling:**
```kotlin
if (response.status == HttpStatusCode.InternalServerError) {
    val error: ApiError = response.body()
    if (error.retryable) {
        showRetryDialog(
            message = error.error,
            onRetry = { retryLastOperation() }
        )
    }
}
```

### Exception Classes

```kotlin
data class ApiError(
    val error: String,
    val message: String? = null,
    val retryable: Boolean = true
)

sealed class ApiException(message: String, val retryable: Boolean = true) : Exception(message) {
    class ValidationException(message: String, retryable: Boolean = true) : ApiException(message, retryable)
    class AuthenticationException(message: String) : ApiException(message, retryable = false)
    class SystemException(message: String, retryable: Boolean = true) : ApiException(message, retryable)
    class NetworkException(message: String) : ApiException(message, retryable = true)
}
```

### Safe API Call Wrapper

```kotlin
class ApiClient(private val httpClient: HttpClient) {
    
    suspend inline fun <reified T> safeApiCall(
        crossinline call: suspend () -> HttpResponse
    ): Result<T> {
        return try {
            val response = call()
            
            when (response.status) {
                HttpStatusCode.OK, HttpStatusCode.Created -> {
                    Result.success(response.body())
                }
                HttpStatusCode.BadRequest -> {
                    val error: ApiError = response.body()
                    Result.failure(
                        ApiException.ValidationException(error.error, error.retryable)
                    )
                }
                HttpStatusCode.Unauthorized -> {
                    Result.failure(
                        ApiException.AuthenticationException("Session expired")
                    )
                }
                HttpStatusCode.InternalServerError -> {
                    val error: ApiError = response.body()
                    Result.failure(
                        ApiException.SystemException(error.error, error.retryable)
                    )
                }
                else -> {
                    Result.failure(Exception("Unknown error: ${response.status}"))
                }
            }
        } catch (e: Exception) {
            Result.failure(
                ApiException.NetworkException("Network error: ${e.message}")
            )
        }
    }
}

// Usage
apiClient.safeApiCall<ScanResponse> {
    httpClient.post("/api/forklift/scan") {
        header("Authorization", "Bearer $token")
        setBody(scanRequest)
    }
}.onSuccess { scan ->
    updateUI(scan)
}.onFailure { error ->
    handleError(error)
}
```

### Retry Strategy

```kotlin
class RetryHandler {
    suspend fun <T> retryWithBackoff(
        maxRetries: Int = 3,
        initialDelay: Long = 1000,
        maxDelay: Long = 10000,
        factor: Double = 2.0,
        block: suspend () -> Result<T>
    ): Result<T> {
        var currentDelay = initialDelay
        
        repeat(maxRetries) { attempt ->
            val result = block()
            
            if (result.isSuccess) {
                return result
            }
            
            // Check if retryable
            val error = result.exceptionOrNull()
            when (error) {
                is ApiException.ValidationException -> {
                    if (!error.retryable) return result
                }
                is ApiException.AuthenticationException -> {
                    return result  // Don't retry auth errors
                }
            }
            
            if (attempt < maxRetries - 1) {
                delay(currentDelay)
                currentDelay = (currentDelay * factor).toLong().coerceAtMost(maxDelay)
            }
        }
        
        return block()  // Last attempt
    }
}

// Usage
retryHandler.retryWithBackoff {
    apiClient.scanDolly(dollyNo)
}
```

### Local Backup (Data Loss Prevention)

```kotlin
class LocalBackupManager(context: Context) {
    private val prefs = context.getSharedPreferences("backup", MODE_PRIVATE)
    
    fun backupSession(session: LoadingSession) {
        val json = Json.encodeToString(session)
        prefs.edit()
            .putString("last_session", json)
            .putLong("backup_timestamp", System.currentTimeMillis())
            .apply()
    }
    
    fun restoreLastSession(): LoadingSession? {
        val json = prefs.getString("last_session", null) ?: return null
        return try {
            Json.decodeFromString(json)
        } catch (e: Exception) {
            null
        }
    }
    
    fun clearBackup() {
        prefs.edit().remove("last_session").apply()
    }
}

// Usage in ViewModel
fun completeLoading(sessionId: String) {
    viewModelScope.launch {
        // Backup before critical operation
        backupManager.backupSession(currentSession)
        
        apiClient.completeLoading(sessionId)
            .onSuccess { 
                backupManager.clearBackup()
                navigateToHome()
            }
            .onFailure { error ->
                if (error is ApiException.SystemException && !error.retryable) {
                    // Restore from backup on critical error
                    val restored = backupManager.restoreLastSession()
                    if (restored != null) {
                        showDialog("Veriler geri yüklendi")
                    }
                }
            }
    }
}
```

### Error Dialog Component

```kotlin
@Composable
fun ErrorDialog(
    error: ApiError,
    onDismiss: () -> Unit,
    onRetry: (() -> Unit)? = null
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(
                    Icons.Default.Warning,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.error
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text("Hata")
            }
        },
        text = { Text(error.error) },
        confirmButton = {
            if (error.retryable && onRetry != null) {
                Button(onClick = {
                    onDismiss()
                    onRetry()
                }) {
                    Text("Tekrar Dene")
                }
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Kapat")
            }
        }
    )
}
```

### Best Practices

**✅ Do's:**
1. Her API çağrısını try-catch içinde yap
2. Error response'u kontrol et ve `retryable` flag'ine göre aksiyon al
3. Kritik işlemleri local'de backup'la
4. Tüm hataları log'la (Firebase Crashlytics)
5. Kullanıcıya anlaşılır mesajlar göster

**❌ Don'ts:**
1. Hataları görmezden gelme
2. Stack trace'i kullanıcıya gösterme
3. `retryable: false` olan hataları retry etme
4. Token expire olunca tekrar tekrar API çağırma
5. Validation'sız form gönderme

**Daha fazla bilgi için:** `docs/ERROR_HANDLING_GUIDE.md`

---

## 🔍 Diğer Endpoint'ler

### 8. Health Check

Sunucunun çalışıp çalışmadığını kontrol eder.

**Endpoint:** `GET /health`

**Response (200 OK):**
```json
{
  "status": "ok",
  "app": "HarmonyEcoSystem"
}
```

---

## 📱 Android Uygulama Örneği (Kotlin)

### MainActivity.kt

```kotlin
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.runtime.*
import androidx.lifecycle.viewmodel.compose.viewModel
import com.google.mlkit.vision.barcode.BarcodeScanning
import com.google.mlkit.vision.common.InputImage

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            ForkliftApp()
        }
    }
}

@Composable
fun ForkliftApp() {
    val viewModel: ForkliftViewModel = viewModel()
    val uiState by viewModel.uiState.collectAsState()
    
    when {
        uiState.sessionToken == null -> LoginScreen(viewModel)
        uiState.currentSession == null -> HomeScreen(viewModel)
        else -> ScanningScreen(viewModel)
    }
}

@Composable
fun LoginScreen(viewModel: ForkliftViewModel) {
    Column(
        modifier = Modifier.fillMaxSize(),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text("Barkodunuzu Okutun", style = MaterialTheme.typography.h4)
        Spacer(modifier = Modifier.height(32.dp))
        
        BarcodeScanner { barcode ->
            viewModel.login(barcode)
        }
        
        if (uiState.isLoading) {
            CircularProgressIndicator()
        }
        
        uiState.error?.let { error ->
            Text(error, color = Color.Red)
        }
    }
}

@Composable
fun ScanningScreen(viewModel: ForkliftViewModel) {
    Column(modifier = Modifier.fillMaxSize()) {
        TopAppBar(
            title = { Text("Yükleme: ${uiState.scannedDollys.size} dolly") },
            actions = {
                IconButton(onClick = { viewModel.logout() }) {
                    Icon(Icons.Default.ExitToApp, "Çıkış")
                }
            }
        )
        
        Box(modifier = Modifier.weight(1f)) {
            BarcodeScanner { dollyNo ->
                viewModel.scanDolly(dollyNo)
            }
        }
        
        LazyColumn(modifier = Modifier.weight(1f)) {
            items(uiState.scannedDollys) { dolly ->
                DollyItem(dolly)
            }
        }
        
        Button(
            onClick = { viewModel.completeLoading() },
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            enabled = uiState.scannedDollys.isNotEmpty()
        ) {
            Text("YÜKLEME TAMAMLANDI")
        }
    }
}
```

### ForkliftViewModel.kt

```kotlin
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter

data class UiState(
    val sessionToken: String? = null,
    val operatorName: String? = null,
    val currentSession: String? = null,
    val scannedDollys: List<ScannedDolly> = emptyList(),
    val isLoading: Boolean = false,
    val error: String? = null
)

data class ScannedDolly(
    val dollyNo: String,
    val vinNo: String,
    val scanOrder: Int,
    val scannedAt: String
)

class ForkliftViewModel : ViewModel() {
    private val _uiState = MutableStateFlow(UiState())
    val uiState = _uiState.asStateFlow()
    
    private val apiService = ForkliftApiService()
    
    fun login(barcode: String) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)
            
            try {
                val response = apiService.login(barcode)
                if (response.success) {
                    _uiState.value = _uiState.value.copy(
                        sessionToken = response.sessionToken,
                        operatorName = response.operatorName,
                        isLoading = false
                    )
                    
                    // Start new session
                    startNewSession()
                } else {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        error = response.message
                    )
                }
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = "Bağlantı hatası: ${e.message}"
                )
            }
        }
    }
    
    private fun startNewSession() {
        val timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss"))
        val operatorName = _uiState.value.operatorName?.replace(" ", "_") ?: "UNKNOWN"
        val sessionId = "LOAD_${timestamp}_${operatorName}"
        
        _uiState.value = _uiState.value.copy(
            currentSession = sessionId,
            scannedDollys = emptyList()
        )
    }
    
    fun scanDolly(dollyNo: String) {
        val sessionToken = _uiState.value.sessionToken ?: return
        val sessionId = _uiState.value.currentSession ?: return
        
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)
            
            try {
                val response = apiService.scanDolly(
                    sessionToken = sessionToken,
                    dollyNo = dollyNo,
                    sessionId = sessionId
                )
                
                val newDolly = ScannedDolly(
                    dollyNo = response.dolly_no,
                    vinNo = response.vin_no,
                    scanOrder = response.scan_order,
                    scannedAt = response.scanned_at
                )
                
                _uiState.value = _uiState.value.copy(
                    scannedDollys = _uiState.value.scannedDollys + newDolly,
                    isLoading = false
                )
                
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = "Okutma hatası: ${e.message}"
                )
            }
        }
    }
    
    fun completeLoading() {
        val sessionToken = _uiState.value.sessionToken ?: return
        val sessionId = _uiState.value.currentSession ?: return
        
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)
            
            try {
                val response = apiService.completeLoading(
                    sessionToken = sessionToken,
                    sessionId = sessionId
                )
                
                // Success - reset to home
                _uiState.value = _uiState.value.copy(
                    currentSession = null,
                    scannedDollys = emptyList(),
                    isLoading = false
                )
                
                // Show success message
                
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = "Tamamlama hatası: ${e.message}"
                )
            }
        }
    }
    
    fun logout() {
        val sessionToken = _uiState.value.sessionToken ?: return
        
        viewModelScope.launch {
            try {
                apiService.logout(sessionToken)
            } finally {
                _uiState.value = UiState()  // Reset
            }
        }
    }
}
```

### ForkliftApiService.kt

```kotlin
import io.ktor.client.*
import io.ktor.client.call.*
import io.ktor.client.engine.android.*
import io.ktor.client.plugins.contentnegotiation.*
import io.ktor.client.request.*
import io.ktor.http.*
import io.ktor.serialization.kotlinx.json.*
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json

class ForkliftApiService {
    private val baseUrl = "http://10.25.1.174:8181/api"
    
    private val client = HttpClient(Android) {
        install(ContentNegotiation) {
            json(Json {
                ignoreUnknownKeys = true
                isLenient = true
            })
        }
    }
    
    @Serializable
    data class LoginRequest(
        val operatorBarcode: String,
        val operatorName: String? = null,
        val deviceId: String? = null
    )
    
    @Serializable
    data class LoginResponse(
        val success: Boolean,
        val sessionToken: String? = null,
        val operatorName: String? = null,
        val operatorBarcode: String? = null,
        val expiresAt: String? = null,
        val message: String
    )
    
    @Serializable
    data class ScanRequest(
        val dollyNo: String,
        val loadingSessionId: String,
        val barcode: String? = null
    )
    
    @Serializable
    data class ScanResponse(
        val id: Int,
        val dolly_no: String,
        val vin_no: String,
        val status: String,
        val terminal_user: String,
        val scanned_at: String,
        val scan_order: Int,
        val customer_referans: String? = null,
        val eol_name: String? = null
    )
    
    @Serializable
    data class CompleteRequest(
        val loadingSessionId: String
    )
    
    @Serializable
    data class CompleteResponse(
        val loadingSessionId: String,
        val status: String,
        val dollyCount: Int,
        val completedAt: String
    )
    
    suspend fun login(barcode: String, deviceId: String? = null): LoginResponse {
        return client.post("$baseUrl/forklift/login") {
            contentType(ContentType.Application.Json)
            setBody(LoginRequest(
                operatorBarcode = barcode,
                deviceId = deviceId
            ))
        }.body()
    }
    
    suspend fun scanDolly(
        sessionToken: String,
        dollyNo: String,
        sessionId: String
    ): ScanResponse {
        return client.post("$baseUrl/forklift/scan") {
            header("Authorization", "Bearer $sessionToken")
            contentType(ContentType.Application.Json)
            setBody(ScanRequest(
                dollyNo = dollyNo,
                loadingSessionId = sessionId
            ))
        }.body()
    }
    
    suspend fun completeLoading(
        sessionToken: String,
        sessionId: String
    ): CompleteResponse {
        return client.post("$baseUrl/forklift/complete-loading") {
            header("Authorization", "Bearer $sessionToken")
            contentType(ContentType.Application.Json)
            setBody(CompleteRequest(loadingSessionId = sessionId))
        }.body()
    }
    
    suspend fun logout(sessionToken: String) {
        client.post("$baseUrl/forklift/logout") {
            header("Authorization", "Bearer $sessionToken")
        }
    }
}
```

---

## 📊 Hata Kodları

| HTTP Kodu | Anlamı | Çözüm | Retryable |
|-----------|--------|-------|-----------|
| 200 | Başarılı | - | - |
| 201 | Kayıt oluşturuldu | - | - |
| 400 | Validation hatası | Kullanıcı düzeltsin, tekrar denesin | ✅ Yes |
| 401 | Token geçersiz | Login ekranına yönlendir | ❌ No |
| 404 | Bulunamadı | Dolly/session ID'yi kontrol et | ✅ Yes |
| 500 | Sunucu/Database hatası | Transaction rollback yapıldı, retry | ✅ Yes |

**Not:** Tüm error response'ları `{"error": "...", "retryable": true/false}` formatındadır.

---

## 🔒 Güvenlik Notları

1. **Token Saklama:** Shared Preferences veya Encrypted Storage kullan
2. **HTTPS:** Production'da mutlaka HTTPS kullan
3. **Token Expiry:** 8 saat sonra auto-logout
4. **Activity Tracking:** Her API çağrısı `LastActivityAt` günceller

---

## 🎯 Test Senaryoları

### Senaryo 1: Normal İş Akışı

```bash
# 1. Login
curl -X POST http://10.25.1.174:8181/api/forklift/login \
  -H "Content-Type: application/json" \
  -d '{"operatorBarcode":"EMP12345","operatorName":"Test User"}'

# 2. Dolly okut
curl -X POST http://10.25.1.174:8181/api/forklift/scan \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"dollyNo":"DL-5170427","loadingSessionId":"LOAD_TEST_001"}'

# 3. Tamamla
curl -X POST http://10.25.1.174:8181/api/forklift/complete-loading \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"loadingSessionId":"LOAD_TEST_001"}'

# 4. Logout
curl -X POST http://10.25.1.174:8181/api/forklift/logout \
  -H "Authorization: Bearer <token>"
```

### Senaryo 2: Yanlış Dolly Okutma ve Düzeltme 🆕

```bash
# 1. Login
curl -X POST http://10.25.1.174:8181/api/forklift/login \
  -H "Content-Type: application/json" \
  -d '{"operatorBarcode":"EMP12345"}'

# 2. İlk dolly okut
curl -X POST http://10.25.1.174:8181/api/forklift/scan \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"dollyNo":"DL-001","loadingSessionId":"LOAD_TEST_002"}'

# 3. İkinci dolly okut
curl -X POST http://10.25.1.174:8181/api/forklift/scan \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"dollyNo":"DL-002","loadingSessionId":"LOAD_TEST_002"}'

# 4. YANLIŞ dolly okuttuk, son dolly'yi çıkar
curl -X POST http://10.25.1.174:8181/api/forklift/remove-last \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"loadingSessionId":"LOAD_TEST_002","dollyBarcode":"BARCODE_002"}'

# 5. Doğru dolly okut
curl -X POST http://10.25.1.174:8181/api/forklift/scan \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"dollyNo":"DL-003","loadingSessionId":"LOAD_TEST_002"}'

# 6. Tamamla
curl -X POST http://10.25.1.174:8181/api/forklift/complete-loading \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"loadingSessionId":"LOAD_TEST_002"}'
```

### Senaryo 3: Error Handling Test 🆕

```bash
# Test 1: Validation Error (400)
curl -X POST http://10.25.1.174:8181/api/forklift/scan \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"loadingSessionId":"LOAD_123"}'
# Expected: {"error": "dollyNo is required", "retryable": true}

# Test 2: Authentication Error (401)
curl -X POST http://10.25.1.174:8181/api/forklift/scan \
  -H "Authorization: Bearer invalid_token" \
  -H "Content-Type: application/json" \
  -d '{"dollyNo":"DL-123","loadingSessionId":"LOAD_123"}'
# Expected: 401 Unauthorized → Navigate to login

# Test 3: Remove non-last dolly (400)
curl -X POST http://10.25.1.174:8181/api/forklift/remove-last \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"loadingSessionId":"LOAD_123","dollyBarcode":"WRONG_BARCODE"}'
# Expected: {"error": "Sadece en son eklenen dolly çıkarılabilir...", "retryable": true}
```

---

## 📞 Destek

**Dokümantasyon:**
- `docs/ERROR_HANDLING_GUIDE.md` - Detaylı error handling rehberi
- `docs/ANDROID_QUICK_REFERENCE.md` - Hızlı referans
- `docs/API_ENDPOINTS.md` - Tüm endpoint listesi

**Sorun olursa:**
1. Log'ları kontrol et (Logcat + Firebase Crashlytics)
2. Network connectivity test et
3. Error response'u kontrol et (`retryable` flag)
4. Local backup'tan restore et (kritik hatalar için)
5. Server admin'e ulaş: IT Departmanı

**Son Güncelleme:** 26 Kasım 2025

---

## 🎯 Özet: Yeni Özellikler

### ✅ Remove Last Dolly (Dolly Çıkartma)
- **Endpoint:** `POST /api/forklift/remove-last`
- **Kural:** Sadece en son eklenen dolly çıkartılabilir (LIFO)
- **Use Case:** Yanlışlıkla okutulan dolly'yi düzeltme

### ✅ Comprehensive Error Handling
- **Format:** `{"error": "...", "retryable": true/false}`
- **Types:** Validation (400), Auth (401), System (500)
- **Rollback:** Hata durumunda transaction otomatik geri alınır
- **Retry:** `retryable: true` olan hatalar tekrar denenebilir

### ✅ Data Loss Prevention
- **Backend:** Transaction rollback (ACID)
- **Android:** Local backup (SharedPreferences)
- **Logging:** AuditLog + Application log

### ✅ Best Practices
- Safe API call wrapper
- Retry with exponential backoff
- User-friendly error messages
- Firebase Crashlytics integration

