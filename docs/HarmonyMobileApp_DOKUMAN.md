# HarmonyMobileApp — Detaylı Teknik Döküman
# Android El Terminali Uygulaması

---

| Alan | Bilgi |
|------|-------|
| **Versiyon** | 1.0 |
| **Tarih** | 2026-02-21 |
| **Teknoloji** | Java, Android SDK 29-36, Retrofit 2.9 |
| **Minimum Android** | 8.0 (API 29) |
| **Hedef Kullanıcı** | Forklift Operatörleri |

---

## İçindekiler

1. [Proje Yapısı](#1-proje-yapısı)
2. [Bağımlılıklar](#2-bağımlılıklar)
3. [API Servisi](#3-api-servisi)
4. [Aktiviteler (Ekranlar)](#4-aktiviteler-ekranlar)
5. [Kimlik Doğrulama Akışı](#5-kimlik-doğrulama-akışı)
6. [Dolly Tarama Akışı](#6-dolly-tarama-akışı)
7. [Veri Modelleri](#7-veri-modelleri)
8. [Oturum Yönetimi](#8-oturum-yönetimi)
9. [Kiosk Modu](#9-kiosk-modu)
10. [Derleme ve Dağıtım](#10-derleme-ve-dağıtım)
11. [API Hata Yönetimi](#11-api-hata-yönetimi)

---

## 1. Proje Yapısı

```
ControlTower/
│
├── app/
│   ├── build.gradle.kts              # Uygulama bağımlılıkları
│   ├── proguard-rules.pro            # Release obfuscation kuralları
│   │
│   └── src/main/java/com/magna/controltower/
│       │
│       ├── BaseActivity.java         # Tüm aktivitelerin base sınıfı
│       ├── GroupActivity.java        # Ana ekran — grup/EOL listesi
│       ├── SessionManager.java       # JWT token yönetimi
│       ├── Prefs.java                # SharedPreferences yardımcısı
│       │
│       ├── api/
│       │   ├── ForkliftApiService.java    # Retrofit API arayüzü
│       │   └── models/
│       │       ├── LoginRequest.java
│       │       ├── LoginResponse.java
│       │       ├── ScanDollyRequest.java
│       │       ├── ManualScanRequest.java
│       │       ├── ManualScanResponse.java
│       │       ├── CompleteLoadingRequest.java
│       │       ├── CompleteLoadingResponse.java
│       │       ├── RemoveLastRequest.java
│       │       ├── ManualSubmitRequest.java
│       │       ├── ManualSubmitResponse.java
│       │       ├── GroupDollysResponse.java
│       │       ├── GroupDolly.java
│       │       ├── EOLInfo.java
│       │       ├── EOLGroup.java
│       │       ├── EOLGroupStatus.java
│       │       ├── EOLStatusResponse.java
│       │       ├── EOLDollysResponse.java
│       │       ├── DollyHoldEntry.java
│       │       ├── ForkliftTelemetryRequest.java
│       │       ├── ForkliftTelemetryResponse.java
│       │       └── ApiError.java
│       │
│       └── model/
│           ├── DollyHold.java        # Dolly tutma modeli
│           ├── GroupData.java        # Grup veri modeli
│           ├── KasaItem.java         # Kasa öğe modeli
│           └── LoadingSession.java   # Yükleme oturumu modeli
│
├── build.gradle.kts                  # Proje yapılandırması
├── settings.gradle.kts               # Proje ayarları
├── setup_kiosk.sh                    # Kiosk modu kurulum scripti
├── check_kiosk.sh                    # Kiosk durum kontrol scripti
└── docs/                             # Android dokümantasyon
```

---

## 2. Bağımlılıklar

### 2.1 app/build.gradle.kts

```kotlin
android {
    namespace = "com.magna.controltower"
    compileSdk = 36
    
    defaultConfig {
        applicationId = "com.magna.controltower"
        minSdk = 29           // Android 10 (Honeywell cihazlar için)
        targetSdk = 36
        versionCode = 1
        versionName = "1.0"
    }
}

dependencies {
    // HTTP İstemcisi
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("com.squareup.okhttp3:logging-interceptor:4.12.0")
    
    // REST API İstemcisi
    implementation("com.squareup.retrofit2:retrofit:2.9.0")
    implementation("com.squareup.retrofit2:converter-gson:2.9.0")
    
    // JSON İşleme
    implementation("com.google.code.gson:gson:2.10.1")
    
    // Konum Servisleri
    implementation("com.google.android.gms:play-services-location:21.2.0")
    
    // Android UI
    implementation(libs.appcompat)
    implementation(libs.material)
    implementation(libs.activity)
    implementation(libs.constraintlayout)
}
```

---

## 3. API Servisi

### 3.1 ForkliftApiService.java

```java
// api/ForkliftApiService.java

public interface ForkliftApiService {

    // ===== KİMLİK DOĞRULAMA =====
    
    @POST("forklift/login")
    Call<LoginResponse> login(@Body LoginRequest request);
    
    @POST("forklift/logout")
    Call<Void> logout(@Header("Authorization") String token);
    
    @GET("forklift/session/validate")
    Call<LoginResponse> validateSession(@Header("Authorization") String token);
    
    // ===== FORKLIFT İŞLEMLERİ =====
    
    @POST("forklift/scan")
    Call<ManualScanResponse> scanDolly(
        @Header("Authorization") String token,
        @Body ScanDollyRequest request
    );
    
    @POST("forklift/complete-loading")
    Call<CompleteLoadingResponse> completeLoading(
        @Header("Authorization") String token,
        @Body CompleteLoadingRequest request
    );
    
    @POST("forklift/remove-last")
    Call<ManualScanResponse> removeLastDolly(
        @Header("Authorization") String token,
        @Body RemoveLastRequest request
    );
    
    @GET("forklift/sessions")
    Call<List<LoadingSession>> getSessions(
        @Header("Authorization") String token,
        @Query("status") String status
    );
    
    // ===== GRUP YÖNETİMİ =====
    
    @GET("manual-collection/groups")
    Call<List<EOLGroup>> getManualCollectionGroups(
        @Header("Authorization") String token
    );
    
    @GET("manual-collection/groups/{groupId}/eols/{eolId}")
    Call<EOLDollysResponse> getEolDollys(
        @Header("Authorization") String token,
        @Path("groupId") int groupId,
        @Path("eolId") int eolId
    );
    
    // ===== SAĞLIK KONTROLÜ =====
    
    @GET("health")
    Call<Map<String, String>> healthCheck();
}
```

### 3.2 Retrofit İstemcisi Oluşturma

```java
// SessionManager.java içinde Retrofit kurulumu

public class SessionManager {
    private static final String BASE_URL = "http://10.25.1.174:8181/api/";
    // ÜRETİM: BASE_URL'i config'den oku ya da BuildConfig kullan
    
    private static Retrofit retrofit;
    private static ForkliftApiService apiService;
    
    public static ForkliftApiService getApiService() {
        if (apiService == null) {
            OkHttpClient client = new OkHttpClient.Builder()
                .connectTimeout(30, TimeUnit.SECONDS)
                .readTimeout(60, TimeUnit.SECONDS)
                .writeTimeout(30, TimeUnit.SECONDS)
                .addInterceptor(new HttpLoggingInterceptor()
                    .setLevel(HttpLoggingInterceptor.Level.BODY))  // Debug için
                .build();
            
            retrofit = new Retrofit.Builder()
                .baseUrl(BASE_URL)
                .client(client)
                .addConverterFactory(GsonConverterFactory.create())
                .build();
            
            apiService = retrofit.create(ForkliftApiService.class);
        }
        return apiService;
    }
}
```

---

## 4. Aktiviteler (Ekranlar)

### 4.1 BaseActivity — Temel Aktivite

```java
// BaseActivity.java
public abstract class BaseActivity extends AppCompatActivity {
    
    protected SessionManager sessionManager;
    protected ForkliftApiService apiService;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        sessionManager = new SessionManager(this);
        apiService = SessionManager.getApiService();
    }
    
    // Tüm aktivitelerde kullanılabilecek ortak metotlar
    protected String getAuthHeader() {
        return "Bearer " + sessionManager.getToken();
    }
    
    protected void handleUnauthorized() {
        sessionManager.clearSession();
        Intent intent = new Intent(this, LoginActivity.class);
        intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
        startActivity(intent);
    }
    
    protected void showError(String message) {
        Toast.makeText(this, message, Toast.LENGTH_LONG).show();
    }
    
    protected void showSuccess(String message) {
        Toast.makeText(this, message, Toast.LENGTH_SHORT).show();
    }
}
```

### 4.2 GroupActivity — Ana Ekran

Ana iş akışı ekranıdır. Operatör grup ve EOL listesini görür, dolly taraması yapar.

```java
// GroupActivity.java
public class GroupActivity extends BaseActivity {
    
    private String currentLoadingSessionId;
    private String currentGroupId;
    private int scanCount = 0;
    
    // Dolly barkodunu oku
    private void onBarcodeScanned(String barcode) {
        ScanDollyRequest request = new ScanDollyRequest();
        request.setBarcode(barcode);
        request.setLoadingSessionId(currentLoadingSessionId);
        
        apiService.scanDolly(getAuthHeader(), request).enqueue(new Callback<ManualScanResponse>() {
            @Override
            public void onResponse(Call<ManualScanResponse> call, Response<ManualScanResponse> response) {
                if (response.isSuccessful() && response.body() != null) {
                    scanCount++;
                    updateScanCounter();
                    showSuccess("Dolly " + response.body().getDollyNo() + " tarandı (#" + scanCount + ")");
                } else if (response.code() == 401) {
                    handleUnauthorized();
                } else {
                    handleApiError(response);
                }
            }
            
            @Override
            public void onFailure(Call<ManualScanResponse> call, Throwable t) {
                showError("Ağ hatası: " + t.getMessage());
            }
        });
    }
    
    // Yükleme tamamla
    private void onCompleteLoading() {
        CompleteLoadingRequest request = new CompleteLoadingRequest();
        request.setLoadingSessionId(currentLoadingSessionId);
        
        apiService.completeLoading(getAuthHeader(), request).enqueue(new Callback<CompleteLoadingResponse>() {
            @Override
            public void onResponse(Call<CompleteLoadingResponse> call, Response<CompleteLoadingResponse> response) {
                if (response.isSuccessful()) {
                    int dollyCount = response.body().getDollyCount();
                    showCompletionDialog(dollyCount);
                }
            }
            
            @Override
            public void onFailure(Call<CompleteLoadingResponse> call, Throwable t) {
                showError("Bağlantı hatası, tekrar deneyin");
            }
        });
    }
}
```

---

## 5. Kimlik Doğrulama Akışı

### 5.1 Giriş Akışı

```
Uygulama Başlar
        │
        ▼
Token Mevcut? ──── Hayır ──► Giriş Ekranı
        │                         │
       Evet                       │ Barkod Okut
        │                         ▼
        ▼                    POST /api/forklift/login
Token Geçerli? ──── Hayır ──► Giriş Ekranı
        │
       Evet
        │
        ▼
Ana Ekran (GroupActivity)
```

### 5.2 Login İsteği

```java
// LoginActivity.java içinde

private void performLogin(String barcode) {
    LoginRequest request = new LoginRequest();
    request.setOperatorBarcode(barcode);
    request.setDeviceId(getDeviceId());
    
    apiService.login(request).enqueue(new Callback<LoginResponse>() {
        @Override
        public void onResponse(Call<LoginResponse> call, Response<LoginResponse> response) {
            if (response.isSuccessful() && response.body() != null) {
                LoginResponse loginData = response.body();
                
                // Token'ı kaydet
                sessionManager.saveSession(
                    loginData.getSessionToken(),
                    loginData.getOperatorName(),
                    loginData.getExpiresAt()
                );
                
                // Ana ekrana geç
                Intent intent = new Intent(LoginActivity.this, GroupActivity.class);
                startActivity(intent);
                finish();
                
            } else {
                showError("Geçersiz barkod. Tekrar deneyin.");
            }
        }
        
        @Override
        public void onFailure(Call<LoginResponse> call, Throwable t) {
            showError("Sunucuya bağlanılamıyor. Ağ bağlantısını kontrol edin.");
        }
    });
}
```

---

## 6. Dolly Tarama Akışı

### 6.1 Tam Tarama Akışı

```
1. Operatör grubu seçer
        │
        ▼
2. GET /api/manual-collection/groups
        │
        ▼
3. Operatör EOL istasyonunu seçer
        │
        ▼
4. GET /api/manual-collection/groups/{gid}/eols/{eid}
   → Dolly listesi görüntülenir
        │
        ▼
5. Operatör dolly barkodunu okutur
        │
        ▼
6. POST /api/forklift/scan
   → ScanOrder: 1, 2, 3... artar
        │
        ▼
7. Yanlış tarama? → POST /api/forklift/remove-last
        │
        ▼
8. Tüm dolly'ler tarandı
        │
        ▼
9. "Yükleme Tamamlandı" butonu
        │
        ▼
10. POST /api/forklift/complete-loading
    → Web Operatöre bildirim gider
```

### 6.2 Loading Session ID Oluşturma

```java
// GroupActivity.java
private String generateLoadingSessionId() {
    String operatorName = sessionManager.getOperatorName()
        .toUpperCase()
        .replaceAll("\\s+", "_")
        .replaceAll("[^A-Z0-9_]", "");
    
    String dateStr = new SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US)
        .format(new Date());
    
    return "LOAD_" + dateStr + "_" + operatorName;
    // Örnek: LOAD_20251126_143022_MEHMET_YILMAZ
}
```

---

## 7. Veri Modelleri

### 7.1 LoginRequest.java

```java
public class LoginRequest {
    @SerializedName("operatorBarcode")
    private String operatorBarcode;
    
    @SerializedName("deviceId")
    private String deviceId;
    
    @SerializedName("operatorName")
    private String operatorName;  // Opsiyonel
    
    // Getter/setter'lar
}
```

### 7.2 LoginResponse.java

```java
public class LoginResponse {
    @SerializedName("success")
    private boolean success;
    
    @SerializedName("sessionToken")
    private String sessionToken;
    
    @SerializedName("operatorName")
    private String operatorName;
    
    @SerializedName("operatorBarcode")
    private String operatorBarcode;
    
    @SerializedName("expiresAt")
    private String expiresAt;
    
    @SerializedName("isAdmin")
    private boolean isAdmin;
    
    @SerializedName("role")
    private String role;
    
    // Getter/setter'lar
}
```

### 7.3 ScanDollyRequest.java

```java
public class ScanDollyRequest {
    @SerializedName("dollyNo")
    private String dollyNo;
    
    @SerializedName("loadingSessionId")
    private String loadingSessionId;
    
    @SerializedName("barcode")
    private String barcode;
    
    // Getter/setter'lar
}
```

### 7.4 ApiError.java

```java
public class ApiError {
    @SerializedName("error")
    private String error;         // Kullanıcıya gösterilecek mesaj
    
    @SerializedName("message")
    private String message;       // Teknik detay
    
    @SerializedName("retryable")
    private boolean retryable;    // Yeniden denenebilir mi?
    
    // Getter'lar
}
```

---

## 8. Oturum Yönetimi

### 8.1 SessionManager.java

```java
// SessionManager.java
public class SessionManager {
    
    private static final String PREF_NAME = "harmony_prefs";
    private static final String KEY_TOKEN = "session_token";
    private static final String KEY_OPERATOR_NAME = "operator_name";
    private static final String KEY_EXPIRES_AT = "expires_at";
    
    private final SharedPreferences prefs;
    
    public SessionManager(Context context) {
        prefs = context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE);
    }
    
    public void saveSession(String token, String operatorName, String expiresAt) {
        prefs.edit()
            .putString(KEY_TOKEN, token)
            .putString(KEY_OPERATOR_NAME, operatorName)
            .putString(KEY_EXPIRES_AT, expiresAt)
            .apply();
    }
    
    public String getToken() {
        return prefs.getString(KEY_TOKEN, null);
    }
    
    public String getOperatorName() {
        return prefs.getString(KEY_OPERATOR_NAME, "");
    }
    
    public boolean hasActiveSession() {
        String token = getToken();
        String expiresAt = prefs.getString(KEY_EXPIRES_AT, null);
        
        if (token == null || expiresAt == null) return false;
        
        try {
            // ISO 8601 formatını parse et
            SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'", Locale.US);
            sdf.setTimeZone(TimeZone.getTimeZone("UTC"));
            Date expiry = sdf.parse(expiresAt);
            return expiry != null && expiry.after(new Date());
        } catch (Exception e) {
            return false;
        }
    }
    
    public void clearSession() {
        prefs.edit().clear().apply();
    }
}
```

---

## 9. Kiosk Modu

### 9.1 Genel Bakış

Kiosk modu, cihazın yalnızca HarmonyMobileApp'i çalıştırmasını sağlar. Operatör uygulamadan çıkamaz veya başka uygulamalara geçemez.

### 9.2 Kiosk Kurulum Adımları

```bash
# 1. Cihazı bilgisayara USB ile bağlayın
# 2. ADB'yi etkinleştirin

# Kiosk modunu etkinleştir
adb shell dpm set-device-owner com.magna.controltower/.DeviceAdminReceiver

# Uygulamayı kiosk olarak pin'le
adb shell am start -a android.app.action.SET_LOCK_TASK_PACKAGES \
  -e packages com.magna.controltower

# Kiosk scriptini çalıştır
chmod +x setup_kiosk.sh
./setup_kiosk.sh
```

### 9.3 AndroidManifest.xml Kiosk Ayarları

```xml
<manifest>
    <!-- Kiosk modu için gerekli izinler -->
    <uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED"/>
    <uses-permission android:name="android.permission.REQUEST_INSTALL_PACKAGES"/>
    
    <application>
        <!-- Device Admin Receiver -->
        <receiver
            android:name=".DeviceAdminReceiver"
            android:exported="true"
            android:permission="android.permission.BIND_DEVICE_ADMIN">
            <meta-data
                android:name="android.app.device_admin"
                android:resource="@xml/device_admin_policies"/>
            <intent-filter>
                <action android:name="android.app.action.DEVICE_ADMIN_ENABLED"/>
            </intent-filter>
        </receiver>
        
        <!-- Sistem başlangıcında otomatik başlat -->
        <receiver android:name=".BootReceiver">
            <intent-filter>
                <action android:name="android.intent.action.BOOT_COMPLETED"/>
            </intent-filter>
        </receiver>
    </application>
</manifest>
```

---

## 10. Derleme ve Dağıtım

### 10.1 Debug APK

```bash
# Android Studio'da
cd ControlTower
./gradlew assembleDebug
# Çıktı: app/build/outputs/apk/debug/app-debug.apk
```

### 10.2 Release APK

```bash
# 1. KeyStore oluştur (ilk seferinde)
keytool -genkey -v -keystore magna-harmony.keystore \
  -alias magna -keyalg RSA -keysize 2048 -validity 10000

# 2. Release APK derle
./gradlew assembleRelease \
  -Pandroid.injected.signing.store.file=magna-harmony.keystore \
  -Pandroid.injected.signing.store.password=KEYSTORE_SIFRE \
  -Pandroid.injected.signing.key.alias=magna \
  -Pandroid.injected.signing.key.password=KEY_SIFRE

# Çıktı: app/build/outputs/apk/release/app-release.apk
```

### 10.3 Toplu Cihaz Dağıtımı

```bash
# ADB ile tüm bağlı cihazlara yükle
for device in $(adb devices | grep -v "List of devices" | awk '{print $1}'); do
    echo "Installing on $device..."
    adb -s $device install -r app/build/outputs/apk/release/app-release.apk
done
```

---

## 11. API Hata Yönetimi

### 11.1 Standart Hata Yanıt Formatı

```json
{
    "error": "Kullanıcıya gösterilecek mesaj (Türkçe)",
    "message": "Teknik detay",
    "retryable": true
}
```

### 11.2 HTTP Durum Kodlarına Göre Davranış

```java
private void handleApiError(Response<?> response) {
    ApiError error = parseError(response);
    
    switch (response.code()) {
        case 400:
            // Doğrulama hatası — kullanıcı düzeltebilir
            showError(error.getError());
            if (error.isRetryable()) showRetryButton();
            break;
            
        case 401:
            // Oturum sona erdi — login'e yönlendir
            sessionManager.clearSession();
            handleUnauthorized();
            break;
            
        case 404:
            // Dolly bulunamadı
            showError("Dolly sistemde bulunamadı: " + error.getError());
            break;
            
        case 409:
            // Zaten taranmış
            showWarning("Bu dolly zaten bu oturumda taranmış");
            break;
            
        case 500:
            // Sistem hatası
            showError("Sistem hatası: " + error.getError());
            if (error.isRetryable()) {
                showRetryDialog(error.getError());
            }
            break;
            
        default:
            showError("Bilinmeyen hata (HTTP " + response.code() + ")");
    }
}

private ApiError parseError(Response<?> response) {
    try {
        Gson gson = new Gson();
        return gson.fromJson(
            response.errorBody().string(),
            ApiError.class
        );
    } catch (Exception e) {
        ApiError fallback = new ApiError();
        fallback.setError("Bilinmeyen hata");
        return fallback;
    }
}
```

### 11.3 Ağ Hatası Yönetimi

```java
@Override
public void onFailure(Call<?> call, Throwable t) {
    if (t instanceof java.net.SocketTimeoutException) {
        showError("Sunucu yanıt vermiyor. İnternet bağlantınızı kontrol edin.");
    } else if (t instanceof java.net.UnknownHostException) {
        showError("Sunucuya ulaşılamıyor. Wi-Fi bağlantınızı kontrol edin.");
    } else if (t instanceof java.net.ConnectException) {
        showError("Bağlantı reddedildi. IT ile iletişime geçin.");
    } else {
        showError("Ağ hatası: " + t.getMessage());
    }
}
```
