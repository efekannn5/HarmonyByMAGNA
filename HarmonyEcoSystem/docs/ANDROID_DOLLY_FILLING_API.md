# 📱 Android - Dolly Dolma Durumu API Dokümantasyonu

## 🎯 Genel Bakış

Bu API, her EOL grubundaki dolly'lerin dolma durumunu anlık olarak gösterir. Android uygulamanızda dolly dolum durumunu ekranda göstermek için bu endpoint'i kullanabilirsiniz.

---

## 🌐 API Endpoint

```
GET http://10.25.64.181:8181/api/yuzde
```

### Kimlik Doğrulama
❌ **Gerekmez** - Public endpoint

### HTTP Method
`GET`

### Content-Type
`application/json`

---

## 📊 Response Format

### Başarılı Response (200 OK)

```json
{
    "success": true,
    "timestamp": "2025-12-25T13:30:00.123456",
    "eol_groups": [
        {
            "eol_name": "V710-MR-EOL",
            "current_dolly": 1062671,
            "current_vin_count": 8,
            "max_vin_capacity": 16,
            "vin_display": "8/16",
            "pending_dollys": 5,
            "total_dollys_scanned": 63,
            "remaining_vins": 8,
            "status": "filling",
            "message": "Dolmasına 8 VIN kaldı",
            "last_vin": "TANXTL71675",
            "last_insert_time": "2025-12-25T07:50:22.260000",
            "can_scan": true
        },
        {
            "eol_name": "V710-LLS-EOL",
            "current_dolly": 1062663,
            "current_vin_count": 11,
            "max_vin_capacity": 14,
            "vin_display": "11/14",
            "pending_dollys": 2,
            "total_dollys_scanned": 37,
            "remaining_vins": 3,
            "status": "filling",
            "message": "Dolmasına 3 VIN kaldı",
            "last_vin": "TANXSE70301",
            "last_insert_time": "2025-12-25T12:47:33.713333",
            "can_scan": true
        }
    ],
    "summary": {
        "total_active_dollys": 2,
        "filling_dollys": 2,
        "full_dollys": 0,
        "empty_dollys": 0
    }
}
```

---

## 📋 Response Field Açıklamaları

### EOL Group Object (`eol_groups[]`)

