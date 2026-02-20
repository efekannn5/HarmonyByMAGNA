# 📚 Android Entegrasyon Dokümanları

Bu klasörde Android Forklift uygulaması için hazırlanmış 3 adet kapsamlı doküman bulunmaktadır.

## 📄 Doküman Listesi

### 1. **ANDROID_COMPLETE_INTEGRATION_GUIDE.md** (Ana Doküman - 200+ sayfa)
**Kim için:** Android geliştiriciler (detaylı rehber)

**İçerik:**
- ✅ Sistem mimarisi ve iş akışı
- ✅ Tüm API endpoint'leri (Login, Scan, Complete, vb.)
- ✅ Request/Response örnekleri
- ✅ Kotlin data class'ları
- ✅ Ekran tasarımları ve UI gereksinimleri
- ✅ Hata yönetimi ve retry logic
- ✅ Örnek Kotlin kodları (Retrofit, ViewModel, Compose)
- ✅ Quick Start kılavuzu

**Ne zaman kullanılır:**
- İlk kez projeye başlarken
- API'leri detaylı anlamak için
- UI tasarımlarını görmek için

---

### 2. **ANDROID_QUICK_REFERENCE_GUIDE.md** (Hızlı Referans - 10 sayfa)
**Kim için:** Deneyimli Android geliştiriciler (özet rehber)

**İçerik:**
- ✅ API endpoint'leri (özet)
- ✅ Request/Response formatları (sadece örnekler)
- ✅ Hata kodları tablosu
- ✅ Kotlin data model'leri
- ✅ Retrofit interface örneği
- ✅ Test credentials

**Ne zaman kullanılır:**
- Hızlıca bir endpoint'e bakmak için
- API formatını hatırlamak için
- Development sırasında hızlı referans

---

### 3. **PART_GROUP_TECHNICAL_SUMMARY.md** (Teknik Özet - 20 sayfa)
**Kim için:** Tüm ekip (backend, Android, PM)

**İçerik:**
- ✅ Veri modeli hiyerarşisi (DollyGroup → DollyEOLInfo → DollySubmissionHold)
- ✅ İş akışı ve database değişiklikleri (adım adım)
- ✅ PartNumber ve Grup ilişkisi açıklaması
- ✅ VIN breakdown mantığı
- ✅ Status değişiklikleri (scanned → loading_completed → completed)
- ✅ Android ekibi için kritik noktalar
- ✅ Backend developer'a sorulacak sorular listesi

**Ne zaman kullanılır:**
- Part ve grup yapısını anlamak için
- VIN breakdown mantığını kavramak için
- Status değişikliklerini takip etmek için
- Backend-Android koordinasyonu için

---

## 🎯 Hangi Dokümanı Okumalıyım?

### Senaryo 1: Yeni Android Geliştiricisi
```
1. ANDROID_COMPLETE_INTEGRATION_GUIDE.md (Baştan sona oku)
2. PART_GROUP_TECHNICAL_SUMMARY.md (Part/Grup mantığını anla)
3. ANDROID_QUICK_REFERENCE_GUIDE.md (Geliştirirken yanında tut)
```

### Senaryo 2: Deneyimli Android Geliştiricisi
```
1. ANDROID_QUICK_REFERENCE_GUIDE.md (Hızlıca API'leri anla)
2. PART_GROUP_TECHNICAL_SUMMARY.md (İş mantığını kavra)
3. ANDROID_COMPLETE_INTEGRATION_GUIDE.md (Sadece detay gereken yerlere bak)
```

### Senaryo 3: Backend Developer
```
1. PART_GROUP_TECHNICAL_SUMMARY.md (Veri akışını kontrol et)
2. ANDROID_COMPLETE_INTEGRATION_GUIDE.md (Android ekibinin ne beklediğini anla)
```

### Senaryo 4: Project Manager / QA
```
1. PART_GROUP_TECHNICAL_SUMMARY.md (İş akışını anla)
2. ANDROID_QUICK_REFERENCE_GUIDE.md (Ekran akışını görüntüle)
```

