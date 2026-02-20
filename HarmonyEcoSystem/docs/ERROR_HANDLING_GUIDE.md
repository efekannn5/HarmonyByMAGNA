# 🚨 Error Handling & Recovery Guide

## Genel Bakış

Bu sistem **sıfır veri kaybı** prensibi ile tasarlanmıştır. Her hata durumunda:
1. ✅ Hata loglanır (AuditLog + Application Log)
2. ✅ Transaction rollback yapılır (database tutarlılığı)
3. ✅ Kullanıcıya anlaşılır hata mesajı gösterilir
4. ✅ Retry mekanizması devreye girer

---

## Error Response Format

Tüm API endpoint'leri standart hata formatı kullanır:

```json
{
  "error": "Kullanıcıya gösterilecek mesaj",
  "message": "Teknik detay (opsiyonel)",
  "retryable": true  // true = Tekrar denenebilir, false = Tekrar denenmemeli
}
```

---

## Error Types

### 1. Validation Errors (400) ✅ Retryable

**Sebep:** Kullanıcı girişi hatalı

**Örnekler:**
- "dollyNo is required"
- "Geçersiz sefer numarası formatı: XYZ. Örnek: SFR20250001"
- "Geçersiz plaka formatı: ABC. Örnek: 34 ABC 123"
- "Sefer numarası SFR123 daha önce kullanılmış"
- "Sadece en son eklenen dolly çıkarılabilir"

**Handling:**
```kotlin
if (response.status == 400) {
    val error: ApiError = response.body()
    showErrorDialog(
        message = error.error,
        retryButton = error.retryable  // true for validation errors
    )
}
```

### 2. System Errors (500) ✅ Retryable

**Sebep:** Sistem hatası (database, network, etc.)

**Örnekler:**
- "Dolly çıkarma hatası: Database connection failed. İşlem geri alındı, lütfen tekrar deneyin."
- "Sevkiyat tamamlama hatası: Transaction timeout. İşlem geri alındı, lütfen tekrar deneyin."

**Handling:**
```kotlin
if (response.status == 500) {
    val error: ApiError = response.body()
    if (error.retryable) {
        showRetryDialog(
            message = error.error,
            onRetry = { retryLastOperation() }
        )
    } else {
        showCriticalError(error.error)
    }
}
```

**Önemli:** Transaction otomatik rollback edilir, veri tutarlılığı korunur!

### 3. Authentication Errors (401) ❌ Not Retryable

**Sebep:** Token geçersiz veya expire olmuş

**Handling:**
```kotlin
if (response.status == 401) {
    tokenManager.clearToken()
    navigateToLogin()
}
```

---

## Transaction Rollback Mekanizması

### Backend Implementation

Her kritik işlem transaction içinde çalışır:

```python
# app/services/dolly_service.py
try:
    # Business logic
    hold.Status = "completed"
    sefer_record = SeferDollyEOL(...)
    db.session.add(sefer_record)
    
    # Commit
    db.session.commit()  # ✅ Başarılı
    
except ValueError:
    # Validation error - no rollback needed
    raise
    
except Exception as e:
    # System error - rollback all changes
    db.session.rollback()  # ✅ Tüm değişiklikler geri alınır
    
    # Log critical error
    self._log_critical_error("operator_complete_shipment", e, context)
    
    # Raise user-friendly error
    raise RuntimeError(
        f"Sevkiyat tamamlama hatası: {str(e)}. "
        "İşlem geri alındı, lütfen tekrar deneyin."
    )
```

**Sonuç:**
- ✅ Database tutarlılığı korunur
- ✅ Partial updates olmaz
- ✅ Tüm değişiklikler ya tamamen uygulanır ya da hiç uygulanmaz (ACID)

---

## Critical Error Logging

### Log Seviyesi

```python
def _log_critical_error(self, function_name: str, error: Exception, context: dict):
    error_details = {
        "function": function_name,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "traceback": traceback.format_exc(),
        "context": context,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # 1. AuditLog (database)
    self.audit.log(
        action="system.critical_error",
        resource="system",
        resource_id=function_name,
        actor_name="system",
        metadata=error_details
    )
    
    # 2. Application log (file)
    logger.critical(
        f"CRITICAL ERROR in {function_name}: {error}", 
        extra=error_details
    )
```

**Log Locations:**
- Database: `AuditLog` tablosu
- File: `logs/app.log`

---

## Android Client Error Handling

### 1. Safe API Call Wrapper

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
                    Result.failure(ValidationException(error.error, error.retryable))
                }
                HttpStatusCode.Unauthorized -> {
                    Result.failure(AuthenticationException("Session expired"))
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
}
```

### 2. Local Backup (Data Loss Prevention)

```kotlin
class LocalBackupManager(context: Context) {
    private val prefs = context.getSharedPreferences("backup", MODE_PRIVATE)
    