| Alan | Tip | Açıklama | Örnek |
|------|-----|----------|-------|
| `eol_name` | String | EOL istasyon adı | "V710-MR-EOL" |
| `current_dolly` | Integer | Şu anda doldurulan dolly numarası | 1062671 |
| `current_vin_count` | Integer | **Dolly'deki FARKLI VIN sayısı** (DISTINCT) | 8 |
| `max_vin_capacity` | Integer | Bu EOL grubunda bir dolly'ye max kaç VIN sığar | 16 |
| `vin_display` | String | **Görsel format: "8/16"** | "8/16" |
| `pending_dollys` | Integer | **Bekleyen dolly sayısı** (DollySubmissionHold'da) | 5 |
| `total_dollys_scanned` | Integer | Bu EOL grubunda şimdiye kadar taranan dolly sayısı | 63 |
| `remaining_vins` | Integer | Dolly'nin dolması için gereken VIN sayısı | 8 |
| `status` | String | Dolma durumu: "empty", "filling", "almost_full", "full" | "filling" |
| `message` | String | Kullanıcıya gösterilecek mesaj | "Dolmasına 8 VIN kaldı" |
| `last_vin` | String | Son eklenen VIN numarası | "TANXTL71675" |
| `last_insert_time` | String (ISO 8601) | Son VIN eklenme zamanı | "2025-12-25T07:50:22.260000" |
| `can_scan` | Boolean | Tarama yapılabilir mi? (Doluysa false) | true |

### Summary Object

| Alan | Tip | Açıklama |
|------|-----|----------|
| `total_active_dollys` | Integer | Toplam aktif dolly sayısı |
| `filling_dollys` | Integer | Doluyor durumundaki dolly sayısı |
| `full_dollys` | Integer | Dolu dolly sayısı |
| `empty_dollys` | Integer | Boş dolly sayısı |

---

## 🔴 ÖNEMLI: DISTINCT VIN Hesaplama

⚠️ **Dikkat:** Sistemde bazen aynı VIN'den birden fazla kayıt bulunabilir. API bu durumu otomatik olarak halleder:

```sql
COUNT(DISTINCT VinNo)  -- Aynı VIN birden fazla olsa bile 1 tane sayar
```

### Örnek:
```
DollyEOLInfo tablosunda:
- VIN123 (2 kayıt)
- VIN456 (1 kayıt)
- VIN789 (1 kayıt)

API Response:
current_vin_count: 3  ✅ (Doğru - DISTINCT sayıldı)
                     ❌ 4 değil!
```

---

## 🎨 Status Durumları

| Status | Koşul | UI Rengi Önerisi | İkon |
|--------|-------|------------------|------|
| `empty` | VIN sayısı = 0 | Gri | ⚪ |
| `filling` | 0 < VIN < 90% | Yeşil | 🟢 |
| `almost_full` | 90% ≤ VIN < 100% | Turuncu | 🟠 |
| `full` | VIN ≥ 100% | Kırmızı | 🔴 |

---

## 📱 Kotlin/Android Kullanımı

### 1. Data Class Tanımları

```kotlin
data class DollyFillingResponse(
    val success: Boolean,
    val timestamp: String,
    val eol_groups: List<EolGroup>,
    val summary: Summary
)

data class EolGroup(
    val eol_name: String,
    val current_dolly: Int,
    val current_vin_count: Int,
    val max_vin_capacity: Int,
    val vin_display: String,  // "8/16" formatı
    val pending_dollys: Int,
    val total_dollys_scanned: Int,
    val remaining_vins: Int,
    val status: String,  // "filling", "full", vb.
    val message: String,
    val last_vin: String?,
    val last_insert_time: String?,
    val can_scan: Boolean
)

data class Summary(
    val total_active_dollys: Int,
    val filling_dollys: Int,
    val full_dollys: Int,
    val empty_dollys: Int
)
```

### 2. Retrofit Interface

```kotlin
interface HarmonyApiService {
    @GET("api/yuzde")
    suspend fun getDollyFillingStatus(): Response<DollyFillingResponse>
}
```

### 3. API Çağrısı (Coroutine)

```kotlin
class DollyFillingViewModel : ViewModel() {
    
    private val _fillingStatus = MutableLiveData<DollyFillingResponse>()
    val fillingStatus: LiveData<DollyFillingResponse> = _fillingStatus
    
    private val _isLoading = MutableLiveData<Boolean>()
    val isLoading: LiveData<Boolean> = _isLoading
    
    fun loadFillingStatus() {
        viewModelScope.launch {
            _isLoading.value = true
            try {
                val response = apiService.getDollyFillingStatus()
                if (response.isSuccessful && response.body()?.success == true) {
                    _fillingStatus.value = response.body()
                } else {
                    // Hata durumu
                    Log.e("API", "Error: ${response.code()}")
                }
            } catch (e: Exception) {
                Log.e("API", "Exception: ${e.message}")
            } finally {
                _isLoading.value = false
            }
        }
    }
}
```

### 4. UI'da Gösterim (RecyclerView Adapter)

```kotlin
class EolGroupAdapter : RecyclerView.Adapter<EolGroupAdapter.ViewHolder>() {
    
    private var eolGroups = listOf<EolGroup>()
    
    class ViewHolder(view: View) : RecyclerView.ViewHolder(view) {
        val eolNameText: TextView = view.findViewById(R.id.tvEolName)
        val dollyNoText: TextView = view.findViewById(R.id.tvDollyNo)
        val vinDisplayText: TextView = view.findViewById(R.id.tvVinDisplay)
        val statusIcon: ImageView = view.findViewById(R.id.ivStatusIcon)
        val messageText: TextView = view.findViewById(R.id.tvMessage)
        val pendingText: TextView = view.findViewById(R.id.tvPending)
        val progressBar: ProgressBar = view.findViewById(R.id.progressBar)
        val scanButton: Button = view.findViewById(R.id.btnScan)
    }
    
    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        val eol = eolGroups[position]
        
        holder.eolNameText.text = eol.eol_name
        holder.dollyNoText.text = "Dolly: ${eol.current_dolly}"
        holder.vinDisplayText.text = eol.vin_display  // "8/16"
        holder.messageText.text = eol.message
        holder.pendingText.text = "Bekleyen: ${eol.pending_dollys}"
        
        // Progress bar
        val percentage = (eol.current_vin_count.toFloat() / eol.max_vin_capacity * 100).toInt()
        holder.progressBar.progress = percentage
        
        // Status icon ve renk
        when (eol.status) {
            "empty" -> {
                holder.statusIcon.setImageResource(R.drawable.ic_circle_white)
                holder.progressBar.progressTintList = ColorStateList.valueOf(Color.GRAY)
            }
            "filling" -> {
                holder.statusIcon.setImageResource(R.drawable.ic_circle_green)
                holder.progressBar.progressTintList = ColorStateList.valueOf(Color.GREEN)
            }
            "almost_full" -> {
                holder.statusIcon.setImageResource(R.drawable.ic_circle_orange)
                holder.progressBar.progressTintList = ColorStateList.valueOf(Color.parseColor("#FF9800"))
            }
            "full" -> {
                holder.statusIcon.setImageResource(R.drawable.ic_circle_red)
                holder.progressBar.progressTintList = ColorStateList.valueOf(Color.RED)
            }
        }
        
        // Scan button durumu
        holder.scanButton.isEnabled = eol.can_scan
        holder.scanButton.alpha = if (eol.can_scan) 1.0f else 0.5f
    }
    
    fun updateData(newData: List<EolGroup>) {
        eolGroups = newData
        notifyDataSetChanged()
    }
    
    override fun getItemCount() = eolGroups.size
}
```

### 5. Activity/Fragment'te Kullanım

```kotlin
class DollyFillingActivity : AppCompatActivity() {
    
    private lateinit var viewModel: DollyFillingViewModel
    private lateinit var adapter: EolGroupAdapter
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_dolly_filling)
        
        viewModel = ViewModelProvider(this)[DollyFillingViewModel::class.java]
        adapter = EolGroupAdapter()
        
        recyclerView.adapter = adapter
        recyclerView.layoutManager = LinearLayoutManager(this)
        
        // Observe data
        viewModel.fillingStatus.observe(this) { response ->
            adapter.updateData(response.eol_groups)
            updateSummary(response.summary)
        }
        
        viewModel.isLoading.observe(this) { isLoading ->
            progressBar.visibility = if (isLoading) View.VISIBLE else View.GONE
        }
        
        // İlk yükleme
        viewModel.loadFillingStatus()
        
        // Yenile butonu
        btnRefresh.setOnClickListener {
            viewModel.loadFillingStatus()
        }
        
        // Otomatik yenileme (10 saniyede bir)
        startAutoRefresh()
    }
    
    private fun startAutoRefresh() {
        lifecycleScope.launch {
            while (isActive) {
                delay(10000)  // 10 saniye
                viewModel.loadFillingStatus()
            }
        }
    }
    
    private fun updateSummary(summary: Summary) {
        tvTotalDollys.text = "Toplam: ${summary.total_active_dollys}"
        tvFillingDollys.text = "Doluyor: ${summary.filling_dollys}"
        tvFullDollys.text = "Dolu: ${summary.full_dollys}"
        tvEmptyDollys.text = "Boş: ${summary.empty_dollys}"
    }
}
```

---

## 🎨 UI Layout Önerisi

```xml
<!-- item_eol_group.xml -->
<androidx.cardview.widget.CardView
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:layout_margin="8dp"
    app:cardCornerRadius="12dp"
    app:cardElevation="4dp">
    
    <LinearLayout
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:orientation="vertical"
        android:padding="16dp">
        
        <!-- Header -->
        <LinearLayout
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:orientation="horizontal"
            android:gravity="center_vertical">
            
            <ImageView
                android:id="@+id/ivStatusIcon"
                android:layout_width="48dp"
                android:layout_height="48dp"
                android:src="@drawable/ic_circle_green"/>
            
            <TextView
                android:id="@+id/tvEolName"
                android:layout_width="0dp"
                android:layout_height="wrap_content"
                android:layout_weight="1"
                android:layout_marginStart="12dp"
                android:text="V710-MR-EOL"
                android:textSize="20sp"
                android:textStyle="bold"/>
        </LinearLayout>
        
        <!-- Dolly Info -->
        <TextView
            android:id="@+id/tvDollyNo"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:layout_marginTop="12dp"
            android:text="Dolly: 1062671"
            android:textSize="16sp"/>
        
        <!-- VIN Display -->
        <TextView
            android:id="@+id/tvVinDisplay"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:layout_marginTop="8dp"
            android:text="8/16"
            android:textSize="24sp"
            android:textStyle="bold"
            android:textColor="@color/primary"/>
        
        <!-- Progress Bar -->
        <ProgressBar
            android:id="@+id/progressBar"
            android:layout_width="match_parent"
            android:layout_height="24dp"
            android:layout_marginTop="8dp"
            style="@style/Widget.AppCompat.ProgressBar.Horizontal"
            android:max="100"
            android:progress="50"/>
        
        <!-- Message -->
        <TextView
            android:id="@+id/tvMessage"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:layout_marginTop="8dp"
            android:text="Dolmasına 8 VIN kaldı"
            android:textSize="14sp"
            android:textColor="@color/text_secondary"/>
        
        <!-- Pending Dollys -->
        <TextView
            android:id="@+id/tvPending"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:layout_marginTop="4dp"
            android:text="Bekleyen: 5"
            android:textSize="14sp"/>
        
        <!-- Scan Button -->
        <Button
            android:id="@+id/btnScan"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:layout_marginTop="12dp"
            android:text="Tarama Yap"
            android:enabled="true"/>
            
    </LinearLayout>
</androidx.cardview.widget.CardView>
```

---

## ⚡ Önemli Notlar

### 1. DISTINCT VIN Mantığı
- API, **aynı VIN'den birden fazla kayıt** varsa otomatik olarak **1 tane sayar**
- `COUNT(DISTINCT VinNo)` kullanılır
- Android tarafında ekstra bir işlem yapmanıza gerek yok

### 2. Otomatik Yenileme
- **10 saniyede bir** API'yi çağırmanız önerilir
- Coroutine + delay kullanabilirsiniz
- Batarya optimizasyonu için WorkManager düşünülebilir

### 3. Hata Yönetimi
```kotlin
try {
    val response = apiService.getDollyFillingStatus()
    if (response.isSuccessful) {
        // Success
    } else {
        // HTTP Error
        showError("Sunucu hatası: ${response.code()}")
    }
} catch (e: IOException) {
    // Network error
    showError("Ağ bağlantısı hatası")
} catch (e: Exception) {
    // Unknown error
    showError("Bilinmeyen hata: ${e.message}")
}
```

### 4. Performans İpuçları
- RecyclerView DiffUtil kullanın (sadece değişen itemlar güncellensin)
- Coroutine Dispatcher.IO'da API çağrısı yapın
- Cache mekanizması ekleyin (Room database)

---

## 🧪 Test

### cURL ile Test
```bash
curl -X GET http://10.25.64.181:8181/api/yuzde
```

### Postman Collection
```json
{
    "name": "Dolly Filling Status",
    "request": {
        "method": "GET",
        "url": "http://10.25.64.181:8181/api/yuzde"
    }
}
```

---

## 🆘 Sık Karşılaşılan Sorunlar

### Q: `current_vin_count` neden beklediğimden az?
**A:** API DISTINCT kullanır. Aynı VIN birden fazla kez kaydedilmişse sadece 1 sayılır.

### Q: `can_scan` false olduğunda ne yapmalıyım?
**A:** Dolly dolu demektir. Tarama butonunu disable edin ve kullanıcıya "Dolly dolu, yeni dolly başlatın" mesajı gösterin.

### Q: `pending_dollys` ne anlama geliyor?
**A:** DollySubmissionHold tablosunda bekleyen (henüz sevk edilmemiş) dolly sayısıdır.

---

## 📞 Destek

Sorun yaşarsanız backend loglarını kontrol edin:
```bash
tail -f /home/sua_it_ai/controltower/HarmonyEcoSystem/logs/app.log
```

---

**📅 Son Güncelleme:** 25 Aralık 2025  
**📝 Versiyon:** 1.0  
**👨‍💻 Hazırlayan:** HarmonyEcoSystem Team
