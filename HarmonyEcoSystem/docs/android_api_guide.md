# 📱 Android Forklift API Kullanım Rehberi

## 🔄 İş Akışı

### 1️⃣ Yükleme Oturumu Başlat
Forklift operatör uygulamayı açtığında otomatik olarak bir `loadingSessionId` üretilir:

```javascript
const loadingSessionId = `LOAD_${Date.now()}_${operatorName}`;
// Örnek: LOAD_20251126_143052_MEHMET
```

### 2️⃣ Dolly Barkod Okutma (SIRAYLA!)

**Endpoint:** `POST /api/forklift/scan`

**Request Body:**
```json
{
  "dollyNo": "DL-5170427",
  "forkliftUser": "Mehmet Yılmaz",
  "loadingSessionId": "LOAD_20251126_143052_MEHMET",
  "barcode": "BARCODE123456"  // Opsiyonel - doğrulama için
}
```

**Response (201 Created):**
```json
{
  "id": 123,
  "dolly_no": "DL-5170427",
  "vin_no": "3FA6P0LU6FR100001",
  "status": "scanned",
  "terminal_user": "Mehmet Yılmaz",
  "scanned_at": "2025-11-26T14:30:52Z",
  "scan_order": 1,  // İLK DOLLY
  "customer_referans": "FORD-EXPORT",
  "eol_name": "EOL-A1"
}
```

**Hata Durumları:**
```json
// Dolly bulunamadı
{
  "message": "Dolly DL-999999 bulunamadı"
}

// Barkod eşleşmedi
{
  "message": "Barkod eşleşmedi"
}
```

### 3️⃣ Birden Fazla Dolly Okut

İkinci dolly:
```json
POST /api/forklift/scan
{
  "dollyNo": "DL-5170428",
  "forkliftUser": "Mehmet Yılmaz",
  "loadingSessionId": "LOAD_20251126_143052_MEHMET"
}
```

Response:
```json
{
  "scan_order": 2,  // İKİNCİ DOLLY
  ...
}
```

Üçüncü dolly:
```json
{
  "scan_order": 3,  // ÜÇÜNCÜ DOLLY
  ...
}
```

### 4️⃣ Yükleme Tamamlandı

TIR'a tüm dolly'ler yüklendi, operatör "Yükleme Tamamlandı" butonuna basar:

**Endpoint:** `POST /api/forklift/complete-loading`

**Request Body:**
```json
{
  "loadingSessionId": "LOAD_20251126_143052_MEHMET",
  "forkliftUser": "Mehmet Yılmaz"
}
```

**Response (200 OK):**
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
    },
    // ... 15 dolly toplam
  ]
}
```

### 5️⃣ Aktif Oturumları Görüntüle (Opsiyonel)

**Endpoint:** `GET /api/forklift/sessions?status=scanned`

```json
[
  {
    "loadingSessionId": "LOAD_20251126_143052_MEHMET",
    "status": "scanned",
    "forkliftUser": "Mehmet Yılmaz",
    "dollyCount": 8,
    "firstScanAt": "2025-11-26T14:30:52Z",
    "completedAt": null
  }
]
```

---

## 🎯 Android Uygulama Örnek Akışı

### Kotlin/Java Örneği

```kotlin
class ForkliftScanActivity : AppCompatActivity() {
    private var loadingSessionId: String? = null
    private var scanCount = 0
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // Yeni oturum başlat
        val timestamp = SimpleDateFormat("yyyyMMdd_HHmmss").format(Date())
        val operatorName = getOperatorName() // SharedPreferences'den
        loadingSessionId = "LOAD_${timestamp}_${operatorName}"
        
        // Barkod okuyucuyu başlat
        startBarcodeScanner()
    }
    
    fun onBarcodeScanned(dollyNo: String) {
        // API'ye gönder
        scanDolly(dollyNo)
    }
    
    private fun scanDolly(dollyNo: String) {
        val request = JSONObject().apply {
            put("dollyNo", dollyNo)
            put("forkliftUser", getOperatorName())
            put("loadingSessionId", loadingSessionId)
        }
        
        apiService.post("/api/forklift/scan", request) { response ->
            scanCount++
            showToast("Dolly ${scanCount} yüklendi: ${dollyNo}")
            updateScanList(response)
        }
    }
    
    fun onCompleteButtonClicked() {
        val request = JSONObject().apply {
            put("loadingSessionId", loadingSessionId)
            put("forkliftUser", getOperatorName())
        }
        
        apiService.post("/api/forklift/complete-loading", request) { response ->
            showSuccess("${response.getInt("dollyCount")} dolly başarıyla tamamlandı!")
            navigateToHome()
        }
    }
}
```

### React Native Örneği

```javascript
import { Camera } from 'expo-camera';