---

## 🚀 Quick Start (5 Dakikada Başla)

### 1. API Test Et
```bash
# Login Test
curl -X POST http://10.25.1.174:8181/api/forklift/login \
  -H "Content-Type: application/json" \
  -d '{"operatorBarcode":"EMP12345"}'

# Response:
# {
#   "success": true,
#   "sessionToken": "eyJhbGc...",
#   "operatorName": "Operator_EMP12345"
# }
```

### 2. Retrofit Setup (Kotlin)
```kotlin
// RetrofitClient.kt
object RetrofitClient {
    private const val BASE_URL = "http://10.25.1.174:8181/api/"
    
    val api: ForkliftApi by lazy {
        Retrofit.Builder()
            .baseUrl(BASE_URL)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(ForkliftApi::class.java)
    }
}

// İlk API çağrısı
suspend fun login(barcode: String) {
    val response = RetrofitClient.api.login(
        LoginRequest(operatorBarcode = barcode)
    )
    if (response.isSuccessful) {
        val token = response.body()?.sessionToken
        // Token'ı sakla ve kullan
    }
}
```

### 3. İlk Ekran: Login
```kotlin
@Composable
fun LoginScreen() {
    var barcode by remember { mutableStateOf("") }
    
    Column {
        TextField(
            value = barcode,
            onValueChange = { barcode = it },
            label = { Text("Operatör Barkodu") }
        )
        
        Button(onClick = { 
            // Login işlemi
            viewModel.login(barcode)
        }) {
            Text("Giriş Yap")
        }
    }
}
```

---

## 📊 Ekran Akış Diyagramı

```
┌─────────────────────────────────────────────────────────────┐
│                       LOGIN EKRANI                          │
│                  (Barkod Okut / Manuel Gir)                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                       ANA MENÜ                              │
│                                                             │
│   ┌────────────────┐  ┌────────────────┐  ┌─────────────┐ │
│   │ Dolly Yükleme  │  │ Manuel Toplama │  │   Geçmiş    │ │
│   └───────┬────────┘  └───────┬────────┘  └─────────────┘ │
└───────────┼───────────────────┼────────────────────────────┘
            │                   │
            ▼                   ▼
    ┌───────────────┐   ┌───────────────┐
    │ DOLLY YÜKLEME │   │ GRUP SEÇİMİ   │
    │               │   │               │
    │ 1. Tara       │   │ V710-MR-EOL   │
    │ 2. Tara       │   │ V720-FR-EOL   │
    │ 3. Tara       │   │ ...           │
    │               │   └───────┬───────┘
    │ [Tamamla]     │           │
    └───────────────┘           ▼
                        ┌───────────────┐
                        │ DOLLY LİSTESİ │
                        │               │
                        │ [ ] 5170427   │
                        │ [✓] 5170428   │
                        │ [ ] 5170429   │
                        │               │
                        │ [Tara] [Çıkar]│
                        └───────────────┘
```

---

## 🔧 Test Bilgileri

### Test Sunucusu
```
Base URL: http://10.25.1.174:8181/api
```

### Test Credentials
```
Operatör Barkodu: EMP12345
Test Dolly: 5170427
Test Barkod: BARCODE123
Test Grup: V710-MR-EOL
```

### Test Senaryoları

#### ✅ Senaryo 1: Normal Dolly Yükleme
```
1. Login (EMP12345)
2. POST /forklift/scan → dollyNo: 5170427
3. POST /forklift/scan → dollyNo: 5170428
4. POST /forklift/scan → dollyNo: 5170429
5. POST /forklift/complete-loading → session tamamla
```

#### ✅ Senaryo 2: Dolly Çıkar (LIFO)
```
1. POST /forklift/scan → dollyNo: 5170427
2. POST /forklift/scan → dollyNo: 5170428
3. POST /forklift/remove-last → dollyNo: 5170428 (son)
4. POST /forklift/scan → dollyNo: 5170429 (yeni)
```