    fun backupLoadingSession(session: LoadingSession) {
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
}

// Usage
viewModelScope.launch {
    // Backup before critical operation
    backupManager.backupLoadingSession(currentSession)
    
    apiClient.completeLoading(sessionId)
        .onSuccess { 
            backupManager.clearBackup()
        }
        .onFailure { error ->
            if (!error.retryable) {
                // Restore on critical error
                val restored = backupManager.restoreLastSession()
                showDialog("Veriler geri yüklendi")
            }
        }
}
```

### 3. Retry Strategy

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
                is ValidationException -> {
                    if (!error.retryable) return result  // Don't retry
                }
                is AuthenticationException -> {
                    return result  // Don't retry, navigate to login
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

---

## Validation Rules

### Sefer Numarası

**Format:** 
- `SFR` + 4-10 digit (örn: `SFR20250001`)
- VEYA 5-20 karakter alphanumeric (örn: `SHIPMENT12345`)

```python
def validate_sefer_format(sefer: str) -> bool:
    import re
    pattern = r'^[A-Z]{2,5}\d{4,10}$|^[A-Z0-9]{5,20}$'
    return bool(re.match(pattern, sefer.strip().upper()))
```

```kotlin
fun validateSeferFormat(sefer: String): Boolean {
    val pattern1 = "^[A-Z]{2,5}\\d{4,10}$".toRegex()
    val pattern2 = "^[A-Z0-9]{5,20}$".toRegex()
    val normalized = sefer.trim().uppercase()
    return pattern1.matches(normalized) || pattern2.matches(normalized)
}
```

### Plaka

**Format:** Turkish license plate (örn: `34 ABC 123`, `34ABC123`)

```python
def validate_plaka_format(plaka: str) -> bool:
    import re
    normalized = plaka.strip().upper().replace(" ", "")
    pattern = r'^\d{2}[A-Z]{1,3}\d{2,5}$'
    return bool(re.match(pattern, normalized))
```

```kotlin
fun validatePlakaFormat(plaka: String): Boolean {
    val normalized = plaka.trim().uppercase().replace(" ", "")
    val pattern = "^\\d{2}[A-Z]{1,3}\\d{2,5}$".toRegex()
    return pattern.matches(normalized)
}
```

### Duplicate Sefer Check

```python
def check_duplicate_sefer(sefer: str) -> bool:
    existing = SeferDollyEOL.query.filter_by(SeferNumarasi=sefer).first()
    return existing is not None
```

---

## UI Error Display

### Error Dialog

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

---

## Best Practices

### ✅ Do's

1. **Her API çağrısını try-catch içinde yap**
```kotlin
viewModelScope.launch {
    try {
        apiClient.scanDolly(...)
    } catch (e: Exception) {
        handleError(e)
    }
}
```

2. **Error response'u kontrol et**
```kotlin
if (!response.isSuccess) {
    val error: ApiError = response.body()
    if (error.retryable) {
        showRetryDialog()
    }
}
```

3. **Kritik işlemleri backup'la**
```kotlin
backupManager.backupSession(currentSession)
apiClient.completeLoading(...)
```

4. **Tüm hataları log'la**
```kotlin
FirebaseCrashlytics.getInstance().recordException(error)
```

### ❌ Don'ts

1. **Hataları görmezden gelme**
```kotlin
// ❌ BAD
apiClient.scanDolly(...)  // No error handling

// ✅ GOOD
apiClient.scanDolly(...)
    .onFailure { handleError(it) }
```

2. **Stack trace'i kullanıcıya gösterme**
```kotlin
// ❌ BAD
showToast("Error: ${error.stackTrace}")

// ✅ GOOD
showDialog("İşlem başarısız. Lütfen tekrar deneyin.")
```

3. **retryable: false olan hataları retry etme**
```kotlin
// ❌ BAD
if (error != null) retry()

// ✅ GOOD
if (error?.retryable == true) retry()
```

---

## Test Scenarios

### 1. Validation Errors
- ✅ Invalid sefer format
- ✅ Invalid plaka format
- ✅ Duplicate sefer
- ✅ Remove non-last dolly

### 2. System Errors
- ✅ Database connection timeout
- ✅ Transaction deadlock
- ✅ Constraint violation

### 3. Network Errors
- ✅ Connection timeout
- ✅ Server unavailable
- ✅ DNS resolution failure

### 4. Authentication Errors
- ✅ Expired token
- ✅ Invalid token
- ✅ No token

---

## Monitoring & Alerts

### Critical Error Alerts

**Trigger:** `action = "system.critical_error"` in AuditLog

**Query:**
```sql
SELECT TOP 10
    CreatedAt,
    ResourceId AS FunctionName,
    Metadata
FROM AuditLog
WHERE Action = 'system.critical_error'
ORDER BY CreatedAt DESC
```

**Alert Rule:**
- 5+ critical errors in 10 minutes → Send email to IT
- 10+ critical errors in 1 hour → Call IT manager

---

## Recovery Procedures

### Scenario 1: Database Connection Lost

**Symptom:** Multiple 500 errors with "database connection" message

**Recovery:**
1. Check SQL Server status
2. Restart Flask application
3. Verify connection string in `config.yaml`
4. Test with `SELECT 1` query

### Scenario 2: Transaction Deadlock

**Symptom:** 500 errors with "transaction timeout"

**Recovery:**
1. Check long-running transactions in SQL Server
2. Kill blocking sessions if needed
3. Restart Flask application
4. Monitor for recurrence

### Scenario 3: Disk Space Full

**Symptom:** Logs not writing, database errors

**Recovery:**
1. Clean old log files in `logs/`
2. Archive old audit logs
3. Free disk space
4. Restart application

---

## Summary

| Error Type | HTTP Code | Retryable | Action |
|------------|-----------|-----------|--------|
| Validation | 400 | ✅ Yes | Show error, allow retry |
| Authentication | 401 | ❌ No | Navigate to login |
| System Error | 500 | ✅ Yes | Rollback + retry |
| Network Error | N/A | ✅ Yes | Retry with backoff |

**Core Principle:** 
> **Hiçbir işlem veri kaybına sebep olmamalı. Her hata durumunda transaction rollback ve retry mekanizması devreye girmelidir.**