const ForkliftScanScreen = () => {
  const [sessionId, setSessionId] = useState(null);
  const [scannedDollys, setScannedDollys] = useState([]);
  
  useEffect(() => {
    // Oturum başlat
    const timestamp = new Date().toISOString().replace(/[-:]/g, '').slice(0, 15);
    const operator = await AsyncStorage.getItem('operatorName');
    setSessionId(`LOAD_${timestamp}_${operator}`);
  }, []);
  
  const handleBarcodeScan = async ({ data }) => {
    try {
      const response = await fetch('http://10.25.1.174:8181/api/forklift/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dollyNo: data,
          forkliftUser: operatorName,
          loadingSessionId: sessionId
        })
      });
      
      const result = await response.json();
      setScannedDollys([...scannedDollys, result]);
      Alert.alert('Başarılı', `Sıra ${result.scan_order}: ${result.dolly_no}`);
    } catch (error) {
      Alert.alert('Hata', error.message);
    }
  };
  
  const completeLoading = async () => {
    const response = await fetch('http://10.25.1.174:8181/api/forklift/complete-loading', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        loadingSessionId: sessionId,
        forkliftUser: operatorName
      })
    });
    
    const result = await response.json();
    Alert.alert('Tamamlandı', `${result.dollyCount} dolly yüklendi`);
    navigation.navigate('Home');
  };
  
  return (
    <View>
      <Camera onBarCodeScanned={handleBarcodeScan} />
      <Text>Okutulan: {scannedDollys.length} dolly</Text>
      <Button title="Yükleme Tamamlandı" onPress={completeLoading} />
    </View>
  );
};
```

---

## 🖥️ Web Operatör Sonrası

Forklift yükleme tamamladıktan sonra:

1. **Web Dashboard:** `/operator/shipments` sayfası açılır
2. **Operatör görür:** Bekleyen sevkiyatlar listesi
3. **Operatör girer:**
   - Sefer Numarası (örn: SFR2025001)
   - Plaka No (örn: 34 ABC 123)
   - ASN / İrsaliye / Her İkisi
4. **Submit butonuna basar**
5. **Sistem otomatik:**
   - SeferDollyEOL tablosuna kayıt atar
   - ASNDate/IrsaliyeDate set eder
   - Lifecycle COMPLETED_* durumuna geçer

---

## ⚠️ Önemli Notlar

1. **Sıra Önemli:** Dolly'ler TIR'a yüklendikleri sırayla okutulmalı (`scanOrder` otomatik artar)
2. **Session ID Unique Olmalı:** Her yükleme için farklı session ID kullan
3. **Network Error Handling:** Bağlantı koparsa retry mekanizması ekle
4. **Offline Mode:** Okutulan dolly'leri cache'le, sonra sync et

---

## 🔧 Test Ortamı

**Base URL:** `http://10.25.1.174:8181`

**Test Kullanıcısı:**
- Username: `forklift_test`
- Şifre: `test123`

**Test Dolly'ler:**
- `DL-5170427`
- `DL-5170428`
- `DL-5170429`

**cURL Test:**
```bash
# 1. Dolly okut
curl -X POST http://10.25.1.174:8181/api/forklift/scan \
  -H "Content-Type: application/json" \
  -d '{
    "dollyNo": "DL-5170427",
    "forkliftUser": "Test User",
    "loadingSessionId": "LOAD_TEST_001"
  }'

# 2. Yükleme tamamla
curl -X POST http://10.25.1.174:8181/api/forklift/complete-loading \
  -H "Content-Type: application/json" \
  -d '{
    "loadingSessionId": "LOAD_TEST_001",
    "forkliftUser": "Test User"
  }'
```