#### ✅ Senaryo 3: Manuel Toplama (Grup Bazlı)
```
1. GET /manual-collection/groups → Grup listesi (EOL'ler dahil)
2. Kullanıcı grup seçer ve istediği EOL'ü seçer
3. GET /manual-collection/groups/2/eols/11 → V710-LLS-EOL dolly'leri
4. POST /manual-collection/scan → barcode: 1062037
5. Kullanıcı başka EOL'e geçer (aynı grup içinde)
6. GET /manual-collection/groups/2/eols/26 → V710-MR-EOL dolly'leri
7. POST /manual-collection/scan → barcode: 1062054
8. (Web operatör tamamlar)
```

**Not:** Aynı grup içinde EOL'ler arasında serbest geçiş yapılabilir, sıralama zorunlu değil.

---

## 🐛 Sık Karşılaşılan Hatalar ve Çözümleri

### Hata 1: "Operatör barkodu gerekli" (400)
**Sebep:** Login request'te `operatorBarcode` eksik  
**Çözüm:** Request body'de mutlaka `operatorBarcode` gönder

### Hata 2: "Oturum geçersiz veya süresi dolmuş" (401)
**Sebep:** Token expire olmuş (8 saat)  
**Çözüm:** Kullanıcıyı login ekranına yönlendir, yeni token al

### Hata 3: "Bu dolly zaten taranmış" (400)
**Sebep:** Aynı dolly 2. kez taranmış  
**Çözüm:** Kullanıcıya bildir, başka dolly taratır

### Hata 4: "dollyNo is required" (400)
**Sebep:** Scan request'te `dollyNo` eksik  
**Çözüm:** Barkod okuyucu düzgün çalışmıyor, manuel giriş dene

### Hata 5: "Bağlantı hatası" (Network Error)
**Sebep:** Sunucuya erişim yok  
**Çözüm:** İnternet bağlantısını kontrol et, retry göster

---

## 📞 İletişim ve Destek

### Backend Developer
- **Server:** 10.25.1.174:8181
- **Logs:** `/home/sua_it_ai/controltower/HarmonyEcoSystem/logs/`
- **Service:** `sudo systemctl status harmonyecosystem.service`

### Dokümantasyon Güncellemeleri
- **Versiyon:** 1.0
- **Tarih:** 14 Aralık 2025
- **Son Güncelleme:** Backend kodları analiz edilerek hazırlandı

### Sorularınız İçin
1. Backend developer ile koordinasyon
2. Bu dokümanları referans göster
3. API test sonuçlarını paylaş

---

## ✅ Checklist: Projeye Başlamadan Önce

### Android Ekibi
- [ ] Tüm dokümanları okudum
- [ ] API'leri Postman/curl ile test ettim
- [ ] Retrofit setup'ı tamamladım
- [ ] Token management'ı anladım
- [ ] VIN breakdown mantığını kavradım
- [ ] Ekran tasarımlarını inceledim
- [ ] Error handling pattern'ini anladım
- [ ] Test credentials'ları aldım

### Backend Developer
- [ ] API'ler test edildi ve çalışıyor
- [ ] Authentication sistemi aktif
- [ ] Database bağlantısı sağlam
- [ ] CEVA entegrasyonu hazır
- [ ] Logging sistemi aktif
- [ ] Android ekibiyle koordinasyon yapıldı

---

## 🎯 Son Notlar

Bu dokümanlar, backend kodları detaylıca analiz edilerek hazırlanmıştır. Tüm API endpoint'leri, veri modelleri ve iş akışları gerçek kodlardan alınmıştır.

**Önemli:** 
- API'ler production'da HTTP kullanıyor. HTTPS'e geçişte sadece URL değişecek.
- Token 8 saat geçerli. Expire kontrolü mutlaka yapılmalı.
- VIN breakdown (\\n ile ayrılmış) parse edilmeli.
- LIFO (Last In First Out) mantığı korunmalı.
- Error handling'de `retryable` flag'ine dikkat edilmeli.

**Başarılar!** 🚀
